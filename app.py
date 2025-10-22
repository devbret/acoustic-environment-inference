import json, subprocess, tempfile, shutil, uuid, hashlib, time, itertools
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import librosa as lr
import soundfile as sf
from scipy.signal import welch, find_peaks
from scipy.stats import kurtosis

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
TARGET_SR = 16000
FRAME_MS = 30
HOP_MS = 15
VAD_THRESH_DB = None
HUM_PRESENT_SNR_DB = 6.0
HUM_TOL_HZ = 0.9
NOISE_FP_MAX_PEAKS = 8
NOISE_FP_MAX_FREQ_HZ = 2000
BAND_COSINE_EPS = 1e-9
RT60_MATCH_TAU = 0.20
MATCH_WEIGHTS = {"fingerprint": 0.40, "bands": 0.15, "ltas": 0.20, "rt60": 0.15, "hum": 0.10}
MATCH_MIN_SCORE = 0.43
MATCH_TOP_K = 50
PIPELINE_VERSION = "2.0.0-osint-upgrade"
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aiff", ".aif", ".opus"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}

def log(msg): 
    print(msg, flush=True)

def has_ffmpeg():
    try:
        subprocess.run(["ffmpeg","-version"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        return True
    except FileNotFoundError:
        return False

def ffprobe_json(path):
    try:
        r = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",str(path)],
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False)
        if r.returncode==0 and r.stdout.strip(): 
            return json.loads(r.stdout)
    except Exception: 
        pass
    return None

def extract_audio_with_ffmpeg(src,dst,sr=TARGET_SR):
    cmd=["ffmpeg","-y","-i",str(src),"-vn","-ac","1","-ar",str(sr),"-hide_banner","-loglevel","error",str(dst)]
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    return r.returncode==0 and dst.exists() and dst.stat().st_size>0

def load_mono(path,sr=TARGET_SR):
    y,_=lr.load(str(path),sr=sr,mono=True,res_type="kaiser_best")
    y=y-np.mean(y)
    return y,sr

def energy_vad(y,sr,thresh_db=None,frame_ms=FRAME_MS,hop_ms=HOP_MS):
    f=int(sr*frame_ms/1000); h=int(sr*hop_ms/1000)
    if len(y)<f: 
        return y
    frames=lr.util.frame(y,frame_length=f,hop_length=h)
    rms=np.sqrt((frames**2).mean(axis=0))
    rms_db=20*np.log10(np.maximum(rms,1e-12))
    if thresh_db is None:
        noise_floor=np.percentile(rms_db,15)
        thresh_db=noise_floor+6.0
    mask=rms_db>thresh_db
    idx=np.repeat(mask,h)
    idx=np.pad(idx,(0,max(0,len(y)-len(idx))),constant_values=mask[-1] if len(mask)>0 else False)[:len(y)]
    kept=y[idx] if idx.any() else y
    return kept if kept.size>int(0.1*len(y)) else y

def psd(y,sr,nperseg=8192,noverlap=4096):
    f,Pxx=welch(y,fs=sr,nperseg=nperseg,noverlap=noverlap,average='median',detrend='constant')
    return f,Pxx

def _quad_interp_peak(f,P,i):
    if i<=0 or i>=len(P)-1: 
        return f[i],P[i]
    a,b,c=P[i-1],P[i],P[i+1]
    p=0.5*(a-c)/(a-2*b+c+1e-15)
    f_hat=f[i]+p*(f[1]-f[0])
    P_hat=b-0.25*(a-c)*p
    return float(f_hat),float(P_hat)

def _freq_tol(f_hz): 
    return max(0.8,0.0015*f_hz)

def detect_hum(y,sr):
    f,P=psd(y,sr)
    scores={}
    for c in (50.0,60.0):
        win=(f>c-0.8)&(f<c+0.8)
        peak=P[win].max() if win.any() else 0.0
        noise_band=(f>c+5)&(f<c+30)
        noise=np.median(P[noise_band]) if noise_band.any() else np.median(P)
        snr=10*np.log10((peak+1e-15)/(noise+1e-15))
        scores[c]=snr
    fund=max(scores,key=scores.get)
    present=scores[fund]>HUM_PRESENT_SNR_DB
    harmonics=[round(fund*k,2) for k in range(2,9)]
    return {"present":bool(present),
            "fundamental_hz":float(fund) if present else None,
            "harmonics":harmonics if present else [],
            "peak_snr_db":float(scores[fund])}

def estimate_rt60(y,sr,band):
    n_fft,hop=1024,256
    S=np.abs(lr.stft(y,n_fft=n_fft,hop_length=hop))**2
    freqs=lr.fft_frequencies(sr=sr,n_fft=n_fft)
    m=(freqs>=band[0])&(freqs<=band[1])
    if not m.any(): 
        return None,0.2
    e=S[m,:].mean(axis=0)+1e-12
    th=np.percentile(e,85)
    starts=np.where((e[:-1]<th)&(e[1:]>=th))[0]
    if starts.size==0: 
        return None,0.25
    rt_list=[]; conf_list=[]
    for s in starts[:12]:
        seg=e[s:s+int(2.5*sr/hop)]
        if seg.size<32: 
            continue
        edc=np.flip(np.cumsum(np.flip(seg)))
        edc_db=10*np.log10(edc/np.max(edc))
        idx=np.where((edc_db<=-5)&(edc_db>=-35))[0]
        if idx.size<20: 
            continue
        t=(idx*hop)/sr
        ydb=edc_db[idx]
        a,b=np.polyfit(t,ydb,1)
        if a>=0: 
            continue
        rt=-60.0/a
        if 0.05<=rt<=6.0:
            ss_res=float(((ydb-(a*t+b))**2).sum())
            ss_tot=float(((ydb-ydb.mean())**2).sum()+1e-12)
            r2=1.0-ss_res/ss_tot
            conf=0.6*r2+0.4*min(1.0,(ydb.max()-ydb.min())/40.0)
            rt_list.append(rt); conf_list.append(conf)
    if not rt_list: 
        return None,0.25
    return float(np.median(rt_list)),float(np.median(conf_list))

def band_db(y,sr):
    f,P=psd(y,sr)
    bands=[(0,120),(120,250),(250,500),(500,1000),(1000,2000),(2000,4000),(4000,8000)]
    out={}
    for lo,hi in bands:
        m=(f>=lo)&(f<hi)
        p=P[m].mean() if m.any() else 1e-15
        out[f"{lo}_{hi}"]=float(10*np.log10(p+1e-15))
    return out

def heuristic_scene(bands,rt60):
    rt=rt60 if rt60 else 0.0
    low=bands.get("120_250",-99)
    mid=(bands.get("250_500",-99)+bands.get("500_1000",-99))/2
    hi=(bands.get("2000_4000",-99)+bands.get("4000_8000",-99))/2
    if rt>0.8: 
        return "large_room_hall"
    if (mid-hi)>5 and rt>0.3: 
        return "indoor_hvac_or_room"
    if (hi-mid)>6 and rt<0.25: 
        return "outdoor_birds_wind"
    if (low>-30 and mid>-28) and rt>0.4: 
        return "indoor_crowd"
    if rt<0.15: 
        return "outdoor_open"
    return "unknown"

def noise_fingerprint(y,sr,hum_fund):
    f,P=psd(y,sr)
    band=(f>20)&(f<=NOISE_FP_MAX_FREQ_HZ)
    fb=f[band]; Pb=P[band]
    if fb.size<10: 
        return []
    peaks,_=find_peaks(Pb,prominence=max(np.median(Pb)*2.0,1e-12))
    result=[]
    for i in peaks:
        freq,pwr=_quad_interp_peak(fb,Pb,i)
        if hum_fund:
            k=round(freq/hum_fund)
            if k>=1 and abs(freq-k*hum_fund)<=HUM_TOL_HZ: 
                continue
        win=(np.abs(fb-freq)<30.0)
        floor=np.median(Pb[win]) if win.any() else np.median(Pb)
        snr_db=10*np.log10((pwr+1e-15)/(floor+1e-15))
        result.append({"freq_hz":round(freq,2),"snr_db":round(float(snr_db),2)})
    result.sort(key=lambda d:d["snr_db"],reverse=True)
    return result[:NOISE_FP_MAX_PEAKS]

def ltas_stats(y,sr):
    S=np.abs(lr.stft(y,n_fft=2048,hop_length=512))**2
    mel=lr.feature.melspectrogram(S=S,sr=sr,n_mels=24)
    mel_db=lr.power_to_db(mel+1e-12)
    mean_spec=mel_db.mean(axis=1).tolist()
    flat=float(lr.feature.spectral_flatness(S=S).mean())
    roll=float(lr.feature.spectral_rolloff(S=S,sr=sr,roll_percent=0.85).mean())
    kurt=float(kurtosis(S.mean(axis=1)))
    return {"mel_mean_db":mean_spec,"flatness":flat,"rolloff":roll,"kurtosis":kurt}

def transient_stats(y, sr):
    hop = 512
    oenv = lr.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    peaks = lr.onset.onset_detect(onset_envelope=oenv, sr=sr, hop_length=hop, backtrack=False)
    times = (np.array(peaks) * hop) / sr if len(peaks) else np.array([])
    intervals = np.diff(times) if times.size > 1 else np.array([])
    return {
        "onset_count": int(times.size),
        "onset_rate_per_min": float((times.size / max(len(y) / sr, 1e-9)) * 60.0),
        "avg_onset_interval_s": float(intervals.mean()) if intervals.size else None,
        "max_onset_strength": float(oenv.max()) if oenv.size else 0.0,
    }

def temporal_clues(y,sr,bands):
    S=np.abs(lr.stft(y,n_fft=1024,hop_length=256))+1e-12
    cent=lr.feature.spectral_centroid(S=S,sr=sr).flatten()
    cent_var=float(np.var(cent))
    lf=bands.get("120_250",-80)+bands.get("250_500",-80)
    hf=bands.get("2000_4000",-80)+bands.get("4000_8000",-80)
    hint,conf="unknown",0.3
    if cent_var>1e9 and (hf-lf)>6: 
        hint,conf="daytime_birds_wind_likely",0.55
    elif lf>-50 and (lf-hf)>4: 
        hint,conf="traffic_heavy_possible_rush_hour",0.5
    elif hf<-60 and lf<-60: 
        hint,conf="night_quiet_possible",0.45
    return {"time_of_day_hint":hint,"confidence":conf,"centroid_variance":cent_var}

def file_provenance(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): 
            h.update(c)
    st=path.stat()
    meta={"sha256":h.hexdigest(),
          "size_bytes":st.st_size,
          "mtime_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(st.st_mtime)),
          "ctime_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(st.st_ctime))}
    probe=ffprobe_json(path)
    if probe:
        fmt=probe.get("format",{}); streams=probe.get("streams",[])
        astreams=[s for s in streams if s.get("codec_type")=="audio"]
        acodec=astreams[0] if astreams else {}
        meta.update({"container":fmt.get("format_name"),
                     "bit_rate":fmt.get("bit_rate"),
                     "tags":fmt.get("tags",{}),
                     "audio_stream":{"codec":acodec.get("codec_name"),
                                     "sample_rate":acodec.get("sample_rate"),
                                     "channels":acodec.get("channels"),
                                     "bit_rate":acodec.get("bit_rate"),
                                     "tags":acodec.get("tags",{})}})
    return meta

def analyze_file(path):
    tmp_dir=None; src_for_load=path; is_video=path.suffix.lower() in VIDEO_EXTS
    try:
        if is_video or (path.suffix.lower() not in AUDIO_EXTS):
            if not has_ffmpeg(): 
                raise RuntimeError("ffmpeg not found")
            tmp_dir=Path(tempfile.mkdtemp(prefix="aei_"))
            tmp_wav=tmp_dir/f"{uuid.uuid4().hex}.wav"
            if not extract_audio_with_ffmpeg(path,tmp_wav,TARGET_SR): 
                raise RuntimeError("ffmpeg failed")
            src_for_load=tmp_wav
        prov=file_provenance(path)
        y,sr=load_mono(src_for_load,TARGET_SR)
        if y.size<sr*0.5: 
            raise RuntimeError("Audio too short")
        y_vad=energy_vad(y,sr,VAD_THRESH_DB)
        hum=detect_hum(y_vad,sr)
        rt60_500,c500=estimate_rt60(y_vad,sr,(400,1250))
        rt60_1k,c1k=estimate_rt60(y_vad,sr,(800,1600))
        parts=[]
        if rt60_500: parts.append((rt60_500,c500))
        if rt60_1k: parts.append((rt60_1k,c1k))
        if parts:
            rt60=float(np.mean([p[0] for p in parts]))
            conf=float(np.mean([p[1] for p in parts]))
        else:
            rt60=None; conf=0.0
        bands=band_db(y_vad,sr)
        scene=heuristic_scene(bands,rt60)
        fp=noise_fingerprint(y_vad,sr,hum.get("fundamental_hz") if hum.get("present") else None)
        ltas=ltas_stats(y_vad,sr)
        trans=transient_stats(y_vad,sr)
        temp=temporal_clues(y_vad,sr,bands)
        result={"file":str(path),
                "basename":path.name,
                "is_video":bool(is_video),
                "sr_analysis":sr,
                "duration_s":round(len(y)/sr,3),
                "pipeline_version":PIPELINE_VERSION,
                "provenance":prov,
                "rt60":{"fullband_s":rt60,"500hz_s":rt60_500,"1khz_s":rt60_1k,"confidence":round(conf,3)},
                "hum":hum,
                "bands_db":bands,
                "scene":{"label":scene,"confidence":round(conf*0.8+0.2,2)},
                "fingerprint":{"narrowband_peaks":fp},
                "ltas":ltas,
                "transients":trans,
                "temporal_clues":temp,
                "notes":[]}
        if result["hum"]["present"]:
            fund=result["hum"]["fundamental_hz"]
            if fund:
                region="50Hz_region" if 49.2<=fund<=50.8 else ("60Hz_region" if 59.2<=fund<=60.8 else "unknown_grid")
                result["notes"].append(f"mains_hum_detected_{region}")
            else:
                result["notes"].append("mains_hum_detected")
        if rt60 and rt60>0.8: 
            result["notes"].append("strong_reverb_large_space")
        elif rt60 and rt60<0.2: 
            result["notes"].append("very_low_reverb_open_space")
        if result["fingerprint"]["narrowband_peaks"]: 
            result["notes"].append("noise_fingerprint_available")
        return result
    finally:
        if tmp_dir and Path(tmp_dir).exists(): 
            shutil.rmtree(tmp_dir,ignore_errors=True)

def find_media_files(root):
    files=[]
    for p in root.rglob("*"):
        if not p.is_file(): 
            continue
        if p.suffix.lower() in (AUDIO_EXTS|VIDEO_EXTS): 
            files.append(p)
    return files

def _fingerprint_similarity(a_peaks: List[Dict[str,float]], b_peaks: List[Dict[str,float]]):
    if not a_peaks or not b_peaks: 
        return 0.0,0,0,0
    A=sorted(a_peaks,key=lambda d:d["freq_hz"])
    B=sorted(b_peaks,key=lambda d:d["freq_hz"])
    i=j=0
    overlap_weight=0.0
    matches=0
    k=min(len(A),len(B))
    cap_weights=sorted([p["snr_db"] for p in A]+[q["snr_db"] for q in B],reverse=True)[:k]
    max_weight=float(sum(cap_weights)) if cap_weights else 1.0
    while i<len(A) and j<len(B):
        fa=A[i]["freq_hz"]; fb=B[j]["freq_hz"]
        tol=_freq_tol((fa+fb)/2.0)
        df=fb-fa
        if abs(df)<=tol:
            overlap_weight+=min(A[i]["snr_db"],B[j]["snr_db"])
            matches+=1
            i+=1; j+=1
        elif df>0:
            i+=1
        else:
            j+=1
    sim=max(0.0,min(1.0,overlap_weight/max(max_weight,1e-6)))
    return sim,matches,len(A),len(B)

def _bands_cosine_similarity(bands_a: Dict[str,float], bands_b: Dict[str,float]) -> float:
    keys=["0_120","120_250","250_500","500_1000","1000_2000","2000_4000","4000_8000"]
    va=np.array([bands_a.get(k,-80.0) for k in keys],dtype=float)
    vb=np.array([bands_b.get(k,-80.0) for k in keys],dtype=float)
    va=va-va.mean()
    vb=vb-vb.mean()
    num=float(np.dot(va,vb))
    den=float(np.sqrt((va**2).sum())*np.sqrt((vb**2).sum())+BAND_COSINE_EPS)
    cos=num/den if den>0 else 0.0
    return 0.5*(cos+1.0)

def _ltas_cosine(a: Dict[str,Any], b: Dict[str,Any]) -> float:
    va=np.array(a.get("mel_mean_db",[]),dtype=float)
    vb=np.array(b.get("mel_mean_db",[]),dtype=float)
    if va.size==0 or vb.size==0 or va.size!=vb.size: 
        return 0.0
    va=va-va.mean()
    vb=vb-vb.mean()
    num=float(np.dot(va,vb))
    den=float(np.sqrt((va**2).sum())*np.sqrt((vb**2).sum())+BAND_COSINE_EPS)
    cos=num/den if den>0 else 0.0
    return 0.5*(cos+1.0)

def _rt60_similarity(rta: Optional[float], rtb: Optional[float], tau: float = RT60_MATCH_TAU) -> float:
    if not rta or not rtb: 
        return 0.0
    diff=abs(rta-rtb)
    return float(np.exp(-diff/max(tau,1e-6)))

def _hum_similarity(huma: Dict[str,Any], humb: Dict[str,Any]) -> float:
    pa, pb = huma.get("present"), humb.get("present")
    if pa and pb:
        fa, fb = huma.get("fundamental_hz"), humb.get("fundamental_hz")
        if fa is None or fb is None:
            return 0.5
        return 1.0 if abs(fa - fb) <= HUM_TOL_HZ else 0.4
    if (not pa) and (not pb):
        return 0.6
    return 0.0

def match_score(item_a: Dict[str,Any], item_b: Dict[str,Any]) -> Dict[str,Any]:
    fp_a=item_a.get("fingerprint",{}).get("narrowband_peaks",[])
    fp_b=item_b.get("fingerprint",{}).get("narrowband_peaks",[])
    fp_sim, fp_olap, na, nb = _fingerprint_similarity(fp_a, fp_b)
    bands_sim=_bands_cosine_similarity(item_a.get("bands_db",{}), item_b.get("bands_db",{}))
    ltas_sim=_ltas_cosine(item_a.get("ltas",{}), item_b.get("ltas",{}))
    rt60_a=item_a.get("rt60",{}).get("fullband_s")
    rt60_b=item_b.get("rt60",{}).get("fullband_s")
    rt60_sim=_rt60_similarity(rt60_a, rt60_b, RT60_MATCH_TAU)
    hum_sim=_hum_similarity(item_a.get("hum",{}), item_b.get("hum",{}))
    score=(MATCH_WEIGHTS["fingerprint"]*fp_sim +
           MATCH_WEIGHTS["bands"]*bands_sim +
           MATCH_WEIGHTS["ltas"]*ltas_sim +
           MATCH_WEIGHTS["rt60"]*rt60_sim +
           MATCH_WEIGHTS["hum"]*hum_sim)
    return {"a_file":item_a.get("file"),
            "b_file":item_b.get("file"),
            "a_basename":item_a.get("basename"),
            "b_basename":item_b.get("basename"),
            "score":round(float(score),4),
            "components":{"fingerprint_sim":round(fp_sim,4),
                          "bands_cosine_sim":round(bands_sim,4),
                          "ltas_cosine_sim":round(ltas_sim,4),
                          "rt60_sim":round(rt60_sim,4),
                          "hum_sim":round(hum_sim,4),
                          "overlap_peaks":int(fp_olap),
                          "peaks_a":int(na),
                          "peaks_b":int(nb)},
            "notes":_match_notes(item_a,item_b,fp_olap,na,nb,rt60_a,rt60_b)}

def _match_notes(item_a, item_b, fp_olap, na, nb, rt60_a, rt60_b):
    notes=[]
    if fp_olap >= max(2, min(na, nb)//2):
        notes.append("strong_fingerprint_overlap")
    ha, hb = item_a.get("hum", {}), item_b.get("hum", {})
    if ha.get("present") and hb.get("present"):
        fa, fb = ha.get("fundamental_hz"), hb.get("fundamental_hz")
        if fa is not None and fb is not None and abs(fa - fb) <= HUM_TOL_HZ:
            notes.append("matching_mains_hum")
    if rt60_a and rt60_b:
        if abs(rt60_a - rt60_b) <= 0.1:
            notes.append("similar_rt60")
        elif abs(rt60_a - rt60_b) >= 0.6:
            notes.append("very_different_rt60")
    return notes

def main():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    media=find_media_files(INPUT_DIR)
    if not media:
        log(f"No media found in '{INPUT_DIR.resolve()}'. Put audio/video files there and rerun.")
        out_path = OUTPUT_DIR / "summary.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"pipeline_version": PIPELINE_VERSION, "results": [], "matches": []}, f, ensure_ascii=False, indent=2)
        return
    log(f"Found {len(media)} file(s). Analyzing…\n")
    results=[]
    for i,path in enumerate(sorted(media)):
        log(f"[{i+1}/{len(media)}] {path.name}")
        try:
            res=analyze_file(path)
            results.append(res)
            log("  -> analyzed")
        except Exception as e:
            log(f"  !! ERROR: {e}")
    log("\nScoring pairwise matches…")
    pairs=list(itertools.combinations(range(len(results)),2))
    match_entries=[]
    for ia,ib in pairs:
        m=match_score(results[ia],results[ib])
        if m["score"]>=MATCH_MIN_SCORE:
            match_entries.append(m)
    match_entries.sort(key=lambda d:d["score"],reverse=True)
    if len(match_entries)>MATCH_TOP_K:
        match_entries=match_entries[:MATCH_TOP_K]
    summary={"pipeline_version":PIPELINE_VERSION,
             "results":results,
             "matches":match_entries,
             "match_config":{"threshold":MATCH_MIN_SCORE,
                             "weights":MATCH_WEIGHTS,
                             "rt60_tau":RT60_MATCH_TAU}}
    summary_path=OUTPUT_DIR/"summary.json"
    with open(summary_path,"w",encoding="utf-8") as f:
        json.dump(summary,f,ensure_ascii=False,indent=2)
    log(f"\nDone. Wrote combined summary: {summary_path.resolve()}")

if __name__ == "__main__":
    main()

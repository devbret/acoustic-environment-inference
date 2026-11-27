import shutil
import tempfile
import uuid
from pathlib import Path

import numpy as np

from aei.audio_loader import load_mono
from aei.bands import band_db
from aei.ffmpeg import extract_audio_with_ffmpeg, has_ffmpeg
from aei.fingerprint import noise_fingerprint
from aei.hum import detect_hum
from aei.ltas import ltas_stats
from aei.provenance import file_provenance
from aei.reverb import estimate_rt60
from aei.scene import heuristic_scene
from aei.settings import AUDIO_EXTS, PIPELINE_VERSION, TARGET_SR, VAD_THRESH_DB, VIDEO_EXTS
from aei.temporal import temporal_clues
from aei.transients import transient_stats
from aei.vad import energy_vad


def analyze_file(path):
    tmp_dir = None
    src_for_load = path
    is_video = path.suffix.lower() in VIDEO_EXTS
    try:
        if is_video or (path.suffix.lower() not in AUDIO_EXTS):
            if not has_ffmpeg():
                raise RuntimeError("ffmpeg not found")
            tmp_dir = Path(tempfile.mkdtemp(prefix="aei_"))
            tmp_wav = tmp_dir / f"{uuid.uuid4().hex}.wav"
            if not extract_audio_with_ffmpeg(path, tmp_wav, TARGET_SR):
                raise RuntimeError("ffmpeg failed")
            src_for_load = tmp_wav
        prov = file_provenance(path)
        y, sr = load_mono(src_for_load, TARGET_SR)
        if y.size < sr * 0.5:
            raise RuntimeError("Audio too short")
        y_vad = energy_vad(y, sr, VAD_THRESH_DB)
        hum = detect_hum(y_vad, sr)
        rt60_500, c500 = estimate_rt60(y_vad, sr, (400, 1250))
        rt60_1k, c1k = estimate_rt60(y_vad, sr, (800, 1600))
        parts = []
        if rt60_500:
            parts.append((rt60_500, c500))
        if rt60_1k:
            parts.append((rt60_1k, c1k))
        if parts:
            rt60 = float(np.mean([p[0] for p in parts]))
            conf = float(np.mean([p[1] for p in parts]))
        else:
            rt60 = None
            conf = 0.0
        bands = band_db(y_vad, sr)
        scene = heuristic_scene(bands, rt60)
        fp = noise_fingerprint(y_vad, sr, hum.get("fundamental_hz") if hum.get("present") else None)
        ltas = ltas_stats(y_vad, sr)
        trans = transient_stats(y_vad, sr)
        temp = temporal_clues(y_vad, sr, bands)
        result = {
            "file": str(path),
            "basename": path.name,
            "is_video": bool(is_video),
            "sr_analysis": sr,
            "duration_s": round(len(y) / sr, 3),
            "pipeline_version": PIPELINE_VERSION,
            "provenance": prov,
            "rt60": {
                "fullband_s": rt60,
                "500hz_s": rt60_500,
                "1khz_s": rt60_1k,
                "confidence": round(conf, 3),
            },
            "hum": hum,
            "bands_db": bands,
            "scene": {"label": scene, "confidence": round(conf * 0.8 + 0.2, 2)},
            "fingerprint": {"narrowband_peaks": fp},
            "ltas": ltas,
            "transients": trans,
            "temporal_clues": temp,
            "notes": [],
        }
        if result["hum"]["present"]:
            fund = result["hum"]["fundamental_hz"]
            if fund:
                region = (
                    "50Hz_region" if 49.2 <= fund <= 50.8
                    else ("60Hz_region" if 59.2 <= fund <= 60.8 else "unknown_grid")
                )
                result["notes"].append(f"mains_hum_detected_{region}")
            else:
                result["notes"].append("mains_hum_detected")
        if rt60 and rt60 > 0.8:
            result["notes"].append("strong_reverb_large_space")
        elif rt60 and rt60 < 0.2:
            result["notes"].append("very_low_reverb_open_space")
        if result["fingerprint"]["narrowband_peaks"]:
            result["notes"].append("noise_fingerprint_available")
        return result
    finally:
        if tmp_dir and Path(tmp_dir).exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)

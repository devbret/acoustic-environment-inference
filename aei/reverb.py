import librosa as lr
import numpy as np


def estimate_rt60(y, sr, band):
    n_fft, hop = 1024, 256
    S = np.abs(lr.stft(y, n_fft=n_fft, hop_length=hop)) ** 2
    freqs = lr.fft_frequencies(sr=sr, n_fft=n_fft)
    m = (freqs >= band[0]) & (freqs <= band[1])
    if not m.any():
        return None, 0.2
    e = S[m, :].mean(axis=0) + 1e-12
    th = np.percentile(e, 85)
    starts = np.where((e[:-1] < th) & (e[1:] >= th))[0]
    if starts.size == 0:
        return None, 0.25
    rt_list = []
    conf_list = []
    for s in starts[:12]:
        seg = e[s:s + int(2.5 * sr / hop)]
        if seg.size < 32:
            continue
        edc = np.flip(np.cumsum(np.flip(seg)))
        edc_db = 10 * np.log10(edc / np.max(edc))
        idx = np.where((edc_db <= -5) & (edc_db >= -35))[0]
        if idx.size < 20:
            continue
        t = (idx * hop) / sr
        ydb = edc_db[idx]
        a, b = np.polyfit(t, ydb, 1)
        if a >= 0:
            continue
        rt = -60.0 / a
        if 0.05 <= rt <= 6.0:
            ss_res = float(((ydb - (a * t + b)) ** 2).sum())
            ss_tot = float(((ydb - ydb.mean()) ** 2).sum() + 1e-12)
            r2 = 1.0 - ss_res / ss_tot
            conf = 0.6 * r2 + 0.4 * min(1.0, (ydb.max() - ydb.min()) / 40.0)
            rt_list.append(rt)
            conf_list.append(conf)
    if not rt_list:
        return None, 0.25
    return float(np.median(rt_list)), float(np.median(conf_list))

import numpy as np

from aei.settings import HUM_PRESENT_SNR_DB
from aei.spectrum import psd


def detect_hum(y, sr):
    f, P = psd(y, sr)
    scores = {}
    for c in (50.0, 60.0):
        win = (f > c - 0.8) & (f < c + 0.8)
        peak = P[win].max() if win.any() else 0.0
        noise_band = (f > c + 5) & (f < c + 30)
        noise = np.median(P[noise_band]) if noise_band.any() else np.median(P)
        snr = 10 * np.log10((peak + 1e-15) / (noise + 1e-15))
        scores[c] = snr
    fund = max(scores, key=scores.get)
    present = scores[fund] > HUM_PRESENT_SNR_DB
    harmonics = [round(fund * k, 2) for k in range(2, 9)]
    return {
        "present": bool(present),
        "fundamental_hz": float(fund) if present else None,
        "harmonics": harmonics if present else [],
        "peak_snr_db": float(scores[fund]),
    }

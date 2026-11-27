import numpy as np
from scipy.signal import find_peaks

from aei.settings import HUM_TOL_HZ, NOISE_FP_MAX_FREQ_HZ, NOISE_FP_MAX_PEAKS
from aei.spectrum import psd


def _quad_interp_peak(f, P, i):
    if i <= 0 or i >= len(P) - 1:
        return f[i], P[i]
    a, b, c = P[i - 1], P[i], P[i + 1]
    p = 0.5 * (a - c) / (a - 2 * b + c + 1e-15)
    f_hat = f[i] + p * (f[1] - f[0])
    P_hat = b - 0.25 * (a - c) * p
    return float(f_hat), float(P_hat)


def noise_fingerprint(y, sr, hum_fund):
    f, P = psd(y, sr)
    band = (f > 20) & (f <= NOISE_FP_MAX_FREQ_HZ)
    fb = f[band]
    Pb = P[band]
    if fb.size < 10:
        return []
    peaks, _ = find_peaks(Pb, prominence=max(np.median(Pb) * 2.0, 1e-12))
    result = []
    for i in peaks:
        freq, pwr = _quad_interp_peak(fb, Pb, i)
        if hum_fund:
            k = round(freq / hum_fund)
            if k >= 1 and abs(freq - k * hum_fund) <= HUM_TOL_HZ:
                continue
        win = np.abs(fb - freq) < 30.0
        floor = np.median(Pb[win]) if win.any() else np.median(Pb)
        snr_db = 10 * np.log10((pwr + 1e-15) / (floor + 1e-15))
        result.append({"freq_hz": round(freq, 2), "snr_db": round(float(snr_db), 2)})
    result.sort(key=lambda d: d["snr_db"], reverse=True)
    return result[:NOISE_FP_MAX_PEAKS]

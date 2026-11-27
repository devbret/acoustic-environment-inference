from typing import Any, Dict, List, Optional

import numpy as np

from aei.settings import BAND_COSINE_EPS, HUM_TOL_HZ, RT60_MATCH_TAU


def _freq_tol(f_hz):
    return max(0.8, 0.0015 * f_hz)


def fingerprint_similarity(a_peaks: List[Dict[str, float]], b_peaks: List[Dict[str, float]]):
    if not a_peaks or not b_peaks:
        return 0.0, 0, 0, 0
    A = sorted(a_peaks, key=lambda d: d["freq_hz"])
    B = sorted(b_peaks, key=lambda d: d["freq_hz"])
    i = j = 0
    overlap_weight = 0.0
    matches = 0
    k = min(len(A), len(B))
    cap_weights = sorted([p["snr_db"] for p in A] + [q["snr_db"] for q in B], reverse=True)[:k]
    max_weight = float(sum(cap_weights)) if cap_weights else 1.0
    while i < len(A) and j < len(B):
        fa = A[i]["freq_hz"]
        fb = B[j]["freq_hz"]
        tol = _freq_tol((fa + fb) / 2.0)
        df = fb - fa
        if abs(df) <= tol:
            overlap_weight += min(A[i]["snr_db"], B[j]["snr_db"])
            matches += 1
            i += 1
            j += 1
        elif df > 0:
            i += 1
        else:
            j += 1
    sim = max(0.0, min(1.0, overlap_weight / max(max_weight, 1e-6)))
    return sim, matches, len(A), len(B)


def bands_cosine_similarity(bands_a: Dict[str, float], bands_b: Dict[str, float]) -> float:
    keys = ["0_120", "120_250", "250_500", "500_1000", "1000_2000", "2000_4000", "4000_8000"]
    va = np.array([bands_a.get(k, -80.0) for k in keys], dtype=float)
    vb = np.array([bands_b.get(k, -80.0) for k in keys], dtype=float)
    va = va - va.mean()
    vb = vb - vb.mean()
    num = float(np.dot(va, vb))
    den = float(np.sqrt((va ** 2).sum()) * np.sqrt((vb ** 2).sum()) + BAND_COSINE_EPS)
    cos = num / den if den > 0 else 0.0
    return 0.5 * (cos + 1.0)


def ltas_cosine(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    va = np.array(a.get("mel_mean_db", []), dtype=float)
    vb = np.array(b.get("mel_mean_db", []), dtype=float)
    if va.size == 0 or vb.size == 0 or va.size != vb.size:
        return 0.0
    va = va - va.mean()
    vb = vb - vb.mean()
    num = float(np.dot(va, vb))
    den = float(np.sqrt((va ** 2).sum()) * np.sqrt((vb ** 2).sum()) + BAND_COSINE_EPS)
    cos = num / den if den > 0 else 0.0
    return 0.5 * (cos + 1.0)


def rt60_similarity(rta: Optional[float], rtb: Optional[float], tau: float = RT60_MATCH_TAU) -> float:
    if rta is None or rtb is None:
        return 0.0
    diff = abs(rta - rtb)
    return float(np.exp(-diff / max(tau, 1e-6)))


def hum_similarity(huma: Dict[str, Any], humb: Dict[str, Any]) -> float:
    pa, pb = huma.get("present"), humb.get("present")
    if pa and pb:
        fa, fb = huma.get("fundamental_hz"), humb.get("fundamental_hz")
        if fa is None or fb is None:
            return 0.5
        return 1.0 if abs(fa - fb) <= HUM_TOL_HZ else 0.4
    if (not pa) and (not pb):
        return 0.6
    return 0.0

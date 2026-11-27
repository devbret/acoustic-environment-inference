import numpy as np

from aei.spectrum import psd


def band_db(y, sr):
    f, P = psd(y, sr)
    bands = [(0, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000)]
    out = {}
    for lo, hi in bands:
        m = (f >= lo) & (f < hi)
        p = P[m].mean() if m.any() else 1e-15
        out[f"{lo}_{hi}"] = float(10 * np.log10(p + 1e-15))
    return out

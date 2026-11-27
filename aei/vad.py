import librosa as lr
import numpy as np

from aei.settings import FRAME_MS, HOP_MS


def energy_vad(y, sr, thresh_db=None, frame_ms=FRAME_MS, hop_ms=HOP_MS):
    f = int(sr * frame_ms / 1000)
    h = int(sr * hop_ms / 1000)
    if len(y) < f:
        return y
    frames = lr.util.frame(y, frame_length=f, hop_length=h)
    rms = np.sqrt((frames ** 2).mean(axis=0))
    rms_db = 20 * np.log10(np.maximum(rms, 1e-12))
    if thresh_db is None:
        noise_floor = np.percentile(rms_db, 15)
        thresh_db = noise_floor + 6.0
    mask = rms_db > thresh_db
    idx = np.repeat(mask, h)
    idx = np.pad(
        idx,
        (0, max(0, len(y) - len(idx))),
        constant_values=mask[-1] if len(mask) > 0 else False,
    )[:len(y)]
    kept = y[idx] if idx.any() else y
    return kept if kept.size > int(0.1 * len(y)) else y

import librosa as lr
import numpy as np


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

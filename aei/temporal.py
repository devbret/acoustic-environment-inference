import librosa as lr
import numpy as np

from aei.settings import CENTROID_CV_HIGH


def temporal_clues(y, sr, bands):
    S = np.abs(lr.stft(y, n_fft=1024, hop_length=256)) + 1e-12
    cent = lr.feature.spectral_centroid(S=S, sr=sr).flatten()

    if cent.size < 2:
        return {
            "time_of_day_hint": "unknown",
            "confidence": 0.2,
            "centroid_variance": 0.0,
            "centroid_mean_hz": float(cent[0]) if cent.size else 0.0,
            "centroid_cv": 0.0,
        }

    cent_var = float(np.var(cent))
    cent_mean = float(cent.mean())
    cent_cv = float(np.sqrt(cent_var) / max(cent_mean, 1e-9))

    lf = bands.get("120_250", -80) + bands.get("250_500", -80)
    hf = bands.get("2000_4000", -80) + bands.get("4000_8000", -80)
    hint, conf = "unknown", 0.3
    if cent_cv > CENTROID_CV_HIGH and (hf - lf) > 6:
        hint, conf = "daytime_birds_wind_likely", 0.55
    elif lf > -50 and (lf - hf) > 4:
        hint, conf = "traffic_heavy_possible_rush_hour", 0.5
    elif hf < -60 and lf < -60:
        hint, conf = "night_quiet_possible", 0.45
    return {
        "time_of_day_hint": hint,
        "confidence": conf,
        "centroid_variance": cent_var,
        "centroid_mean_hz": cent_mean,
        "centroid_cv": cent_cv,
    }

import librosa as lr
import numpy as np
from scipy.stats import kurtosis


def ltas_stats(y, sr):
    S = np.abs(lr.stft(y, n_fft=2048, hop_length=512)) ** 2
    mel = lr.feature.melspectrogram(S=S, sr=sr, n_mels=24)
    mel_db = lr.power_to_db(mel + 1e-12)
    mean_spec = mel_db.mean(axis=1).tolist()
    flat = float(lr.feature.spectral_flatness(S=S).mean())
    roll = float(lr.feature.spectral_rolloff(S=S, sr=sr, roll_percent=0.85).mean())
    kurt = float(kurtosis(S.mean(axis=1)))
    return {"mel_mean_db": mean_spec, "flatness": flat, "rolloff": roll, "kurtosis": kurt}

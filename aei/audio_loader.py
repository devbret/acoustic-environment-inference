import librosa as lr
import numpy as np

from aei.settings import TARGET_SR


def load_mono(path, sr=TARGET_SR):
    y, _ = lr.load(str(path), sr=sr, mono=True, res_type="kaiser_best")
    y = y - np.mean(y)
    return y, sr

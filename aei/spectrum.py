from scipy.signal import welch


def psd(y, sr, nperseg=8192, noverlap=4096):
    f, Pxx = welch(y, fs=sr, nperseg=nperseg, noverlap=noverlap, average='median', detrend='constant')
    return f, Pxx

from pathlib import Path

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
SUMMARY_PATH = OUTPUT_DIR / "summary.json"
TARGET_SR = 16000
FRAME_MS = 30
HOP_MS = 15
VAD_THRESH_DB = None
HUM_PRESENT_SNR_DB = 6.0
HUM_TOL_HZ = 0.9
NOISE_FP_MAX_PEAKS = 8
NOISE_FP_MAX_FREQ_HZ = 2000
BAND_COSINE_EPS = 1e-9
RT60_MATCH_TAU = 0.20
CENTROID_CV_HIGH = 0.35
MATCH_WEIGHTS = {"fingerprint": 0.40, "bands": 0.15, "ltas": 0.20, "rt60": 0.15, "hum": 0.10}
MATCH_MIN_SCORE = 0.43
MATCH_TOP_K = 50
PIPELINE_VERSION = "2.0.1-osint-upgrade"
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aiff", ".aif", ".opus"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}

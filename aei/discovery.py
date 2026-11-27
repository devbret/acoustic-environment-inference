from aei.settings import AUDIO_EXTS, VIDEO_EXTS


def find_media_files(root):
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in (AUDIO_EXTS | VIDEO_EXTS):
            files.append(p)
    return files

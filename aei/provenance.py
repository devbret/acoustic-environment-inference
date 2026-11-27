import hashlib
import time

from aei.ffmpeg import ffprobe_json


def file_provenance(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    st = path.stat()
    meta = {
        "sha256": h.hexdigest(),
        "size_bytes": st.st_size,
        "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
        "ctime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_ctime)),
    }
    probe = ffprobe_json(path)
    if probe:
        fmt = probe.get("format", {})
        streams = probe.get("streams", [])
        astreams = [s for s in streams if s.get("codec_type") == "audio"]
        acodec = astreams[0] if astreams else {}
        meta.update({
            "container": fmt.get("format_name"),
            "bit_rate": fmt.get("bit_rate"),
            "tags": fmt.get("tags", {}),
            "audio_stream": {
                "codec": acodec.get("codec_name"),
                "sample_rate": acodec.get("sample_rate"),
                "channels": acodec.get("channels"),
                "bit_rate": acodec.get("bit_rate"),
                "tags": acodec.get("tags", {}),
            },
        })
    return meta

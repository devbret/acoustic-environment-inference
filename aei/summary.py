import json

from aei.settings import MATCH_MIN_SCORE, MATCH_WEIGHTS, PIPELINE_VERSION, RT60_MATCH_TAU


def empty_summary():
    return {"pipeline_version": PIPELINE_VERSION, "results": [], "matches": []}


def build_summary(results, matches):
    return {
        "pipeline_version": PIPELINE_VERSION,
        "results": results,
        "matches": matches,
        "match_config": {
            "threshold": MATCH_MIN_SCORE,
            "weights": MATCH_WEIGHTS,
            "rt60_tau": RT60_MATCH_TAU,
        },
    }


def write_summary(path, summary):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

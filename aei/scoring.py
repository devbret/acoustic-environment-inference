from typing import Any, Dict

from aei.settings import HUM_TOL_HZ, MATCH_WEIGHTS, RT60_MATCH_TAU
from aei.similarity import (
    bands_cosine_similarity,
    fingerprint_similarity,
    hum_similarity,
    ltas_cosine,
    rt60_similarity,
)


def match_score(item_a: Dict[str, Any], item_b: Dict[str, Any]) -> Dict[str, Any]:
    fp_a = item_a.get("fingerprint", {}).get("narrowband_peaks", [])
    fp_b = item_b.get("fingerprint", {}).get("narrowband_peaks", [])
    fp_sim, fp_olap, na, nb = fingerprint_similarity(fp_a, fp_b)
    bands_sim = bands_cosine_similarity(item_a.get("bands_db", {}), item_b.get("bands_db", {}))
    ltas_sim = ltas_cosine(item_a.get("ltas", {}), item_b.get("ltas", {}))
    rt60_a = item_a.get("rt60", {}).get("fullband_s")
    rt60_b = item_b.get("rt60", {}).get("fullband_s")
    rt60_sim = rt60_similarity(rt60_a, rt60_b, RT60_MATCH_TAU)
    hum_sim = hum_similarity(item_a.get("hum", {}), item_b.get("hum", {}))
    score = (
        MATCH_WEIGHTS["fingerprint"] * fp_sim
        + MATCH_WEIGHTS["bands"] * bands_sim
        + MATCH_WEIGHTS["ltas"] * ltas_sim
        + MATCH_WEIGHTS["rt60"] * rt60_sim
        + MATCH_WEIGHTS["hum"] * hum_sim
    )
    return {
        "a_file": item_a.get("file"),
        "b_file": item_b.get("file"),
        "a_basename": item_a.get("basename"),
        "b_basename": item_b.get("basename"),
        "score": round(float(score), 4),
        "components": {
            "fingerprint_sim": round(fp_sim, 4),
            "bands_cosine_sim": round(bands_sim, 4),
            "ltas_cosine_sim": round(ltas_sim, 4),
            "rt60_sim": round(rt60_sim, 4),
            "hum_sim": round(hum_sim, 4),
            "overlap_peaks": int(fp_olap),
            "peaks_a": int(na),
            "peaks_b": int(nb),
        },
        "notes": _match_notes(item_a, item_b, fp_olap, na, nb, rt60_a, rt60_b),
    }


def _match_notes(item_a, item_b, fp_olap, na, nb, rt60_a, rt60_b):
    notes = []
    if fp_olap >= max(2, min(na, nb) // 2):
        notes.append("strong_fingerprint_overlap")
    ha, hb = item_a.get("hum", {}), item_b.get("hum", {})
    if ha.get("present") and hb.get("present"):
        fa, fb = ha.get("fundamental_hz"), hb.get("fundamental_hz")
        if fa is not None and fb is not None and abs(fa - fb) <= HUM_TOL_HZ:
            notes.append("matching_mains_hum")
    if rt60_a and rt60_b:
        if abs(rt60_a - rt60_b) <= 0.1:
            notes.append("similar_rt60")
        elif abs(rt60_a - rt60_b) >= 0.6:
            notes.append("very_different_rt60")
    return notes

import itertools

from aei.settings import MATCH_MIN_SCORE, MATCH_TOP_K
from aei.scoring import match_score


def rank_matches(results):
    match_entries = []
    for ia, ib in itertools.combinations(range(len(results)), 2):
        m = match_score(results[ia], results[ib])
        if m["score"] >= MATCH_MIN_SCORE:
            match_entries.append(m)
    match_entries.sort(key=lambda d: d["score"], reverse=True)
    return match_entries[:MATCH_TOP_K]

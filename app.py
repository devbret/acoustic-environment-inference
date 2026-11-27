from aei.analyzer import analyze_file
from aei.discovery import find_media_files
from aei.logger import log
from aei.ranking import rank_matches
from aei.settings import INPUT_DIR, OUTPUT_DIR, SUMMARY_PATH
from aei.summary import build_summary, empty_summary, write_summary


def main():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    media = find_media_files(INPUT_DIR)
    if not media:
        log(f"No media found in '{INPUT_DIR.resolve()}'. Put audio/video files there and rerun.")
        write_summary(SUMMARY_PATH, empty_summary())
        return
    log(f"Found {len(media)} file(s). Analyzing…\n")
    results = []
    for i, path in enumerate(sorted(media)):
        log(f"[{i + 1}/{len(media)}] {path.name}")
        try:
            res = analyze_file(path)
            results.append(res)
            log("  -> analyzed")
        except Exception as e:
            log(f"  !! ERROR: {e}")
    log("\nScoring pairwise matches…")
    matches = rank_matches(results)
    write_summary(SUMMARY_PATH, build_summary(results, matches))
    log(f"\nDone. Wrote combined summary: {SUMMARY_PATH.resolve()}")


if __name__ == "__main__":
    main()

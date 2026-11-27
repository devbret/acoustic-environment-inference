import { DEFAULT_THRESHOLD } from "./constants.js";

export function normalizeData(json) {
  if (Array.isArray(json)) {
    return {
      pipeline_version: "unknown",
      results: json,
      matches: [],
      match_config: { threshold: DEFAULT_THRESHOLD },
    };
  }
  return {
    pipeline_version: json.pipeline_version ?? "unknown",
    results: json.results ?? [],
    matches: json.matches ?? [],
    match_config: json.match_config ?? { threshold: DEFAULT_THRESHOLD },
  };
}

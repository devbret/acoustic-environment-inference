export function renderDataset(els, data) {
  els.metaPanel.classList.remove("hidden");
  els.pipelineVersion.textContent = data.pipeline_version;
  els.totalFiles.textContent = data.results.length;
  els.totalMatches.textContent = data.matches.length;
  els.threshold.textContent = data.match_config.threshold ?? "—";
}

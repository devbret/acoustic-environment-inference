import { drawBands } from "./js/bandsChart.js";
import { bindDropzone, bindFetchButton, bindFileInput } from "./js/dataSources.js";
import { renderDataset } from "./js/datasetPanel.js";
import { queryElements } from "./js/elements.js";
import { populateFileSelect } from "./js/fileSelect.js";
import { drawFingerprint } from "./js/fingerprintChart.js";
import { drawHum } from "./js/humChart.js";
import { renderMatches } from "./js/matchTable.js";
import { renderNetwork } from "./js/network.js";
import { normalizeData } from "./js/normalize.js";
import { renderOverview } from "./js/overview.js";
import { drawRT60 } from "./js/rt60Chart.js";
import { drawTemporal } from "./js/temporalPanel.js";
import { drawTransients } from "./js/transientsPanel.js";

const els = queryElements();

let DATA = null;
let network = null;

function loadData(json) {
  DATA = normalizeData(json);
  renderDataset(els, DATA);

  populateFileSelect(els.fileSelect, DATA.results);
  if (DATA.results.length) {
    els.fileSelect.selectedIndex = 0;
    renderForIndex(0);
  }

  renderMatches(DATA.matches);
  network = renderNetwork(
    DATA.matches,
    DATA.results,
    DATA.match_config.threshold,
  );
}

function renderForIndex(i) {
  const r = DATA.results[i];
  if (!r) return;

  renderOverview(els, r);
  drawRT60("#rt60Chart", r.rt60);
  drawHum("#humChart", r.hum);
  drawBands("#bandsChart", r.bands_db);
  drawFingerprint("#fpChart", r.fingerprint?.narrowband_peaks || []);
  drawTransients("#transients", r.transients);
  drawTemporal("#temporal", r.temporal_clues);
}

bindFetchButton(els.btnFetch, loadData);
bindFileInput(els.fileInput, loadData);
bindDropzone(els.dropzone, loadData);

els.fileSelect.addEventListener("change", (e) => {
  renderForIndex(+e.target.value);
});

els.fitNetwork.addEventListener("click", () => network?.zoomToFit());

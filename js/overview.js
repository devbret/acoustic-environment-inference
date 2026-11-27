import { fmtBytes, fmtHz, fmtNum } from "./format.js";

export function renderOverview(els, r) {
  els.ovName.textContent = r.basename || r.file || "—";
  els.ovDur.textContent =
    r.duration_s != null ? `${r.duration_s.toFixed(2)} s` : "—";
  els.ovScene.innerHTML = "";
  const scene = r.scene?.label || "—";
  const scConf = r.scene?.confidence;
  els.ovScene.append(scene);
  if (scConf != null) els.ovScene.append(` (conf ${scConf})`);
  const hum = r.hum || {};
  els.ovHum.textContent = hum.present
    ? `Yes, ${fmtHz(hum.fundamental_hz)} (SNR ${fmtNum(hum.peak_snr_db)} dB)`
    : "No";

  els.ovTags.innerHTML = "";
  (r.notes || []).forEach((tag) => {
    const span = document.createElement("span");
    span.className = "tag";
    if (/strong_reverb|large_space/.test(tag)) span.classList.add("warn");
    if (/very_low_reverb|open_space/.test(tag)) span.classList.add("accent");
    if (/mains_hum/.test(tag)) span.classList.add("alert");
    span.textContent = tag;
    els.ovTags.appendChild(span);
  });

  els.ovHash.textContent = r.provenance?.sha256
    ? r.provenance.sha256.slice(0, 16) + "…"
    : "—";
  els.ovSize.textContent = r.provenance?.size_bytes
    ? fmtBytes(r.provenance.size_bytes)
    : "—";
  els.ovMtime.textContent = r.provenance?.mtime_utc || "—";
}

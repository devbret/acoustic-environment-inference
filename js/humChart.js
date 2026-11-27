import { fmtHz, fmtNum } from "./format.js";

export function drawHum(sel, hum) {
  const box = d3.select(sel);
  box.selectAll("*").remove();
  const w = box.node().clientWidth,
    h = box.node().clientHeight,
    pad = 30;
  const svg = box.append("svg").attr("width", w).attr("height", h);
  if (!hum || !hum.present) {
    svg
      .append("text")
      .attr("x", w / 2)
      .attr("y", h / 2)
      .attr("fill", "#9aa3c7")
      .attr("text-anchor", "middle")
      .text("No mains hum detected");
    return;
  }
  const harmonics = [hum.fundamental_hz, ...(hum.harmonics || [])].filter(
    (v) => v != null,
  );
  const maxF = Math.max(500, d3.max(harmonics) || 120);
  const x = d3
    .scaleLinear()
    .domain([0, maxF])
    .range([pad, w - pad]);
  const y = d3
    .scaleLinear()
    .domain([0, 1])
    .range([h - pad, pad]);
  const ax = d3.axisBottom(x).ticks(6);
  svg
    .append("g")
    .attr("transform", `translate(0,${h - pad})`)
    .call(ax)
    .selectAll("text")
    .attr("fill", "#cbd5ff");
  svg
    .append("line")
    .attr("x1", pad)
    .attr("x2", w - pad)
    .attr("y1", y(0.2))
    .attr("y2", y(0.2))
    .attr("stroke", "#2a2f55");
  svg
    .selectAll("line.stem")
    .data(harmonics)
    .join("line")
    .attr("class", "stem")
    .attr("x1", (d) => x(d))
    .attr("x2", (d) => x(d))
    .attr("y1", y(0.2))
    .attr("y2", y(0.9))
    .attr("stroke", "#8ab4ff")
    .attr("stroke-width", 2);
  svg
    .append("text")
    .attr("x", pad)
    .attr("y", pad - 8)
    .attr("fill", "#9aa3c7")
    .attr("font-size", 11)
    .text(
      `Fundamental: ${fmtHz(hum.fundamental_hz)} • Peak SNR: ${fmtNum(
        hum.peak_snr_db,
      )} dB`,
    );
}

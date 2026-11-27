export function drawFingerprint(sel, peaks) {
  const box = d3.select(sel);
  box.selectAll("*").remove();
  const w = box.node().clientWidth,
    h = box.node().clientHeight,
    pad = 30;
  const svg = box.append("svg").attr("width", w).attr("height", h);
  if (!peaks || !peaks.length) {
    svg
      .append("text")
      .attr("x", w / 2)
      .attr("y", h / 2)
      .attr("fill", "#9aa3c7")
      .attr("text-anchor", "middle")
      .text("No narrowband peaks captured");
    return;
  }
  const x = d3
    .scaleLinear()
    .domain([0, d3.max(peaks, (d) => d.freq_hz) || 2000])
    .nice()
    .range([pad, w - pad]);
  const y = d3
    .scaleLinear()
    .domain([0, d3.max(peaks, (d) => d.snr_db) || 10])
    .nice()
    .range([h - pad, pad]);
  svg
    .append("g")
    .attr("transform", `translate(0,${h - pad})`)
    .call(d3.axisBottom(x))
    .selectAll("text")
    .attr("fill", "#cbd5ff");
  svg
    .append("g")
    .attr("transform", `translate(${pad},0)`)
    .call(d3.axisLeft(y))
    .selectAll("text")
    .attr("fill", "#cbd5ff");
  svg
    .selectAll("line.stem")
    .data(peaks)
    .join("line")
    .attr("class", "stem")
    .attr("x1", (d) => x(d.freq_hz))
    .attr("x2", (d) => x(d.freq_hz))
    .attr("y1", y(0))
    .attr("y2", (d) => y(d.snr_db))
    .attr("stroke", "#7ee787")
    .attr("stroke-width", 2.2);
  svg
    .selectAll("circle.dot")
    .data(peaks)
    .join("circle")
    .attr("class", "dot")
    .attr("cx", (d) => x(d.freq_hz))
    .attr("cy", (d) => y(d.snr_db))
    .attr("r", 3.2)
    .attr("fill", "#ffcc66")
    .attr("stroke", "#1a1e3f");
}

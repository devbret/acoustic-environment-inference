export function drawRT60(sel, rt) {
  const box = d3.select(sel);
  box.selectAll("*").remove();
  const w = box.node().clientWidth,
    h = box.node().clientHeight,
    pad = 28;
  const svg = box.append("svg").attr("width", w).attr("height", h);
  const data = [
    { k: "Full", v: rt?.fullband_s ?? null, c: "#8ab4ff" },
    { k: "500Hz", v: rt?.["500hz_s"] ?? null, c: "#7ee787" },
    { k: "1kHz", v: rt?.["1khz_s"] ?? null, c: "#ffcc66" },
  ].filter((d) => d.v != null);
  const x = d3
    .scaleBand()
    .domain(data.map((d) => d.k))
    .range([pad, w - pad])
    .padding(0.3);
  const maxV = Math.max(1.2, d3.max(data, (d) => d.v) || 1.0);
  const y = d3
    .scaleLinear()
    .domain([0, maxV])
    .nice()
    .range([h - pad, pad]);
  const ax = d3.axisBottom(x);
  const ay = d3.axisLeft(y).ticks(5);
  svg
    .append("g")
    .attr("transform", `translate(0,${h - pad})`)
    .call(ax)
    .selectAll("text")
    .attr("fill", "#cbd5ff");
  svg
    .append("g")
    .attr("transform", `translate(${pad},0)`)
    .call(ay)
    .selectAll("text")
    .attr("fill", "#cbd5ff");
  svg
    .selectAll("rect.bar")
    .data(data)
    .join("rect")
    .attr("class", "bar")
    .attr("x", (d) => x(d.k))
    .attr("y", (d) => y(d.v))
    .attr("width", x.bandwidth())
    .attr("height", (d) => y(0) - y(d.v))
    .attr("fill", (d) => d.c)
    .attr("rx", 4);
  svg
    .append("text")
    .attr("x", pad)
    .attr("y", pad - 8)
    .attr("fill", "#9aa3c7")
    .attr("font-size", 11)
    .text(
      `Confidence: ${rt?.confidence != null ? rt.confidence.toFixed(2) : "—"}`,
    );
}

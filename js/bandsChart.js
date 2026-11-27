export function drawBands(sel, bands) {
  const keys = [
    "0_120",
    "120_250",
    "250_500",
    "500_1000",
    "1000_2000",
    "2000_4000",
    "4000_8000",
  ];
  const data = keys.map((k) => ({ k, v: bands?.[k] ?? -80 }));
  const box = d3.select(sel);
  box.selectAll("*").remove();
  const w = box.node().clientWidth,
    h = box.node().clientHeight,
    pad = 30;
  const svg = box.append("svg").attr("width", w).attr("height", h);
  const x = d3
    .scaleBand()
    .domain(keys)
    .range([pad, w - pad])
    .padding(0.25);
  const y = d3
    .scaleLinear()
    .domain([d3.min(data, (d) => d.v) - 2, d3.max(data, (d) => d.v) + 2])
    .nice()
    .range([h - pad, pad]);
  svg
    .append("g")
    .attr("transform", `translate(0,${h - pad})`)
    .call(d3.axisBottom(x))
    .selectAll("text")
    .attr("fill", "#cbd5ff")
    .attr("font-size", 11);
  svg
    .append("g")
    .attr("transform", `translate(${pad},0)`)
    .call(d3.axisLeft(y).ticks(5))
    .selectAll("text")
    .attr("fill", "#cbd5ff");
  svg
    .selectAll("rect")
    .data(data)
    .join("rect")
    .attr("x", (d) => x(d.k))
    .attr("y", (d) => y(d.v))
    .attr("width", x.bandwidth())
    .attr("height", (d) => y(y.domain()[0]) - y(d.v))
    .attr("fill", "#8ab4ff")
    .attr("rx", 4);
}

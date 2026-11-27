export function drawTemporal(sel, t) {
  const wrap = d3.select(sel);
  wrap.selectAll("*").remove();
  const entries = [
    { k: "Time-of-Day Hint", v: t?.time_of_day_hint || "unknown" },
    {
      k: "Confidence",
      v: t?.confidence != null ? t.confidence.toFixed(2) : "—",
    },
    {
      k: "Centroid Variance",
      v: t?.centroid_variance != null ? t.centroid_variance.toFixed(0) : "—",
    },
    { k: "Note", v: "Heuristic only; low accuracy." },
  ];
  wrap
    .selectAll("div.meta")
    .data(entries)
    .join("div")
    .attr("class", "meta")
    .html((d) => `<strong>${d.k}:</strong> ${d.v}`);
}

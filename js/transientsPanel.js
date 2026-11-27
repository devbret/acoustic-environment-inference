export function drawTransients(sel, t) {
  const wrap = d3.select(sel);
  wrap.selectAll("*").remove();
  const entries = [
    { k: "Onset Count", v: t?.onset_count },
    {
      k: "Onset Rate (/min)",
      v: t?.onset_rate_per_min != null ? t.onset_rate_per_min.toFixed(2) : "—",
    },
    {
      k: "Avg Onset Interval (s)",
      v:
        t?.avg_onset_interval_s != null
          ? t.avg_onset_interval_s.toFixed(2)
          : "—",
    },
    {
      k: "Max Onset Strength",
      v: t?.max_onset_strength != null ? t.max_onset_strength.toFixed(2) : "—",
    },
  ];
  wrap
    .selectAll("div.meta")
    .data(entries)
    .join("div")
    .attr("class", "meta")
    .html((d) => `<strong>${d.k}:</strong> ${d.v ?? "—"}`);
}

export function renderMatches(matches) {
  const tbody = d3.select("#matchTable tbody");
  tbody.selectAll("tr").remove();
  matches
    .slice()
    .sort((a, b) => d3.descending(a.score, b.score))
    .forEach((m) => {
      const tr = tbody.append("tr");
      tr.append("td").text(m.score.toFixed(3));
      tr.append("td").text(m.a_basename || m.a_file);
      tr.append("td").text(m.b_basename || m.b_file);
      tr.append("td").text(m.components?.fingerprint_sim?.toFixed(2));
      tr.append("td").text(m.components?.bands_cosine_sim?.toFixed(2));
      tr.append("td").text(m.components?.ltas_cosine_sim?.toFixed(2));
      tr.append("td").text(m.components?.rt60_sim?.toFixed(2));
      tr.append("td").text(m.components?.hum_sim?.toFixed(2));
      tr.append("td").html(
        (m.notes || []).map((n) => `<span class="tag">${n}</span>`).join(" "),
      );
    });
}

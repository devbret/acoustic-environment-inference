export function buildNodes(results) {
  return results.map((r, i) => ({
    id: i,
    name: r.basename || r.file || `Item ${i + 1}`,
    hum: r.hum?.present ? 1 : 0,
    rt60: r.rt60?.fullband_s ?? null,
  }));
}

function indexByName(nodes, base, file) {
  const name = base || file;
  if (!name) return null;
  const idx = nodes.findIndex((n) => n.name === name);
  if (idx >= 0) return idx;
  const idx2 = nodes.findIndex(
    (n) => file && (n.name.endsWith(file) || n.name === file),
  );
  return idx2 >= 0 ? idx2 : null;
}

export function buildLinks(matches, nodes) {
  return matches
    .map((m) => {
      const ai = indexByName(nodes, m.a_basename, m.a_file);
      const bi = indexByName(nodes, m.b_basename, m.b_file);
      return { source: ai, target: bi, score: m.score };
    })
    .filter((l) => l.source != null && l.target != null);
}

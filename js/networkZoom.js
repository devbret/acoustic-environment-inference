export function createZoom(layer) {
  return d3
    .zoom()
    .scaleExtent([0.1, 5])
    .on("zoom", (event) => {
      layer.attr("transform", event.transform);
    });
}

export function createZoomToFit(svg, zoom, nodes, w, h) {
  return function zoomToFit(pad = 40) {
    if (!nodes.length) return;
    const xs = nodes.map((n) => n.x),
      ys = nodes.map((n) => n.y);
    const minX = Math.min(...xs),
      maxX = Math.max(...xs);
    const minY = Math.min(...ys),
      maxY = Math.max(...ys);
    const dx = maxX - minX || 1,
      dy = maxY - minY || 1;
    const scale = Math.min((w - pad * 2) / dx, (h - pad * 2) / dy);
    const tx = (w - scale * (minX + maxX)) / 2;
    const ty = (h - scale * (minY + maxY)) / 2;
    const t = d3.zoomIdentity.translate(tx, ty).scale(scale);
    svg.transition().duration(350).call(zoom.transform, t);
  };
}

import { DEFAULT_THRESHOLD } from "./constants.js";
import { nodeDrag } from "./networkDrag.js";
import { buildLinks, buildNodes } from "./networkModel.js";
import { createZoom, createZoomToFit } from "./networkZoom.js";

export function renderNetwork(matches, results, threshold) {
  const nodes = buildNodes(results);
  const links = buildLinks(matches, nodes);

  const box = d3.select("#network");
  box.selectAll("*").remove();
  const w = box.node().clientWidth,
    h = box.node().clientHeight;

  const svg = box.append("svg").attr("width", w).attr("height", h);
  const g = svg.append("g").attr("class", "zoom-layer");

  const zoom = createZoom(g);
  svg.call(zoom).on("dblclick.zoom", null);

  const linkScale = d3
    .scaleLinear()
    .domain([threshold ?? DEFAULT_THRESHOLD, 1.0])
    .range([1, 6])
    .clamp(true);
  const color = d3.scaleLinear().domain([0, 1]).range(["#c3d1ff", "#8ab4ff"]);

  const sim = d3
    .forceSimulation(nodes)
    .force("charge", d3.forceManyBody().strength(-160))
    .force(
      "link",
      d3
        .forceLink(links)
        .distance((d) => 220 - d.score * 120)
        .strength(0.4),
    )
    .force("center", d3.forceCenter(w / 2, h / 2))
    .force("collide", d3.forceCollide(26));

  const link = g
    .append("g")
    .attr("stroke", "#3a4277")
    .attr("stroke-opacity", 0.8)
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke-width", (d) => linkScale(d.score));

  const node = g
    .append("g")
    .selectAll("g.node")
    .data(nodes)
    .join("g")
    .attr("class", "node")
    .call(nodeDrag(sim));

  node
    .append("circle")
    .attr("r", 12)
    .attr("fill", (d) => color(d.hum))
    .attr("stroke", "#1a1e3f")
    .attr("stroke-width", 1.5);

  node.append("title").text((d) => `${d.name}\nRT60: ${d.rt60 ?? "—"} s`);

  node
    .append("text")
    .text((d) => d.name)
    .attr("x", 15)
    .attr("y", 4)
    .attr("fill", "#dfe6ff")
    .attr("font-size", 11);

  sim.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);
    node.attr("transform", (d) => `translate(${d.x},${d.y})`);
  });

  const zoomToFit = createZoomToFit(svg, zoom, nodes, w, h);

  setTimeout(() => {
    zoomToFit();
  }, 600);

  return { zoomToFit };
}

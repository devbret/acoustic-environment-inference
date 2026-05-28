(() => {
  const fileSelect = document.getElementById("fileSelect");
  const metaPanel = document.getElementById("metaPanel");
  const els = {
    pipelineVersion: document.getElementById("pipelineVersion"),
    totalFiles: document.getElementById("totalFiles"),
    totalMatches: document.getElementById("totalMatches"),
    threshold: document.getElementById("threshold"),

    ovName: document.getElementById("ovName"),
    ovDur: document.getElementById("ovDur"),
    ovScene: document.getElementById("ovScene"),
    ovHum: document.getElementById("ovHum"),
    ovTags: document.getElementById("ovTags"),
    ovHash: document.getElementById("ovHash"),
    ovSize: document.getElementById("ovSize"),
    ovMtime: document.getElementById("ovMtime"),
  };

  let DATA = null;

  document.getElementById("btnFetch").addEventListener("click", async () => {
    try {
      const res = await fetch("output/summary.json");
      if (!res.ok) throw new Error("Fetch failed");
      const json = await res.json();
      loadData(json);
    } catch (e) {
      alert(
        "Could not fetch output/summary.json. Use file picker or drag & drop instead.",
      );
    }
  });
  document.getElementById("fileInput").addEventListener("change", async (e) => {
    const f = e.target.files?.[0];
    if (f) {
      const text = await f.text();
      try {
        loadData(JSON.parse(text));
      } catch (e) {
        alert("Invalid JSON file.");
      }
    }
  });
  const dz = document.getElementById("dropzone");
  dz.addEventListener("dragover", (e) => {
    e.preventDefault();
    dz.style.borderColor = "#8ab4ff";
  });
  dz.addEventListener("dragleave", (e) => {
    dz.style.borderColor = "#3b4291";
  });
  dz.addEventListener("drop", async (e) => {
    e.preventDefault();
    dz.style.borderColor = "#3b4291";
    const f = e.dataTransfer.files?.[0];
    if (f) {
      const text = await f.text();
      try {
        loadData(JSON.parse(text));
      } catch (e) {
        alert("Invalid JSON file.");
      }
    }
  });

  function loadData(json) {
    if (Array.isArray(json)) {
      DATA = {
        pipeline_version: "unknown",
        results: json,
        matches: [],
        match_config: { threshold: 0.6 },
      };
    } else {
      DATA = {
        pipeline_version: json.pipeline_version ?? "unknown",
        results: json.results ?? [],
        matches: json.matches ?? [],
        match_config: json.match_config ?? { threshold: 0.6 },
      };
    }
    metaPanel.classList.remove("hidden");
    els.pipelineVersion.textContent = DATA.pipeline_version;
    els.totalFiles.textContent = DATA.results.length;
    els.totalMatches.textContent = DATA.matches.length;
    els.threshold.textContent = DATA.match_config.threshold ?? "—";

    fileSelect.innerHTML = "";
    DATA.results.forEach((r, i) => {
      const opt = document.createElement("option");
      opt.value = i;
      opt.textContent = r.basename || r.file || `Item ${i + 1}`;
      fileSelect.appendChild(opt);
    });
    if (DATA.results.length) {
      fileSelect.selectedIndex = 0;
      renderForIndex(0);
    }

    renderMatches(DATA.matches);
    renderNetwork(DATA.matches, DATA.results);
  }

  fileSelect.addEventListener("change", (e) => {
    const idx = +e.target.value;
    renderForIndex(idx);
  });

  function renderForIndex(i) {
    const r = DATA.results[i];
    if (!r) return;

    els.ovName.textContent = r.basename || r.file || "—";
    els.ovDur.textContent =
      r.duration_s != null ? `${r.duration_s.toFixed(2)} s` : "—";
    els.ovScene.innerHTML = "";
    const scene = r.scene?.label || "—";
    const scConf = r.scene?.confidence;
    els.ovScene.append(scene);
    if (scConf != null) els.ovScene.append(` (conf ${scConf})`);
    const hum = r.hum || {};
    els.ovHum.textContent = hum.present
      ? `Yes, ${fmtHz(hum.fundamental_hz)} (SNR ${fmtNum(hum.peak_snr_db)} dB)`
      : "No";

    els.ovTags.innerHTML = "";
    (r.notes || []).forEach((tag) => {
      const span = document.createElement("span");
      span.className = "tag";
      if (/strong_reverb|large_space/.test(tag)) span.classList.add("warn");
      if (/very_low_reverb|open_space/.test(tag)) span.classList.add("accent");
      if (/mains_hum/.test(tag)) span.classList.add("alert");
      span.textContent = tag;
      els.ovTags.appendChild(span);
    });

    els.ovHash.textContent = r.provenance?.sha256
      ? r.provenance.sha256.slice(0, 16) + "…"
      : "—";
    els.ovSize.textContent = r.provenance?.size_bytes
      ? fmtBytes(r.provenance.size_bytes)
      : "—";
    els.ovMtime.textContent = r.provenance?.mtime_utc || "—";

    drawRT60("#rt60Chart", r.rt60);
    drawHum("#humChart", r.hum);
    drawBands("#bandsChart", r.bands_db);
    drawFingerprint("#fpChart", r.fingerprint?.narrowband_peaks || []);
    drawTransients("#transients", r.transients);
    drawTemporal("#temporal", r.temporal_clues);
  }

  function fmtHz(v) {
    return v == null ? "—" : `${(+v).toFixed(1)} Hz`;
  }
  function fmtNum(v) {
    return v == null ? "—" : (+v).toFixed(2);
  }
  function fmtBytes(b) {
    if (b == null) return "—";
    const u = ["B", "KB", "MB", "GB", "TB"];
    let i = 0;
    let n = +b;
    while (n >= 1024 && i < u.length - 1) {
      n /= 1024;
      i++;
    }
    return `${n.toFixed(1)} ${u[i]}`;
  }

  function drawRT60(sel, rt) {
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
        `Confidence: ${
          rt?.confidence != null ? rt.confidence.toFixed(2) : "—"
        }`,
      );
  }

  function drawHum(sel, hum) {
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

  function drawBands(sel, bands) {
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

  function drawFingerprint(sel, peaks) {
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

  function drawTransients(sel, t) {
    const wrap = d3.select(sel);
    wrap.selectAll("*").remove();
    const entries = [
      { k: "Onset Count", v: t?.onset_count },
      {
        k: "Onset Rate (/min)",
        v:
          t?.onset_rate_per_min != null ? t.onset_rate_per_min.toFixed(2) : "—",
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
        v:
          t?.max_onset_strength != null ? t.max_onset_strength.toFixed(2) : "—",
      },
    ];
    wrap
      .selectAll("div.meta")
      .data(entries)
      .join("div")
      .attr("class", "meta")
      .html((d) => `<strong>${d.k}:</strong> ${d.v ?? "—"}`);
  }

  function drawTemporal(sel, t) {
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

  function renderMatches(matches) {
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
        tr.append("td").text(m.components?.rt60_sim?.toFixed(2));
        tr.append("td").text(m.components?.hum_sim?.toFixed(2));
        tr.append("td").html(
          (m.notes || []).map((n) => `<span class="tag">${n}</span>`).join(" "),
        );
      });
  }

  let _networkAPI = null;

  function renderNetwork(matches, results) {
    const idMap = new Map();
    results.forEach((r, i) => idMap.set(r.file || r.basename || String(i), i));

    const nodes = results.map((r, i) => ({
      id: i,
      name: r.basename || r.file || `Item ${i + 1}`,
      hum: r.hum?.present ? 1 : 0,
      rt60: r.rt60?.fullband_s ?? null,
    }));

    const links = matches
      .map((m) => {
        const ai = indexByName(m.a_basename, m.a_file);
        const bi = indexByName(m.b_basename, m.b_file);
        return { source: ai, target: bi, score: m.score };
      })
      .filter((l) => l.source != null && l.target != null);

    function indexByName(base, file) {
      const name = base || file;
      if (!name) return null;
      const idx = nodes.findIndex((n) => n.name === name);
      if (idx >= 0) return idx;
      const idx2 = nodes.findIndex(
        (n) => file && (n.name.endsWith(file) || n.name === file),
      );
      return idx2 >= 0 ? idx2 : null;
    }

    const box = d3.select("#network");
    box.selectAll("*").remove();
    const w = box.node().clientWidth,
      h = box.node().clientHeight;

    const svg = box.append("svg").attr("width", w).attr("height", h);
    const bg = svg
      .append("rect")
      .attr("x", 0)
      .attr("y", 0)
      .attr("width", w)
      .attr("height", h)
      .attr("fill", "#0f1220")
      .attr("opacity", 0);

    const g = svg.append("g").attr("class", "zoom-layer");

    const zoom = d3
      .zoom()
      .scaleExtent([0.1, 5])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom).on("dblclick.zoom", null);

    const linkScale = d3
      .scaleLinear()
      .domain([0.6, 1.0])
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

    setTimeout(() => {
      zoomToFit();
    }, 600);

    _networkAPI = { zoomToFit };

    function nodeDrag(sim) {
      function dragstarted(event, d) {
        if (!event.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
        event.sourceEvent.stopPropagation();
      }
      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }
      function dragended(event, d) {
        if (!event.active) sim.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }
      return d3
        .drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    }

    function zoomToFit(pad = 40) {
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
    }

    document.getElementById("fitNetwork").onclick = () =>
      _networkAPI && _networkAPI.zoomToFit();
  }
})();

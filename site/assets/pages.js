// Seiten hinter #/…: Suche, Einheit, Adresse, Gemeinde, Orte, Vorbehalte.
// Daten aus data/ (scripts/build_pages.py), in Teilen geladen.
(async function () {
  const lang = (document.documentElement.lang || "de").slice(0, 2);
  const t = await fetch(`i18n/${lang}.json`).then(r => r.json());
  const nf = new Intl.NumberFormat("de-CH");
  const n = v => nf.format(v);
  const el = (tag, attrs = {}, ...kids) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") e.className = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
    for (const k of kids) if (k !== null && k !== undefined && k !== false) e.append(k);
    return e;
  };
  const view = document.getElementById("view");
  const overview = document.getElementById("overview");
  const cache = new Map();
  // Teile liegen gzip-gepackt (.json.gz) und werden hier entpackt
  const get = url => {
    if (!cache.has(url)) cache.set(url, fetch(url).then(r => {
      if (!r.ok) throw new Error(url);
      return url.endsWith(".gz") ? new Response(r.body.pipeThrough(new DecompressionStream("gzip"))).json() : r.json();
    }));
    return cache.get(url);
  };

  // gleich gerechnet wie fold() und fnv() in scripts/build_pages.py
  const fold = s => (s || "").replace(/ß/g, "ss").replace(/[æÆ]/g, "ae").replace(/[œŒ]/g, "oe")
    .toLowerCase().normalize("NFD").replace(/\p{M}/gu, "").replace(/[^a-z]/g, "");
  const strip = s => (s || "").trim().replace(/^(von|v\.|de|du|la|le|van|zum|zur)\s+/i, "");
  const shardOf = s => { const k = fold(strip(s)); return k ? (k + "__").slice(0, 2) : "__"; };
  const fnv = s => {
    let h = 0x811c9dc5;
    for (const b of new TextEncoder().encode(s)) { h ^= b; h = Math.imul(h, 0x01000193) >>> 0; }
    return (h & 0xff).toString(16).padStart(2, "0");
  };
  const hashArgs = () => {
    const [path, query = ""] = location.hash.slice(2).split("?");
    return [path.split("/").map(decodeURIComponent), new URLSearchParams(query)];
  };
  const link = (href, text, cls) => el("a", cls ? { href, class: cls } : { href }, text);
  const placeHref = m => `#/g/${encodeURIComponent(m)}`;
  const entries = c => (c === 1 ? t.pg_entry_one : t.pg_entries).replace("{n}", n(c));
  const years = y => (y[0] === y[1] ? `${y[0]}` : `${y[0]}–${y[1]}`);
  const tierBadge = tier => tier ? el("span", { class: `pill tier-${tier}` }, t[`tier_${tier}`] || tier) : "";
  const srcBadge = s => el("span", { class: `pill src-${s}` }, s === "ptt" ? t.pg_src_ptt : t.pg_src_ab);

  let places;
  const placeIndex = async () => {
    if (!places) places = new Map((await get("data/places.json")).map(([name, canton, total]) => [name, { canton, total }]));
    return places;
  };

  // Karte (Leaflet erst laden, wenn eine Seite sie braucht)
  let leaflet;
  const loadLeaflet = () => leaflet ??= new Promise((res, rej) => {
    document.head.append(el("link", { rel: "stylesheet", href: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" }));
    const s = el("script", { src: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js" });
    s.onload = () => res(window.L); s.onerror = rej;
    document.head.append(s);
  });
  const map = async (box, geo, label) => {
    if (!geo) { box.remove(); return; }
    try {
      const L = await loadLeaflet();
      const m = L.map(box, { scrollWheelZoom: false }).setView(geo, 12);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18, attribution: "© OpenStreetMap",
      }).addTo(m);
      L.circleMarker(geo, { radius: 8 }).addTo(m).bindTooltip(label);
    } catch { box.replaceChildren(el("p", { class: "muted" }, t.pg_map_error)); }
  };

  // ── Ansichten ────────────────────────────────────────────────────────────
  let focusPlace = false;
  const srcSelect = value => {
    const lab = el("label", { class: "ctl" }, el("span", {}, t.pg_src_filter),
      el("select", { name: "src" }, ...[["", t.pg_src_all], ["t", t.pg_src_only_ptt], ["a", t.pg_src_only_ab]].map(([v, txt]) => {
        const o = el("option", { value: v }, txt); if (v === value) o.selected = true; return o;
      })));
    return lab;
  };
  const srcOk = (flag, want) => !want || flag === want || flag === "b";
  const searchTabs = active => el("nav", { class: "tabs", "aria-label": t.pg_search_h },
    el("a", { href: "#/suche", class: active === "name" ? "on" : "", "aria-current": active === "name" ? "page" : "false" }, t.pg_tab_name),
    el("a", { href: "#/suche?b=", class: active === "beruf" ? "on" : "", "aria-current": active === "beruf" ? "page" : "false" }, t.pg_tab_occ));

  async function search(params) {
    if (params.has("b")) return occSearch(params);
    const q = params.get("q") || "", m = params.get("m") || "", src = params.get("s") || "";
    const srcSel = srcSelect(src);
    const input = el("input", { type: "search", value: q, placeholder: t.pg_search_ph, "aria-label": t.pg_search_ph, class: "q" });
    const muni = el("input", { type: "search", value: m, placeholder: t.pg_search_place, "aria-label": t.pg_search_place, class: "q q-place" });
    const out = el("div", { class: "results" });
    const go = () => { location.replace(`#/suche?q=${encodeURIComponent(input.value)}&m=${encodeURIComponent(muni.value)}&s=${srcSel.querySelector("select").value}`); };
    srcSel.querySelector("select").addEventListener("change", go);
    let timer;
    const onInput = () => { clearTimeout(timer); timer = setTimeout(go, 300); };
    input.addEventListener("input", onInput);
    muni.addEventListener("input", onInput);
    view.replaceChildren(el("h1", {}, t.pg_search_h), searchTabs("name"), el("p", { class: "intro" }, t.pg_search_p),
      el("div", { class: "searchbar" }, input, muni, srcSel), out);
    muni.addEventListener("focus", () => { focusPlace = true; });
    input.addEventListener("focus", () => { focusPlace = false; });
    const f = focusPlace ? muni : input;
    f.focus();
    f.setSelectionRange(f.value.length, f.value.length);
    const words = q.split(/[\s,]+/).filter(Boolean);
    if (!words.length || fold(strip(q)).length < 2) { out.append(el("p", { class: "muted" }, t.pg_search_hint)); return; }
    const first = fold(strip(q).split(/[\s,]+/)[0]);
    const rest = words.slice(1).map(fold).filter(Boolean);
    const mf = fold(m);
    let rows;
    try { rows = await get(`data/names/${shardOf(q)}.json.gz`); } catch { rows = []; }
    const hits = rows.filter(r => {
      const lk = fold(strip(r[1]));
      return lk.startsWith(first) && rest.every(w => fold(r[1]).includes(w) || fold(r[8]).includes(w))
        && (!mf || fold(r[2]).includes(mf)) && srcOk(r[9], src);
    });
    out.replaceChildren(el("p", { class: "count" }, t.pg_hits.replace("{n}", n(hits.length))
      + (hits.length > 300 ? " " + t.pg_hits_more : "")));
    const ul = el("ul", { class: "hitlist" });
    for (const [id, label, place, y0, y1, kind, cnt, tier, occ] of hits.slice(0, 300)) {
      ul.append(el("li", {},
        link(`#/e/${id}`, label, "hit"),
        el("span", { class: "meta" }, `${place} · ${years([y0, y1])} · ${kind === "f" ? t.pg_kind_firma : t.pg_kind_person} · ${entries(cnt)}`),
        tier ? el("span", { class: "pill tier-" + (tier === "w" ? "wahrscheinlich" : "möglich") }, t.pg_authority) : "",
        occ ? el("span", { class: "occ" }, occ) : ""));
    }
    out.append(ul);
  }

  async function entity([id]) {
    let shard;
    try { shard = await get(`data/e/${id.slice(1, 3)}.json.gz`); } catch { shard = {}; }
    const e = shard[id];
    if (!e) { view.replaceChildren(el("h1", {}, t.pg_not_found)); return; }
    document.title = `${e.n} · Vernetzte Schweiz`;
    const head = el("header", { class: "ent-head" },
      el("p", { class: "kicker" }, e.k === "firma" ? t.pg_kind_firma : t.pg_kind_person),
      el("h1", {}, e.n),
      el("p", { class: "lead" }, link(placeHref(e.m), e.m), e.c ? ` (${e.c})` : "", ` · ${years(e.y)}`,
        e.ph ? ` · ${t.pg_phone} ${e.ph}` : ""));
    const parts = [head];
    if (e.au) {
      const a = e.au;
      const ids = [
        link(`https://www.wikidata.org/wiki/${a.qid}`, `Wikidata ${a.qid}`),
        a.hls_id ? link(`https://hls-dhs-dss.ch/de/articles/${a.hls_id}/`, `HLS ${a.hls_id}`) : "",
        a.gnd ? link(`https://d-nb.info/gnd/${a.gnd}`, `GND ${a.gnd}`) : "",
      ].filter(Boolean).flatMap((x, i) => i ? [" · ", x] : [x]);
      parts.push(el("section", { class: "card auth" },
        el("h2", {}, t.pg_auth_h, " ", tierBadge(a.tier)),
        el("p", {}, el("b", {}, a.label || a.qid), a.birth ? ` (${a.birth.slice(0, 4)}–${(a.death || "").slice(0, 4)})` : ""),
        el("p", {}, ...ids),
        el("p", { class: "sub" }, `${a.source === "stadt" ? t.pg_auth_city : t.pg_auth_ptt} ${t.pg_auth_evidence} ${a.evidence}`),
        a.hls_check && a.hls_check !== "ungeprüft" ? el("p", { class: "sub" }, `${t.pg_auth_check} ${a.hls_check}`) : "",
        el("p", { class: "sub note" }, t.pg_auth_note)));
    }
    parts.push(timeline(e.r));
    // gleiche Zeile im selben Jahr (mehrere Ausgaben, Haupt- und Nachtrag) nur einmal, mit allen Fundstellen
    const rows = new Map();
    for (const r of e.r) {
      const k = [r.y, r.s, r.t, r.a, r.ph].join("\u0001");
      if (!rows.has(k)) rows.set(k, { ...r, cites: [] });
      rows.get(k).cites.push(r);
    }
    const tbody = el("tbody");
    for (const r of rows.values()) {
      tbody.append(el("tr", {},
        el("td", { class: "yr" }, String(r.y)),
        el("td", {}, srcBadge(r.s)),
        el("td", {}, r.t),
        el("td", {}, r.ak ? link(`#/a/${encodeURIComponent(r.ak)}`, r.a) : (r.a || "")),
        el("td", { class: "ph" }, r.ph || ""),
        el("td", { class: "cite" }, ...r.cites.flatMap((c, i) => [i ? el("br") : "", c.u ? link(c.u, c.c) : c.c]))));
    }
    parts.push(el("h2", {}, t.pg_entries_h.replace("{n}", n(e.r.length))),
      rows.size < e.r.length ? el("p", { class: "intro" }, t.pg_entries_merged.replace("{n}", n(rows.size))) : "",
      el("div", { class: "grid-scroll" }, el("table", { class: "entries" },
        el("thead", {}, el("tr", {}, ...[t.pg_col_year, t.pg_col_src, t.pg_col_text, t.pg_col_addr, t.pg_col_phone, t.pg_col_cite].map(h => el("th", {}, h)))),
        tbody)));
    if (e.mb) {
      parts.push(el("h2", {}, t.pg_maybe_h), el("p", { class: "intro" }, t.pg_maybe_p),
        el("ul", { class: "maybe" }, ...e.mb.map(m => el("li", {}, el("b", {}, String(m.y)), " ", tierBadge(m.tier), " ", m.t))));
    }
    const box = el("div", { class: "map" });
    parts.push(el("h2", {}, t.pg_map_h), box, el("p", { class: "sub note" }, t.pg_map_note));
    view.replaceChildren(...parts);
    const idx = await placeIndex();
    const p = idx.get(e.m);
    const g = p ? (await get(`data/g/${fnv(e.m)}.json.gz`))[e.m] : null;
    map(box, g && g.geo, e.m);
  }

  function timeline(rs) {
    const y0 = 1860, y1 = 1914, w = 100 / (y1 - y0 + 1);
    const bar = el("div", { class: "tl", role: "img", "aria-label": t.pg_timeline_label });
    const seen = new Set();
    for (const r of rs) {
      const k = `${r.y}-${r.s}`;
      if (seen.has(k)) continue;
      seen.add(k);
      bar.append(el("span", { class: `tl-dot src-${r.s}`, style: `left:${(r.y - y0) * w}%;width:${w}%`, title: `${r.y} · ${r.s === "ptt" ? t.pg_src_ptt : t.pg_src_ab}` }));
    }
    const ticks = el("div", { class: "tl-ticks" }, ...[1860, 1870, 1880, 1890, 1900, 1910].map(y => el("span", { style: `left:${(y - y0) * w}%` }, String(y))));
    return el("section", { class: "tl-box" }, el("h2", {}, t.pg_timeline_h), bar, ticks,
      el("ul", { class: "legend" }, el("li", {}, el("span", { class: "sw src-ptt" }), t.pg_src_ptt), el("li", {}, el("span", { class: "sw src-ab" }), t.pg_src_ab)));
  }

  async function address([key]) {
    let shard;
    try { shard = await get(`data/a/${fnv(key)}.json.gz`); } catch { shard = {}; }
    const a = shard[key];
    if (!a) { view.replaceChildren(el("h1", {}, t.pg_not_found)); return; }
    document.title = `${a.n}, ${a.m} · Vernetzte Schweiz`;
    const tbody = el("tbody");
    for (const r of a.r) {
      tbody.append(el("tr", {}, el("td", { class: "yr" }, String(r.y)), el("td", {}, srcBadge(r.s)), el("td", {}, link(`#/e/${r.e}`, r.t))));
    }
    view.replaceChildren(
      el("p", { class: "kicker" }, t.pg_address),
      el("h1", {}, a.n),
      el("p", { class: "lead" }, link(placeHref(a.m), a.m), ` · ${entries(a.r.length)}`),
      el("p", { class: "intro" }, t.pg_address_p),
      el("div", { class: "grid-scroll" }, el("table", { class: "entries" },
        el("thead", {}, el("tr", {}, el("th", {}, t.pg_col_year), el("th", {}, t.pg_col_src), el("th", {}, t.pg_col_text))), tbody)));
  }

  async function place([name]) {
    const idx = await placeIndex();
    const p = idx.get(name);
    if (!p) { view.replaceChildren(el("h1", {}, t.pg_not_found)); return; }
    const g = (await get(`data/g/${fnv(name)}.json.gz`))[name];
    document.title = `${g.n} · Vernetzte Schweiz`;
    const ys = Object.entries(g.years).map(([y, c]) => [+y, c]);
    const max = Math.max(1, ...ys.map(x => x[1]));
    const chart = el("div", { class: "bars", role: "img", "aria-label": t.pg_place_years },
      ...ys.map(([y, c]) => el("div", { class: "bar", title: `${y}: ${n(c)}` },
        el("span", { class: "fill", style: `height:${Math.max(2, (c / max) * 100)}%` }),
        y % 5 === 0 || y === ys[0][0] || y === ys[ys.length - 1][0] ? el("span", { class: "lbl" }, String(y)) : "")));
    const top = el("ol", { class: "top" }, ...g.top.map(([s, c]) =>
      el("li", {}, link(`#/suche?q=${encodeURIComponent(s)}&m=${encodeURIComponent(g.n)}`, s), ` ${t.pg_top_count.replace("{n}", n(c))}`)));
    const box = el("div", { class: "map" });
    view.replaceChildren(
      el("p", { class: "kicker" }, t.pg_place),
      el("h1", {}, g.n),
      el("p", { class: "lead" }, [g.c, g.bfs ? `BFS ${g.bfs}` : "", t.pg_place_entities.replace("{p}", n(g.ent.person || 0)).replace("{f}", n(g.ent.firma || 0))].filter(Boolean).join(" · ")),
      el("h2", {}, t.pg_place_years), el("p", { class: "intro" }, t.pg_place_years_p), ys.length ? chart : el("p", { class: "muted" }, "–"),
      el("h2", {}, t.pg_place_top), el("p", { class: "intro" }, t.pg_place_top_p), top,
      el("p", {}, link(`#/suche?m=${encodeURIComponent(g.n)}`, t.pg_place_search)),
      el("h2", {}, t.pg_map_h), box);
    map(box, g.geo, g.n);
  }

  async function placeList(params) {
    const idx = await placeIndex();
    const q = params.get("q") || "";
    const input = el("input", { type: "search", value: q, placeholder: t.pg_places_ph, "aria-label": t.pg_places_ph, class: "q" });
    const list = el("ul", { class: "hitlist cols" });
    const render = () => {
      const f = fold(input.value);
      const rows = [...idx.entries()].filter(([name]) => !f || fold(name).includes(f)).sort((a, b) => b[1].total - a[1].total);
      list.replaceChildren(...rows.slice(0, 400).map(([name, p]) =>
        el("li", {}, link(placeHref(name), name), el("span", { class: "meta" }, ` ${p.canton} · ${n(p.total)}`))));
    };
    input.addEventListener("input", render);
    view.replaceChildren(el("h1", {}, t.pg_places_h), el("p", { class: "intro" }, t.pg_places_p),
      el("div", { class: "searchbar" }, input), list);
    render();
  }

  function caveats() {
    view.replaceChildren(el("h1", {}, t.pg_caveats_h),
      ...t.pg_caveats.map(([h, p]) => el("section", { class: "caveat" }, el("h2", {}, h), el("p", {}, p))));
  }


  // ── Karten (M6) ──────────────────────────────────────────────────────────
  const CH = [[45.78, 5.9], [47.86, 10.55]];
  let mapsData;
  const maps = async () => mapsData ??= await get("data/maps.json.gz");
  let heatLoaded;
  const loadHeat = async () => {
    const L = await loadLeaflet();
    heatLoaded ??= new Promise((res, rej) => {
      const s = el("script", { src: "https://cdnjs.cloudflare.com/ajax/libs/leaflet.heat/0.2.0/leaflet-heat.js" });
      s.onload = () => res(L); s.onerror = rej;
      document.head.append(s);
    });
    return heatLoaded;
  };
  const chMap = async box => {
    const L = await loadHeat();
    const m = L.map(box, { scrollWheelZoom: false, zoomSnap: 0.25 }).fitBounds(CH);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 16, attribution: "© OpenStreetMap" }).addTo(m);
    return [L, m];
  };
  // Kreise nach Anzahl (Fläche ∝ Anzahl)
  const circles = (L, counts, places, color, label) => L.layerGroup([...counts].map(([p, c]) => {
    const [name, , lat, lon] = places[p];
    return L.circleMarker([lat, lon], { radius: Math.max(3, Math.sqrt(c) * 1.6), color, weight: 1, fillOpacity: 0.45 })
      .bindTooltip(`${name}: ${label(c)}`);
  }));
  const heat = (L, counts, places) => {
    const vals = [...counts.values()].sort((a, b) => a - b);
    const max = vals.length ? vals[Math.floor(vals.length * 0.97)] || vals[vals.length - 1] : 1;
    return L.heatLayer([...counts].map(([p, c]) => [places[p][2], places[p][3], c]), { radius: 22, blur: 18, maxZoom: 11, max: Math.max(1, max) });
  };
  const select = (opts, value, label) => el("label", { class: "ctl" }, el("span", {}, label),
    el("select", {}, ...opts.map(([v, txt]) => { const o = el("option", { value: v }, txt); if (String(v) === String(value)) o.selected = true; return o; })));
  const yearBars = (counts, y0, y1, current, onPick) => {
    const max = Math.max(1, ...counts);
    return el("div", { class: "bars small", role: "img", "aria-label": t.mp_bars_label },
      ...counts.map((c, i) => {
        const y = y0 + i;
        const b = el("div", { class: "bar" + (y === current ? " on" : ""), title: `${y}: ${n(c)}` },
          el("span", { class: "fill", style: `height:${Math.max(c ? 2 : 0, (c / max) * 100)}%` }),
          y % 5 === 0 || y === y0 || y === y1 ? el("span", { class: "lbl" }, String(y)) : "");
        if (onPick) b.addEventListener("click", () => onPick(y));
        return b;
      }));
  };

  async function occSearch(params) {
    const b = params.get("b") || "", m = params.get("m") || "", per = params.get("p") || "alle", src = params.get("s") || "";
    const srcSel = srcSelect(src);
    const input = el("input", { type: "search", value: b, placeholder: t.pg_occ_ph, "aria-label": t.pg_occ_ph, class: "q" });
    const muni = el("input", { type: "search", value: m, placeholder: t.pg_search_place, "aria-label": t.pg_search_place, class: "q q-place" });
    const D = await maps();
    const perSel = select(D.periods.map(x => [x, x === "alle" ? t.mp_all_years : x]), per, t.mp_period);
    const go = () => location.replace(`#/suche?b=${encodeURIComponent(input.value)}&m=${encodeURIComponent(muni.value)}&p=${encodeURIComponent(perSel.querySelector("select").value)}&s=${srcSel.querySelector("select").value}`);
    let timer;
    const onInput = () => { clearTimeout(timer); timer = setTimeout(go, 350); };
    input.addEventListener("input", onInput);
    muni.addEventListener("input", onInput);
    perSel.querySelector("select").addEventListener("change", go);
    srcSel.querySelector("select").addEventListener("change", go);
    muni.addEventListener("focus", () => { focusPlace = true; });
    input.addEventListener("focus", () => { focusPlace = false; });
    const out = el("div", { class: "results" });
    view.replaceChildren(el("h1", {}, t.pg_search_h), searchTabs("beruf"), el("p", { class: "intro" }, t.pg_occ_p),
      el("div", { class: "searchbar" }, input, muni, perSel, srcSel), out);
    const f = focusPlace ? muni : input;
    f.focus(); f.setSelectionRange(f.value.length, f.value.length);
    const toks = b.split(/[\s,;]+/).map(fold).filter(w => w.length >= 3);
    if (!toks.length) { out.append(el("p", { class: "muted" }, t.pg_occ_hint)); return; }
    let shard;
    try { shard = await get(`data/ow/${toks[0].slice(0, 2)}.json.gz`); } catch { shard = { w: {}, e: {} }; }
    const ids = new Set();
    for (const [w, list] of Object.entries(shard.w)) if (w.startsWith(toks[0])) list.forEach(id => ids.add(id));
    const [a0, a1] = per === "alle" ? [1800, 1914] : per.split("–").map(Number);
    const mf = fold(m);
    const hits = [...ids].map(id => [id, ...shard.e[id]]).filter(([, label, p, y0, y1, occ, flag]) =>
      toks.slice(1).every(w => fold(occ).includes(w)) && (!mf || fold(D.places[p][0]).includes(mf)) && y0 <= a1 && y1 >= a0
      && srcOk(flag, src));
    hits.sort((x, y) => D.places[x[2]][0].localeCompare(D.places[y[2]][0], "de") || x[1].localeCompare(y[1], "de"));
    const byPlace = new Map();
    for (const h of hits) byPlace.set(h[2], (byPlace.get(h[2]) || 0) + 1);
    out.replaceChildren(el("p", { class: "count" }, t.pg_occ_hits.replace("{n}", n(hits.length)).replace("{g}", n(byPlace.size))));
    if (!hits.length) return;
    const box = el("div", { class: "map tall" });
    out.append(box, el("p", { class: "sub note" }, t.pg_occ_map_note));
    const top = [...byPlace].sort((x, y) => y[1] - x[1]).slice(0, 12);
    out.append(el("p", { class: "intro" }, t.pg_occ_top, " ", ...top.flatMap(([p, c], i) => [i ? ", " : "", link(placeHref(D.places[p][0]), D.places[p][0]), ` (${n(c)})`])));
    const ul = el("ul", { class: "hitlist" });
    for (const [id, label, p, y0, y1, occ] of hits.slice(0, 300)) {
      ul.append(el("li", {}, link(`#/e/${id}`, label, "hit"), el("span", { class: "meta" }, `${D.places[p][0]} · ${years([y0, y1])}`), el("span", { class: "occ" }, occ)));
    }
    out.append(el("h2", {}, t.pg_occ_list), hits.length > 300 ? el("p", { class: "muted" }, t.pg_hits_more) : "", ul);
    try {
      const [L, mp] = await chMap(box);
      circles(L, byPlace, D.places, "#9e323c", c => t.pg_occ_place_hits.replace("{n}", n(c))).addTo(mp);
    } catch { box.replaceChildren(el("p", { class: "muted" }, t.pg_map_error)); }
  }

  async function karten(params) {
    const v = params.get("v") || "telefon";
    const D = await maps();
    const tabs = el("nav", { class: "tabs" }, ...[["telefon", t.mp_tab_phone], ["berufe", t.mp_tab_occ], ["namen", t.mp_tab_names]].map(([k, txt]) =>
      el("a", { href: `#/karten?v=${k}`, class: v === k ? "on" : "", "aria-current": v === k ? "page" : "false" }, txt)));
    const set = upd => {
      const p = new URLSearchParams(params);
      for (const [k, val] of Object.entries(upd)) p.set(k, val);
      location.replace(`#/karten?${p}`);
    };
    const box = el("div", { class: "map tall" });
    const side = el("div", { class: "map-side" });
    const ctl = el("div", { class: "controls" });
    view.replaceChildren(el("h1", {}, t.mp_h), tabs, el("p", { class: "intro" }, t[`mp_${v}_p`]), ctl, box, side,
      el("p", { class: "sub note" }, t[`mp_${v}_note`]));
    let L, mp;
    try { [L, mp] = await chMap(box); } catch { box.replaceChildren(el("p", { class: "muted" }, t.pg_map_error)); return; }

    if (v === "telefon") {
      const year = +(params.get("y") || 1914), mode = params.get("mode") || "neu";
      const kind = params.get("k") || "alle", cls = params.get("c") || "alle", can = params.get("kt") || "alle";
      const cantons = [...new Set(D.places.map(p => p[1]).filter(Boolean))].sort();
      const ok = e => (kind === "alle" || e[3] === (kind === "firma" ? 1 : 0)) && (cls === "alle" || e[4] === +cls)
        && (can === "alle" || D.places[e[0]][1] === can);
      const ents = D.ent.filter(ok);
      const counts = new Map();
      for (const e of ents) if (mode === "neu" ? e[1] === year : e[1] <= year) counts.set(e[0], (counts.get(e[0]) || 0) + 1);
      const perYear = Array.from({ length: 35 }, (_, i) => ents.filter(e => e[1] === 1880 + i).length);
      const slider = el("input", { type: "range", min: 1880, max: 1914, step: 1, value: year, "aria-label": t.mp_year });
      slider.addEventListener("change", () => set({ y: slider.value }));
      slider.addEventListener("input", () => { yl.textContent = slider.value; });
      const yl = el("b", { class: "yr-label" }, String(year));
      ctl.append(el("label", { class: "ctl wide" }, el("span", {}, t.mp_year), slider, yl),
        select([["neu", t.mp_mode_new], ["bis", t.mp_mode_cum]], mode, t.mp_mode),
        select([["alle", t.mp_all], ["person", t.pg_kind_person], ["firma", t.pg_kind_firma]], kind, t.mp_kind),
        select([["alle", t.mp_all], ...D.classes.map(([k, lab], i) => [i, lab])], cls, t.mp_class),
        select([["alle", t.mp_all], ...cantons.map(c => [c, c])], can, t.mp_canton));
      ctl.querySelectorAll("select").forEach((s, i) => s.addEventListener("change", () => set({ [["mode", "k", "c", "kt"][i]]: s.value })));
      heat(L, counts, D.places).addTo(mp);
      const total = [...counts.values()].reduce((a, b) => a + b, 0);
      const eds = D.editions.filter(e => e.includes(year)).length;
      side.append(el("p", { class: "count" }, (mode === "neu" ? t.mp_new_count : t.mp_cum_count).replace("{n}", n(total)).replace("{y}", year).replace("{g}", n(counts.size))),
        el("p", { class: "sub" }, t.mp_editions.replace("{n}", n(eds)).replace("{y}", year)),
        el("h2", {}, t.mp_first_year_h), yearBars(perYear, 1880, 1914, year, y => set({ y })));
    } else if (v === "berufe") {
      const cls = +(params.get("c") ?? 1), per = params.get("p") || "alle", metric = params.get("m") || "anzahl";
      const [a0, a1] = per === "alle" ? [1880, 1914] : per.split("–").map(Number);
      const present = D.ent.filter(e => e[1] <= a1 && e[2] >= a0);
      const all = new Map(), hit = new Map();
      for (const e of present) {
        all.set(e[0], (all.get(e[0]) || 0) + 1);
        if (e[4] === cls) hit.set(e[0], (hit.get(e[0]) || 0) + 1);
      }
      ctl.append(select(D.classes.map(([k, lab], i) => [i, lab]), cls, t.mp_class),
        select(D.periods.map(x => [x, x === "alle" ? t.mp_all_years : x]), per, t.mp_period),
        select([["anzahl", t.mp_metric_count], ["anteil", t.mp_metric_share]], metric, t.mp_metric));
      ctl.querySelectorAll("select").forEach((s, i) => s.addEventListener("change", () => set({ [["c", "p", "m"][i]]: s.value })));
      if (metric === "anzahl") heat(L, hit, D.places).addTo(mp);
      else {
        const steps = ["#f3d9da", "#e7aeb2", "#d47b82", "#b54a54", "#7d1f28"];
        const rows = [...all].filter(([, c]) => c >= 20).map(([p, c]) => [p, c, (hit.get(p) || 0) / c]);
        // Stufen: 0 % für sich, darüber Quartile der Gemeinden mit Anteil > 0
        const shares = rows.map(r => r[2]).filter(x => x > 0).sort((a, b) => a - b);
        const q = k => shares[Math.floor((shares.length - 1) * k)] ?? 0;
        const cuts = [0, q(0.25), q(0.5), q(0.75)];
        const pct = x => `${Math.round(x * 1000) / 10}\u00a0%`;
        L.layerGroup(rows.map(([p, c, sh]) => {
          const [name, , lat, lon] = D.places[p];
          const col = sh === 0 ? steps[0] : steps[1 + cuts.slice(1).filter(x => sh > x).length];
          return L.circleMarker([lat, lon], { radius: 3 + Math.min(12, Math.sqrt(c) / 3), color: "#555", weight: 0.5, fillColor: col, fillOpacity: 0.85 })
            .bindTooltip(`${name}: ${pct(sh)} (${n(hit.get(p) || 0)} / ${n(c)})`);
        })).addTo(mp);
        const labels = ["0\u00a0%", `bis ${pct(cuts[1])}`, `${pct(cuts[1])}–${pct(cuts[2])}`, `${pct(cuts[2])}–${pct(cuts[3])}`, `über ${pct(cuts[3])}`];
        side.append(el("ul", { class: "legend" }, ...steps.map((c, i) => el("li", {}, el("span", { class: "sw", style: `background:${c}` }), labels[i]))),
          el("p", { class: "sub" }, t.mp_share_size));
      }
      const tot = [...hit.values()].reduce((a, b) => a + b, 0);
      const ranked = [...hit].filter(([p]) => (all.get(p) || 0) >= 20).sort((x, y) => y[1] / all.get(y[0]) - x[1] / all.get(x[0])).slice(0, 10);
      side.prepend(el("p", { class: "count" }, t.mp_occ_count.replace("{n}", n(tot)).replace("{c}", D.classes[cls][1]).replace("{g}", n(hit.size))));
      side.append(el("h2", {}, t.mp_occ_top), el("ol", { class: "top" }, ...ranked.map(([p, c]) =>
        el("li", {}, link(placeHref(D.places[p][0]), D.places[p][0]), ` ${Math.round(c / all.get(p) * 1000) / 10} % (${n(c)} / ${n(all.get(p))})`))),
        el("p", {}, link(`#/suche?b=`, t.mp_occ_free)));
    } else {
      const per = params.get("p") || "alle", name = params.get("n") || "";
      const inp = el("input", { type: "search", value: name, placeholder: t.mp_name_ph, "aria-label": t.mp_name_ph, class: "q" });
      const form = el("form", { class: "searchbar" }, inp, el("button", { type: "submit" }, t.mp_name_go));
      form.addEventListener("submit", ev => { ev.preventDefault(); set({ n: inp.value }); });
      ctl.append(select(D.periods.map(x => [x, x === "alle" ? t.mp_all_years : x]), per, t.mp_period), form);
      ctl.querySelector("select").addEventListener("change", e => set({ p: e.target.value }));
      if (!name) {
        // häufigste Namen je Gemeinde: Klick auf einen Ort
        const pts = Object.entries(D.top).filter(([, v]) => v[per]?.length);
        L.layerGroup(pts.map(([p, v]) => {
          const [nm, , lat, lon] = D.places[+p];
          const tot = v[per].reduce((a, x) => a + x[1], 0);
          return L.circleMarker([lat, lon], { radius: 3 + Math.min(9, Math.sqrt(tot) / 2), color: "#175b5b", weight: 1, fillOpacity: 0.5 })
            .bindTooltip(`${nm}: ${v[per][0][0]}`)
            .on("click", () => {
              side.replaceChildren(el("h2", {}, link(placeHref(nm), nm)), el("p", { class: "sub" }, t.mp_top5_p.replace("{p}", per === "alle" ? t.mp_all_years : per)),
                el("ol", { class: "top one" }, ...v[per].map(([s, c]) => el("li", {},
                  link(`#/karten?v=namen&n=${encodeURIComponent(s)}&p=${encodeURIComponent(per)}`, s), ` (${n(c)})`))));
            });
        })).addTo(mp);
        side.append(el("p", { class: "muted" }, t.mp_top5_hint));
      } else {
        let rows;
        try { rows = (await get(`data/nm/${shardOf(name)}.json.gz`))[Object.keys(await get(`data/nm/${shardOf(name)}.json.gz`)).find(k => fold(k) === fold(name))]; } catch { rows = null; }
        if (!rows) { side.append(el("p", {}, t.mp_name_none)); return; }
        const yrs = [...new Set(rows.map(r => r[1]))].sort((a, b) => a - b);
        const year = +(params.get("y") || yrs[yrs.length - 1]);
        const at = new Map(rows.filter(r => r[1] === year).map(r => [r[0], r[2]]));
        circles(L, at, D.places, "#175b5b", c => t.mp_persons.replace("{n}", n(c))).addTo(mp);
        // Schwerpunkt je Jahr
        const cent = yrs.map(y => {
          const rs = rows.filter(r => r[1] === y);
          const w = rs.reduce((a, r) => a + r[2], 0);
          return [y, rs.reduce((a, r) => a + D.places[r[0]][2] * r[2], 0) / w, rs.reduce((a, r) => a + D.places[r[0]][3] * r[2], 0) / w, w];
        });
        L.polyline(cent.map(c => [c[1], c[2]]), { color: "#d21938", weight: 2, dashArray: "4 4" }).addTo(mp);
        cent.forEach(c => L.circleMarker([c[1], c[2]], { radius: c[0] === year ? 6 : 3, color: "#d21938", fillOpacity: 1 }).bindTooltip(`${t.mp_centroid} ${c[0]}`).addTo(mp));
        const firstAt = new Map();
        for (const r of rows) if (!firstAt.has(r[0]) || r[1] < firstAt.get(r[0])) firstAt.set(r[0], r[1]);
        const slider = el("input", { type: "range", min: yrs[0], max: yrs[yrs.length - 1], step: 1, value: year, "aria-label": t.mp_year });
        const yl = el("b", { class: "yr-label" }, String(year));
        slider.addEventListener("input", () => { yl.textContent = slider.value; });
        slider.addEventListener("change", () => set({ y: slider.value }));
        ctl.append(el("label", { class: "ctl wide" }, el("span", {}, t.mp_year), slider, yl));
        const tot = [...at.values()].reduce((a, b) => a + b, 0);
        side.append(el("p", { class: "count" }, t.mp_name_count.replace("{s}", name).replace("{y}", year).replace("{n}", n(tot)).replace("{g}", n(at.size))),
          el("h2", {}, t.mp_name_first),
          el("ul", { class: "hitlist cols" }, ...[...firstAt].sort((a, b) => a[1] - b[1] || D.places[a[0]][0].localeCompare(D.places[b[0]][0], "de"))
            .slice(0, 60).map(([p, y]) => el("li", {}, el("b", {}, String(y)), " ", link(placeHref(D.places[p][0]), D.places[p][0])))),
          el("p", {}, link(`#/suche?q=${encodeURIComponent(name)}`, t.mp_name_search)));
      }
    }
  }

  // ── Router ───────────────────────────────────────────────────────────────
  const routes = { suche: search, e: entity, a: address, g: place, orte: placeList, vorbehalte: caveats, karten };
  async function route() {
    if (!location.hash.startsWith("#/")) {
      const wasHidden = overview.hidden;
      view.hidden = true; overview.hidden = false;
      document.title = "Vernetzte Schweiz 1860–1914";
      if (wasHidden) {
        const target = location.hash.length > 1 && document.getElementById(location.hash.slice(1));
        target ? target.scrollIntoView() : window.scrollTo(0, 0);
      }
      return;
    }
    const [[name, ...args], params] = hashArgs();
    const fn = routes[name];
    overview.hidden = true; view.hidden = false;
    if (!fn) { view.replaceChildren(el("h1", {}, t.pg_not_found)); return; }
    if (name !== "suche") window.scrollTo(0, 0);
    document.title = `${t["nav_" + { suche: "search", orte: "places", vorbehalte: "caveats", karten: "maps" }[name]] || "…"} · Vernetzte Schweiz`;
    view.replaceChildren(el("p", { class: "muted" }, t.loading));
    try { await (["suche", "orte", "karten"].includes(name) ? fn(params) : fn(args)); }
    catch (err) { console.error(err); view.replaceChildren(el("h1", {}, t.pg_not_found)); }
  }
  const hero = document.getElementById("hero-search");
  if (hero) {
    hero.q.placeholder = t.pg_search_ph;
    hero.addEventListener("submit", ev => { ev.preventDefault(); location.hash = `#/suche?q=${encodeURIComponent(hero.q.value)}`; });
  }
  window.addEventListener("hashchange", route);
  route();
})();

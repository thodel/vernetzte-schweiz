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
  async function search(params) {
    const q = params.get("q") || "", m = params.get("m") || "";
    const input = el("input", { type: "search", value: q, placeholder: t.pg_search_ph, "aria-label": t.pg_search_ph, class: "q" });
    const muni = el("input", { type: "search", value: m, placeholder: t.pg_search_place, "aria-label": t.pg_search_place, class: "q q-place" });
    const out = el("div", { class: "results" });
    const go = () => { location.replace(`#/suche?q=${encodeURIComponent(input.value)}&m=${encodeURIComponent(muni.value)}`); };
    let timer;
    const onInput = () => { clearTimeout(timer); timer = setTimeout(go, 300); };
    input.addEventListener("input", onInput);
    muni.addEventListener("input", onInput);
    view.replaceChildren(el("h1", {}, t.pg_search_h), el("p", { class: "intro" }, t.pg_search_p),
      el("div", { class: "searchbar" }, input, muni), out);
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
        && (!mf || fold(r[2]).includes(mf));
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

  // ── Router ───────────────────────────────────────────────────────────────
  const routes = { suche: search, e: entity, a: address, g: place, orte: placeList, vorbehalte: caveats };
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
    document.title = `${t["nav_" + { suche: "search", orte: "places", vorbehalte: "caveats" }[name]] || "…"} · Vernetzte Schweiz`;
    view.replaceChildren(el("p", { class: "muted" }, t.loading));
    try { await (name === "suche" || name === "orte" ? fn(params) : fn(args)); }
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

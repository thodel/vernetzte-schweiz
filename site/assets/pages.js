// Seiten hinter #/…: Suche, Einheit, Adresse, Gemeinde, Orte, Vorbehalte.
// Daten aus data/ (scripts/build_pages.py), in Teilen geladen.
(async function () {
  const lang = (document.documentElement.lang || "de").slice(0, 2);
  const t = await fetch(`i18n/${lang}.json`).then(r => r.json());
  const nf = new Intl.NumberFormat("de-CH");
  const n = v => nf.format(v);
  const hlsUrl = id => `https://hls-dhs-dss.ch/${lang === "fr" ? "fr" : "de"}/articles/${id}/`;  // HLS: de, fr, it
  const el = (tag, attrs = {}, ...kids) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") e.className = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
    for (const k of kids.flat()) if (k !== null && k !== undefined && k !== false) e.append(k);
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
  const fnv = (s, mask = 0xff) => {
    let h = 0x811c9dc5;
    for (const b of new TextEncoder().encode(s)) { h ^= b; h = Math.imul(h, 0x01000193) >>> 0; }
    return (h & mask).toString(16).padStart(2, "0");
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

  // Karten der aktuellen Ansicht; beim Wechsel der Ansicht abgebaut, sonst zeichnen sie weiter
  let liveMaps = [];
  const dropMaps = () => { for (const m of liveMaps) { try { m.remove(); } catch { /* schon weg */ } } liveMaps = []; };
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
      liveMaps.push(m);
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
    el("a", { href: "#/suche?b=", class: active === "beruf" ? "on" : "", "aria-current": active === "beruf" ? "page" : "false" }, t.pg_tab_occ),
    el("a", { href: "#/suche?v=ft", class: active === "ft" ? "on" : "", "aria-current": active === "ft" ? "page" : "false" }, t.pg_tab_ft));

  // ── Unscharfer Namensvergleich (M7), gleich gerechnet wie scripts/fuzzy.py ─────
  const OCR_PAIRS = new Set(["bh", "hn", "ce", "il", "lt", "ft", "nu", "ao", "eo", "un", "cg", "bp", "do", "mn", "rn", "ij", "kh", "ec",
    "gc", "hk", "ei", "lr", "fl", "fs"].map(p => [...p].sort().join("")));
  const fkey = s => {
    s = (s || "").toLowerCase().replace(/ß/g, "ss").replace(/œ/g, "oe").replace(/æ/g, "ae")
      .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue");
    s = s.normalize("NFKD").replace(/[^\x00-\x7f]/g, "").replace(/[^a-z]/g, "");
    for (const [x, y] of [["ae", "a"], ["oe", "o"], ["ue", "u"], ["ss", "s"], ["ck", "k"], ["th", "t"], ["y", "i"], ["dt", "t"],
      ["tz", "z"], ["ph", "f"], ["ff", "f"], ["ll", "l"], ["mm", "m"], ["nn", "n"], ["rr", "r"], ["tt", "t"]]) s = s.split(x).join(y);
    return s;
  };
  const ocrForm = s => s.split("ii").join("u").split("rn").join("m");
  const dist = (a, b, cap = 3) => {
    a = ocrForm(a); b = ocrForm(b);
    if (Math.abs(a.length - b.length) > cap) return cap + 1;
    let prev2 = null, prev = Array.from({ length: b.length + 1 }, (_, j) => j);
    for (let i = 1; i <= a.length; i++) {
      const cur = [i];
      for (let j = 1; j <= b.length; j++) {
        const x = a[i - 1], y = b[j - 1];
        const sub = x === y ? 0 : (OCR_PAIRS.has([x, y].sort().join("")) ? 0.5 : 1);
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + sub);
        if (prev2 && i > 1 && j > 1 && x === b[j - 2] && a[i - 2] === y) cur[j] = Math.min(cur[j], prev2[j - 2] + 1);
      }
      if (Math.min(...cur) > cap) return cap + 1;
      prev2 = prev; prev = cur;
    }
    return prev[b.length];
  };
  const threshold = k => (k.length <= 3 ? 0.5 : k.length <= 6 ? 1 : 2);
  const keyOfLabel = (label, kind) => {
    const bare = strip(label || "");
    return fkey(kind === "p" ? bare.split(",")[0].split("-")[0] : (bare.split(/\s+/)[0] || ""));
  };
  let keyList, foreGroups;
  const keys = async () => keyList ??= await get("data/keys.json.gz");
  const forenames = async () => {
    if (!foreGroups) {
      foreGroups = new Map();
      (await get("data/forenames.json")).forEach((g, i) => g.forEach(w => foreGroups.set(fold(w), i)));
    }
    return foreGroups;
  };
  // passt ein Suchwort zum Namen, Vornamen oder Beruf einer Zeile? (Sprachformen: Charles = Carl)
  const wordOk = (w, label, occ, groups) => {
    if (fold(label).includes(w) || fold(occ).includes(w)) return true;
    const g = groups.get(w);
    return g !== undefined && label.split(/[\s,.-]+/).some(x => groups.get(fold(x)) === g);
  };

  async function search(params) {
    if (params.has("b")) return occSearch(params);
    if (params.get("v") === "ft") return fulltext(params);
    const q = params.get("q") || "", m = params.get("m") || "", src = params.get("s") || "";
    const fuzzy = params.get("f") === "1", kind = params.get("k") || "", withAuth = params.get("n") === "1";
    const sort = params.get("o") || "name", ya = +(params.get("a") || 1860), yz = +(params.get("z") || 1914);
    const extra = new Set((params.get("x") || "").split(",").filter(Boolean));
    const srcSel = srcSelect(src);
    const input = el("input", { type: "search", value: q, placeholder: t.pg_search_ph, "aria-label": t.pg_search_ph, class: "q" });
    const muni = el("input", { type: "search", value: m, placeholder: t.pg_search_place, "aria-label": t.pg_search_place, class: "q q-place" });
    const fz = el("input", { type: "checkbox" }); fz.checked = fuzzy;
    const au = el("input", { type: "checkbox" }); au.checked = withAuth;
    const kindSel = select([["", t.mp_all], ["p", t.pg_kind_person], ["f", t.pg_kind_firma]], kind, t.mp_kind);
    const sortSel = select([["name", t.pg_sort_name], ["ort", t.pg_sort_place], ["jahr", t.pg_sort_year]], sort, t.pg_sort);
    let range = [ya, yz];
    const out = el("div", { class: "results" });
    const state = (upd = {}) => {
      const p = new URLSearchParams({ q: input.value, m: muni.value, s: srcSel.querySelector("select").value,
        f: fz.checked ? "1" : "", k: kindSel.querySelector("select").value, n: au.checked ? "1" : "",
        o: sortSel.querySelector("select").value, a: range[0], z: range[1], x: [...extra].join(","), ...upd });
      for (const [k, v] of [...p]) if (!v || (k === "a" && v === "1860") || (k === "z" && v === "1914") || (k === "o" && v === "name")) p.delete(k);
      return `#/suche?${p}`;
    };
    const go = upd => location.replace(state(upd));
    let timer;
    const onInput = () => { clearTimeout(timer); timer = setTimeout(() => go({ x: "" }), 300); };
    input.addEventListener("input", onInput);
    muni.addEventListener("input", onInput);
    for (const c of [srcSel, kindSel, sortSel]) c.querySelector("select").addEventListener("change", () => go());
    fz.addEventListener("change", () => go({ x: "" }));
    au.addEventListener("change", () => go());
    const yearCtl = rangeSlider(1860, 1914, ya, yz, (x, y) => { range = [x, y]; go(); });
    const filters = el("details", { class: "filters", ...(fuzzy || kind || withAuth || ya !== 1860 || yz !== 1914 || sort !== "name" ? { open: "" } : {}) },
      el("summary", {}, t.pg_more_filters),
      el("div", { class: "controls" }, yearCtl, kindSel, sortSel,
        el("label", { class: "check" }, au, " ", t.pg_only_auth)));
    view.replaceChildren(el("h1", {}, t.pg_search_h), searchTabs("name"), el("p", { class: "intro" }, t.pg_search_p),
      el("div", { class: "searchbar" }, input, muni, srcSel),
      el("label", { class: "check fuzzy" }, fz, " ", el("b", {}, t.pg_fuzzy), " ", el("span", { class: "muted" }, t.pg_fuzzy_hint)),
      filters, out);
    muni.addEventListener("focus", () => { focusPlace = true; });
    input.addEventListener("focus", () => { focusPlace = false; });
    const fcs = focusPlace ? muni : input;
    fcs.focus();
    fcs.setSelectionRange(fcs.value.length, fcs.value.length);
    const words = q.split(/[\s,]+/).filter(Boolean);
    if (!words.length || fold(strip(q)).length < 2) { out.append(el("p", { class: "muted" }, t.pg_search_hint)); return; }
    const firstRaw = strip(q).split(/[\s,]+/)[0];
    const first = fold(firstRaw);
    const rest = words.slice(1).map(fold).filter(Boolean);
    const mf = fold(m);
    const groups = await forenames();
    let rows = [], keyset = null, chips = [];
    if (fuzzy) {
      const qk = fkey(firstRaw);
      const K = await keys();
      const count = new Map(K.map(k => [k[0], k[2]]));
      const qc = count.get(qk) || 0;
      const near = [];
      for (const [k, disp, c, sh] of K) {
        if (Math.abs(k.length - qk.length) > 2) continue;
        const d = k === qk ? 0 : dist(qk, k);
        if (d <= threshold(qk)) near.push({ k, disp, c, sh, d });
      }
      near.sort((x, y) => x.d - y.d || y.c - x.c);
      keyset = new Set([qk, ...extra]);
      chips = near.filter(x => x.k !== qk).slice(0, 40);
      const shards = new Set(near.filter(x => keyset.has(x.k)).flatMap(x => x.sh));
      if (!shards.size) shards.add(shardOf(q));
      for (const sh of shards) { try { rows = rows.concat(await get(`data/names/${sh}.json.gz`)); } catch { /* fehlt */ } }
      out.append(el("div", { class: "chips" },
        el("p", { class: "sub" }, t.pg_fuzzy_exact.replace("{k}", qk).replace("{n}", n(qc))),
        chips.length ? el("p", { class: "sub" }, t.pg_fuzzy_similar) : el("p", { class: "muted" }, t.pg_fuzzy_none),
        ...chips.map(x => {
          const ocrLike = x.d <= 0.5 && x.c <= Math.max(2, 0.1 * qc);
          const on = extra.has(x.k);
          const b = el("button", { type: "button", class: "chip" + (on ? " on" : "") + (ocrLike ? " ocr" : ""), "aria-pressed": on ? "true" : "false",
            title: x.d <= 0.5 ? t.pg_chip_ocr : t.pg_chip_dist.replace("{d}", String(x.d)) }, `${x.disp} (${n(x.c)})`);
          b.addEventListener("click", () => { on ? extra.delete(x.k) : extra.add(x.k); go({ x: [...extra].join(",") }); });
          return b;
        })));
    } else {
      try { rows = await get(`data/names/${shardOf(q)}.json.gz`); } catch { rows = []; }
    }
    const hits = rows.filter(r => {
      const nameOk = keyset ? keyset.has(keyOfLabel(r[1], r[5])) : fold(strip(r[1])).startsWith(first);
      return nameOk && rest.every(w => wordOk(w, r[1], r[8], groups))
        && (!mf || fold(r[2]).includes(mf)) && srcOk(r[9], src)
        && (!kind || r[5] === kind) && (!withAuth || r[7]) && r[3] <= range[1] && r[4] >= range[0];
    });
    const cmp = {
      name: (x, y) => fold(x[1]).localeCompare(fold(y[1])) || x[2].localeCompare(y[2], "de") || x[3] - y[3],
      ort: (x, y) => x[2].localeCompare(y[2], "de") || fold(x[1]).localeCompare(fold(y[1])),
      jahr: (x, y) => x[3] - y[3] || fold(x[1]).localeCompare(fold(y[1])),
    }[sort] || (() => 0);
    hits.sort(cmp);
    out.append(el("p", { class: "count" }, t.pg_hits.replace("{n}", n(hits.length))
      + (hits.length > 300 ? " " + t.pg_hits_more : "")));
    const qk0 = keyset ? fkey(firstRaw) : "";
    const ul = el("ul", { class: "hitlist" });
    for (const [id, label, place, y0, y1, knd, cnt, tier, occ] of hits.slice(0, 300)) {
      const why = keyset ? (keyOfLabel(label, knd) === qk0 ? (fold(firstRaw) === fold(keyOfLabel(label, knd)) || fold(strip(label)).startsWith(first) ? "" : t.pg_why_variant) : t.pg_why_similar) : "";
      ul.append(el("li", {},
        link(`#/e/${id}`, label, "hit"),
        el("span", { class: "meta" }, `${place} · ${years([y0, y1])} · ${knd === "f" ? t.pg_kind_firma : t.pg_kind_person} · ${entries(cnt)}`),
        why ? el("span", { class: "pill why" }, why) : "",
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
        a.hls_id ? link(hlsUrl(a.hls_id), `${t.hls_abbr || "HLS"} ${a.hls_id}`) : "",
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
    if (e.hk) {
      parts.push(el("section", { class: "card hl-hint" },
        el("h2", {}, t.hl_hint_h, " ", hlBadge("wahrscheinlich")),
        ...e.hk.map(([hid, name, b, d, why]) => el("p", {}, el("b", {}, name), ` (${life(b, d)}) · `,
          link(`#/hls/${hid}`, t.hl_hint_check), " · ", link(hlsUrl(hid), `${t.hls_abbr || "HLS"} ${hid}`),
          el("span", { class: "muted" }, ` — ${why.split(" ").map(x => x.split("+").map(y => t["hl_why_" + y] || y).join(" + ")).join("; ")}`))),
        el("p", { class: "sub note" }, t.hl_hint_note)));
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
    const g = p ? (await get(`data/g/${fnv(e.m, 0x3f)}.json.gz`))[e.m] : null;
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
    const g = (await get(`data/g/${fnv(name, 0x3f)}.json.gz`))[name];
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
    liveMaps.push(m);
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
  const yearBars = (counts, y0, y1, current, onPick, range) => {
    const max = Math.max(1, ...counts);
    return el("div", { class: "bars small", role: "img", "aria-label": t.mp_bars_label },
      ...counts.map((c, i) => {
        const y = y0 + i;
        const on = y === current || (range && y >= range[0] && y <= range[1]);
        const b = el("div", { class: "bar" + (on ? " on" : ""), title: `${y}: ${n(c)}` },
          el("span", { class: "fill", style: `height:${Math.max(c ? 2 : 0, (c / max) * 100)}%` }),
          y % 5 === 0 || y === y0 || y === y1 ? el("span", { class: "lbl" }, String(y)) : "");
        if (onPick) b.addEventListener("click", () => onPick(y));
        return b;
      }));
  };

  async function occSearch(params) {
    const b = params.get("b") || "", m = params.get("m") || "", src = params.get("s") || "";
    const a0 = +(params.get("a") || 1860), a1 = +(params.get("z") || 1914);
    const srcSel = srcSelect(src);
    const input = el("input", { type: "search", value: b, placeholder: t.pg_occ_ph, "aria-label": t.pg_occ_ph, class: "q" });
    const muni = el("input", { type: "search", value: m, placeholder: t.pg_search_place, "aria-label": t.pg_search_place, class: "q q-place" });
    const D = await maps();
    let range = [a0, a1];
    const go = () => location.replace(`#/suche?b=${encodeURIComponent(input.value)}&m=${encodeURIComponent(muni.value)}&a=${range[0]}&z=${range[1]}&s=${srcSel.querySelector("select").value}`);
    const perSel = rangeSlider(1860, 1914, a0, a1, (x, y) => { range = [x, y]; go(); });
    let timer;
    const onInput = () => { clearTimeout(timer); timer = setTimeout(go, 350); };
    input.addEventListener("input", onInput);
    muni.addEventListener("input", onInput);
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
    try { shard = await get(`data/ow/${toks[0].slice(0, 1)}.json.gz`); } catch { shard = { w: {}, e: {} }; }
    const ids = new Set();
    for (const [w, list] of Object.entries(shard.w)) if (w.startsWith(toks[0])) list.forEach(id => ids.add(id));
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

  // Jahresbereich mit zwei Griffen: ein Jahr oder mehrere
  const rangeSlider = (min, max, a, b, onChange) => {
    const lo = el("input", { type: "range", min, max, step: 1, value: a, "aria-label": t.mp_from });
    const hi = el("input", { type: "range", min, max, step: 1, value: b, "aria-label": t.mp_to });
    const lab = el("b", { class: "yr-label" });
    const fill = el("span", { class: "rs-fill" });
    const show = () => {
      const x = Math.min(+lo.value, +hi.value), y = Math.max(+lo.value, +hi.value);
      lab.textContent = x === y ? String(x) : `${x}–${y}`;
      const w = max - min || 1;
      fill.style.left = `${(x - min) / w * 100}%`; fill.style.width = `${(y - x) / w * 100}%`;
    };
    const done = () => { const x = Math.min(+lo.value, +hi.value), y = Math.max(+lo.value, +hi.value); onChange(x, y); };
    for (const i of [lo, hi]) { i.addEventListener("input", show); i.addEventListener("change", done); }
    show();
    return el("div", { class: "ctl wide" }, el("span", {}, t.mp_years), el("div", { class: "rs" }, el("span", { class: "rs-track" }), fill, lo, hi), lab);
  };
  const srcSel = (value, withAll = true) => select([["t", t.mp_src_ptt], ...(withAll ? [["ta", t.mp_src_both]] : []), ["a", t.mp_src_ab]], value, t.pg_src_filter);
  // ist eine Einheit (Zeile aus maps.ent) im Bereich a–b in der gewählten Quelle belegt?
  const present = (e, a, b, src) => (src !== "a" && e[1] && e[1] <= b && e[2] >= a) || (src !== "t" && e[3] && e[3] <= b && e[4] >= a);
  const rowIn = (r, a, b, src, off = 0) => (src === "ta" || (src === "t" ? r[off + 2] === 0 : r[off + 2] === 1)) && r[off] <= b && r[off + 1] >= a;

  const mapTabs = v => el("nav", { class: "tabs" }, ...[["telefon", t.mp_tab_phone], ["berufe", t.mp_tab_occ], ["namen", t.mp_tab_names], ["wanderungen", t.mw_tab]].map(([k, txt]) =>
    el("a", { href: `#/karten?v=${k}`, class: v === k ? "on" : "", "aria-current": v === k ? "page" : "false" }, txt)));

  // ── Wanderungen (M10, experimentell; scripts/migration.py) ──────────────
  // moves: [von, nach, letztes Jahr alt, erstes Jahr neu, Klasse, Stufe 0–2, km, Name, Beruf alt, Beruf neu, entity alt, entity neu, beide vorliegend]
  let migData;
  async function wanderungen(params) {
    const D = migData ??= await get("data/wanderungen.json.gz");
    const set = upd => {
      const p = new URLSearchParams(params);
      for (const [k, val] of Object.entries(upd)) p.set(k, val);
      location.replace(`#/karten?${p}`);
    };
    const a = +(params.get("a") || 1860), b = +(params.get("b") || 1914);
    const tier = +(params.get("t") ?? 1), cls = params.get("c") || "alle", dir = params.get("d") || "linien";
    const near = params.get("n") || "ohne", seen = params.get("g") || "alle";
    const tierNames = [t.mw_tier_0, t.mw_tier_1, t.mw_tier_2];
    const clsName = i => i < 0 ? t.mw_no_class : (t[`occ_${D.classes[i][0]}`] || D.classes[i][1]);
    const moves = D.moves.filter(m => m[3] >= a && m[3] <= b && m[5] <= tier && (cls === "alle" || m[4] === +cls)
      && (near === "mit" || m[6] >= 5) && (seen === "alle" || m[12] === 1));
    const box = el("div", { class: "map tall" });
    const side = el("div", { class: "map-side" });
    const ctl = el("div", { class: "controls" });
    view.replaceChildren(el("h1", {}, t.mp_h), mapTabs("wanderungen"), el("p", { class: "intro" }, t.mw_p), ctl, box, side,
      el("p", { class: "sub note" }, t.mw_note, " ", link("https://github.com/thodel/vernetzte-schweiz/blob/main/docs/wanderungen.md", t.mw_doc)));
    ctl.append(rangeSlider(1860, 1914, a, b, (x, y) => set({ a: x, b: y })),
      select([[0, tierNames[0]], [1, `${tierNames[0]} + ${tierNames[1]}`], [2, t.mp_all]], tier, t.mw_tier),
      select([["alle", t.mp_all], ...D.classes.map((_, i) => [i, clsName(i)])], cls, t.mp_class),
      select([["linien", t.mw_view_lines], ["saldo", t.mw_view_net]], dir, t.mp_metric),
      select([["ohne", t.mw_near_without], ["mit", t.mw_near_with]], near, t.mw_near),
      select([["alle", t.mw_seen_all], ["ja", t.mw_seen_yes]], seen, t.mw_seen));
    ctl.querySelectorAll("select").forEach((s, i) => s.addEventListener("change", () => set({ [["t", "c", "d", "n", "g"][i]]: s.value })));

    let L, mp;
    try { [L, mp] = await chMap(box); } catch { box.replaceChildren(el("p", { class: "muted" }, t.pg_map_error)); return; }
    const P = D.places;
    const flows = new Map();
    for (const m of moves) {
      const k = `${m[0]}>${m[1]}`;
      if (!flows.has(k)) flows.set(k, []);
      flows.get(k).push(m);
    }
    if (dir === "linien") {
      // Bogen von alt nach neu (rechts gekrümmt, damit Hin und Zurück getrennt bleiben), Punkt am Ziel
      const arc = (p, q) => {
        const [la1, lo1] = [P[p][2], P[p][3]], [la2, lo2] = [P[q][2], P[q][3]];
        const mx = (la1 + la2) / 2 + (lo2 - lo1) * 0.15, my = (lo1 + lo2) / 2 - (la2 - la1) * 0.15;
        return Array.from({ length: 17 }, (_, i) => { const u = i / 16; return [(1 - u) ** 2 * la1 + 2 * (1 - u) * u * mx + u * u * la2, (1 - u) ** 2 * lo1 + 2 * (1 - u) * u * my + u * u * lo2]; });
      };
      const layer = [];
      for (const [k, ms] of [...flows].sort((x, y) => x[1].length - y[1].length)) {
        const [p, q] = k.split(">").map(Number);
        const tip = `${P[p][0]} → ${P[q][0]}: ${ms.length === 1 ? ms[0][7] : t.mw_persons.replace("{n}", n(ms.length))}`;
        layer.push(L.polyline(arc(p, q), { color: "#175b5b", weight: 1 + Math.sqrt(ms.length) * 1.5, opacity: 0.55 }).bindTooltip(tip));
        layer.push(L.circleMarker([P[q][2], P[q][3]], { radius: 2 + Math.sqrt(ms.length), color: "#d21938", weight: 1, fillOpacity: 0.8 }).bindTooltip(tip));
      }
      L.layerGroup(layer).addTo(mp);
    } else {
      const net = new Map(), gross = new Map();
      for (const m of moves) {
        net.set(m[0], (net.get(m[0]) || 0) - 1); net.set(m[1], (net.get(m[1]) || 0) + 1);
        gross.set(m[0], (gross.get(m[0]) || 0) + 1); gross.set(m[1], (gross.get(m[1]) || 0) + 1);
      }
      L.layerGroup([...gross].map(([p, g]) => {
        const v = net.get(p) || 0;
        return L.circleMarker([P[p][2], P[p][3]], { radius: Math.max(3, Math.sqrt(g) * 2.2), weight: 1, fillOpacity: 0.55,
          color: v > 0 ? "#175b5b" : v < 0 ? "#d21938" : "#888" })
          .bindTooltip(t.mw_net_tip.replace("{g}", P[p][0]).replace("{in}", n((g + v) / 2)).replace("{out}", n((g - v) / 2)));
      })).addTo(mp);
    }

    // Seitenleiste: Zahl, nach Berufsklasse, nach Entfernung, häufigste Ortspaare, Fälle
    const hbars = rows => {
      const max = Math.max(1, ...rows.map(r => r[1]));
      return el("div", { class: "hbars" }, ...rows.map(([lab, c, extra]) => el("div", { class: "hbar" },
        el("span", { class: "lab" }, lab), el("span", { class: "track" }, el("span", { class: "fill", style: `width:${c / max * 100}%` })),
        el("span", { class: "num" }, n(c), extra ? el("span", { class: "muted" }, ` · ${extra}`) : ""))));
    };
    const med = xs => { const s2 = [...xs].sort((x, y) => x - y); return s2.length ? s2[Math.floor((s2.length - 1) / 2)] : 0; };
    const byCls = new Map();
    for (const m of moves) { if (!byCls.has(m[4])) byCls.set(m[4], []); byCls.get(m[4]).push(m[6]); }
    const bins = [[0, 5], [5, 20], [20, 50], [50, 100], [100, 999]];
    const span = a === b ? String(a) : `${a}–${b}`;
    side.append(el("p", { class: "count" }, t.mw_count.replace("{n}", n(moves.length)).replace("{y}", span).replace("{f}", n(flows.size))),
      el("h2", {}, t.mw_by_class),
      hbars([...byCls].sort((x, y) => y[1].length - x[1].length).map(([c, ks]) => [clsName(c), ks.length, t.mw_median_km.replace("{k}", n(Math.round(med(ks))))])),
      el("h2", {}, t.mw_by_km),
      hbars(bins.map(([x, y]) => [y > 500 ? `≥ ${x} km` : `${x}–${y} km`, moves.filter(m => m[6] >= x && m[6] < y).length])),
      el("h2", {}, t.mw_by_year),
      yearBars(Array.from({ length: 55 }, (_, i) => moves.filter(m => m[3] === 1860 + i).length), 1860, 1914, null, y => set({ a: y, b: y }), [a, b]),
      el("h2", {}, t.mw_top_flows),
      hbars([...flows].sort((x, y) => y[1].length - x[1].length).slice(0, 12).map(([k, ms]) => {
        const [p, q] = k.split(">").map(Number);
        return [`${P[p][0]} → ${P[q][0]}`, ms.length];
      })),
      el("h2", {}, t.mw_cases),
      el("ul", { class: "hitlist" }, ...moves.slice().sort((x, y) => x[5] - y[5] || x[3] - y[3]).slice(0, 300).map(m => el("li", {},
        el("b", {}, m[7]), el("span", { class: `pill mw-tier-${m[5]}` }, tierNames[m[5]]),
        el("span", { class: "meta" }, link(`#/e/${m[10]}`, `${P[m[0]][0]} ${m[2]}`), " → ", link(`#/e/${m[11]}`, `${P[m[1]][0]} ${m[3]}`), ` · ${n(Math.round(m[6]))} km`),
        el("span", { class: "occ" }, m[8] === m[9] || !m[9] ? m[8] : `${m[8] || "–"} → ${m[9]}`)))),
      moves.length > 300 ? el("p", { class: "muted" }, t.mw_more.replace("{n}", n(moves.length - 300))) : "");
  }

  async function karten(params) {
    const v = params.get("v") || "telefon";
    if (v === "wanderungen") return wanderungen(params);
    const D = await maps();
    const tabs = mapTabs(v);
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
    const wire = (names) => ctl.querySelectorAll("select").forEach((s, i) => s.addEventListener("change", () => set({ [names[i]]: s.value })));

    if (v === "telefon") {
      const a = +(params.get("a") || 1914), b = +(params.get("b") || a);
      const kind = params.get("k") || "alle", cls = params.get("c") || "alle", can = params.get("kt") || "alle";
      const cantons = [...new Set(D.places.map(p => p[1]).filter(Boolean))].sort();
      const ents = D.ent.filter(e => e[1] && (kind === "alle" || e[5] === (kind === "firma" ? 1 : 0))
        && (cls === "alle" || e[6] === +cls) && (can === "alle" || D.places[e[0]][1] === can));
      const counts = new Map();
      for (const e of ents) if (e[1] >= a && e[1] <= b) counts.set(e[0], (counts.get(e[0]) || 0) + 1);
      const perYear = Array.from({ length: 35 }, (_, i) => ents.filter(e => e[1] === 1880 + i).length);
      ctl.append(rangeSlider(1880, 1914, a, b, (x, y) => set({ a: x, b: y })),
        select([["alle", t.mp_all], ["person", t.pg_kind_person], ["firma", t.pg_kind_firma]], kind, t.mp_kind),
        select([["alle", t.mp_all], ...D.classes.map(([k, lab], i) => [i, t[`occ_${k}`] || lab])], cls, t.mp_class),
        select([["alle", t.mp_all], ...cantons.map(c => [c, c])], can, t.mp_canton));
      wire(["k", "c", "kt"]);
      heat(L, counts, D.places).addTo(mp);
      const total = [...counts.values()].reduce((x, y) => x + y, 0);
      const span = a === b ? String(a) : `${a}–${b}`;
      const eds = D.editions.filter(e => e.some(y => y >= a && y <= b)).length;
      side.append(el("p", { class: "count" }, t.mp_new_count.replace("{n}", n(total)).replace("{y}", span).replace("{g}", n(counts.size))),
        el("p", { class: "sub" }, t.mp_editions.replace("{n}", n(eds)).replace("{y}", span)),
        el("h2", {}, t.mp_first_year_h), yearBars(perYear, 1880, 1914, null, y => set({ a: y, b: y }), [a, b]));
    } else if (v === "berufe") {
      const cls = +(params.get("c") ?? 1), metric = params.get("m") || "anzahl", src = params.get("s") || "t";
      const a = +(params.get("a") || (src === "t" ? 1880 : 1860)), b = +(params.get("b") || 1914);
      const all = new Map(), hit = new Map();
      for (const e of D.ent) {
        if (!present(e, a, b, src)) continue;
        all.set(e[0], (all.get(e[0]) || 0) + 1);
        if (e[6] === cls) hit.set(e[0], (hit.get(e[0]) || 0) + 1);
      }
      ctl.append(rangeSlider(1860, 1914, a, b, (x, y) => set({ a: x, b: y })),
        select(D.classes.map(([k, lab], i) => [i, t[`occ_${k}`] || lab]), cls, t.mp_class), srcSel(src),
        select([["anzahl", t.mp_metric_count], ["anteil", t.mp_metric_share]], metric, t.mp_metric));
      wire(["c", "s", "m"]);
      if (metric === "anzahl") heat(L, hit, D.places).addTo(mp);
      else {
        const steps = ["#f3d9da", "#e7aeb2", "#d47b82", "#b54a54", "#7d1f28"];
        const rows = [...all].filter(([, c]) => c >= 20).map(([p, c]) => [p, c, (hit.get(p) || 0) / c]);
        // Stufen: 0 % für sich, darüber Quartile der Gemeinden mit Anteil > 0
        const shares = rows.map(r => r[2]).filter(x => x > 0).sort((x, y) => x - y);
        const q = k => shares[Math.floor((shares.length - 1) * k)] ?? 0;
        const cuts = [0, q(0.25), q(0.5), q(0.75)];
        const pct = x => `${Math.round(x * 1000) / 10} %`;
        L.layerGroup(rows.map(([p, c, sh]) => {
          const [name, , lat, lon] = D.places[p];
          const col = sh === 0 ? steps[0] : steps[1 + cuts.slice(1).filter(x => sh > x).length];
          return L.circleMarker([lat, lon], { radius: 3 + Math.min(12, Math.sqrt(c) / 3), color: "#555", weight: 0.5, fillColor: col, fillOpacity: 0.85 })
            .bindTooltip(`${name}: ${pct(sh)} (${n(hit.get(p) || 0)} / ${n(c)})`);
        })).addTo(mp);
        const labels = ["0 %", t.mp_upto.replace("{p}", pct(cuts[1])), `${pct(cuts[1])}–${pct(cuts[2])}`, `${pct(cuts[2])}–${pct(cuts[3])}`, t.mp_over.replace("{p}", pct(cuts[3]))];
        side.append(el("ul", { class: "legend" }, ...steps.map((c, i) => el("li", {}, el("span", { class: "sw", style: `background:${c}` }), labels[i]))),
          el("p", { class: "sub" }, t.mp_share_size));
      }
      const tot = [...hit.values()].reduce((x, y) => x + y, 0);
      const ranked = [...hit].filter(([p]) => (all.get(p) || 0) >= 20).sort((x, y) => y[1] / all.get(y[0]) - x[1] / all.get(x[0])).slice(0, 10);
      side.prepend(el("p", { class: "count" }, t.mp_occ_count.replace("{n}", n(tot)).replace("{c}", t[`occ_${D.classes[cls][0]}`] || D.classes[cls][1]).replace("{g}", n(hit.size))));
      side.append(el("h2", {}, t.mp_occ_top), el("ol", { class: "top" }, ...ranked.map(([p, c]) =>
        el("li", {}, link(placeHref(D.places[p][0]), D.places[p][0]), ` ${Math.round(c / all.get(p) * 1000) / 10} % (${n(c)} / ${n(all.get(p))})`))),
        el("p", {}, link(`#/suche?b=`, t.mp_occ_free)));
    } else {
      const src = params.get("s") || "t", name = params.get("n") || "";
      const a = +(params.get("a") || (src === "t" ? 1880 : 1860)), b = +(params.get("b") || 1914);
      const inp = el("input", { type: "search", value: name, placeholder: t.mp_name_ph, "aria-label": t.mp_name_ph, class: "q" });
      const form = el("form", { class: "searchbar" }, inp, el("button", { type: "submit" }, t.mp_name_go));
      form.addEventListener("submit", ev => { ev.preventDefault(); set({ n: inp.value }); });
      ctl.append(rangeSlider(1860, 1914, a, b, (x, y) => set({ a: x, b: y })), srcSel(src), form);
      wire(["s"]);
      const span = a === b ? String(a) : `${a}–${b}`;
      if (!name) {
        // Personen je Gemeinde im Bereich; Klick zeigt die fünf häufigsten Namen
        const per = new Map();
        for (const e of D.ent) if (e[5] === 0 && present(e, a, b, src)) per.set(e[0], (per.get(e[0]) || 0) + 1);
        L.layerGroup([...per].map(([p, c]) => {
          const [nm, , lat, lon] = D.places[p];
          return L.circleMarker([lat, lon], { radius: 3 + Math.min(9, Math.sqrt(c) / 2), color: "#175b5b", weight: 1, fillOpacity: 0.5 })
            .bindTooltip(`${nm}: ${t.mp_persons.replace("{n}", n(c))}`)
            .on("click", async () => {
              const rows = (await get(`data/pl/${fnv(nm, 0x3f)}.json.gz`))[nm] || [];
              const c5 = new Map();
              for (const r of rows) if (rowIn(r, a, b, src, 1)) c5.set(r[0], (c5.get(r[0]) || 0) + 1);
              const top = [...c5].sort((x, y) => y[1] - x[1] || x[0].localeCompare(y[0], "de")).slice(0, 5);
              side.replaceChildren(el("h2", {}, link(placeHref(nm), nm)), el("p", { class: "sub" }, t.mp_top5_p.replace("{p}", span)),
                el("ol", { class: "top one" }, ...top.map(([s2, c2]) => el("li", {},
                  link(`#/karten?v=namen&n=${encodeURIComponent(s2)}&s=${src}&a=${a}&b=${b}`, s2), ` (${n(c2)})`))));
            });
        })).addTo(mp);
        side.append(el("p", { class: "muted" }, t.mp_top5_hint));
      } else {
        let all = null;
        try { const sh = await get(`data/nm/${fnv(fold(name), 0x3f)}.json.gz`); all = sh[Object.keys(sh).find(k => fold(k) === fold(name))]; } catch { /* kein Teil */ }
        const rows = (all || []).filter(r => src === "ta" || r[3] === (src === "t" ? 0 : 1));
        if (!rows.length) { side.append(el("p", {}, t.mp_name_none)); return; }
        const at = new Map();
        for (const r of rows) if (r[1] <= b && r[2] >= a) at.set(r[0], (at.get(r[0]) || 0) + 1);
        circles(L, at, D.places, "#175b5b", c => t.mp_persons.replace("{n}", n(c))).addTo(mp);
        // Schwerpunkt je Jahr (Personen, die das Jahr umspannen)
        const y0 = Math.min(...rows.map(r => r[1])), y1 = Math.max(...rows.map(r => r[2]));
        const cent = [];
        for (let y = y0; y <= y1; y++) {
          const rs = rows.filter(r => r[1] <= y && r[2] >= y);
          if (!rs.length) continue;
          cent.push([y, rs.reduce((s2, r) => s2 + D.places[r[0]][2], 0) / rs.length, rs.reduce((s2, r) => s2 + D.places[r[0]][3], 0) / rs.length]);
        }
        L.polyline(cent.map(c => [c[1], c[2]]), { color: "#d21938", weight: 2, dashArray: "4 4" }).addTo(mp);
        cent.forEach(c => L.circleMarker([c[1], c[2]], { radius: c[0] >= a && c[0] <= b ? 5 : 2, color: "#d21938", fillOpacity: 1 }).bindTooltip(`${t.mp_centroid} ${c[0]}`).addTo(mp));
        const firstAt = new Map();
        for (const r of rows) if (!firstAt.has(r[0]) || r[1] < firstAt.get(r[0])) firstAt.set(r[0], r[1]);
        const tot = [...at.values()].reduce((x, y) => x + y, 0);
        side.append(el("p", { class: "count" }, t.mp_name_count.replace("{s}", name).replace("{y}", span).replace("{n}", n(tot)).replace("{g}", n(at.size))),
          el("h2", {}, t.mp_name_first),
          el("ul", { class: "hitlist cols" }, ...[...firstAt].sort((x, y) => x[1] - y[1] || D.places[x[0]][0].localeCompare(D.places[y[0]][0], "de"))
            .slice(0, 60).map(([p, y]) => el("li", {}, el("b", {}, String(y)), " ", link(placeHref(D.places[p][0]), D.places[p][0])))),
          el("p", {}, link(`#/suche?q=${encodeURIComponent(name)}`, t.mp_name_search)));
      }
    }
  }


  // ── Telefonbücher und Volltext (M8) ───────────────────────────────────────
  let booksData;
  const books = async () => booksData ??= await get("data/books.json");
  const cellFile = c => `data/r/${encodeURIComponent(c.kt)}-${c.y}.json.gz`;
  const iiif = (ref, img, size = "max") => `https://iiif.ptt-archiv.ch/iiif/3/${ref}_${String(img).padStart(4, "0")}.jp2/full/${size}/0/default.jpg`;
  // ein Eintrag als Zeile; `marks` = gefundene Wörter (hervorgehoben)
  const mark = (text, marks) => {
    if (!marks || !marks.size || !text) return text || "";
    const parts = String(text).split(/([A-Za-zÀ-ÿ0-9]+)/);
    return el("span", {}, ...parts.map(p => (marks.has(fold(p)) || marks.has(p.replace(/\D/g, ""))) && p ? el("mark", {}, p) : p));
  };
  const entryRow = (r, B, marks) => {
    const [ref, page, img, n1, n2, sup, street, phone, muni, eid] = r;
    const refName = B.refs[ref];
    return el("li", { class: "entry" },
      el("span", { class: "e-name" }, mark(n1, marks), n2 ? ", " : "", mark(n2, marks)),
      sup ? el("span", { class: "e-sup" }, mark(sup, marks)) : "",
      street ? el("span", { class: "e-st" }, mark(street, marks)) : "",
      phone ? el("span", { class: "e-ph" }, `${t.pg_phone} `, mark(phone, marks)) : "",
      el("span", { class: "meta" }, muni ? link(placeHref(muni), muni) : "", muni ? " · " : "", refName,
        page ? ` · ${t.ft_page} ${page}` : "",
        img ? [" · ", link(iiif(refName, img), t.ft_image)] : "",
        eid ? [" · ", link(`#/e/${eid}`, t.ft_entity)] : ""));
  };

  async function phonebook(params) {
    const kt = params.get("kt") || "", y = +(params.get("y") || 0);
    const q = params.get("q") || "", gm = params.get("g") || "", ref = params.get("r") || "", page = +(params.get("p") || 0);
    const B = await books();
    const cell = B.cells.find(c => c.kt === kt && c.y === y);
    if (!cell) { view.replaceChildren(el("h1", {}, t.pg_not_found)); return; }
    document.title = `${t.ft_book} ${kt} ${y} · Vernetzte Schweiz`;
    const rows = await get(cellFile(cell));
    const input = el("input", { type: "search", value: q, placeholder: t.ft_filter_ph, "aria-label": t.ft_filter_ph, class: "q" });
    const muniSel = select([["", t.mp_all], ...cell.munis.map(m => [m, m])], gm, t.ft_muni);
    const refSel = select([["", t.mp_all], ...cell.refs.map(i => [String(i), B.refs[i]])], ref, t.ft_book);
    const go = upd => {
      const p = new URLSearchParams({ kt, y, q: input.value, g: muniSel.querySelector("select").value, r: refSel.querySelector("select").value, ...upd });
      for (const [k, v] of [...p]) if (!v || v === "0") p.delete(k);
      location.replace(`#/buch?${p}`);
    };
    let timer;
    input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => go({ p: 0 }), 300); });
    for (const c of [muniSel, refSel]) c.querySelector("select").addEventListener("change", () => go({ p: 0 }));
    const toks = q.split(/\s+/).map(w => (/^\d/.test(w) ? w.replace(/\D/g, "") : fold(w))).filter(Boolean);
    const hits = rows.filter(r => (!gm || r[8] === gm) && (!ref || String(r[0]) === ref)
      && toks.every(w => [r[3], r[4], r[5], r[6], r[8]].some(x => fold(x).includes(w)) || String(r[7]).replace(/\D/g, "").includes(w)));
    const per = 200, pages = Math.max(1, Math.ceil(hits.length / per)), cur = Math.min(page, pages - 1);
    const marks = new Set(toks);
    const nav = () => pages > 1 ? el("nav", { class: "pager" },
      cur > 0 ? el("a", { href: "#", onclick: e => { e.preventDefault(); go({ p: cur - 1 }); } }, `← ${t.ft_prev}`) : "",
      el("span", {}, t.ft_page_of.replace("{a}", cur + 1).replace("{b}", pages)),
      cur < pages - 1 ? el("a", { href: "#", onclick: e => { e.preventDefault(); go({ p: cur + 1 }); } }, `${t.ft_next} →`) : "") : "";
    const others = B.cells.filter(c => c.kt === kt).map(c => c.y);
    view.replaceChildren(
      el("p", { class: "kicker" }, t.ft_book),
      el("h1", {}, `${kt === "–" ? t.ft_no_canton : kt} ${y}`),
      el("p", { class: "lead" }, t.ft_book_lead.replace("{n}", n(cell.n)).replace("{b}", n(cell.refs.length)).replace("{g}", n(cell.munis.length))),
      el("p", { class: "years-nav" }, `${t.ft_other_years} `, ...others.flatMap((oy, i) => [i ? " · " : "", oy === y ? el("b", {}, String(oy)) : link(`#/buch?kt=${encodeURIComponent(kt)}&y=${oy}`, String(oy))])),
      el("div", { class: "searchbar" }, input, muniSel, refSel),
      el("p", { class: "count" }, (hits.length === 1 ? t.pg_hit_one : t.pg_hits).replace("{n}", n(hits.length))), nav(),
      el("ul", { class: "entries-list" }, ...hits.slice(cur * per, cur * per + per).map(r => entryRow(r, B, marks))), nav(),
      el("p", { class: "sub note" }, t.ft_image_note));
    const fcs = input; fcs.focus(); fcs.setSelectionRange(q.length, q.length);
  }

  // Volltext über alle Einträge: Wörter je Feld, genau oder ungefähr, Treffer nach Jahr
  let vocabList;
  const vocab = async () => vocabList ??= await get("data/vocab.json.gz");
  const FT_FIELDS = ["n", "v", "b", "s", "o", "t"];
  async function fulltext(params) {
    const B = await books();
    const vals = Object.fromEntries(["q", ...FT_FIELDS].map(k => [k, params.get(k === "q" ? "q" : `f${k}`) || ""]));
    const approx = params.get("u") === "1", ya = +(params.get("a") || 1880), yz = +(params.get("z") || 1914);
    const shown = +(params.get("j") || 3);
    const inputs = Object.fromEntries(Object.keys(vals).map(k => [k, el("input", { type: "search", value: vals[k], class: "q",
      placeholder: k === "q" ? t.ft_all_ph : t[`ft_f_${k}`], "aria-label": k === "q" ? t.ft_all_ph : t[`ft_f_${k}`] })]));
    const modeSel = select([["0", t.ft_exact], ["1", t.ft_approx]], approx ? "1" : "0", t.ft_mode);
    let range = [ya, yz];
    const go = upd => {
      const p = new URLSearchParams({ v: "ft", q: inputs.q.value, u: modeSel.querySelector("select").value === "1" ? "1" : "",
        a: range[0], z: range[1], ...Object.fromEntries(FT_FIELDS.map(k => [`f${k}`, inputs[k].value])), ...upd });
      for (const [k, v] of [...p]) if (!v || (k === "a" && v === "1880") || (k === "z" && v === "1914")) p.delete(k);
      location.replace(`#/suche?${p}`);
    };
    const form = el("form", { class: "ft-form" });
    form.addEventListener("submit", ev => { ev.preventDefault(); go({ j: "" }); });
    modeSel.querySelector("select").addEventListener("change", () => go({ j: "" }));
    const fieldsOpen = FT_FIELDS.some(k => vals[k]);
    form.append(el("div", { class: "searchbar" }, inputs.q, el("button", { type: "submit" }, t.pg_search_go)),
      el("div", { class: "controls" }, rangeSlider(1880, 1914, ya, yz, (x, y) => { range = [x, y]; go({ j: "" }); }), modeSel),
      el("details", { class: "filters", ...(fieldsOpen ? { open: "" } : {}) }, el("summary", {}, t.ft_fields),
        el("div", { class: "field-grid" }, ...FT_FIELDS.map(k => el("label", { class: "ctl" }, el("span", {}, t[`ft_f_${k}`]), inputs[k]))),
        el("p", { class: "sub" }, t.ft_fields_note)));
    const out = el("div", { class: "results" });
    view.replaceChildren(el("h1", {}, t.pg_search_h), searchTabs("ft"), el("p", { class: "intro" }, t.ft_p), form, out);
    inputs.q.focus();
    // Suchbegriffe: [Feld oder null, Wort]
    const terms = [];
    const tok = (s, f) => s.split(/\s+/).filter(Boolean).forEach(w => {
      const k = (f === "t" || (/^\d/.test(w) && !f)) ? w.replace(/\D/g, "") : fold(w);
      if (k.length >= (f === "t" || /^\d+$/.test(k) ? 1 : 2)) terms.push([/^\d+$/.test(k) && !f ? "t" : f, k]);
    });
    tok(vals.q, null);
    FT_FIELDS.forEach(f => tok(vals[f], f));
    if (!terms.length) { out.append(el("p", { class: "muted" }, t.ft_hint)); return; }
    out.append(el("p", { class: "muted" }, t.loading));
    const V = approx ? await vocab() : null;
    const marks = new Set();
    let result = null;
    for (const [f, w] of terms) {
      let forms = [w];
      if (approx && !/^\d+$/.test(w)) {
        const qk = fkey(w);
        forms = V.filter(([x, fs]) => (!f || fs.includes(f)) && Math.abs(x.length - w.length) <= 2 && (x === w || dist(qk, fkey(x)) <= threshold(qk))).map(x => x[0]);
      }
      const ids = new Set();
      for (const form of forms) {
        let sh;
        try { sh = await get(`data/ft/${fnv(form, 0x3f)}.json.gz`); } catch { continue; }
        for (const fld of f ? [f] : FT_FIELDS) for (const id of sh[`${fld}:${form}`] || []) ids.add(id);
        marks.add(form);
      }
      result = result === null ? ids : new Set([...result].filter(id => ids.has(id)));
      if (!result.size) break;
    }
    const byYear = new Map();
    for (const id of result) {
      const c = B.cells[Math.floor(id / 100000)];
      if (c.y < range[0] || c.y > range[1]) continue;
      if (!byYear.has(c.y)) byYear.set(c.y, []);
      byYear.get(c.y).push(id);
    }
    const yearsSorted = [...byYear.keys()].sort((x, y) => x - y);
    const total = [...byYear.values()].reduce((a, b) => a + b.length, 0);
    const parts = [el("p", { class: "count" }, (total === 1 ? t.ft_hits_one : t.ft_hits).replace("{n}", n(total))
      .replace("{j}", n(yearsSorted.length)).replace("{jj}", yearsSorted.length === 1 ? t.ft_year1 : t.ft_yearN)),
      approx ? el("p", { class: "sub" }, t.ft_approx_forms.replace("{w}", [...marks].slice(0, 30).join(", "))) : ""];
    for (const y of yearsSorted.slice(0, shown)) {
      const ids = byYear.get(y).sort((a, b) => a - b);
      const list = el("ul", { class: "entries-list" });
      for (const id of ids.slice(0, 100)) {
        const c = B.cells[Math.floor(id / 100000)];
        const rows = await get(cellFile(c));
        list.append(entryRow(rows[id % 100000], B, marks));
      }
      parts.push(el("h2", { class: "year-h" }, String(y), " ", el("span", { class: "muted" }, `(${n(ids.length)})`)), list,
        ids.length > 100 ? el("p", { class: "muted" }, t.ft_year_more.replace("{n}", n(ids.length - 100))) : "");
    }
    if (yearsSorted.length > shown) {
      const more = el("button", { type: "button", class: "more" }, t.ft_more_years);
      more.addEventListener("click", () => go({ j: shown + 3 }));
      parts.push(more);
    }
    out.replaceChildren(...parts);
  }

  // ── M9: vom HLS zum Eintrag (scripts/build_hls.py, docs/hls_abdeckung.md) ──────
  const HL_TIERS = ["normdaten", "wahrscheinlich", "möglich", "schwach", "nicht_gefunden"];
  const fieldName = f => (t.hl_fields || {})[f] || f;  // Fachgebiet des HLS in der Sprache der Seite
  const hlBadge = f => el("span", { class: `pill hl-${f}` }, t[`hl_t_${f}`] || f);
  const life = (b, d) => `${b}–${d || ""}`;
  let hlsIndex;
  const hlsData = async () => hlsIndex ??= await get("data/hls.json.gz");

  async function hls(args, params) {
    if (args[0]) return hlsPerson(args[0]);
    const H = await hlsData();
    const q = params.get("q") || "", tf = params.get("t") || "", kt = params.get("k") || "", ff = params.get("f") || "";
    const by = params.get("g") || "kt", page = +(params.get("p") || 0);
    const go = upd => {
      const p = new URLSearchParams({ q, t: tf, k: kt, f: ff, g: by, ...upd });
      for (const [k, v] of [...p]) if (!v || (k === "g" && v === "kt")) p.delete(k);
      location.replace(`#/hls?${p}`);
    };
    // Übersicht
    const count = rows => { const c = Object.fromEntries(HL_TIERS.map(x => [x, 0])); for (const r of rows) c[r[5]]++; return c; };
    const bar = c => {
      const tot = HL_TIERS.reduce((s, x) => s + c[x], 0) || 1;
      return el("div", { class: "hl-bar", role: "img", "aria-label": HL_TIERS.map(x => `${t["hl_t_" + x]} ${c[x]}`).join(", ") },
        ...HL_TIERS.map(x => el("span", { class: `hl-${x}`, style: `width:${100 * c[x] / tot}%`, title: `${t["hl_t_" + x]}: ${n(c[x])}` })));
    };
    const share = c => { const tot = HL_TIERS.reduce((s, x) => s + c[x], 0); return tot ? Math.round(100 * (c.normdaten + c.wahrscheinlich) / tot) : 0; };
    const all = count(H.rows);
    const groupKey = {
      kt: r => r[7] || "–",
      jz: r => `${Math.floor(r[2] / 10) * 10}er`,
      g: r => (r[4] === "f" ? t.hl_women : t.hl_men),
      s: r => t["hl_s_" + r[6]] || r[6],
      fg: r => r[10].length ? r[10].map(i => fieldName(H.fields[i])) : ["–"],
    }[by] || (r => r[7]);
    const groups = new Map();
    for (const r of H.rows) for (const k of [groupKey(r)].flat()) { if (!groups.has(k)) groups.set(k, []); groups.get(k).push(r); }
    const gsel = select([["kt", t.hl_by_kt], ["jz", t.hl_by_jz], ["g", t.hl_by_g], ["s", t.hl_by_s], ["fg", t.hl_by_fg]], by, t.hl_group);
    gsel.querySelector("select").addEventListener("change", ev => go({ g: ev.target.value }));
    const gtab = el("tbody");
    for (const [k, rs] of [...groups].sort((a, b) => (by === "kt" || by === "fg" ? b[1].length - a[1].length : String(a[0]).localeCompare(String(b[0]), "de")))) {
      const c = count(rs);
      gtab.append(el("tr", {}, el("td", {}, k), el("td", { class: "num" }, n(rs.length)), el("td", { class: "barcell" }, bar(c)),
        el("td", { class: "num" }, `${share(c)} %`)));
    }
    const legend = el("ul", { class: "legend" }, ...HL_TIERS.map(x => el("li", {}, el("span", { class: `sw hl-${x}` }), `${t["hl_t_" + x]} (${n(all[x])})`)));
    // Liste
    const input = el("input", { type: "search", value: q, placeholder: t.hl_search_ph, "aria-label": t.hl_search_ph, class: "q" });
    let timer;
    input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => go({ q: input.value, p: "" }), 300); });
    const tsel = select([["", t.mp_all], ...HL_TIERS.map(x => [x, t["hl_t_" + x]])], tf, t.hl_tier);
    tsel.querySelector("select").addEventListener("change", ev => go({ t: ev.target.value, p: "" }));
    const kts = [...new Set(H.rows.map(r => r[7]).filter(Boolean))].sort();
    const ksel = select([["", t.mp_all], ...kts.map(k => [k, k])], kt, t.hl_canton);
    ksel.querySelector("select").addEventListener("change", ev => go({ k: ev.target.value, p: "" }));
    const fsel = select([["", t.mp_all], ...H.fields.map((f, i) => [String(i), fieldName(f)])], ff, t.hl_field);
    fsel.querySelector("select").addEventListener("change", ev => go({ f: ev.target.value, p: "" }));
    const qf = fold(q), qn = q.replace(/\D/g, "");
    const hits = H.rows.filter(r => (!q || (qn && r[0].includes(qn)) || (qf && fold(r[1]).includes(qf)))
      && (!tf || r[5] === tf) && (!kt || r[7] === kt) && (!ff || r[10].includes(+ff)));
    const PER = 100;
    const ul = el("ul", { class: "hitlist" });
    for (const r of hits.slice(page * PER, page * PER + PER)) {
      ul.append(el("li", {}, link(`#/hls/${r[0]}`, r[1], "hit"),
        el("span", { class: "meta" }, `${life(r[2], r[3])} · ${r[8]}${r[7] ? ` (${r[7]})` : ""}`), hlBadge(r[5]),
        r[9] && r[5] !== "normdaten" ? el("span", { class: "muted" }, ` ${r[9] === 1 ? t.hl_cand1 : t.hl_cands.replace("{n}", n(r[9]))}`) : ""));
    }
    const pager = el("p", { class: "pager" },
      page > 0 ? el("button", { type: "button", onclick: () => go({ p: page - 1 }) }, t.hl_prev) : "",
      ` ${n(page * PER + 1)}–${n(Math.min(hits.length, page * PER + PER))} / ${n(hits.length)} `,
      (page + 1) * PER < hits.length ? el("button", { type: "button", onclick: () => go({ p: page + 1 }) }, t.hl_next) : "");
    view.replaceChildren(el("h1", {}, t.hl_h), el("p", { class: "intro" }, t.hl_intro),
      el("section", { class: "card hl-sum" },
        el("p", { class: "big" }, t.hl_sum.replace("{e}", n(H.rows.length)).replace("{s}", n(all.normdaten + all.wahrscheinlich))
          .replace("{c}", n(all.möglich + all.schwach))),
        bar(all), legend, el("p", { class: "sub" }, t.hl_sum_note, " ", link("https://github.com/thodel/vernetzte-schweiz/blob/main/docs/hls_abdeckung.md", t.hl_method))),
      el("h2", {}, t.hl_groups_h), el("div", { class: "controls" }, gsel),
      el("div", { class: "grid-scroll" }, el("table", { class: "hl-groups" },
        el("thead", {}, el("tr", {}, ...[t.hl_col_group, t.hl_col_expected, t.hl_col_tiers, t.hl_col_share].map(h => el("th", {}, h)))), gtab)),
      el("h2", {}, t.hl_list_h),
      el("div", { class: "searchbar" }, input), el("div", { class: "controls" }, tsel, ksel, fsel),
      el("p", { class: "count" }, t.pg_hits.replace("{n}", n(hits.length))), ul, hits.length > PER ? pager : "");
    if (q) { input.focus(); input.setSelectionRange(q.length, q.length); }
  }

  async function hlsPerson(id) {
    let shard;
    try { shard = await get(`data/hls/${fnv(id, 0x3f)}.json.gz`); } catch { shard = {}; }
    const p = shard[id];
    if (!p) { view.replaceChildren(el("h1", {}, t.pg_not_found)); return; }
    document.title = `${p.n} · ${t.hls_abbr || "HLS"} · Vernetzte Schweiz`;
    const here = p.c.filter(c => c[7] === "ort"), far = p.c.filter(c => c[7] === "anderswo");
    const parts = [el("header", { class: "ent-head" },
      el("p", { class: "kicker" }, t.hl_kicker),
      el("h1", {}, p.n),
      el("p", { class: "lead" }, `${life(p.b, p.d)} · `, link(hlsUrl(id), `${t.hls_abbr || "HLS"} ${id}`), " ", hlBadge(p.f))),
      el("p", { class: "intro" }, t.hl_expected.replace("{a}", p.a[0]).replace("{z}", p.a[1]), " ", t["hl_s_long_" + p.s] || "")];
    // Raster: Orte × Jahre
    const [y0, y1] = p.a, w = 100 / (y1 - y0 + 1);
    const grid = el("div", { class: "hl-grid" });
    for (const [muni, a, z, srcs, yrs] of p.p) {
      const got = new Map();
      for (const c of here) if (c[2] === muni) for (const y of c[3]) {
        if (!got.has(y) || HL_TIERS.indexOf(c[4]) < HL_TIERS.indexOf(got.get(y))) got.set(y, c[4]);
      }
      const row = el("div", { class: "hl-row" });
      for (let y = y0; y <= y1; y++) {
        const inSpan = y >= a && y <= z, book = yrs.includes(y), hit = got.get(y);
        row.append(el("span", { class: `hl-cell${inSpan ? " span" : ""}${book ? " book" : ""}${hit ? " hit hl-" + hit : ""}`,
          style: `left:${(y - y0) * w}%;width:${w}%`,
          title: `${muni} ${y}: ${hit ? t["hl_t_" + hit] : book ? t.hl_cell_book : inSpan ? t.hl_cell_nobook : t.hl_cell_out}` }));
      }
      grid.append(el("div", { class: "hl-line" },
        el("div", { class: "hl-place" }, link(placeHref(muni), muni), el("span", { class: "muted" },
          ` ${years([a, z])} · ${srcs.split("+").map(s => t["hl_src_" + s] || s).filter((v, i, xs) => xs.indexOf(v) === i).join(", ")}`)),
        row));
    }
    const ticks = el("div", { class: "tl-ticks" }, ...[...new Set([y0, ...[1880, 1890, 1900, 1910].filter(y => y > y0 && y < y1), y1])]
      .map(y => el("span", { style: `left:${(y - y0) * w}%` }, String(y))));
    parts.push(el("h2", {}, t.hl_grid_h), grid, el("div", { class: "hl-line" }, el("div"), ticks),
      el("ul", { class: "legend" },
        el("li", {}, el("span", { class: "sw hl-span" }), t.hl_cell_nobook),
        el("li", {}, el("span", { class: "sw hl-book" }), t.hl_cell_book),
        ...["normdaten", "wahrscheinlich", "möglich", "schwach"].map(x => el("li", {}, el("span", { class: `sw hl-${x}` }), t["hl_t_" + x]))));
    // Kandidaten
    const candList = cs => el("ul", { class: "hitlist" }, ...cs.map(([eid, label, muni, ys, tier, why, occ]) => el("li", {},
      link(`#/e/${eid}`, label, "hit"),
      el("span", { class: "meta" }, `${muni} · ${ys.length ? years([ys[0], ys[ys.length - 1]]) : ""}`),
      tier !== "anderswo" ? hlBadge(tier) : "",
      el("span", { class: "pill why" }, why.split(" ").map(x => x.split("+").map(y => t["hl_why_" + y] || y).join(" + ")).join("; ")),
      occ ? el("span", { class: "occ" }, occ) : "")));
    if (here.length) {
      parts.push(el("h2", {}, t.hl_cands_h.replace("{n}", n(here.length))), el("p", { class: "intro" }, t.hl_cands_p), candList(here));
    } else {
      parts.push(el("h2", {}, t.hl_none_h), el("p", { class: "intro" }, t["hl_r_" + p.r] || ""));
    }
    if (far.length) parts.push(el("h2", {}, t.hl_far_h), el("p", { class: "intro" }, t.hl_far_p), candList(far));
    parts.push(el("p", { class: "sub note" }, t.hl_note, " ", link("#/hls", t.hl_back)));
    view.replaceChildren(...parts);
  }

  // ── Router ───────────────────────────────────────────────────────────────
  const routes = { suche: search, e: entity, a: address, g: place, orte: placeList, vorbehalte: caveats, karten, buch: phonebook, hls };
  async function route() {
    dropMaps();
    if (!location.hash.startsWith("#/") || location.hash === "#/") {
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
    document.title = `${t["nav_" + { suche: "search", orte: "places", vorbehalte: "caveats", karten: "maps", buch: "phone", hls: "hls" }[name]] || "…"} · Vernetzte Schweiz`;
    view.replaceChildren(el("p", { class: "muted" }, t.loading));
    try { await (name === "hls" ? fn(args, params) : ["suche", "orte", "karten", "buch"].includes(name) ? fn(params) : fn(args)); }
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

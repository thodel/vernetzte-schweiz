// Startseite: Texte aus i18n/<lang>.json, Zahlen aus data/stats.json.
(async function () {
  const lang = (document.documentElement.lang || "de").slice(0, 2);
  const t = await fetch(`i18n/${lang}.json`).then(r => r.json());
  const nf = new Intl.NumberFormat("de-CH");  // Zahlen schweizerisch in allen Sprachen (21'948)

  // Sprachwahl: aktuelle Sprache markieren; Wechsel behält die aufgerufene Seite (#/…)
  document.querySelectorAll("#langs a").forEach(a => {
    if (a.hreflang === lang) a.setAttribute("aria-current", "true");
    a.addEventListener("click", ev => {
      ev.preventDefault();
      try { localStorage.setItem("lang", a.hreflang); } catch (e) {}
      location.href = `?lang=${a.hreflang}${location.hash}`;
    });
  });
  if (t.lang_switch) document.getElementById("langs")?.setAttribute("aria-label", t.lang_switch);
  if (t.meta_description) document.querySelector('meta[name="description"]')?.setAttribute("content", t.meta_description);
  const n = v => nf.format(v);
  const el = (tag, attrs = {}, ...kids) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) k === "class" ? (e.className = v) : e.setAttribute(k, v);
    for (const k of kids) e.append(k);
    return e;
  };

  document.querySelectorAll("[data-i18n]").forEach(e => {
    const v = t[e.dataset.i18n];
    if (typeof v === "string") e.textContent = v;
  });

  const steps = document.getElementById("steps");
  for (const [id, text, status] of t.plan_items) {
    steps.append(el("li", {}, el("b", {}, id), el("span", {}, text),
      status ? el("span", { class: `badge ${status}` }, t[`status_${status}`]) : ""));
  }

  let s;
  try {
    s = await fetch("data/stats.json").then(r => { if (!r.ok) throw r; return r.json(); });
  } catch (e) {
    document.getElementById("kpis").textContent = t.load_error;
    return;
  }

  const kpis = document.getElementById("kpis");
  kpis.replaceChildren(...[
    ["kpi_ab", s.totals.ab_entries, "cat-source"], ["kpi_ptt", s.totals.ptt_entries, "cat-ann"],
    ["kpi_networks", s.ptt.municipalities, "cat-ann"], ["kpi_linked", s.totals.ptt_linked, "cat-link"],
    ["kpi_qids", s.totals.qids, "cat-pers"],
  ].map(([k, v, cat]) => el("div", { class: cat }, el("dt", {}, t[k]), el("dd", {}, n(v)))));

  const cities = document.getElementById("cities");
  for (const c of s.cities) {
    const a = c.authority;
    const rows = [
      [t.city_entries, n(c.entries)],
      ...Object.entries(c.kinds).map(([k, v]) => [`·\u00a0${t["kind_" + k] || k}`, n(v)]),
      // Normdaten nur, wo das Quell-Repo welche liefert (Baden, Bern, Lausanne: keine)
      ...(a.entries ? [
        [t.city_authority, n(a.entries), "auth"],
        ...Object.entries(a.tiers).map(([k, v]) => [`·\u00a0${k}`, n(v), "auth"]),
        [t.city_confirmed, n(a.hls_confirmed), "auth"],
        [t.city_hls, n(a.hls), "auth"],
        [t.city_gnd, n(a.gnd), "auth"],
      ] : []),
    ];
    cities.append(el("article", { class: "card" },
      el("h3", {}, c.label),
      el("p", { class: "sub" }, `${t.city_volumes}: ${c.volumes.length}`),
      el("div", { class: "vols" }, ...c.volumes.map(v => el("span", { class: "vol", title: `${n(v.entries)} ${t.city_entries}` }, String(v.year)))),
      el("table", {}, el("tbody", {}, ...rows.map(([k, v, cls]) => el("tr", cls ? { class: cls } : {}, el("td", {}, k), el("td", {}, v))))),
      a.entries ? "" : el("p", { class: "sub" }, t.city_no_authority),
      el("p", { class: "links" },
        ...(c.site ? [el("a", { href: c.site }, t.city_open), " · "] : []),
        el("a", { href: `https://github.com/${c.repo}/tree/${c.commit}` }, `${t.city_pinned} ${c.commit}`)),
    ));
  }

  const heat = document.getElementById("heat");
  const max = Math.max(...s.ptt.grid.flatMap(g => g.counts));
  heat.append(el("thead", {}, el("tr", {}, el("th", { class: "net" }, t.phone_network),
    ...s.ptt.years.map(y => el("th", {}, y)), el("th", {}, t.phone_total))));
  const body = el("tbody");
  for (const g of s.ptt.grid) {
    const tr = el("tr", {}, el("th", { class: "net" }, g.canton));
    g.counts.forEach((v, i) => {
      const td = el("td", { class: "cell", title: `${g.canton} ${s.ptt.years[i]}: ${v ? n(v) : t.phone_none}` });
      if (v) {
        td.style.background = `rgba(var(--cat-ann-rgb), ${0.12 + 0.88 * Math.sqrt(v / max)})`;
        // Klick: alle Einträge dieses Kantons und Jahrgangs (#/buch, pages.js)
        td.append(el("a", { href: `#/buch?kt=${encodeURIComponent(g.canton)}&y=${s.ptt.years[i]}`, class: "cell-link",
          "aria-label": `${g.canton} ${s.ptt.years[i]}: ${n(v)} ${t.phone_entries_open}` }));
      }
      tr.append(td);
    });
    tr.append(el("td", { class: "tot" }, n(g.total)));
    body.append(tr);
  }
  heat.append(body);
  // Total je Jahrgang (Spaltensumme über alle Kantone)
  const col = s.ptt.years.map((_, i) => s.ptt.grid.reduce((a, g) => a + g.counts[i], 0));
  heat.append(el("tfoot", {}, el("tr", {}, el("th", { class: "net" }, t.phone_total),
    ...col.map((v, i) => el("td", { class: "ytot", title: `${s.ptt.years[i]}: ${n(v)}` }, n(v))),
    el("td", { class: "tot" }, n(col.reduce((a, b) => a + b, 0))))));

  // Ortsqualität: gestapelter Balken je Charge, Arten der Einträge
  const q = document.getElementById("quality");
  const order = ["hoch", "mittel", "unsicher", "keine"];
  for (const c of s.ptt.confidence) {
    const bar = el("div", { class: "stack" });
    for (const k of order) {
      const v = c.counts[k];
      if (!v) continue;
      const seg = el("span", { class: `seg conf-${k}`, title: `${t["conf_" + k]}: ${n(v)}` });
      seg.style.flexGrow = v;
      bar.append(seg);
    }
    q.append(el("div", { class: "qrow" },
      el("div", { class: "qlabel" }, `${t.quality_batch} ${c.batch} · ${c.years[0]}–${c.years[1]}`, el("span", { class: "muted" }, ` · ${n(c.total)}`)),
      bar));
  }
  q.append(el("ul", { class: "legend" }, ...order.map(k => {
    const tot = s.ptt.confidence.reduce((a, c) => a + c.counts[k], 0);
    return el("li", {}, el("span", { class: `sw conf-${k}` }), `${t["conf_" + k]} `, el("b", {}, n(tot)));
  })));
  const facts = [
    [t.quality_recovered, s.ptt.recovered],
    ...Object.entries(s.ptt.types).map(([k, v]) => [t["type_" + k] || k, v]),
    [t.phone_with_street, s.ptt.with_street],
    [t.phone_with_initials, s.ptt.with_initials],
  ];
  q.append(el("table", { class: "facts" }, el("tbody", {}, ...facts.map(([k, v]) => el("tr", {}, el("td", {}, k), el("td", {}, n(v)))))));

  // Verknüpfung Telefonbuch ↔ Adressbuch
  const pct = v => `${Math.round(v * 100)}\u00a0%`;
  const lk = document.getElementById("links");
  for (const c of s.links) {
    const rows = [
      [t.links_volumes, c.volumes.join(", ")],
      [t.links_entries, n(c.ptt_entries)],
      [t.links_linked, `${n(c.ptt_linked)} (${pct(c.ptt_linked / Math.max(c.ptt_entries, 1))})`],
    ];
    const tiers = c.tiers.filter(x => x.decisions);
    lk.append(el("article", { class: "card link" },
      el("h3", {}, c.label),
      el("table", {}, el("tbody", {}, ...rows.map(([k, v]) => el("tr", {}, el("td", {}, k), el("td", {}, v))))),
      el("table", { class: "tiers" },
        el("thead", {}, el("tr", {}, el("th", {}, t.links_tier), el("th", {}, t.links_decisions), el("th", {}, t.links_precision.replace("{n}", tiers.find(x => x.precision)?.precision.n ?? "–")))),
        el("tbody", {}, ...tiers.map(x => el("tr", {},
          el("td", {}, el("span", { class: `sw tier-${x.tier}` }), t["tier_" + x.tier]),
          el("td", {}, n(x.decisions)),
          el("td", {}, x.precision ? `${Math.round(x.precision.low * 100)}–${pct(x.precision.high)}` : "–"))))),
      c.id === "basel" ? el("p", { class: "sub note" }, t.links_gap) : "",
    ));
  }
  const rc = s.recall.map(r => t.links_recall_item.replace("{vol}", r.volume).replace("{flagged}", n(r.flagged))
    .replace("{reachable}", n(r.reachable)).replace("{linked}", n(r.linked)).replace("{pct}", pct(r.linked / r.reachable)));
  document.getElementById("recall").textContent = [t.links_recall, ...rc].join(" ");

  // Einheiten über die Jahre und Normdaten (M3)
  const en = s.entities, ek = document.getElementById("entities");
  const range = (lo, hi) => Math.round(lo * 100) === Math.round(hi * 100) ? pct(lo) : `${Math.round(lo * 100)}–${pct(hi)}`;
  const facts3 = [
    [t.ent_records, n(en.records)],
    [t.ent_entities, n(en.entities)],
    [t.ent_persons, n(en.by_kind.person || 0)],
    [t.ent_firms, n(en.by_kind.firma || 0)],
    [t.ent_multi, n(en.entities_multi)],
    [t.ent_span, n(en.span_10y)],
    [t.ent_both, n(en.with_ptt_and_ab)],
  ];
  ek.append(el("article", { class: "card link" }, el("h3", {}, t.ent_card_bundle),
    el("table", {}, el("tbody", {}, ...facts3.map(([k, v]) => el("tr", {}, el("td", {}, k), el("td", {}, v)))))));
  const ql = en.quality.map(q => [t["ent_layer_" + q.layer] || q.layer, q.n,
    q.recall_low != null ? range(q.recall_low, q.recall_high) : range(q.precision_low, q.precision_high)]);
  ek.append(el("article", { class: "card link" }, el("h3", {}, t.ent_card_quality),
    el("table", { class: "tiers wrap" },
      el("thead", {}, el("tr", {}, el("th", {}, t.ent_layer), el("th", {}, "n"), el("th", {}, t.ent_value))),
      el("tbody", {}, ...ql.map(([a, b, c]) => el("tr", {}, el("td", {}, a), el("td", {}, n(b)), el("td", {}, c))))),
    el("p", { class: "sub note" }, t.ent_quality_note)));
  const au = s.authority;
  const arows = [
    [t.auth_city, n(au.stadt)],
    ...["wahrscheinlich", "möglich"].map(x => [`${t.auth_ptt} · ${t["tier_" + x]}`, n(au.ptt[x] || 0)]),
    [t.auth_hls, n(au.hls)], [t.auth_gnd, n(au.gnd)],
  ];
  ek.append(el("article", { class: "card link" }, el("h3", {}, t.ent_card_auth),
    el("table", {}, el("tbody", {}, ...arows.map(([k, v]) => el("tr", {}, el("td", {}, k), el("td", {}, v))))),
    el("p", { class: "sub note" }, au.precision ? t.auth_note.replace("{p}", range(au.precision.low, au.precision.high)).replace("{n}", au.precision.n)
      .replace("{p2}", range(au.precision2.low, au.precision2.high)).replace("{n2}", au.precision2.n) : t.auth_note_none)));
})();

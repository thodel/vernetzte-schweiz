// Startseite: Texte aus i18n/<lang>.json, Zahlen aus data/stats.json.
(async function () {
  const lang = (document.documentElement.lang || "de").slice(0, 2);
  const t = await fetch(`i18n/${lang}.json`).then(r => r.json());
  const nf = new Intl.NumberFormat("de-CH");
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
    ["kpi_networks", s.ptt.municipalities, "cat-ann"], ["kpi_qids", s.totals.qids, "cat-pers"],
  ].map(([k, v, cat]) => el("div", { class: cat }, el("dt", {}, t[k]), el("dd", {}, n(v)))));

  const cities = document.getElementById("cities");
  for (const c of s.cities) {
    const a = c.authority;
    const rows = [
      [t.city_entries, n(c.entries)],
      ...Object.entries(c.kinds).map(([k, v]) => [`· ${t["kind_" + k] || k}`, n(v)]),
      [t.city_authority, n(a.entries), "auth"],
      [t.city_tiers, Object.entries(a.tiers).map(([k, v]) => `${k} ${n(v)}`).join(" · "), "auth"],
      [t.city_confirmed, n(a.hls_confirmed), "auth"],
      [t.city_hls, n(a.hls), "auth"],
      [t.city_gnd, n(a.gnd), "auth"],
    ];
    cities.append(el("article", { class: "card" },
      el("h3", {}, c.label),
      el("p", { class: "sub" }, `${t.city_volumes}: ${c.volumes.length}`),
      el("div", { class: "vols" }, ...c.volumes.map(v => el("span", { class: "vol", title: `${n(v.entries)} ${t.city_entries}` }, String(v.year)))),
      el("table", {}, el("tbody", {}, ...rows.map(([k, v, cls]) => el("tr", cls ? { class: cls } : {}, el("td", {}, k), el("td", {}, v))))),
      el("p", { class: "links" },
        el("a", { href: c.site }, t.city_open), " · ",
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
      if (v) td.style.background = `rgba(var(--cat-ann-rgb), ${0.12 + 0.88 * Math.sqrt(v / max)})`;
      tr.append(td);
    });
    tr.append(el("td", { class: "tot" }, n(g.total)));
    body.append(tr);
  }
  heat.append(body);

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
})();

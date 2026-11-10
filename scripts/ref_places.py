"""Ortsregister → data/ref/municipalities_1914.csv, data/ref/localities.csv.

- Gemeinden mit Stand 1914 aus dem Historisierten Gemeindeverzeichnis des BFS
  (Schnappschuss zum Stichtag in `config/sources.toml`, [places].hgv_date).
- Ortschaften (auch Weiler und Dörfer, die nie Gemeinde waren) aus dem amtlichen
  Ortschaftenverzeichnis von swisstopo, mit heutiger Gemeinde und Koordinaten.

Beide Tabellen liegen im Repo, damit die Ortsauflösung ohne Netz reproduzierbar ist.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import math
import urllib.request
import zipfile

from common import ROOT, config, write_csv

REF = ROOT / "data" / "ref"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "vernetzte-schweiz-ref"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def lv95_to_wgs84(e: float, n: float) -> tuple[float, float]:
    """Näherungsformel von swisstopo (Genauigkeit ~1 m), LV95 → WGS84."""
    y, x = (e - 2_600_000) / 1_000_000, (n - 1_200_000) / 1_000_000
    lon = 2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x * x - 0.0436 * y ** 3
    lat = 16.9023892 + 3.238272 * x - 0.270978 * y * y - 0.002528 * x * x - 0.0447 * y * y * x - 0.0140 * x ** 3
    return round(lat * 100 / 36, 6), round(lon * 100 / 36, 6)


API = "https://www.agvchapp.bfs.admin.ch/api/communes"


def api_csv(path: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(get(f"{API}/{path}").decode("utf-8-sig"))))


def successors(date: str) -> tuple[dict[str, set[str]], dict[str, dict]]:
    """Nachfolger je Historisierungsnummer seit dem Stichtag, und die heutigen Gemeinden.

    Der Schnappschuss gibt Gemeinden, die später neu nummeriert oder fusioniert wurden, die
    Platzhalter-BFS-Nummer 7700 (Zürich, Bern, Winterthur …); die heutige Nummer findet
    nur, wer die Mutationen bis heute verfolgt.
    """
    today = {r["HistoricalCode"]: r for r in api_csv(f"snapshot?date={dt.date.today():%d-%m-%Y}")
             if r["Level"] == "3"}
    nxt: dict[str, set[str]] = {}
    d, m, y = date.split("-")
    start = (dt.date(int(y), int(m), int(d)) + dt.timedelta(days=1)).strftime("%d-%m-%Y")
    for r in api_csv(f"mutations?startPeriod={start}&endPeriod={dt.date.today():%d-%m-%Y}"
                     "&includeTerritoryExchange=false"):
        if r["InitialHistoricalCode"] != r["TerminalHistoricalCode"]:
            nxt.setdefault(r["InitialHistoricalCode"], set()).add(r["TerminalHistoricalCode"])
    return nxt, today


def follow(code: str, nxt: dict[str, set[str]], today: dict[str, dict]) -> list[dict]:
    seen, todo, out = set(), [code], []
    while todo:
        c = todo.pop()
        if c in seen:
            continue
        seen.add(c)
        if c in today:
            out.append(today[c])
        else:
            todo.extend(nxt.get(c, ()))
    return out


def municipalities(date: str) -> list[dict]:
    rows = api_csv(f"snapshot?date={date}")
    nxt, today = successors(date)
    # HistoricalCode ist nur je Ebene eindeutig (10053 = Bezirk Affoltern und Poschiavo)
    by_hist = {(r["Level"], r["HistoricalCode"]): r for r in rows}
    out = []
    for r in rows:
        if r["Level"] != "3":
            continue
        district = by_hist.get(("2", r["Parent"]), {})
        canton = by_hist.get(("1", district.get("Parent", "")), {})
        succ = follow(r["HistoricalCode"], nxt, today)
        out.append({
            "hist_code": r["HistoricalCode"], "bfs": "" if r["BfsCode"] == "7700" else r["BfsCode"],
            "name": r["Name"], "district": district.get("Name", ""), "canton": canton.get("ShortName", ""),
            "valid_from": r["ValidFrom"], "valid_to": r["ValidTo"],
            "bfs_today": ";".join(sorted({x["BfsCode"] for x in succ}, key=int)),
            "name_today": ";".join(sorted({x["Name"] for x in succ})),
        })
    return sorted(out, key=lambda r: (r["canton"], r["name"]))


def localities(url: str) -> list[dict]:
    z = zipfile.ZipFile(io.BytesIO(get(url)))
    name = next(n for n in z.namelist() if n.endswith(".csv"))
    rows = csv.DictReader(io.StringIO(z.read(name).decode("utf-8-sig")), delimiter=";")
    seen, out = set(), []
    for r in rows:
        key = (r["Ortschaftsname"], r["PLZ4"], r["BFS-Nr"])
        if key in seen:
            continue
        seen.add(key)
        try:
            lat, lon = lv95_to_wgs84(float(r["E"]), float(r["N"]))
        except ValueError:
            lat = lon = math.nan
        out.append({
            "name": r["Ortschaftsname"], "plz": r["PLZ4"], "municipality_today": r["Gemeindename"],
            "bfs_today": r["BFS-Nr"], "canton": r["Kantonskürzel"], "lang": r["Sprache"],
            "share": r["Adressenanteil"].replace("%", "").strip(),
            "lat": lat, "lon": lon,
        })
    return sorted(out, key=lambda r: (r["name"], r["bfs_today"]))


def main() -> None:
    p = config()["places"]
    m = municipalities(p["hgv_date"])
    loc = localities(p["localities_url"])
    write_csv(REF / "municipalities_1914.csv", list(m[0]), m)
    write_csv(REF / "localities.csv", list(loc[0]), loc)
    print(f"Gemeinden {p['hgv_date']}: {len(m)} · Ortschaften: {len(loc)}")


if __name__ == "__main__":
    main()

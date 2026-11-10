"""Adressbuch-Einträge und Normdaten der Städte → data/norm/ab_entries.csv, ab_authority.csv.

Liest jede Stadt aus `config/sources.toml` am gepinnten Commit (siehe docs/datenvertrag.md).
"""

from __future__ import annotations

from collections import Counter

from common import NORM, config, fetch, in_window, read_csv, write_csv

ENTRY_FIELDS = [
    "id", "city", "volume", "kind", "page", "entry_type",
    "surname", "alliance_name", "maiden_name", "forename", "title", "civil_status",
    "occupation", "origin", "street", "building_no", "building_no_system",
    "phone_flag", "parse_confidence", "text",
]
AUTH_FIELDS = [
    "id", "city", "volume", "qid", "label", "birth", "death", "hls_id", "gnd",
    "tier", "hls_check", "evidence", "score",
]
VISIBLE_TIERS = {"wahrscheinlich", "möglich", "sicher"}


def visible(row: dict) -> bool:
    """Sichtbar ist alles bis «möglich»; verworfen oder in der HLS-Prüfung falsch fällt weg."""
    if row.get("tier", "") not in VISIBLE_TIERS:
        return False
    return not (row.get("hls_check") or "").strip().lower().startswith("falsch")


def entry(city: str, kind: str, r: dict) -> dict:
    occupation = (r.get("occupation_raw") or "").strip()
    if not occupation and kind == "berufe":
        occupation = (r.get("heading") or "").strip()
    return {
        "id": f"{city}:{r['entry_id']}",
        "city": city,
        "volume": r["volume"],
        "kind": kind,
        "page": r.get("page", ""),
        "entry_type": r.get("entry_type", ""),
        "surname": (r.get("surname") or r.get("surname_inherited") or "").strip(),
        "alliance_name": r.get("alliance_name", ""),
        "maiden_name": r.get("maiden_name", ""),
        "forename": r.get("forename", ""),
        "title": r.get("title", ""),
        "civil_status": r.get("civil_status", ""),
        "occupation": occupation,
        "origin": r.get("origin_raw", ""),
        "street": r.get("street_raw", ""),
        "building_no": r.get("building_no", ""),
        "building_no_system": r.get("building_no_system", ""),
        "phone_flag": r.get("phone_flag", ""),
        "parse_confidence": r.get("parse_confidence", ""),
        "text": r.get("text", ""),
    }


def officeholders(city: str, rows: list[dict], cfg: dict) -> list[dict]:
    """Amtsträger aus den Behördenverzeichnissen (Basel): ein Eintrag je Kandidat und Band."""
    out = []
    for c in rows:
        if "behoerden" not in c.get("sources", ""):
            continue
        for v in (c.get("office_volumes") or c.get("volumes") or "").split(";"):
            if not in_window(v, cfg):
                continue
            roles = " ".join(c.get("roles", "").split())
            out.append({
                "id": f"{city}:{c['cand_id']}-{v}", "city": city, "volume": v, "kind": "behoerden",
                "entry_type": "person", "surname": c["surname"], "alliance_name": c.get("alliance_name", ""),
                "forename": c.get("forename", ""), "title": c.get("title", ""), "occupation": roles[:200],
                "text": f"{c.get('title', '')} {c.get('forename', '')} {c['surname']} — {roles}".strip(),
                "parse_confidence": "",
            })
    return out


def main() -> None:
    cfg = config()
    entries: dict[str, dict] = {}
    authority: list[dict] = []
    stats: Counter = Counter()
    for c in cfg["city"]:
        cid, repo, commit = c["id"], c["repo"], c["commit"]
        for f in c["files"]:
            for r in read_csv(fetch(repo, commit, f["path"])):
                if not in_window(r.get("volume", ""), cfg):
                    stats[(cid, "ausserhalb Zeitfenster")] += 1
                    continue
                e = entry(cid, f["kind"], r)
                prev = entries.get(e["id"])
                if prev is None:
                    entries[e["id"]] = e
                    stats[(cid, "einträge")] += 1
                elif e["street"] and e["street"] not in prev["street"].split(" | "):
                    # weitere Adresse desselben Eintrags (address_seq > 1)
                    prev["street"] += " | " + e["street"]
                    prev["building_no"] += " | " + e["building_no"]
        if c.get("officeholders"):
            for e in officeholders(cid, read_csv(fetch(repo, commit, c["officeholders"])), cfg):
                entries.setdefault(e["id"], e)
                stats[(cid, "amtsträger")] += 1
        for r in read_csv(fetch(repo, commit, c["authority"])):
            if not in_window(r.get("volume", ""), cfg):
                continue
            if not visible(r):
                stats[(cid, "normdaten ausgeblendet")] += 1
                continue
            authority.append({**r, "id": f"{cid}:{r['entry_id']}", "city": cid})
            stats[(cid, "normdaten sichtbar")] += 1
    missing = [a["id"] for a in authority if a["id"] not in entries]
    write_csv(NORM / "ab_entries.csv", ENTRY_FIELDS, sorted(entries.values(), key=lambda e: e["id"]))
    write_csv(NORM / "ab_authority.csv", AUTH_FIELDS, sorted(authority, key=lambda a: (a["id"], a["qid"])))
    for k in sorted(stats):
        print(f"{k[0]:8} {k[1]:26} {stats[k]:>7}")
    print(f"Normdaten ohne Eintrag in den gelesenen Dateien: {len(missing)}", missing[:5])


if __name__ == "__main__":
    main()

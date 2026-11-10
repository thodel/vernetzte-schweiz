"""Gemeinsames für die Adapter: Konfiguration, Abruf am gepinnten Commit, CSV schreiben."""

from __future__ import annotations

import csv
import gzip
import io
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
NORM = ROOT / "data" / "norm"

csv.field_size_limit(1 << 30)


def config() -> dict:
    with open(ROOT / "config" / "sources.toml", "rb") as f:
        return tomllib.load(f)


def fetch(repo: str, commit: str, path: str) -> str:
    """Datei eines GitHub-Repos an einem Commit, zwischengespeichert unter .cache/."""
    target = CACHE / repo.replace("/", "__") / commit[:12] / path
    if not target.exists():
        url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
        req = urllib.request.Request(url, headers={"User-Agent": "vernetzte-schweiz-ingest"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return target.read_text(encoding="utf-8")


def read_csv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    """Schreibt CSV; endet der Pfad auf .gz, reproduzierbar gepackt (ohne Zeitstempel)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        raw = open(path, "wb")
        f = io.TextIOWrapper(gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename=""),
                             encoding="utf-8", newline="")
    else:
        f = open(path, "w", newline="", encoding="utf-8")
    with f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def in_window(year: str | int, cfg: dict) -> bool:
    try:
        y = int(str(year).strip())
    except ValueError:
        return False
    return cfg["window"]["year_from"] <= y <= cfg["window"]["year_to"]


def open_csv(path: Path) -> list[dict]:
    """Liest eine CSV-Datei aus data/, gepackt oder nicht."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

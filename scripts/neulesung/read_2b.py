"""Band 2b 1913/14 neu lesen (ab dem Block Luzern): eine Seite → JSONL. read_2b.py VOL RUN SCALE FIRST LAST [PAR] [SEITENLISTE]"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.expanduser("~/Desktop/claude-workspace/ptt-1947-qwen-test/scripts"))
from PIL import Image
from run_qwen import call

PROMPT = """You are transcribing one page of the 1913/1914 Swiss telephone directory "Verzeichnis der Telephon-Abonnenten, Netzgruppe IIb" (Basel, Aargau, central Switzerland and Ticino; printed in German and Italian). The page has two columns; read the left column top to bottom, then the right column.
If the page is NOT a list of subscribers (title page, instructions, tariff tables, advertisements, blank or memo page), output only {"header": "", "end": true, "entries": 0}.

First output one line {"header": "..."} with the running title printed at the very top of the page (e.g. "Meggen-Mellingen" or "M-S Baden"), "" if none.

Places: the directory is ordered by place. A place heading stands on its own line in heavy or larger type, usually followed by the telephone exchange in parentheses and by letter codes, e.g. "Melide (Bissone) ER", "Meisterschwanden (Fahrwangen) E2R-n", "Lugano". All entries below it belong to that place until the next heading. Headings are not entries.
Each subscriber is one entry: the telephone number at the left (e.g. "25", "1.33", "6.13"), then the name in bold type, then in normal type first names, occupation, business and address, separated by commas. An entry may wrap onto two or three indented lines; merge them and undo end-of-line hyphenation ("Vorder-" + "meggen" -> "Vordermeggen").
A line with a number but without bold name (e.g. "2.52 Filiale, Grosse Bäder", "13 Dieselben, Haselstrasse") is its own entry: put its first words in "name".
Lines without a number that are centred or bold sub-headings (e.g. "Sprechstationen, öffentl.:", "Alberghi:") are not entries; skip them.
The sign „ (or ») is a ditto mark for the word above it. Keep every ditto mark exactly where printed, written as »; do not resolve it.

Then output ONE compact JSON object per entry, one per line (JSON Lines), in reading order, nothing else. Fields:
- "place": the place heading in force for this entry, as printed, without the parentheses and codes (e.g. "Melide"). Use "" for entries at the top of the page that come before any heading on THIS page.
- "net": the text in parentheses after that heading (e.g. "Bissone"), "" if none or if "place" is "".
- "phone": the number as printed; "" if the entry has none.
- "name": the bold part as printed, including any » (e.g. "Scherer-Haas", "Restaurant Gotthardt", "» Metropol").
- "rest": the normal-type text after the name, as printed, without the leading comma; "" if none.

Transcribe letter by letter. Do not correct, translate, expand or normalise names, and never invent entries. Write "?" for a digit or letter you cannot read.
After the last entry output {"end": true, "entries": N} with the number of entries."""


def page(vol, run, scale, n):
    out = f"raw/{vol}/{run}/{n:04d}.jsonl"
    if os.path.exists(out):
        return n, "skip"
    img = Image.open(f"img/{vol}/{n:04d}.jpg").convert("RGB")
    if scale != 1:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    resp, dt = call(img, PROMPT, max_tokens=16000)
    ch = resp["choices"][0]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out + ".tmp", "w") as f:
        f.write(ch["message"]["content"].strip() + "\n")
        f.write(json.dumps({"meta": True, "finish": ch.get("finish_reason"), "usage": resp.get("usage"), "s": round(dt)}) + "\n")
    os.replace(out + ".tmp", out)
    return n, f"{ch.get('finish_reason')} {resp.get('usage', {}).get('completion_tokens')} tok {dt:.0f}s"


if __name__ == "__main__":
    vol, run, scale, a, b = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    par = int(sys.argv[6]) if len(sys.argv) > 6 else 3
    pages = [n for n in range(a, b + 1) if os.path.exists(f"img/{vol}/{n:04d}.jpg")]
    if len(sys.argv) > 7:
        keep = {int(x) for x in open(sys.argv[7]).read().split()}
        pages = [n for n in pages if n in keep]
    with ThreadPoolExecutor(par) as ex:
        for n, msg in ex.map(lambda n: page(vol, run, scale, n), pages):
            print(n, msg, flush=True)

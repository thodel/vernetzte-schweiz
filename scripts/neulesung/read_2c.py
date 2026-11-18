"""Band 2c (Tessin) 1911/1912 neu lesen: eine Seite → JSONL. read_2c.py VOL RUN SCALE FIRST LAST [PAR]"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.expanduser("~/Desktop/claude-workspace/ptt-1947-qwen-test/scripts"))
from PIL import Image
from run_qwen import call

PROMPT = """You are transcribing one page of the 1911/1912 Swiss telephone directory for Ticino ("Elenco ufficiale degli abbonati al telefono, Gruppo di reti IIc"), printed in Italian.
If the page is NOT a list of subscribers (title page, instructions, tariff tables, index of localities, blank or memo page), output only {"end": true, "entries": 0}.

Layout of a subscriber page: the name of the telephone network (rete) stands in the top corner and, on the first page of a network, as a large title followed by opening hours. Skip titles, opening hours ("ORARIO"), notes and the line "Abbonati.".
Each subscriber is one entry: the telephone number at the left (e.g. "25", "1.33", "2.07"), then the name in bold type, then after a comma a description in normal type (occupation, business, owner), then dot leaders, then at the right the street or house. An entry may wrap onto two or three lines; merge them and undo end-of-line hyphenation.
A place name in larger bold type followed by a dash "—" at the start of a line (e.g. "Arbedo — 1.33 Tami Fulgenzio, impresario") starts a new locality: this entry and all following ones belong to it until the next such place name.
Centred sub-headings inside a locality (e.g. "Alberghi.", "Amministrazioni ed istituti cantonali.", "Abbonati.") are not entries: give them in "section".
The sign » is a ditto mark for the word above it. Keep every » exactly as printed; do not resolve it.

Output ONE compact JSON object per entry, one per line (JSON Lines), in reading order, nothing else. Fields:
- "place": the bold place name in force for this entry, as printed. Use "" for entries at the top of the page that come before any place name on THIS page.
- "section": the centred sub-heading in force on this page, else "".
- "phone": the number as printed (e.g. "1.33"); "" if the entry has none.
- "name": the bold part as printed, including any leading » (e.g. "» Schweizerhof et Poste", "» Popolare Ticinese").
- "desc": the normal-type text after the name up to the dot leaders, without the leaders; "" if none.
- "street": the text at the right end of the entry, as printed, including any »; "" if none.

Transcribe letter by letter. Do not correct, translate, expand or normalise names, and never invent entries. Write "?" for a digit or letter you cannot read.
After the last entry output {"end": true, "entries": N} with the number of entries."""


def page(vol, run, scale, n):
    out = f"raw/{vol}/{run}/{n:04d}.jsonl"
    if os.path.exists(out):
        return n, "skip"
    img = Image.open(f"img/{vol}/{n:04d}.jpg").convert("RGB")
    if scale != 1:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    resp, dt = call(img, PROMPT, max_tokens=12000)
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
    with ThreadPoolExecutor(par) as ex:
        for n, msg in ex.map(lambda n: page(vol, run, scale, n), range(a, b + 1)):
            print(n, msg, flush=True)

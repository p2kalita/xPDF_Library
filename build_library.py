"""Build library.html: a bookshelf of every PDF under this folder.

Usage: python build_library.py
Renders the first page of each PDF to .library/covers/ (cached) and writes
library.html next to this script. Open library.html in Chrome; clicking a
cover opens the PDF in Chrome's built-in viewer.
"""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent
COVERS = ROOT / ".library" / "covers"
OUTPUT = ROOT / "library.html"
COVER_WIDTH = 320  # px

BAD_TITLES = re.compile(r"untitled|microsoft word|\.docx?$|\.indd$|^\s*$", re.I)


def pretty_name(stem):
    words = re.split(r"[-_\s]+", stem)
    return " ".join(w if w.isupper() else w.capitalize() for w in words if w)


def pick_title(meta_title, stem):
    t = (meta_title or "").strip()
    if 4 <= len(t) <= 150 and not BAD_TITLES.search(t):
        return t
    return pretty_name(stem)


def render_cover(doc, dest):
    page = doc[0]
    zoom = COVER_WIDTH / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(dest, jpg_quality=85)


def scan():
    COVERS.mkdir(parents=True, exist_ok=True)
    books, rendered = [], 0
    pdfs = sorted(
        (p for p in ROOT.rglob("*.pdf") if ".library" not in p.parts),
        key=lambda p: str(p).lower(),
    )
    for pdf in pdfs:
        rel = pdf.relative_to(ROOT)
        cover = COVERS / (hashlib.md5(rel.as_posix().encode()).hexdigest()[:16] + ".jpg")
        book = {
            "title": pretty_name(pdf.stem),
            "category": rel.parts[0] if len(rel.parts) > 1 else "Uncategorized",
            "href": quote(rel.as_posix()),
            "cover": None,
            "pages": None,
            "sizeMB": round(pdf.stat().st_size / 2**20, 1),
        }
        try:
            with fitz.open(pdf) as doc:
                book["pages"] = doc.page_count
                book["title"] = pick_title(doc.metadata.get("title"), pdf.stem)
                if not cover.exists() or cover.stat().st_mtime < pdf.stat().st_mtime:
                    render_cover(doc, cover)
                    rendered += 1
            book["cover"] = cover.relative_to(ROOT).as_posix()
        except Exception as e:
            print(f"  ! could not read {rel}: {e}")
        books.append(book)
        print(f"  {'+' if book['cover'] else '-'} {rel}")
    return books, rendered


def main():
    books, rendered = scan()
    data = json.dumps(books, ensure_ascii=False).replace("</", "<\\/")
    OUTPUT.write_text(TEMPLATE.replace("__BOOKS__", data), encoding="utf-8")
    print(f"\n{len(books)} books ({rendered} covers rendered) -> {OUTPUT.name}")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>My Library</title>
<style>
  :root {
    --bg: #f4f1ea; --fg: #2b2620; --muted: #7a7064; --card: #fffdf8;
    --chip: #e7e1d5; --chip-on: #2b2620; --chip-on-fg: #f4f1ea; --shadow: rgba(60,40,20,.25);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #1a1916; --fg: #ece6da; --muted: #9a9284; --card: #26241f;
      --chip: #33302a; --chip-on: #ece6da; --chip-on-fg: #1a1916; --shadow: rgba(0,0,0,.6);
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--fg);
         font: 15px/1.4 system-ui, -apple-system, "Segoe UI", sans-serif; }
  header { position: sticky; top: 0; z-index: 1; background: var(--bg);
           padding: 20px 24px 12px; border-bottom: 1px solid var(--chip); }
  h1 { margin: 0 0 12px; font: 600 26px/1.2 Georgia, serif; }
  h1 small { font: 14px system-ui, sans-serif; color: var(--muted); margin-left: 8px; }
  #search { width: 100%; max-width: 420px; padding: 9px 14px; font: inherit;
            border: 1px solid var(--chip); border-radius: 8px; background: var(--card); color: var(--fg); }
  #chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
  .chip { border: 0; padding: 5px 12px; border-radius: 99px; background: var(--chip);
          color: var(--fg); font: inherit; font-size: 13px; cursor: pointer; }
  .chip.on { background: var(--chip-on); color: var(--chip-on-fg); }
  main { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
         gap: 32px 24px; padding: 28px 24px 60px; }
  .book { text-decoration: none; color: inherit; display: flex; flex-direction: column; }
  .cover { aspect-ratio: 2 / 3; border-radius: 2px 6px 6px 2px; overflow: hidden;
           background: var(--card); box-shadow: 4px 6px 14px var(--shadow), inset 4px 0 6px rgba(0,0,0,.15);
           transition: transform .18s, box-shadow .18s; position: relative; }
  .cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .cover .ph { padding: 16px; height: 100%; display: flex; align-items: center; text-align: center;
               font: 600 15px/1.3 Georgia, serif; }
  .book:hover .cover, .book:focus-visible .cover { transform: translateY(-6px) rotate(-1deg);
           box-shadow: 8px 14px 24px var(--shadow); }
  .title { margin-top: 10px; font-weight: 600; font-size: 14px; display: -webkit-box;
           -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .meta { color: var(--muted); font-size: 12px; margin-top: 2px; }
  #empty { grid-column: 1 / -1; text-align: center; color: var(--muted); padding: 40px; }
  @media (max-width: 520px) {
    header { padding: 16px 16px 10px; }
    main { padding: 20px 16px 40px; grid-template-columns: repeat(2, 1fr); gap: 24px 16px; }
  }
</style>
</head>
<body>
<header>
  <h1>My Library <small id="count"></small></h1>
  <input id="search" type="search" placeholder="Search books…" autofocus>
  <div id="chips"></div>
</header>
<main id="shelf"></main>
<script>
const BOOKS = __BOOKS__;
let cat = "All", q = "";
const shelf = document.getElementById("shelf");
const esc = s => s.replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

const cats = ["All", ...[...new Set(BOOKS.map(b => b.category))].sort((a, b) => a.localeCompare(b))];
document.getElementById("chips").innerHTML = cats.map(c =>
  `<button class="chip${c === cat ? " on" : ""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("");
document.getElementById("chips").onclick = e => {
  const b = e.target.closest(".chip"); if (!b) return;
  cat = b.dataset.cat;
  document.querySelectorAll(".chip").forEach(x => x.classList.toggle("on", x === b));
  render();
};
document.getElementById("search").oninput = e => { q = e.target.value.trim().toLowerCase(); render(); };

function render() {
  const list = BOOKS.filter(b => (cat === "All" || b.category === cat) &&
    (!q || (b.title + " " + b.category).toLowerCase().includes(q)));
  document.getElementById("count").textContent = `${list.length} of ${BOOKS.length} books`;
  shelf.innerHTML = list.length ? list.map(b => `
    <a class="book" href="${b.href}" target="_blank" title="${esc(b.title)}">
      <div class="cover">${b.cover
        ? `<img src="${encodeURI(b.cover)}" alt="" loading="lazy">`
        : `<div class="ph">${esc(b.title)}</div>`}</div>
      <div class="title">${esc(b.title)}</div>
      <div class="meta">${esc(b.category)}${b.pages ? ` · ${b.pages} pages` : ""} · ${b.sizeMB} MB</div>
    </a>`).join("") : `<div id="empty">No books match.</div>`;
}
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()

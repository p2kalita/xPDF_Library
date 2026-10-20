# My Library

A local bookshelf for your PDF collection. It scans this folder for PDFs, shows the front page of each one as a cover, and opens the book in Chrome's built-in PDF viewer when you click it.

![Library preview](preview.png)

## Features

- Shows the first page of every PDF as a cover, including PDFs in subfolders
- Filter buttons, one per subfolder
- Search by title
- Each book shows its folder, page count and file size
- Light and dark themes that follow your system setting
- Covers are cached, so rebuilding after adding books is quick
- No server needed: it's a single static HTML page

## Requirements

- Python 3.9+
- Google Chrome (or any browser with a built-in PDF viewer)

```
pip install -r requirements.txt
```

## Usage

**Easiest:** double-click **`Open Library.bat`**. It rebuilds the library and opens it in Chrome.

**Manually:**

```
python build_library.py
```

Then open `library.html` in Chrome. Click any cover to open that book in a new tab.

When you add, remove or move PDFs, run the build again (or double-click the `.bat`) to update the shelf.

## How it works

`build_library.py` does the following:

1. Finds every `*.pdf` under this folder.
2. Uses PyMuPDF to render page 1 of each PDF to a JPEG in `.library/covers/`. A cover is only rendered again when its PDF is newer than the cover.
3. Picks a title from the PDF's own metadata. If that's missing or looks like junk (e.g. "Untitled"), it uses the file name instead.
4. Uses the top-level subfolder as the category. PDFs in the root folder go under "Uncategorized".
5. Writes `library.html` with all the book data embedded, so the page works offline over `file://`.

## Files

| File | Purpose |
| --- | --- |
| `build_library.py` | Scans the PDFs, renders covers and generates the page |
| `library.html` | The bookshelf page (generated, don't edit by hand) |
| `Open Library.bat` | Rebuilds the library and opens it in Chrome |
| `requirements.txt` | Python dependencies |
| `.library/covers/` | Cached cover images (safe to delete; they'll be regenerated) |

## Notes

- Only PDFs are included. EPUBs and videos are skipped because Chrome can't open them on its own.
- If the folder is synced with OneDrive, files stored online only are downloaded the first time their cover is rendered.
- Cover width is set by `COVER_WIDTH` in `build_library.py`. To regenerate every cover, delete `.library/covers/` and rebuild.

# PAKU

A modern, offline manga and PDF reader with a beautiful, responsive interface and advanced library management features.

## Project Structure

- `main.py`: Application entry point.
- `ui/`: GUI layout files (Qt Designer).
- `assets/`: Images, icons, flags, banners, and fonts.
- `styles/`: Custom style definitions (all QSS lives here).
- `requirements.txt`: Python dependencies.

## Features

### Library

- **Bookshelf**: Add folders, rename them with an alias, set a custom cover, batch-select and remove entries.
- **Search, sort & filter**: Live search bar, A-Z / Z-A sorting, and filter options.
- **Per-item language**: Pick a language from the ⋯ menu (French, English, Arabic, Spanish, German, Japanese). The matching flag is drawn in the bottom-right corner of the cover. Works both on collections and on individual files, and survives a restart.
- **Manga info**: Synopsis, tags and banner pulled from AniList and MangaDex.
  - The lookup uses the **alias** when you set one, so renaming a badly-named folder fixes its metadata.
  - The synopsis is shown **in the language you picked**, falling back to English when no translation exists. Translations already fetched are kept, so switching back and forth costs nothing.
- **Covers**: Auto-generated for PDF, CBZ, ZIP, RAR/CBR, and image folders — including folders that only contain chapter sub-folders, where the first page of the first chapter becomes the cover.
- **High-resolution thumbnails**: Cached at 3× the display size and rendered at the screen's exact physical pixels, so covers stay sharp at 100 %, 125 %, 150 % and 200 % Windows scaling.

### Reader

- **Multi-format**: PDF, CBZ, ZIP, RAR, and plain image folders.
- **Mouse wheel to zoom**, anchored on the cursor — the point under the pointer stays put.
- **Left-click and drag to pan** when the page is larger than the window.
- **Auto-fit**: Each page fits the window until you zoom manually; after that your zoom level is kept across pages.

### Interface

- Unified header bar across the library, folder and chapter pages: a translucent action pill, a single accent-coloured primary action, and a scrim that keeps the artwork readable behind the title.
- Frameless progress card matching the app theme, with elided file names.
- Responsive grid that adapts to the window width.
- Donation buttons: BuyMeACoffee and Paypal, from the home page.

### Keyboard Shortcuts (reader)

| Key | Action |
|---|---|
| `←` `↑` `Page Up` | Previous page |
| `→` `↓` `Page Down` | Next page |
| `Home` / `End` | First / last page |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `Esc` | Back |

## Dependencies

- **PySide6**: Qt GUI
- **PyMuPDF**: PDF reading and rendering
- **rarfile**: RAR archive support
- **requests**: AniList / MangaDex API integration

```bash
pip install -r requirements.txt
python main.py
```

## Troubleshooting

Debug traces are silent by default — they used to cost a hundred console writes on startup and thousands on a large folder. To turn them back on:

```powershell
$env:PAKU_DEBUG=1 ; python main.py
```

### Local data files

The application writes small hidden files next to your manga:

| File | Contents |
|---|---|
| `.thumbnails/` | Generated covers plus `.cache.json`, which records the render version so covers you set yourself are never overwritten |
| `.alias.json` | Per-file display names |
| `.languages.json` | Per-file language choice |
| `.anilist.json` | Synopsis (one entry per language), tags and banner |

`library.json`, at the root of the project, holds the list of folders in your bookshelf.

### Flags

The six flags in `assets/icons/flags/` are plain SVG files and can be swapped without touching any code. The Arabic one is a simplified Saudi flag — field and sword, without the shahada, which would be illegible at 21 px.

## Future Development

- Fullscreen mode
- Page rotation
- Text extraction
- Recent files history
- Customizable themes
- Virtualised grid for very large folders

## Releases

You can download the latest Windows executable from the [Releases](https://github.com/ezakariaa/PAKU/releases) page on GitHub.

### How to use the release

1. Go to the Releases page and download `Paku.exe`.
2. Double-click it to launch the application. No installation required.
3. All features and assets are included in the executable.

**Note:** If Windows SmartScreen warns you, click "More info" then "Run anyway". This is normal for a new unsigned application.

---

**If you enjoy this project, please consider supporting via BuyMeACoffee or Paypal (links in the app)!**

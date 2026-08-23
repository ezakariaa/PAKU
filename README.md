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

### Themes

- **Light and dark**, toggled by the moon / sun button next to the gear on the home page — one click in, one click out. The same choice sits in Settings → General → Theme, and it is remembered between sessions.
- Colours live as tokens (`@surface`, `@text`, `@border`…) in `styles/styles.py` and are resolved for the active theme, so a new palette is a table entry, not a hunt through the code.
- Switching rebuilds the pages and puts you back where you were — same page of the same file, same zoom.
- Icons ship in a light and a dark variant and follow the theme; the icons that sit on a banner's dark scrim stay white in both.

### Settings

A gear button sits next to **BOOKSHELF** on the home page and opens a separate
settings window. Every change is written to `settings.json` immediately — there
is no Apply button — and takes effect at once, except where noted.

| Tab | Setting | Effect |
|---|---|---|
| General | Theme | Light or dark, same as the moon button on the home page |
| General | Opening page | Land on Home or straight in the Bookshelf |
| General | Start fullscreen | Applied on the next launch |
| Library | Thumbnail size | Small (150 px), Medium (200 px) or Large (260 px) covers; the grid reflows immediately |
| Library | Default sort | Order applied to the bookshelf when it opens |
| Library | Hide extensions | Shows `Chapter 12` instead of `Chapter 12.cbz`; items you renamed keep their alias |
| Library | Generate thumbnails on add | Off, covers are built as they are displayed and adding a folder is instant |
| Library | Fetch online info | Off, adding a folder contacts no server at all |
| Reader | Wheel zoom step | 5 % to 50 % per notch |
| Reader | Invert wheel | Wheel up zooms out |
| Reader | Keep zoom | Off, every page starts fitted to the window again |
| Advanced | Thumbnail cache | Deletes every `.thumbnails` folder of the library, after confirmation |
| Advanced | Configuration files | Opens the folder holding `library.json` and `settings.json` |
| Advanced | Debug traces | Same traces as `PAKU_DEBUG`, without restarting the app |

**Reset settings** at the bottom left puts every option back to its original
value, which is also the behaviour of a fresh install: as long as no setting is
touched, PAKU behaves exactly as before.

### Reader

- **Multi-format**: PDF, CBZ, ZIP, RAR, and plain image folders.
- **Mouse wheel to zoom**, anchored on the cursor — the point under the pointer stays put.
- **Left-click and drag to pan** when the page is larger than the window.
- **Auto-fit**: Each page fits the window until you zoom manually; after that your zoom level is kept across pages.
- **Reader bar**: back on the left, page navigation in the middle, zoom on the right — icon buttons whose tooltips carry the keyboard shortcut. The current page is bold, the total stays muted, and the chevrons dim at the first and last page.
- **Zoom indicator**: the percentage between the two zoom buttons is itself a button — click it to fit the page back to the window after zooming by hand.

### Interface

- Unified header bar across the library, folder and chapter pages: a translucent action pill, a single accent-coloured primary action, and a scrim that keeps the artwork readable behind the title.
- The reader repeats that grammar on a light ground: a detached round back button, actions gathered in pills, and a page area framed as a card with slim rounded scrollbars.
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

`settings.json`, next to `library.json`, holds the options of the settings
window. Deleting it restores every default.

`library.json`, at the root of the project, holds the list of folders in your bookshelf.

### Flags

The six flags in `assets/icons/flags/` are plain SVG files and can be swapped without touching any code. The Arabic one is a simplified Saudi flag — field and sword, without the shahada, which would be illegible at 21 px.

## Future Development

- Fullscreen toggle from the reader
- Page rotation
- Text extraction
- Recent files history
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

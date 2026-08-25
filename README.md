# PAKU

A modern, offline manga and PDF reader with a beautiful, responsive interface and advanced library management features.

## Project Structure

- `main.py`: Application entry point.
- `ui/`: GUI layout files (Qt Designer).
- `assets/`: Images, icons, flags, banners, and fonts.
- `styles/`: Custom style definitions (all QSS lives here).
- `i18n.py`: Display language — the French → English string table.
- `requirements.txt`: Python dependencies.

## Features

### Library

- **Bookshelf**: Add folders, rename them with an alias, set a custom cover, batch-select and remove entries.
- **Status**: The ⋯ menu can mark a collection *Ongoing* or *Finished*. The status shows as a coloured pill on the cover, right above the chapter count — blue while it goes on, green once it's done. Pick *None* to clear it. Works on items inside a folder too.
- **Subtitle**: The ⋯ menu can add a small second line under a cover's title — an edition, an author, a reading order. Smaller and muted so it stays a note rather than a second title; leave the field empty to remove it. Works on collections and on items inside a folder, and survives a restart.
- **Search, sort & filter**: Live search bar, A-Z / Z-A sorting, and filter options.
- **Per-item language**: Pick a language from the ⋯ menu (French, English, Arabic, Spanish, German, Japanese). The matching flag is drawn in the bottom-right corner of the cover. Works both on collections and on individual files, and survives a restart.
- **Manga info**: Synopsis, tags and banner pulled from AniList and MangaDex.
  - The lookup uses the **alias** when you set one, so renaming a badly-named folder fixes its metadata.
  - **Hiding the synopsis**: the eye button in a folder's banner hides the summary and tags for that folder alone, and remembers it in a `.paku.json` next to it. Settings → Bookshelf → Hide every synopsis does the same for every folder at once; the banner button then steps aside and says so.
  - Synopsis and tags live in their own scrolling column: a long summary followed by twenty tags stays reachable instead of running off the bottom of the window. With neither, the column steps aside and the grid takes the width.
  - The synopsis is shown **in the language you picked**, falling back to English when no translation exists. Translations already fetched are kept, so switching back and forth costs nothing.
- **Covers**: Auto-generated for PDF, CBZ, ZIP, RAR/CBR, and image folders — including folders that only contain chapter sub-folders, where the first page of the first chapter becomes the cover.
- **Cover shadows**: Each cover casts a soft drop shadow, so the grid reads as a shelf rather than a sheet of stickers. The shadow follows the theme — light and diffuse on the light ground, deeper on the dark one.
- **Chapter count**: A collection shows how many items it holds in the bottom-left corner of its cover, facing the language flag. Sub-folders carry one too; single files don't, and an empty collection stays bare. The count is cached on the folder's timestamp, so typing in the search bar doesn't re-scan the library.
- **High-resolution thumbnails**: Cached at 3× the display size and rendered at the screen's exact physical pixels, so covers stay sharp at 100 %, 125 %, 150 % and 200 % Windows scaling.

### Display language

- **French and English**, switched in Settings → General → Display language, and remembered between sessions.
- The code is written in French and `i18n.py` holds the French → English table, so a string with no translation falls back to French rather than to a technical key: an omission shows up, but nothing breaks.
- Switching rebuilds the pages and puts you back where you were, exactly like the theme.
- This is the language of the *interface* only. Synopses keep following the language you picked for each collection.

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
| General | Display language | French or English for the whole interface |
| General | Opening page | Land on Home or straight in the Bookshelf |
| General | Start fullscreen | Applied on the next launch |
| Library | Thumbnail size | Small (150 px), Medium (200 px) or Large (260 px) covers; the grid reflows immediately |
| Library | Default sort | Order applied to the bookshelf when it opens |
| Library | Hide every synopsis | Removes the summary and tags from every folder view |
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
- A folder's banner carries its name large and bold; a name too long for the window is cut short rather than pushing the action buttons off screen, and the full text stays in the tooltip.
- The reader repeats that grammar on a light ground: a detached round back button, actions gathered in pills, and a page area framed as a card with slim rounded scrollbars.
- Frameless progress card matching the app theme, with elided file names.
- Responsive grid that adapts to the window width.
- The ⋯ menu of a cover is a themed card: rounded, icon per entry, grouped by separators, and in one language throughout.
- Renaming and subtitling use the app's own input card rather than a system dialog — Enter validates, Escape cancels.
- One scrollbar design everywhere — slim, rounded, no end arrows — in both themes.
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

## Startup

- **Splash**: the PAKU logo shows on a themed card while the window is being built, then steps aside.
- **Lazy imports**: PyMuPDF, `requests` and `rarfile` are loaded on first use — opening a PDF, the first network call, the first RAR — instead of at launch. They were the bulk of the startup wait and none of them is needed to draw the window. `if TYPE_CHECKING: import …` keeps them visible to PyInstaller's analysis, so the packaged build still bundles them. `PySide6.QtSvg` follows the same rule: it is only needed to draw a language flag.
- Measured on this machine: **8.5 s → ~0.6 s** to a usable window, first launch after boot included.
- If you package with PyInstaller, add `--splash assets/images/logo.png`: the delay *before* Python starts (the exe unpacking itself) is out of the app's reach, and only PyInstaller's own splash covers it.

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
| `.subtitles.json` | Per-file subtitle |
| `.status.json` | Per-file reading status |
| `.paku.json` | Display preferences of the folder itself, such as a hidden synopsis |
| `.anilist.json` | Synopsis (one entry per language), tags and banner |

`settings.json`, next to `library.json`, holds the options of the settings
window. Deleting it restores every default.

`library.json`, at the root of the project, holds the list of folders in your bookshelf. A folder that cannot be reached — an external drive asleep or unplugged — is simply left out of the grid; it is **never** removed from the file. Only *Remove from the bookshelf* deletes an entry.

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

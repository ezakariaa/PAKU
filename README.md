# MangaPDFReader

A modern, offline manga and PDF reader with a beautiful, responsive interface and advanced library management features.

## Project Structure

- `main.py`: Application entry point.
- `ui/`: GUI layout files (Qt Designer).
- `assets/`: Images, icons, banners, and fonts.
- `styles/`: Custom style definitions.
- `requirements.txt`: Python dependencies.

## Features

### ✅ Main Features
- **Modern Home Page**: Stylish, manga-inspired welcome screen.
- **Library Management**: Add folders, set aliases, custom covers, and remove items from your bookshelf.
- **AniList Integration**: Automatic retrieval of manga info, banners, tags, and genres from AniList when adding a new folder.
- **Thumbnails**: Auto-generated covers for folders and files (PDF, CBZ, ZIP, RAR, images), with fallback and custom cover support.
- **Multi-format Support**: Read PDF, CBZ, ZIP, RAR, and image folders seamlessly.
- **Multiple Selection & Batch Delete**: Select multiple items and delete them in one click.
- **Search, Sort & Filter**: Powerful search bar, A-Z/Z-A sorting, and filter options for your library.
- **Contextual Menus**: Right-click (⋯) menu for alias, original cover, open in explorer, and remove actions.
- **Customizable Header**: Change the banner/header image for each folder.
- **Keyboard Shortcuts**: Fast navigation and zoom controls.
- **Responsive Design**: Adapts to all window sizes, with a modern look and feel.
- **Donation Buttons**: BuyMeACoffee and Paypal support directly from the home page.

### 🎮 Keyboard Shortcuts
- **Left/Right arrows**: Navigate between pages
- **Home/End**: Go to first/last page
- **Ctrl +**: Zoom in
- **Ctrl -**: Zoom out
- **Ctrl 0**: Reset zoom

## Dependencies

- **PySide6**: Qt GUI
- **PyMuPDF**: PDF reading and rendering
- **rarfile**: RAR archive support
- **requests**: AniList API integration

## Future Development

- 🔄 Fullscreen mode
- 🔄 Page rotation
- 🔄 Text extraction
- 🔄 Recent files history
- 🔄 Customizable themes
- 🔄 More advanced filters and tags
- 🔄 Enhanced CBZ/CBR support

## Releases

You can download the latest Windows executable from the [Releases](https://github.com/your-username/your-repo/releases) page on GitHub.

### How to use the release
1. Go to the Releases page and download the file `main.exe` (for example, from tag `v1.0.0`).
2. Double-click `main.exe` to launch the application. No installation required.
3. All features and assets are included in the executable.

**Note:** If you encounter a warning from Windows SmartScreen, click on "More info" and then "Run anyway". This is normal for new unsigned applications.

---

**If you enjoy this project, please consider supporting via BuyMeACoffee or Paypal (links in the app)!** 
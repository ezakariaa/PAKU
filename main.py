import sys
import os
import json
import functools
import zipfile
import pymupdf as fitz  # l'alias historique `fitz` est déprécié depuis PyMuPDF 1.26
import rarfile
import requests

# === AJOUT : Fonction utilitaire pour les chemins d'assets compatible PyInstaller ===
# Traces de mise au point : muettes par défaut. Elles représentent une centaine
# d'écritures console au démarrage, et plusieurs milliers sur un gros dossier.
DEBUG = os.environ.get("PAKU_DEBUG", "").strip().lower() in ("1", "true", "yes", "on")


def debug(message):
    # La variable d'environnement force les traces ; le réglage « Traces de
    # débogage » permet de les allumer sans relancer l'application.
    if DEBUG or settings.get("debug_traces"):
        print(message)


def themed_icon(name):
    """Chemin d'une icône dans la teinte du thème courant.

    Les icônes posées sur un bandeau à voile sombre gardent leur variante
    blanche en dur : ce sont les seules dont le fond ne change pas.
    """
    suffix = "-white" if current_theme() == "dark" else ""
    return resource_path(f"assets/icons/{name}{suffix}.svg")


def resource_path(relative_path):
    """Retourne le chemin absolu vers un fichier ressource, compatible PyInstaller et dev."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QPushButton, QLabel, QStackedWidget, QGridLayout, QScrollArea,
    QFileDialog, QMenu, QInputDialog, QDialog, QProgressBar, QMessageBox,
    QGraphicsDropShadowEffect, QLineEdit
)
from PySide6.QtGui import (
    QFont, QFontMetrics, QPixmap, QIcon, QImage, QImageReader, QFontDatabase,
    QPainter, QColor,
    QDesktopServices, QBrush, QPen, QPainterPath, QLinearGradient, QPalette,
    QActionGroup
)
from PySide6.QtCore import (Qt, Signal, QSize, QTimer, QUrl, QRect, QRectF, QPoint, QPointF,
                            QPropertyAnimation, QEasingCurve)  # imports nettoyés
from PySide6.QtSvg import QSvgRenderer

# Importer les styles
from styles.styles import (
    S, set_theme, current_theme, theme_color, ACCENT,
    HOME_SUPPORT_HEIGHT,
    READER_BAR_HEIGHT, READER_BTN_SIZE, READER_GROUP_HEIGHT,
)

from ui.flowlayout import FlowLayout
# Réglages système : lus partout, écrits par la fenêtre de paramètres.
from app_settings import settings
from ui.settings_window import SettingsWindow

LIBRARY_FILE = "library.json"
GENERATE_THUMBNAILS = True
VERSION = "1.0.0"
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
ARCHIVE_EXTENSIONS = ('.pdf', '.cbz', '.zip', '.rar', '.cbr')

os.environ["QT_STYLE_OVERRIDE"] = ""

# =====================================================================================
# PIPELINE DE VIGNETTES HAUTE QUALITÉ
# =====================================================================================
# Taille logique d'une pochette dans la grille. C'est la valeur de référence du
# cache ; l'affichage, lui, suit le réglage « Taille des vignettes ».
THUMB_DISPLAY_SIZE = (200, 280)


def thumb_display_size():
    """Taille d'affichage courante d'une pochette, réglage compris."""
    return settings.thumbnail_pixel_size()


# Épaisseur et rayon intérieur de la bordure : doivent rester synchronisés avec
# THUMBNAIL_IMAGE_STYLE dans styles/styles.py (border: 4px, border-radius: 14px).
THUMB_BORDER_WIDTH = 4
THUMB_CORNER_RADIUS = 14 - THUMB_BORDER_WIDTH
# --- Boîte de progression ---
PROGRESS_CARD_WIDTH = 560
PROGRESS_CARD_MARGIN = 14      # place laissée à l'ombre portée

HOME_BUTTON_WIDTH = 190       # entrées principales de la page d'accueil
HOME_BUTTON_HEIGHT = 54
# --- Langues ---
# Drapeau conventionnel de chaque langue. Les SVG vivent dans
# assets/icons/flags/ et se remplacent sans toucher au code.
LANGUAGES = (
    ("fr", "Français"),
    ("en", "Anglais"),
    ("ar", "Arabe"),
    ("es", "Espagnol"),
    ("de", "Allemand"),
    ("ja", "Japonais"),
)
LANGUAGE_LABELS = dict(LANGUAGES)
LANGUAGE_FILE = ".languages.json"
THUMB_FLAG_HEIGHT = 21

THUMB_MENU_SIZE = 28          # pastille ⋯ dans le coin de la pochette
# Marge laissée autour d'une pochette pour que son ombre portée ait la place de
# s'étaler : gauche, haut, droite, bas. L'ombre descend, d'où le bas plus large.
THUMB_SHADOW_MARGINS = (12, 6, 18, 22)
# L'espacement de la grille vient en plus de ces marges.
GRID_SPACING = 8
# Les vignettes sont mises en cache à 3x la taille d'affichage : de quoi rester nettes
# jusqu'à une mise à l'échelle Windows de 300 %.
THUMB_CACHE_SIZE = (THUMB_DISPLAY_SIZE[0] * 3, THUMB_DISPLAY_SIZE[1] * 3)
# Ancien standard de cache : en dessous, une vignette date du rendu basse résolution.
LEGACY_THUMB_SIZE = (THUMB_DISPLAY_SIZE[0] * 2, THUMB_DISPLAY_SIZE[1] * 2)
# À incrémenter dès que le rendu change, pour réinvalider les vignettes en cache.
THUMB_CACHE_VERSION = "2"

# --- Barre d'en-tête de la bibliothèque ---
HEADER_HEIGHT = 84
HEADER_RADIUS = 14
HEADER_TOOLBAR_HEIGHT = 42
HEADER_BTN_SIZE = 34
HEADER_SEARCH_WIDTH = 210
# Voile appliqué sur les bannières : c'est lui qui rend lisibles le titre et les
# icônes blancs, quelle que soit la clarté de l'image de fond.
HEADER_SCRIM = ((17, 20, 27, 214), (17, 20, 27, 168))

# --- Lecteur ---
VIEWER_ZOOM_MIN = 0.2
VIEWER_ZOOM_MAX = 5.0
# Le pas d'un cran de molette est reglable : voir app_settings.wheel_zoom_factor().


def smooth_resize(image, target_w, target_h, expanding=False):
    """Redimensionne en réduisant par moitiés successives.

    Un scaling bilinéaire en une passe sous-échantillonne les fortes réductions
    (moiré sur les trames de manga) ; le demi-pas moyenne tous les pixels source.
    """
    if image.isNull() or image.width() <= 0 or image.height() <= 0:
        return image
    pick = max if expanding else min
    scale = pick(target_w / image.width(), target_h / image.height())
    while scale < 0.5:
        image = image.scaled(max(1, image.width() // 2), max(1, image.height() // 2),
                             Qt.AspectRatioMode.IgnoreAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
        scale *= 2
    mode = (Qt.AspectRatioMode.KeepAspectRatioByExpanding if expanding
            else Qt.AspectRatioMode.KeepAspectRatio)
    return image.scaled(target_w, target_h, mode, Qt.TransformationMode.SmoothTransformation)


def fit_cover(image, target_w, target_h):
    """Remplit exactement target_w x target_h, en recadrant au centre."""
    scaled = smooth_resize(image, target_w, target_h, expanding=True)
    x = max(0, (scaled.width() - target_w) // 2)
    y = max(0, (scaled.height() - target_h) // 2)
    return scaled.copy(x, y, min(target_w, scaled.width()), min(target_h, scaled.height()))


def render_pdf_cover(pdf_path):
    """Rend la première page d'un PDF à la résolution du cache de vignettes."""
    doc = fitz.open(pdf_path)
    try:
        if doc.page_count == 0:
            return QImage()
        page = doc[0]
        rect = page.rect
        if rect.width <= 0 or rect.height <= 0:
            return QImage()
        # Zoom relatif aux 72 dpi de PyMuPDF, borné pour ne pas exploser la mémoire.
        zoom = min(8.0, max(1.0, max(THUMB_CACHE_SIZE[0] / rect.width,
                                     THUMB_CACHE_SIZE[1] / rect.height)))
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        # copy() : le tampon de pix est libéré en même temps que le document.
        return QImage(pix.samples, pix.width, pix.height, pix.stride,
                      QImage.Format.Format_RGB888).copy()
    finally:
        doc.close()


def first_archive_image(archive):
    """Décode la première image d'une archive zip/rar déjà ouverte."""
    pages = sorted(n for n in archive.namelist() if n.lower().endswith(IMAGE_EXTENSIONS))
    return QImage.fromData(archive.read(pages[0])) if pages else QImage()


def extract_cover_image(source_path):
    """Couverture d'un PDF, d'une archive (cbz/zip/rar/cbr) ou d'une image."""
    low = source_path.lower()
    if low.endswith('.pdf'):
        return render_pdf_cover(source_path)
    if low.endswith(('.cbz', '.zip')):
        with zipfile.ZipFile(source_path, 'r') as archive:
            return first_archive_image(archive)
    if low.endswith(('.rar', '.cbr')):
        with rarfile.RarFile(source_path, 'r') as archive:
            return first_archive_image(archive)
    if low.endswith(IMAGE_EXTENSIONS):
        return QImage(source_path)
    return QImage()


def save_cover_thumbnail(image, thumb_path):
    """Écrit une couverture dans le cache sans jamais l'agrandir. True si écrite."""
    if image.isNull():
        return False
    if image.width() > THUMB_CACHE_SIZE[0] or image.height() > THUMB_CACHE_SIZE[1]:
        image = smooth_resize(image, *THUMB_CACHE_SIZE)
    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
    return image.save(thumb_path, "PNG")


def write_cover_thumbnail(source_path, thumb_path):
    """Génère la vignette haute qualité de source_path. True si écrite."""
    try:
        return save_cover_thumbnail(extract_cover_image(source_path), thumb_path)
    except Exception as e:
        print(f"Erreur vignette {source_path}: {e}")
        return False


def folder_cover_source(folder_path, depth=1):
    """Fichier dont dériver la pochette d'un dossier.

    Une archive d'abord, sinon une image à la racine, sinon la première image
    d'un sous-dossier : un manga rangé en dossiers de chapitres n'a rien
    d'exploitable à sa racine.
    """
    try:
        entries = sorted(os.listdir(folder_path))
    except OSError:
        return None
    for extensions in (ARCHIVE_EXTENSIONS, IMAGE_EXTENSIONS):
        matches = [f for f in entries if f.lower().endswith(extensions)]
        if matches:
            return os.path.join(folder_path, matches[0])
    if depth > 0:
        for name in entries:
            if name.startswith('.'):
                continue
            sub_folder = os.path.join(folder_path, name)
            if os.path.isdir(sub_folder):
                source = folder_cover_source(sub_folder, depth - 1)
                if source:
                    return source
    return None


def ensure_folder_thumbnail(folder_path):
    """Pochette d'un dossier, fabriquée à la demande si elle manque encore."""
    existing = get_thumbnail_path(None, folder_path=folder_path)
    if existing:
        return existing
    source = folder_cover_source(folder_path)
    if not source:
        return None
    cover_path = os.path.join(folder_path, '.thumbnails', '_folder_thumb.png')
    if write_cover_thumbnail(source, cover_path):
        record_generated_cover(cover_path)
        return cover_path
    return None


def load_language_map(folder):
    """Langue choisie pour chaque élément d'un dossier."""
    try:
        with open(os.path.join(folder, LANGUAGE_FILE), 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_item_language(item_path, code):
    """Écrit la langue d'un élément dans le .languages.json de son dossier parent.

    Même convention que le .alias.json déjà utilisé pour les renommages.
    """
    folder = os.path.dirname(item_path)
    languages = load_language_map(folder)
    name = os.path.basename(item_path)
    if code:
        languages[name] = code
    else:
        languages.pop(name, None)
    try:
        with open(os.path.join(folder, LANGUAGE_FILE), 'w', encoding='utf-8') as f:
            json.dump(languages, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Erreur lors de l'enregistrement de la langue : {e}")


def load_thumb_cache_index(thumb_dir):
    """Version du rendu ayant produit chaque vignette auto-générée du dossier.

    Une couverture posée par l'utilisateur ou téléchargée n'y figure pas : elle ne
    sera donc jamais réécrite par la génération automatique.
    """
    try:
        with open(os.path.join(thumb_dir, '.cache.json'), 'r', encoding='utf-8') as f:
            index = json.load(f)
        return index if isinstance(index, dict) else {}
    except (OSError, ValueError):
        return {}


def save_thumb_cache_index(thumb_dir, index):
    try:
        with open(os.path.join(thumb_dir, '.cache.json'), 'w', encoding='utf-8') as f:
            json.dump(index, f)
    except OSError as e:
        print(f"Impossible d'écrire l'index des vignettes : {e}")


def mark_cover_as_custom(cover_path):
    """Sort une couverture de l'index : posée à la main ou téléchargée, la
    génération automatique ne doit plus jamais l'écraser."""
    thumb_dir = os.path.dirname(cover_path)
    index = load_thumb_cache_index(thumb_dir)
    if index.pop(os.path.basename(cover_path), None) is not None:
        save_thumb_cache_index(thumb_dir, index)


def record_generated_cover(cover_path):
    """Inscrit une couverture auto-générée dans l'index du dossier."""
    thumb_dir = os.path.dirname(cover_path)
    index = load_thumb_cache_index(thumb_dir)
    index[os.path.basename(cover_path)] = THUMB_CACHE_VERSION
    save_thumb_cache_index(thumb_dir, index)


def thumbnail_needs_render(thumb_path, source_path, index):
    """Vignette absente, périmée, ou issue d'une version antérieure du rendu."""
    if not os.path.exists(thumb_path):
        return True
    name = os.path.basename(thumb_path)
    if name in index:
        if index[name] != THUMB_CACHE_VERSION:
            return True
    else:
        # Vignette antérieure à l'index : on ne la refait que si sa définition est
        # sous l'ancien standard 400x560 (typiquement les PDF rendus à 14 dpi).
        size = QImageReader(thumb_path).size()
        if not size.isValid():
            return True
        if size.width() < LEGACY_THUMB_SIZE[0] or size.height() < LEGACY_THUMB_SIZE[1]:
            return True
    try:
        return os.path.getmtime(thumb_path) < os.path.getmtime(source_path)
    except OSError:
        return True

# =====================================================================================
# LABEL AVEC COINS ARRONDIS
# =====================================================================================
class RoundedLabel(QLabel):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 10
        self.deferred_load = None

    def paintEvent(self, event):
        """Charge la pochette au premier rendu réel.

        Qt ne peint que ce qui est dans la fenêtre : sur un dossier de 700
        volumes, seule la dizaine visible paie le décodage du PNG, au lieu des
        700 au moment de bâtir la grille.
        """
        if self.deferred_load is not None:
            load, self.deferred_load = self.deferred_load, None
            # Hors du cycle de peinture (setPixmap redemande un rendu), et lié à
            # ce label : une grille reconstruite détruit ses vignettes, le rappel
            # doit mourir avec elles plutôt que toucher un objet libéré.
            QTimer.singleShot(0, self, load)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

# =====================================================================================
# HEADER AVEC COINS ARRONDIS
# =====================================================================================
class FlagBadge(QLabel):
    """Drapeau de langue posé dans le coin d'une pochette."""

    def __init__(self, code, height=THUMB_FLAG_HEIGHT, parent=None):
        super().__init__(parent)
        self.code = code
        self.setFixedSize(round(height * 3 / 2), height)
        self.setToolTip(LANGUAGE_LABELS.get(code, code))
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        # THUMBNAIL_IMAGE_STYLE est posé sur la pochette sans sélecteur : Qt le
        # propage aux enfants. Sans cette remise à zéro, le drapeau héritait du
        # cadre noir de 4 px et se retrouvait rogné à l'intérieur.
        self.setStyleSheet("background: transparent; border: none;")
        self._render()

    def _render(self):
        """Rend le SVG aux pixels physiques de l'écran, sans habillage."""
        ratio = self.devicePixelRatioF()
        w = max(1, round(self.width() * ratio))
        h = max(1, round(self.height() * ratio))
        canvas = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        shape = QPainterPath()
        shape.addRoundedRect(QRectF(0, 0, w, h), 2 * ratio, 2 * ratio)
        painter.setClipPath(shape)
        renderer = QSvgRenderer(resource_path(f"assets/icons/flags/{self.code}.svg"))
        if renderer.isValid():
            renderer.render(painter, QRectF(0, 0, w, h))
        else:
            painter.fillRect(QRectF(0, 0, w, h), QColor("#4a5160"))
        painter.end()
        pixmap = QPixmap.fromImage(canvas)
        pixmap.setDevicePixelRatio(ratio)
        self.setPixmap(pixmap)


class CountBadge(QLabel):
    """Nombre de chapitres d'une collection, posé dans le coin d'une pochette.

    Peinte plutôt qu'habillée en QSS : elle repose sur l'illustration, où un
    fond opaque et un texte blanc restent lisibles quelle que soit la pochette.
    """

    def __init__(self, count, height=THUMB_FLAG_HEIGHT, parent=None):
        super().__init__(parent)
        self.count = count
        self.setFixedSize(max(round(height * 3 / 2), self._text_width(height)), height)
        self.setToolTip("1 chapitre" if count == 1 else f"{count} chapitres")
        # Le clic doit continuer d'ouvrir la collection, pas mourir sur la
        # pastille.
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        # Même remise à zéro que le drapeau : la feuille de la pochette n'a pas
        # de sélecteur et Qt la propage aux enfants.
        self.setStyleSheet("background: transparent; border: none;")
        self._render()

    def _font(self, height):
        font = QFont("Inter", max(8, round(height * 0.52)), QFont.Weight.Bold)
        return font

    def _text_width(self, height):
        metrics = QFontMetrics(self._font(height))
        return metrics.horizontalAdvance(str(self.count)) + 14

    def _render(self):
        colors = S.THUMBNAIL_BADGE_COLORS
        ratio = self.devicePixelRatioF()
        w = max(1, round(self.width() * ratio))
        h = max(1, round(self.height() * ratio))
        canvas = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        background = QColor(colors["background"])
        background.setAlpha(int(colors["background_alpha"]))
        border = QColor(colors["border"])
        border.setAlpha(int(colors["border_alpha"]))
        pen = QPen(border)
        pen.setWidthF(ratio)
        painter.setPen(pen)
        painter.setBrush(background)
        # Le tracé est rentré d'un demi-pixel : sinon le contour bave hors du
        # rectangle et l'arrondi paraît ébréché.
        inset = ratio / 2
        painter.drawRoundedRect(QRectF(inset, inset, w - 2 * inset, h - 2 * inset),
                                5 * ratio, 5 * ratio)

        font = self._font(self.height())
        font.setPointSizeF(font.pointSizeF() * ratio)
        painter.setFont(font)
        painter.setPen(QColor(colors["text"]))
        painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, str(self.count))
        painter.end()

        pixmap = QPixmap.fromImage(canvas)
        pixmap.setDevicePixelRatio(ratio)
        self.setPixmap(pixmap)


class ThumbnailMenuButton(QPushButton):
    """Pastille de menu posée sur la pochette.

    Les points sont dessinés plutôt qu'écrits : le glyphe U+22EF manque dans
    beaucoup de polices, qui retombent alors sur un caractère de substitution.
    """
    DOT_RADIUS = 1.7
    DOT_GAP = 5.5

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        center = QPointF(self.width() / 2, self.height() / 2)
        for offset in (-self.DOT_GAP, 0.0, self.DOT_GAP):
            painter.drawEllipse(center + QPointF(offset, 0), self.DOT_RADIUS, self.DOT_RADIUS)


class RoundedHeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 8
        self.background_image = None
        self.scrim = None
    def set_background_image(self, image_path):
        if image_path and os.path.exists(image_path):
            self.background_image = image_path
            self.update()
        else:
            self.background_image = None
            self.update()
    def set_scrim(self, top_color=None, bottom_color=None):
        """Voile dégradé posé sur l'image de fond.

        Sans lui, les icônes et le titre blancs disparaissent sur une bannière
        claire comme le collage par défaut.
        """
        top = QColor(*HEADER_SCRIM[0]) if top_color is None else QColor(top_color)
        bottom = QColor(*HEADER_SCRIM[1]) if bottom_color is None else QColor(bottom_color)
        self.scrim = (top, bottom)
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # Découpe arrondie au tracé : le masque 1 bit d'avant crénelait les coins.
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), self.radius, self.radius)
        painter.setClipPath(clip)
        painted = False
        if self.background_image and os.path.exists(self.background_image):
            source = QImage(self.background_image)
            if not source.isNull():
                # Fond rendu aux pixels physiques de l'écran, comme les vignettes.
                ratio = self.devicePixelRatioF()
                cover = fit_cover(source, max(1, round(self.width() * ratio)),
                                  max(1, round(self.height() * ratio)))
                cover.setDevicePixelRatio(ratio)
                painter.drawImage(0, 0, cover)
                painted = True
        if not painted:
            painter.fillRect(self.rect(),
                             QColor("#1b1f27" if self.scrim else theme_color("surface")))
        if self.scrim:
            veil = QLinearGradient(0, 0, 0, self.height())
            veil.setColorAt(0.0, self.scrim[0])
            veil.setColorAt(1.0, self.scrim[1])
            painter.fillRect(self.rect(), QBrush(veil))
            painter.setPen(QColor(255, 255, 255, 28))
        else:
            painter.setPen(QColor(theme_color("border")))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

# =====================================================================================
# PAGE D'ACCUEIL
# =====================================================================================
class HomePage(QWidget):
    open_bookshelf = Signal()
    open_file_dialog = Signal()
    open_settings = Signal()
    toggle_theme = Signal()
    def __init__(self):
        super().__init__()
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("assets/images/logo.png"))
        logo_label.setPixmap(logo_pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Un Lecteur de Manga Offline")
        subtitle.setFont(QFont("Inter", 13))
        subtitle.setStyleSheet(S.HOME_SUBTITLE_STYLE)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        # Deux entrées : la bibliothèque porte l'accent, le fichier isolé reste sobre.
        btn_layout1 = QHBoxLayout()
        btn_layout1.setSpacing(16)
        open_btn = QPushButton("OPEN FILE")
        open_btn.setFixedSize(HOME_BUTTON_WIDTH, HOME_BUTTON_HEIGHT)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.setStyleSheet(S.HOME_SECONDARY_BUTTON_STYLE)
        open_btn.clicked.connect(self.open_file_dialog.emit)
        btn_layout1.addWidget(open_btn)
        bookshelf_btn = QPushButton("BOOKSHELF")
        bookshelf_btn.setFixedSize(HOME_BUTTON_WIDTH, HOME_BUTTON_HEIGHT)
        bookshelf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bookshelf_btn.setStyleSheet(S.HOME_PRIMARY_BUTTON_STYLE)
        bookshelf_btn.clicked.connect(self.open_bookshelf.emit)
        btn_layout1.addWidget(bookshelf_btn)

        # Engrenage : voisin de la bibliothèque, mais sans nom ni couleur pleine
        # pour rester une porte de service à côté des deux entrées principales.
        settings_btn = QPushButton()
        settings_btn.setIcon(QIcon(themed_icon("gear")))
        settings_btn.setIconSize(QSize(22, 22))
        settings_btn.setFixedSize(HOME_BUTTON_HEIGHT, HOME_BUTTON_HEIGHT)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet(S.HOME_ICON_BUTTON_STYLE)
        settings_btn.setToolTip("Paramètres")
        settings_btn.clicked.connect(self.open_settings.emit)
        btn_layout1.addWidget(settings_btn)

        # Bascule clair / sombre : l'icône annonce ce vers quoi elle mène, une
        # lune tant qu'on est en clair, un soleil une fois passé au sombre.
        dark = current_theme() == "dark"
        self.theme_btn = QPushButton()
        self.theme_btn.setIcon(QIcon(themed_icon("sun" if dark else "moon")))
        self.theme_btn.setIconSize(QSize(22, 22))
        self.theme_btn.setFixedSize(HOME_BUTTON_HEIGHT, HOME_BUTTON_HEIGHT)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.setStyleSheet(S.HOME_ICON_BUTTON_STYLE)
        self.theme_btn.setToolTip("Revenir au thème clair" if dark
                                  else "Passer au thème sombre")
        self.theme_btn.clicked.connect(self.toggle_theme.emit)
        btn_layout1.addWidget(self.theme_btn)

        layout.addLayout(btn_layout1)

        bmc_btn = QPushButton('☕ Buy me a coffee')
        bmc_btn.setFixedHeight(HOME_SUPPORT_HEIGHT)
        bmc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bmc_btn.setStyleSheet(S.BMC_BUTTON_STYLE)
        bmc_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://www.buymeacoffee.com/ezakaria')))
        layout.addWidget(bmc_btn, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

        paypal_btn = QPushButton('💙 Paypal Me')
        paypal_btn.setFixedHeight(HOME_SUPPORT_HEIGHT)
        paypal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paypal_btn.setStyleSheet(S.PAYPAL_BUTTON_STYLE)
        paypal_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://www.paypal.me/ZELORCHE')))
        layout.addWidget(paypal_btn, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

# =====================================================================================
# WIDGET VIGNETTE (Utilisé pour Dossiers et PDF)
# =====================================================================================
class ThumbnailWidget(QWidget):
    # Cache partagé des pochettes déjà mises à l'échelle, indexé par
    # (chemin, date de modification, taille, densité d'écran).
    _cover_cache = {}
    COVER_CACHE_MAX = 400

    clicked = Signal()
    remove_requested = Signal(str)
    alias_requested = Signal(str, str)
    cover_requested = Signal(str)
    tags_requested = Signal(str)
    language_requested = Signal(str, str)   # chemin, code de langue ("" pour aucune)

    def __init__(self, thumb_path, title_text, path=None, width=None,
                 height=None, show_menu=True, checkbox=None,
                 language=None, count=None):
        super().__init__()
        self.thumb_path = thumb_path
        self._rendered_ratio = None
        self.title_text = title_text
        self.path = path
        # Taille resolue a la construction : une valeur par defaut figee dans la
        # signature ignorerait le reglage change en cours de session.
        default_width, default_height = thumb_display_size()
        self.thumb_width = width if width is not None else default_width
        self.thumb_height = height if height is not None else default_height
        self.show_menu = show_menu
        self.checkbox = checkbox
        self.language = language
        # None : la vignette n'est pas une collection. 0 : elle est vide, et il
        # n'y a rien d'utile à afficher non plus.
        self.count = count
        self.setObjectName("thumbnailWidget")
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        # L'ombre portée déborde de la pochette : sans ces marges, le parent la
        # rognerait net.
        layout.setContentsMargins(*THUMB_SHADOW_MARGINS)
        layout.setSpacing(2)
        self.setStyleSheet("")
        self.img_label = RoundedLabel()
        self.img_label.setContentsMargins(0, 0, 0, 0)
        self.img_label.setFixedSize(self.thumb_width, self.thumb_height)
        self.img_label.setStyleSheet(S.THUMBNAIL_IMAGE_STYLE)
        self.img_label.setGraphicsEffect(self.build_shadow())
        self.img_label.deferred_load = self.update_image
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.img_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.img_label.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.img_label.clicked.connect(self.clicked)
        info_widget = QWidget()
        info_widget.setFixedWidth(self.thumb_width)
        info_widget.setMinimumHeight(50)  # Hauteur minimale pour s'adapter aux titres longs
        info_layout = QHBoxLayout() if self.checkbox else QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        if self.checkbox:
            self.checkbox.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.checkbox.setEnabled(True)
            self.checkbox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            info_layout.addWidget(self.checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)
            self.title_label = QLabel(self.title_text)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_label.setWordWrap(True)
            self.title_label.setMinimumHeight(40)  # Hauteur minimale pour les titres longs
            self.title_label.setStyleSheet(S.THUMBNAIL_TITLE_STYLE)
            info_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignVCenter)
            info_layout.addStretch(1)
        else:
            self.title_label = QLabel(self.title_text)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_label.setWordWrap(True)
            self.title_label.setMinimumHeight(40)  # Hauteur minimale pour les titres longs
            self.title_label.setStyleSheet(S.THUMBNAIL_TITLE_STYLE)
            info_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        info_widget.setLayout(info_layout)
        layout.addWidget(info_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        if self.language:
            # Coin inférieur droit, aligné sur le retrait de la pastille de menu.
            flag = FlagBadge(self.language, parent=self.img_label)
            corner = THUMB_BORDER_WIDTH + 5
            flag.move(self.thumb_width - flag.width() - corner,
                      self.thumb_height - flag.height() - corner)
            flag.raise_()
        if self.count:
            # Coin inférieur gauche, en vis-à-vis du drapeau de langue.
            badge = CountBadge(self.count, parent=self.img_label)
            corner = THUMB_BORDER_WIDTH + 5
            badge.move(corner, self.thumb_height - badge.height() - corner)
            badge.raise_()
        if self.show_menu and self.path:
            debug(f"[DEBUG] Création du menu contextuel pour : {self.path}")
            # Enfant du visuel, posé dans son coin supérieur droit : le bouton
            # flotte sur la pochette au lieu d'occuper une ligne sous le titre.
            menu_btn = ThumbnailMenuButton(self.img_label)
            menu_btn.setFixedSize(THUMB_MENU_SIZE, THUMB_MENU_SIZE)
            menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            menu_btn.setStyleSheet(S.THUMBNAIL_MENU_BUTTON_STYLE)
            inset = THUMB_BORDER_WIDTH + 5
            menu_btn.move(self.thumb_width - THUMB_MENU_SIZE - inset, inset)
            menu_btn.raise_()
            def build_menu():
                """Menu assemblé au clic.

                Le construire pour chaque vignette représentait plus de la
                moitié du coût de fabrication d'une grille.
                """
                menu = QMenu()
                alias_action = menu.addAction("Set alias")
                alias_action.triggered.connect(lambda: self.alias_requested.emit(self.path, self.title_text))

                language_menu = menu.addMenu("Langue")
                choices = QActionGroup(language_menu)
                choices.setExclusive(True)
                for code, label in LANGUAGES:
                    action = language_menu.addAction(label)
                    action.setCheckable(True)
                    action.setChecked(code == self.language)
                    choices.addAction(action)
                    action.triggered.connect(
                        lambda _checked=False, c=code: self.language_requested.emit(self.path, c))
                language_menu.addSeparator()
                clear_action = language_menu.addAction("Aucune")
                clear_action.setCheckable(True)
                clear_action.setChecked(not self.language)
                choices.addAction(clear_action)
                clear_action.triggered.connect(
                    lambda: self.language_requested.emit(self.path, ""))
                if os.path.isdir(self.path):
                    # Remplacer Add Tags par Original Cover
                    def set_original_cover():
                        folder_path = self.path
                        # Chercher le premier fichier supporté
                        files = [f for f in os.listdir(folder_path) if f.lower().endswith(ARCHIVE_EXTENSIONS)]
                        files.sort()
                        file_for_thumb = os.path.join(folder_path, files[0]) if files else None
                        if not file_for_thumb:
                            # Si aucune archive, chercher une image
                            images = [f for f in os.listdir(folder_path) if f.lower().endswith(IMAGE_EXTENSIONS)]
                            images.sort()
                            if images:
                                file_for_thumb = os.path.join(folder_path, images[0])
                        if file_for_thumb:
                            thumb_dir = os.path.join(folder_path, '.thumbnails')
                            cover_path = os.path.join(thumb_dir, '_folder_thumb.png')
                            if write_cover_thumbnail(file_for_thumb, cover_path):
                                record_generated_cover(cover_path)
                                # Rafraîchir la vignette
                                self.update_thumbnail(cover_path)

                    original_cover_action = menu.addAction("Original Cover")
                    original_cover_action.triggered.connect(set_original_cover)
                

            
                # Ajouter l'option Download Cover pour tous les éléments (dossiers et fichiers)
                def download_cover_from_anilist_for_all():
                    # Fonction pour récupérer l'alias d'un dossier
                    def get_folder_alias(folder_path):
                        try:
                            # Chercher dans la bibliothèque principale
                            if os.path.exists(LIBRARY_FILE):
                                with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                                    library = json.load(f)
                                for entry in library:
                                    if entry["path"] == folder_path:
                                        return entry.get("alias")
                        except Exception as e:
                            print(f"Erreur lecture alias bibliothèque : {e}")
                        return None
                
                    # Fonction pour récupérer l'alias d'un fichier
                    def get_file_alias(file_path):
                        parent_dir = os.path.dirname(file_path)
                        alias_file = os.path.join(parent_dir, '.alias.json')
                        if os.path.exists(alias_file):
                            try:
                                with open(alias_file, 'r', encoding='utf-8') as f:
                                    alias_map = json.load(f)
                                return alias_map.get(os.path.basename(file_path))
                            except Exception as e:
                                print(f"Erreur lecture alias fichier : {e}")
                        return None
                
                    if os.path.isdir(self.path):
                        # Pour les dossiers, utiliser l'alias si disponible, sinon le nom du dossier
                        alias = get_folder_alias(self.path)
                        manga_name = alias if alias else os.path.basename(self.path)
                        target_path = self.path
                    else:
                        # Pour les fichiers, utiliser l'alias si disponible, sinon le nom du fichier
                        alias = get_file_alias(self.path)
                        if alias:
                            manga_name = alias
                        else:
                            manga_name = os.path.splitext(os.path.basename(self.path))[0]
                        target_path = os.path.dirname(self.path)
                
                    debug(f"[DEBUG] Tentative de téléchargement de couverture pour : {manga_name}")
                
                    # Récupérer les informations depuis AniList puis MangaDex si pas trouvé
                    info = fetch_manga_info(manga_name)
                    if info and info.get('cover'):
                        cover_url = info['cover']
                        thumb_dir = os.path.join(target_path, '.thumbnails')
                        try:
                            os.makedirs(thumb_dir, exist_ok=True)
                        except OSError as e:
                            print(f"Impossible de créer le dossier de vignettes : {thumb_dir}. Erreur : {e}")
                            return
                    
                        if os.path.isdir(self.path):
                            # Pour les dossiers, sauvegarder comme _folder_thumb.png
                            cover_path = os.path.join(thumb_dir, '_folder_thumb.png')
                        else:
                            # Pour les fichiers, sauvegarder avec le nom du fichier
                            base_name = os.path.splitext(os.path.basename(self.path))[0]
                            cover_path = os.path.join(thumb_dir, base_name + '.png')
                    
                        try:
                            resp = requests.get(cover_url, timeout=10)
                            if resp.status_code == 200:
                                with open(cover_path, 'wb') as imgf:
                                    imgf.write(resp.content)
                                mark_cover_as_custom(cover_path)
                                debug(f"[DEBUG] Couverture téléchargée : {cover_path}")
                                # Rafraîchir la vignette
                                self.update_thumbnail(cover_path)
                            
                                # Afficher un message de confirmation
                                from PySide6.QtWidgets import QMessageBox
                                QMessageBox.information(None, "Succès", f"Couverture téléchargée pour {manga_name}")
                            
                                # Sauvegarder les informations AniList si pas déjà fait
                                anilist_file = os.path.join(target_path, '.anilist.json')
                                if not os.path.exists(anilist_file):
                                    try:
                                        with open(anilist_file, 'w', encoding='utf-8') as f:
                                            json.dump(info, f, ensure_ascii=False, indent=2)
                                        debug(f"[DEBUG] Informations API sauvegardées")
                                    except Exception as e:
                                        debug(f"[DEBUG] Erreur sauvegarde API : {e}")
                            else:
                                debug(f"[DEBUG] Erreur téléchargement couverture : {resp.status_code}")
                                if resp.status_code == 404:
                                    debug(f"[DEBUG] Couverture introuvable sur le serveur : {cover_url}")
                                # Afficher un message d'erreur spécifique
                                from PySide6.QtWidgets import QMessageBox
                                if resp.status_code == 404:
                                    QMessageBox.warning(None, "Couverture introuvable", f"La couverture pour {manga_name} n'est plus disponible sur le serveur")
                                else:
                                    QMessageBox.warning(None, "Erreur de téléchargement", f"Impossible de télécharger la couverture pour {manga_name} (Erreur {resp.status_code})")
                        except Exception as e:
                            debug(f"[DEBUG] Exception téléchargement couverture : {e}")
                            # Afficher un message d'erreur pour les exceptions réseau
                            from PySide6.QtWidgets import QMessageBox
                            QMessageBox.warning(None, "Erreur réseau", f"Erreur de connexion lors du téléchargement de la couverture pour {manga_name}")
                    else:
                        debug(f"[DEBUG] Aucune couverture trouvée pour : {manga_name}")
                        # Afficher un message d'erreur
                        from PySide6.QtWidgets import QMessageBox
                        QMessageBox.warning(None, "Aucune couverture trouvée", f"Aucune couverture trouvée pour {manga_name} sur AniList ou MangaDex")
            
                download_cover_action = menu.addAction("Download Cover")
                download_cover_action.triggered.connect(download_cover_from_anilist_for_all)
            
                # Ajouter l'option Cover From My Computer
                def cover_from_computer():
                    if not self.path:
                        return
                
                    # Ouvrir le sélecteur de fichier pour choisir une image
                    from PySide6.QtWidgets import QFileDialog
                    image_path, _ = QFileDialog.getOpenFileName(
                        None,
                        "Choisir une image de couverture",
                        "",
                        "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
                    )
                
                    if image_path and os.path.exists(image_path):
                        try:
                            # Déterminer le chemin de destination
                            if os.path.isdir(self.path):
                                # Pour les dossiers, sauvegarder comme _folder_thumb.png
                                target_path = self.path
                                thumb_dir = os.path.join(target_path, '.thumbnails')
                                cover_path = os.path.join(thumb_dir, '_folder_thumb.png')
                            else:
                                # Pour les fichiers, sauvegarder avec le nom du fichier
                                target_path = os.path.dirname(self.path)
                                thumb_dir = os.path.join(target_path, '.thumbnails')
                                base_name = os.path.splitext(os.path.basename(self.path))[0]
                                cover_path = os.path.join(thumb_dir, base_name + '.png')
                        
                            # Créer le dossier de vignettes si nécessaire
                            os.makedirs(thumb_dir, exist_ok=True)
                        
                            # Charger l'image en conservant sa pleine résolution
                            if save_cover_thumbnail(QImage(image_path), cover_path):
                                mark_cover_as_custom(cover_path)
                                # Rafraîchir la vignette
                                self.update_thumbnail(cover_path)
                            
                                # Afficher un message de confirmation
                                from PySide6.QtWidgets import QMessageBox
                                QMessageBox.information(
                                    None, 
                                    "Succès", 
                                    f"Couverture personnalisée ajoutée avec succès"
                                )
                            else:
                                QMessageBox.warning(
                                    None, 
                                    "Erreur", 
                                    "Impossible de charger l'image sélectionnée"
                                )
                        except Exception as e:
                            debug(f"[DEBUG] Erreur lors de l'ajout de la couverture : {e}")
                            from PySide6.QtWidgets import QMessageBox
                            QMessageBox.warning(
                                None, 
                                "Erreur", 
                                f"Erreur lors de l'ajout de la couverture : {e}"
                            )
            
                cover_from_computer_action = menu.addAction("Cover From My Computer")
                cover_from_computer_action.triggered.connect(cover_from_computer)
            
                explorer_action = menu.addAction("Open in Explorer")
                explorer_action.triggered.connect(lambda: self.open_in_explorer(self.path))
                remove_action = menu.addAction("Remove from bookshelf")
                remove_action.triggered.connect(lambda checked=False, p=self.path: self.remove_requested.emit(p))
                return menu

            menu_btn.clicked.connect(lambda: build_menu().exec(
                menu_btn.mapToGlobal(menu_btn.rect().bottomLeft())))

    def _device_pixel_ratio(self):
        """Ratio de pixels physiques de l'écran qui affiche la vignette."""
        handle = self.window().windowHandle() if self.window() else None
        if handle is not None:
            return handle.devicePixelRatio()
        screen = QApplication.primaryScreen()
        return screen.devicePixelRatio() if screen else 1.0

    def _inner_size(self):
        """Zone utile du label, bordure déduite."""
        return (max(1, self.thumb_width - 2 * THUMB_BORDER_WIDTH),
                max(1, self.thumb_height - 2 * THUMB_BORDER_WIDTH))

    def _cover_pixmap(self, image, ratio):
        """Rend la couverture à la résolution physique exacte du label.

        Le pixmap est produit en pixels écran puis étiqueté avec le
        devicePixelRatio : Qt le recopie tel quel au lieu de le rééchantillonner.
        """
        w, h = self._inner_size()
        dw, dh = max(1, round(w * ratio)), max(1, round(h * ratio))
        canvas = QImage(dw, dh, QImage.Format.Format_ARGB32_Premultiplied)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        radius = THUMB_CORNER_RADIUS * ratio
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, dw, dh), radius, radius)
        painter.setClipPath(clip)
        painter.drawImage(0, 0, fit_cover(image, dw, dh))
        painter.end()
        pixmap = QPixmap.fromImage(canvas)
        pixmap.setDevicePixelRatio(ratio)
        return pixmap

    def _placeholder_pixmap(self, background, text, text_color, ratio):
        """Vignette de repli, rendue elle aussi à la résolution de l'écran."""
        w, h = self._inner_size()
        pixmap = QPixmap(max(1, round(w * ratio)), max(1, round(h * ratio)))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(background)
        painter = QPainter(pixmap)
        painter.setPen(text_color)
        painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return pixmap

    def _cached_cover(self, ratio):
        """Pochette prête à afficher, mémorisée pour toute l'application.

        Les grilles sont reconstruites en entier à chaque frappe dans la
        recherche et à chaque retour de page ; sans ce cache, chaque PNG de
        600x840 serait redécodé à chaque fois.
        """
        if not self.thumb_path:
            return None
        try:
            stamp = os.path.getmtime(self.thumb_path)
        except OSError:
            return None
        key = (self.thumb_path, stamp, self.thumb_width, self.thumb_height, ratio)
        pixmap = ThumbnailWidget._cover_cache.get(key)
        if pixmap is None:
            image = QImage(self.thumb_path)
            if image.isNull():
                return None
            pixmap = self._cover_pixmap(image, ratio)
            if len(ThumbnailWidget._cover_cache) >= ThumbnailWidget.COVER_CACHE_MAX:
                ThumbnailWidget._cover_cache.clear()
            ThumbnailWidget._cover_cache[key] = pixmap
        return pixmap

    def update_image(self):
        ratio = self._device_pixel_ratio()
        self._rendered_ratio = ratio
        try:
            pixmap = self._cached_cover(ratio)
            if pixmap is None:
                debug(f"[DEBUG] Aucune image exploitable pour : {self.thumb_path}")
                pixmap = self._placeholder_pixmap(
                    QColor(240, 240, 240), "No\nPreview\nAvailable",
                    QColor(100, 100, 100), ratio)
            self.img_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image {self.thumb_path}: {e}")
            try:
                self.img_label.setPixmap(self._placeholder_pixmap(
                    QColor(255, 200, 200), "Error\nLoading\nImage", QColor(150, 0, 0), ratio))
            except Exception as e:
                self.img_label.setText("Error\nImage")
                self.img_label.setStyleSheet("border: 4px solid #111; "
                                             "border-radius: 14px; "
                                             "background: white; "
                                             "color: #666; "
                                             "font-size: 12px;")
                print(f"Erreur fatale lors de la création de l'image d'erreur: {e}")

    def build_shadow(self):
        """Ombre portée de la pochette, à la couleur du thème."""
        values = S.THUMBNAIL_SHADOW_COLORS
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(int(values["blur"]))
        shadow.setOffset(int(values["offset_x"]), int(values["offset_y"]))
        color = QColor(values["color"])
        color.setAlpha(int(values["alpha"]))
        shadow.setColor(color)
        return shadow

    def showEvent(self, event):
        """Re-rend la vignette si elle atterrit sur un écran d'un autre DPI."""
        super().showEvent(event)
        # _rendered_ratio est None tant que la pochette n'a pas été peinte :
        # ne pas déclencher le chargement ici, c'est tout l'intérêt du différé.
        if self._rendered_ratio is not None and self._device_pixel_ratio() != self._rendered_ratio:
            self.update_image()

    def update_thumbnail(self, new_thumb_path):
        try:
            self.thumb_path = new_thumb_path
            self.update_image()
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la vignette: {e}")
    def enterEvent(self, event):
        self.img_label.setStyleSheet(S.THUMBNAIL_IMAGE_HOVER_STYLE)
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.img_label.setStyleSheet(S.THUMBNAIL_IMAGE_STYLE)
        super().leaveEvent(event)
    def open_in_explorer(self, path):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        import os
        if os.path.isdir(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))

# =====================================================================================
# VUE RESPONSIVE (Grille pour dossiers ou PDFs)
# =====================================================================================
class ResponsiveGridView(QWidget):
    def __init__(self):
        super().__init__()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(GRID_SPACING)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)  # centrer horizontalement
        self.grid_widget = QWidget()
        self.grid_widget.setLayout(self.grid_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.grid_widget)
        self.scroll_area.setStyleSheet(S.SCROLL_AREA_STYLE)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
        self._items = []
        self._columns = 0
        # Un redimensionnement émet des dizaines d'événements : on attend la fin
        # du geste avant de replacer les vignettes.
        self._relayout_timer = QTimer(self)
        self._relayout_timer.setSingleShot(True)
        self._relayout_timer.timeout.connect(self.refresh_grid)

    def column_count(self):
        width = self.width()
        # Une colonne = la pochette, ses marges d'ombre et l'espacement.
        step = (thumb_display_size()[0] + THUMB_SHADOW_MARGINS[0]
                + THUMB_SHADOW_MARGINS[2] + GRID_SPACING)
        return max(1, width // step) if width > 0 else 1

    def set_items(self, widgets):
        # Nettoyer les anciens widgets
        for widget in self._items:
            self.grid_layout.removeWidget(widget)
            widget.deleteLater()
        self._items = widgets
        self.refresh_grid(force=True)

    def refresh_grid(self, force=False):
        """Replace les vignettes en grille.

        Vider puis remplir un QGridLayout coûte du temps quadratique : on ne le
        refait que si le nombre de colonnes a réellement changé, et sans
        repeindre entre chaque ajout.
        """
        columns = self.column_count()
        if not force and columns == self._columns:
            return
        self._columns = columns
        self.grid_widget.setUpdatesEnabled(False)
        try:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            for i, widget in enumerate(self._items):
                self.grid_layout.addWidget(widget, i // columns, i % columns)
        finally:
            self.grid_widget.setUpdatesEnabled(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_timer.start(80)

# =====================================================================================
# PAGE BIBLIOTHEQUE
# =====================================================================================
class ProgressDialog(QDialog):
    """Carte de progression flottante, sans cadre système.

    Le libellé est un nom de fichier : il est coupé proprement plutôt que de
    déborder d'une boîte à largeur fixe.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Génération des vignettes")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._message = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(PROGRESS_CARD_MARGIN, PROGRESS_CARD_MARGIN,
                                 PROGRESS_CARD_MARGIN, PROGRESS_CARD_MARGIN + 4)
        card = QWidget()
        card.setObjectName("progressCard")
        card.setStyleSheet(S.PROGRESS_CARD_STYLE)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 22)
        layout.setSpacing(5)

        head = QHBoxLayout()
        head.setSpacing(12)
        self.title_label = QLabel(self.windowTitle())
        self.title_label.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet(S.PROGRESS_TITLE_STYLE)
        self.percent_label = QLabel("0 %")
        self.percent_label.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.percent_label.setStyleSheet(S.PROGRESS_PERCENT_STYLE)
        head.addWidget(self.title_label)
        head.addStretch()
        head.addWidget(self.percent_label)
        layout.addLayout(head)

        self.label = QLabel("Préparation…")
        self.label.setFont(QFont("Inter", 10))
        self.label.setStyleSheet(S.PROGRESS_MESSAGE_STYLE)
        layout.addWidget(self.label)
        layout.addSpacing(8)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet(S.PROGRESS_BAR_STYLE)
        layout.addWidget(self.progress)

        self.setFixedSize(PROGRESS_CARD_WIDTH, self.sizeHint().height())

    def setWindowTitle(self, title):
        super().setWindowTitle(title)
        # Appelé une première fois avant que la carte n'existe.
        if hasattr(self, "title_label"):
            self.title_label.setText(title)

    def showEvent(self, event):
        """Sans cadre système, Qt ne recentre pas la boîte sur la fenêtre."""
        super().showEvent(event)
        parent = self.parentWidget()
        if parent is not None:
            self.move(parent.window().frameGeometry().center() - self.rect().center())

    def _elided(self, text):
        """Coupe le nom de fichier à la largeur de la carte."""
        available = PROGRESS_CARD_WIDTH - 2 * PROGRESS_CARD_MARGIN - 48
        return self.label.fontMetrics().elidedText(
            text, Qt.TextElideMode.ElideRight, available)

    def update_message(self, msg, value=None):
        self._message = msg
        self.label.setText(self._elided(msg))
        if value is not None:
            self.progress.setValue(value)
            self.percent_label.setText(f"{value} %")
        QApplication.processEvents()


class BookShelfPage(QWidget):
    folder_selected = Signal(str)
    add_folder_clicked = Signal()
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.library = []
        self.grid_view = ResponsiveGridView()
        self.selection_mode = False
        self.selected_items = set()
        self.load_library()
        self.setup_ui()
        # La grille est construite par show_bookshelf : la remplir ici allongeait
        # le démarrage d'une page que l'on ne voit pas encore.

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # En-tête : collage de fond, voile sombre, puis contenu en blanc par-dessus.
        header_widget = RoundedHeaderWidget()
        header_widget.radius = HEADER_RADIUS
        header_widget.setFixedHeight(HEADER_HEIGHT)
        header_widget.set_background_image(resource_path('assets/images/header.png'))
        header_widget.set_scrim()

        header = QHBoxLayout(header_widget)
        header.setContentsMargins(18, 0, 18, 0)
        header.setSpacing(16)

        # Retour : isolé à gauche, là où on le cherche.
        header.addWidget(make_back_btn(self.back_clicked.emit))

        # Titre + compteur de collections.
        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(0)
        title = QLabel("BookShelf")
        title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title.setStyleSheet(S.PAGE_TITLE_STYLE_BOOKSHELF)
        self.count_label = QLabel()
        self.count_label.setFont(QFont("Inter", 9))
        self.count_label.setStyleSheet(S.HEADER_SUBTITLE_STYLE)
        # Hauteur figée sur le texte : sinon la colonne étire les deux labels et
        # rouvre un blanc entre le titre et le compteur.
        for label in (title, self.count_label):
            label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        title.setFixedHeight(title.fontMetrics().ascent() + 3)
        title_col.addStretch()
        title_col.addWidget(title)
        title_col.addWidget(self.count_label)
        title_col.addStretch()
        header.addLayout(title_col)
        header.addStretch()

        # Actions secondaires réunies dans une seule pilule translucide.
        toolbar = make_toolbar_group()
        filter_bar = toolbar.layout()

        filter_btn = make_toolbar_btn(resource_path("assets/icons/funnel-white.svg"),
                                      "Filtrer", lambda: None)
        filter_bar.addWidget(filter_btn)

        # Bouton Sélectionner (sélection multiple)
        self.select_btn = make_toolbar_btn(resource_path("assets/icons/check2-all-white.svg"),
                                           "Sélectionner des fichiers",
                                           self.toggle_selection_mode, checkable=True)
        filter_bar.addWidget(self.select_btn)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Rechercher une collection")
        self.search_field.setStyleSheet(S.HEADER_SEARCH_STYLE)
        self.search_field.setFixedHeight(HEADER_BTN_SIZE)
        self.search_field.setFixedWidth(0)
        placeholder = self.search_field.palette()
        placeholder.setColor(QPalette.ColorRole.PlaceholderText, QColor(255, 255, 255, 120))
        self.search_field.setPalette(placeholder)
        self.search_field.textChanged.connect(self.refresh_shelf)
        filter_bar.addWidget(self.search_field)

        # Le champ se déplie à l'ouverture au lieu d'apparaître d'un coup.
        self._search_anim = QPropertyAnimation(self.search_field, b"maximumWidth", self)
        self._search_anim.setDuration(180)
        self._search_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # Animer maximumWidth ne suffit pas : la largeur retomberait sur le
        # sizeHint du champ. On recopie la valeur animée en largeur fixe.
        self._search_anim.valueChanged.connect(
            lambda value: self.search_field.setFixedWidth(int(value)))
        # La dernière image n'est pas garantie : on cale la largeur finale à la main,
        # sinon le champ reste ouvert de quelques pixels.
        self._search_anim.finished.connect(
            lambda: self.search_field.setFixedWidth(int(self._search_anim.endValue())))

        def toggle_search():
            # L'état vient du bouton, déjà basculé par le clic : lire la largeur
            # courante donnerait un faux etat pendant l'animation.
            opened = search_btn.isChecked()
            self._search_anim.stop()
            self._search_anim.setStartValue(self.search_field.maximumWidth())
            self._search_anim.setEndValue(HEADER_SEARCH_WIDTH if opened else 0)
            self._search_anim.start()
            if opened:
                self.search_field.setFocus()
            else:
                # clear() relance refresh_shelf : inutile si le champ était vide,
                # et la reconstruction de la grille saccaderait l'animation.
                if self.search_field.text():
                    self.search_field.clear()
                self.search_field.clearFocus()

        search_btn = make_toolbar_btn(resource_path("assets/icons/search-white.svg"),
                                      "Rechercher", toggle_search, checkable=True)
        filter_bar.addWidget(search_btn)

        self.sort_az = True
        self.sort_btn = make_toolbar_btn(resource_path("assets/icons/sort-alpha-down-white.svg"),
                                         "Trier A-Z", self.toggle_sort)
        filter_bar.addWidget(self.sort_btn)
        # Ordre d'ouverture choisi dans les paramètres. La bibliothèque n'est pas
        # réécrite au passage : seul un tri demandé à la main est enregistré.
        self.apply_sort(settings.get("default_sort") == "az", save=False)

        header.addWidget(toolbar)

        # Action principale, la seule en couleur pleine.
        add_btn = QPushButton("  Ajouter")
        add_btn.setIcon(QIcon(resource_path("assets/icons/folder-plus-white.svg")))
        add_btn.setIconSize(QSize(18, 18))
        add_btn.setFixedHeight(HEADER_TOOLBAR_HEIGHT)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(S.HEADER_PRIMARY_BUTTON_STYLE)
        add_btn.setToolTip("Ajouter un dossier")
        add_btn.clicked.connect(self.add_folder_clicked.emit)
        header.addWidget(add_btn)

        layout.addWidget(header_widget)
        layout.addWidget(self.grid_view)

    def load_library(self):
        try:
            with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                self.library = json.load(f)
        except Exception:
            self.library = []

    def save_library(self):
        with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.library, f, ensure_ascii=False, indent=2)

    def add_folder(self, folder_path):
        if folder_path and folder_path not in [d["path"] for d in self.library]:
            # Afficher le popup de progression
            progress_dialog = ProgressDialog(self)
            progress_dialog.show()
            def progress_callback(msg, value=None):
                progress_dialog.update_message(msg, value)
            try:
                # Vignettes préparées d'un bloc, sauf si le réglage préfère les
                # laisser se créer à l'affichage.
                if settings.get("auto_thumbnails"):
                    generate_all_thumbnails_for_folder(folder_path, progress_callback)
                self.library.append({"path": folder_path})
                self.save_library()
                self.refresh_shelf()
                # --- Récupération automatique AniList/MangaDex ---
                manga_name = os.path.basename(folder_path)
                if not settings.get("fetch_online_info"):
                    debug("[DEBUG API] Récupération en ligne désactivée dans les paramètres")
                    return
                debug(f"[DEBUG API] Tentative de récupération pour : {manga_name}")
                info = fetch_manga_info(manga_name)
                if info:
                    debug(f"[DEBUG API] Succès, création de .anilist.json")
                    import json
                    try:
                        with open(os.path.join(folder_path, '.anilist.json'), 'w', encoding='utf-8') as f:
                            json.dump(info, f, ensure_ascii=False, indent=2)
                        # Télécharger la bannière si elle existe (AniList uniquement)
                        banner_url = info.get('banner')
                        if banner_url:
                            import requests
                            thumb_dir = os.path.join(folder_path, '.thumbnails')
                            try:
                                os.makedirs(thumb_dir, exist_ok=True)
                            except OSError as e:
                                print(f"Impossible de créer le dossier de vignettes : {thumb_dir}. Erreur : {e}")
                                raise e
                            banner_path = os.path.join(thumb_dir, '_header_banner.png')
                            try:
                                resp = requests.get(banner_url, timeout=10)
                                if resp.status_code == 200:
                                    with open(banner_path, 'wb') as imgf:
                                        imgf.write(resp.content)
                                    debug(f"[DEBUG API] Bannière téléchargée : {banner_path}")
                                else:
                                    debug(f"[DEBUG API] Erreur téléchargement bannière : {resp.status_code}")
                            except Exception as e:
                                debug(f"[DEBUG API] Exception téléchargement bannière : {e}")
                        # Télécharger la couverture comme vignette du dossier
                        cover_url = info.get('cover')
                        if cover_url:
                            import requests
                            thumb_dir = os.path.join(folder_path, '.thumbnails')
                            try:
                                os.makedirs(thumb_dir, exist_ok=True)
                            except OSError as e:
                                print(f"Impossible de créer le dossier de vignettes : {thumb_dir}. Erreur : {e}")
                                raise e
                            thumb_path = os.path.join(thumb_dir, '_folder_thumb.png')
                            try:
                                resp = requests.get(cover_url, timeout=10)
                                if resp.status_code == 200:
                                    with open(thumb_path, 'wb') as imgf:
                                        imgf.write(resp.content)
                                    debug(f"[DEBUG API] Vignette téléchargée : {thumb_path}")
                                else:
                                    debug(f"[DEBUG API] Erreur téléchargement vignette : {resp.status_code}")
                            except Exception as e:
                                debug(f"[DEBUG API] Exception téléchargement vignette : {e}")
                    except Exception as e:
                        debug(f"[DEBUG API] Erreur lors de l'écriture du fichier : {e}")
                else:
                    debug(f"[DEBUG API] Aucun résultat pour : {manga_name}")
            except OSError as e:
                error_msg = (f"Impossible d'accéder au dossier ou de créer le répertoire des vignettes.\n\n"
                             f"Vérifiez que le disque est bien connecté et que vous avez les droits d'écriture.\n\n"
                             f"Erreur: {e}")
                QMessageBox.critical(self, "Erreur d'accès au dossier", error_msg)
            finally:
                progress_dialog.close()
    
    def refresh_shelf(self):
        widgets = []
        search = self.search_field.text().strip().lower() if hasattr(self, 'search_field') else ""
        # On va filtrer les dossiers inexistants
        valid_library = []
        for entry in self.library:
            path = entry["path"]
            if not os.path.exists(path):
                continue  # Ignore les dossiers qui n'existent plus
            name = entry.get("alias", os.path.basename(path))  # Utilise l'alias s'il existe
            if not search or search in name.lower():
                thumb_path = ensure_folder_thumbnail(path)
                language = entry.get("language")
                if not thumb_path:
                    thumb_path = create_default_thumbnail() or "assets/images/manga_sample.png"
                chapters = count_chapters(path)
                vignette = ThumbnailWidget(thumb_path, name, path=path, language=language,
                                           count=chapters)
                def on_folder_selected(p=path):
                    debug(f"[DEBUG] Signal folder_selected émis avec : {p}")
                    self.folder_selected.emit(p)
                
                # Ajout case à cocher si mode sélection
                if self.selection_mode:
                    from PySide6.QtWidgets import QCheckBox
                    checkbox = QCheckBox()
                    checkbox.setChecked(path in self.selected_items)
                    checkbox.setStyleSheet("")
                    checkbox.setFixedSize(24, 24)
                    def on_state_changed(state, p=path):
                        if state:
                            self.selected_items.add(p)
                        else:
                            self.selected_items.discard(p)
                        if self.selected_items:
                            self.select_btn.setIcon(QIcon("assets/icons/trash-white.svg"))
                            self.select_btn.setToolTip("Supprimer la sélection")
                        else:
                            self.select_btn.setIcon(QIcon("assets/icons/check2-all-white.svg"))
                            self.select_btn.setToolTip("Sélectionner des dossiers")
                    checkbox.stateChanged.connect(on_state_changed)
                    vignette = ThumbnailWidget(thumb_path, name, path=path, checkbox=checkbox,
                                               language=language, count=chapters)
                    vignette.clicked.connect(on_folder_selected)
                
                # Connecter les signaux une seule fois
                vignette.clicked.connect(on_folder_selected)
                vignette.remove_requested.connect(self.remove_folder)
                vignette.alias_requested.connect(self.set_folder_alias)
                vignette.cover_requested.connect(self.set_folder_cover)
                vignette.language_requested.connect(self.set_folder_language)
                widgets.append(vignette)
            valid_library.append(entry)
        if len(valid_library) != len(self.library):
            self.library = valid_library
            self.save_library()
        debug("[DEBUG] Aucun fichier ou dossier supporté trouvé dans ce dossier.")
        self.grid_view.set_items(widgets)
        # Mettre à jour l'icône du bouton après le refresh
        if self.selection_mode:
            if self.selected_items:
                self.select_btn.setIcon(QIcon("assets/icons/trash-white.svg"))
                self.select_btn.setToolTip("Supprimer la sélection")
            else:
                self.select_btn.setIcon(QIcon("assets/icons/check2-all-white.svg"))
                self.select_btn.setToolTip("Sélectionner des fichiers")
        else:
            self.select_btn.setIcon(QIcon("assets/icons/check2-all-white.svg"))
            self.select_btn.setToolTip("Sélectionner des fichiers")
        self.select_btn.setChecked(self.selection_mode)
        count = len(valid_library)
        self.count_label.setText("Aucune collection" if count == 0
                                 else f"{count} collection{'s' if count > 1 else ''}")

    def remove_folder(self, folder_path):
        self.library = [d for d in self.library if d["path"] != folder_path]
        self.save_library()
        self.refresh_shelf()

    def set_folder_cover(self, folder_path):
        """Définit une couverture personnalisée pour un dossier."""
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir une image de couverture",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )

        if image_path and os.path.exists(image_path):
            thumb_dir = os.path.join(folder_path, '.thumbnails')
            try:
                os.makedirs(thumb_dir, exist_ok=True)
            except OSError as e:
                print(f"Impossible de créer le dossier de vignettes : {thumb_dir}. Erreur : {e}")
                raise e
            cover_path = os.path.join(thumb_dir, '_folder_thumb.png')

            try:
                # Copier l'image en conservant sa pleine résolution
                if not save_cover_thumbnail(QImage(image_path), cover_path):
                    raise ValueError(f"Image de couverture illisible : {image_path}")
                mark_cover_as_custom(cover_path)

                # Mettre à jour la date de modification pour éviter l'écrasement
                os.utime(cover_path, None)
                print(f"Nouvelle couverture définie pour {folder_path}")
                self.refresh_shelf()
            except Exception as e:
                print(f"Erreur lors de la définition de la couverture : {e}")

    def reload_manga_info(self, folder_path, entry):
        """Récupère la fiche du manga sous le nom courant, dans la bonne langue."""
        title = entry.get("alias") or os.path.basename(folder_path)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            refresh_manga_info(folder_path, title, entry.get("language"))
        finally:
            QApplication.restoreOverrideCursor()

    def has_description(self, folder_path, language):
        """Vrai si le synopsis est déjà en cache dans cette langue."""
        try:
            with open(os.path.join(folder_path, '.anilist.json'), 'r', encoding='utf-8') as f:
                info = json.load(f)
        except (OSError, ValueError):
            return False
        descriptions = info.get('descriptions')
        if not isinstance(descriptions, dict):
            return False
        return any(descriptions.get(code) for code in description_candidates(language)[:-1] or ("en",))

    def set_folder_language(self, folder_path, code):
        """Langue d'une collection : rangée dans la bibliothèque, comme l'alias."""
        for entry in self.library:
            if entry["path"] == folder_path:
                if code:
                    entry["language"] = code
                else:
                    entry.pop("language", None)
                self.save_library()
                # Un synopsis déjà en cache dans cette langue évite l'appel réseau.
                if code and not self.has_description(folder_path, code):
                    self.reload_manga_info(folder_path, entry)
                break
        self.refresh_shelf()

    def set_folder_alias(self, folder_path, current_name):
        """Définit un alias pour un dossier"""
        # Trouver l'entrée dans la bibliothèque
        entry = None
        for lib_entry in self.library:
            if lib_entry["path"] == folder_path:
                entry = lib_entry
                break
        if entry:
            # Ouvrir une boîte de dialogue pour saisir le nouvel alias
            new_alias, ok = QInputDialog.getText(
                self, 
                "Définir un alias", 
                f"Entrez le nouveau nom pour '{current_name}':",
                text=current_name
            )
            # Vérifier que l'utilisateur a cliqué sur OK et que le texte n'est pas vide
            if ok and new_alias and new_alias.strip():
                # Mettre à jour l'alias
                entry["alias"] = new_alias.strip()
                self.save_library()
                # Le synopsis est cherché sous ce nom : il doit suivre.
                self.reload_manga_info(folder_path, entry)
                # Optimisation : ne régénérer la vignette que si le dossier contient des fichiers supportés
                fichiers = [f for f in os.listdir(folder_path) if f.lower().endswith(ARCHIVE_EXTENSIONS)]
                if fichiers:
                    debug(f"[DEBUG] Régénération de la vignette pour {folder_path} après changement d'alias.")
                    generate_all_thumbnails_for_folder(folder_path)
                else:
                    debug(f"[DEBUG] Pas de fichiers supportés dans {folder_path}, pas de régénération de vignette.")
                # Vérification de la présence de .anilist.json
                anilist_file = os.path.join(folder_path, '.anilist.json')
                if not os.path.exists(anilist_file):
                    debug(f"[DEBUG] Attention : .anilist.json absent dans {folder_path} après changement d'alias.")
                self.refresh_shelf()

    def apply_sort(self, az, save=True):
        """Trie la bibliothèque et prépare le bouton pour l'ordre inverse."""
        self.library.sort(key=lambda d: d.get("alias", os.path.basename(d["path"])).lower(),
                          reverse=not az)
        icon = "sort-alpha-up-white.svg" if az else "sort-alpha-down-white.svg"
        self.sort_btn.setIcon(QIcon(resource_path(f"assets/icons/{icon}")))
        self.sort_btn.setToolTip("Trier Z-A" if az else "Trier A-Z")
        self.sort_az = not az
        if save:
            self.save_library()

    def toggle_sort(self):
        self.apply_sort(self.sort_az)
        self.refresh_shelf()

    def toggle_selection_mode(self):
        # Si on est en mode suppression (icône trash-white) et qu'il y a des éléments sélectionnés
        if self.selection_mode and self.selected_items:
            # Suppression directe des dossiers sélectionnés
            self.library = [d for d in self.library if d["path"] not in self.selected_items]
            self.save_library()
            self.selected_items.clear()
            self.selection_mode = False
            self.refresh_shelf()
            debug(f"[DEBUG] Dossiers supprimés : {self.selected_items}")
        else:
            self.selection_mode = not self.selection_mode
            if not self.selection_mode:
                self.selected_items.clear()
            self.refresh_shelf()
            debug(f"[DEBUG] Mode sélection : {self.selection_mode}")

def make_toolbar_btn(icon_path, tooltip, callback, checkable=False):
    """Bouton icône de la barre bibliothèque : plat, sans ombre, état actif en accent."""
    btn = QPushButton()
    btn.setIcon(QIcon(icon_path))
    btn.setIconSize(QSize(19, 19))
    btn.setFixedSize(HEADER_BTN_SIZE, HEADER_BTN_SIZE)
    btn.setCheckable(checkable)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(S.HEADER_ICON_BUTTON_STYLE)
    btn.setToolTip(tooltip)
    btn.clicked.connect(callback)
    return btn


def make_back_btn(callback):
    """Retour : détaché de la pilule, mais de la même matière."""
    btn = make_toolbar_btn(resource_path("assets/icons/arrow-left-white.png"),
                           "Retour", callback)
    btn.setFixedSize(HEADER_TOOLBAR_HEIGHT, HEADER_TOOLBAR_HEIGHT)
    btn.setStyleSheet(S.HEADER_BACK_BUTTON_STYLE)
    return btn


def make_toolbar_group(*buttons):
    """Pilule translucide qui réunit les actions d'un en-tête."""
    toolbar = QWidget()
    toolbar.setObjectName("headerToolbar")
    toolbar.setStyleSheet(S.HEADER_TOOLBAR_STYLE)
    toolbar.setFixedHeight(HEADER_TOOLBAR_HEIGHT)
    # Sans taille fixe, la pilule absorbe l'espace libre et les icônes se dispersent.
    toolbar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    row = QHBoxLayout(toolbar)
    row.setContentsMargins(4, 4, 4, 4)
    row.setSpacing(4)
    for button in buttons:
        row.addWidget(button)
    return toolbar


# =====================================================================================
# PAGE DOSSIER (Vignettes PDF)
# =====================================================================================
class FolderViewPage(QWidget):
    file_selected = Signal(str)  # Changé de pdf_selected à file_selected
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.folder_path = ""
        self.path_stack = []  # Pour l'historique de navigation
        self.grid_view = ResponsiveGridView()
        self.session_hidden_files = set()  # fichiers masqués pour la session
        self.selection_mode = False
        self.selected_items = set()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Nouveau header moderne avec overlay
        self.header_widget = RoundedHeaderWidget()
        self.header_widget.setFixedHeight(200)

        # Overlay sombre pour la lisibilité
        self.overlay = QWidget(self.header_widget)
        self.overlay.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0,0,0,140), stop:1 rgba(0,0,0,220)); border-radius: 18px;"
        )
        self.overlay.setGeometry(0, 0, self.header_widget.width(), self.header_widget.height())
        self.overlay.lower()

        def resize_overlay():
            self.overlay.setGeometry(0, 0, self.header_widget.width(), self.header_widget.height())
        self.header_widget.resizeEvent = lambda event: (resize_overlay(), QWidget.resizeEvent(self.header_widget, event))

        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(32, 24, 32, 24)
        header_layout.setSpacing(0)

        # Colonne 1 : bloc vertical titre + chemin
        left_col = QVBoxLayout()
        left_col.setSpacing(0)
        left_col.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Inter", 40, QFont.Weight.Bold))
        self.title_label.setStyleSheet(
            "color: #fff; text-shadow: 2px 2px 12px #000; background: transparent; margin: 0; padding: 0;"
        )
        self.path_label = QLabel()
        self.path_label.setFont(QFont("Inter", 15))
        self.path_label.setStyleSheet(
            "color: #e6e6e6; text-shadow: 1px 1px 8px #000; background: transparent; margin: 0; padding: 0;"
        )
        left_col.addWidget(self.title_label)
        left_col.addWidget(self.path_label)
        left_col.addStretch(1)
        header_layout.addLayout(left_col, 1)

        # Colonne 2 : retour détaché, puis les actions réunies dans la pilule
        right_col = QHBoxLayout()
        right_col.setSpacing(14)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.addWidget(make_back_btn(self.navigate_back))

        # Bouton unique de sélection/suppression
        self.select_btn = make_toolbar_btn(resource_path("assets/icons/check2-all-white.svg"),
                                           "Sélectionner des fichiers",
                                           self.on_select_btn_clicked, checkable=True)
        right_col.addWidget(make_toolbar_group(
            make_toolbar_btn(resource_path("assets/icons/palette-white.svg"),
                             "Changer la bannière", self.set_header_background),
            make_toolbar_btn(resource_path("assets/icons/arrow-clockwise-white.svg"),
                             "Rafraîchir", self.refresh_folder),
            self.select_btn,
        ))
        header_layout.addLayout(right_col)

        layout.addWidget(self.header_widget)

        # --- Layout central en deux colonnes (inchangé) ---
        central_layout = QHBoxLayout()
        central_layout.setSpacing(30)

        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        self.anilist_desc_label = QLabel()
        # Les synopsis AniList et MangaDex contiennent du HTML (<br>, <i>) :
        # sans cela les balises s'affichaient telles quelles dans le texte.
        self.anilist_desc_label.setTextFormat(Qt.TextFormat.RichText)
        self.anilist_desc_label.setOpenExternalLinks(True)
        self.anilist_desc_label.setWordWrap(True)
        self.anilist_desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.anilist_desc_label.setStyleSheet(S.FOLDER_DESC_STYLE)
        self.anilist_desc_label.setMaximumWidth(400)
        left_col.addWidget(self.anilist_desc_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.anilist_tags_widget = QWidget()
        self.anilist_tags_layout = FlowLayout(self.anilist_tags_widget, margin=0, spacing=8)
        left_col.addWidget(self.anilist_tags_widget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        left_col.addStretch(1)

        right_col = QVBoxLayout()
        right_col.addWidget(self.grid_view)

        central_layout.addLayout(left_col, 1)
        central_layout.addLayout(right_col, 3)

        layout.addLayout(central_layout)

    def on_select_btn_clicked(self):
        if self.select_btn.icon().name() == "trash-white.svg" or (self.selection_mode and self.selected_items):
            # Supprimer la sélection
            for p in list(self.selected_items):
                base_name = os.path.basename(p)
                self.session_hidden_files.add(base_name)
            self.selected_items.clear()
            self.selection_mode = False
            self.refresh_view()
        else:
            # Activer/désactiver le mode sélection
            self.selection_mode = not self.selection_mode
            if not self.selection_mode:
                self.selected_items.clear()
            self.refresh_view()

    def navigate_back(self):
        """Gère la navigation retour dans les dossiers."""
        if len(self.path_stack) > 1:
            self.path_stack.pop()
            previous_path = self.path_stack[-1]
            self.set_folder(previous_path, is_main_entry=False)
        else:
            self.back_clicked.emit()

    def set_folder(self, folder_path, is_main_entry=True):
        debug(f"[DEBUG] Appel de set_folder avec folder_path = '{folder_path}'")
        if is_main_entry:
            self.path_stack = [folder_path]
        self.folder_path = folder_path
        # Chercher l'alias dans la bibliothèque uniquement pour le dossier racine
        alias = None
        language = None
        if len(self.path_stack) <= 1:
            try:
                if os.path.exists(LIBRARY_FILE):
                    with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                        library = json.load(f)
                    for entry in library:
                        if entry["path"] == folder_path:
                            alias = entry.get("alias")
                            language = entry.get("language")
                            break
            except Exception as e:
                print(f"Erreur lecture alias: {e}")
        # Afficher l'alias si disponible, sinon le nom du dossier
        self.title_label.setText(alias if alias else os.path.basename(folder_path))
        self.path_label.setText(folder_path)
        # Charger l'image de fond du header
        self.load_header_background()
        # Charger le descriptif et les tags AniList
        anilist_file = os.path.join(folder_path, '.anilist.json')
        desc = ''
        tags_list = []
        if os.path.exists(anilist_file):
            try:
                with open(anilist_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                debug(f"[DEBUG] .anilist.json trouvé : {anilist_file}")
                debug(f"[DEBUG] Contenu .anilist.json : {info}")
                desc = pick_description(info, language)
                tags_list = info.get('tags', [])
            except Exception as e:
                debug(f"[DEBUG set_folder] Erreur lecture anilist.json: {e}")
        else:
            debug(f"[DEBUG] .anilist.json absent dans : {folder_path}")
        self.anilist_desc_label.setText(desc)
        # Affichage des tags façon 'pills'
        # Nettoyer l'ancien contenu
        for i in reversed(range(self.anilist_tags_layout.count())):
            item = self.anilist_tags_layout.itemAt(i)
            if item is not None and item.widget() is not None:
                item.widget().setParent(None)
        for tag in tags_list:
            tag_label = QLabel(tag)
            tag_label.setStyleSheet(S.FOLDER_TAG_STYLE)
            self.anilist_tags_layout.addWidget(tag_label)
        self.refresh_view()

    def load_header_background(self):
        """Charge l'image de fond du header"""
        try:
            # 1. Chercher une bannière AniList téléchargée
            banner_path = os.path.join(self.folder_path, '.thumbnails', '_header_banner.png')
            if os.path.exists(banner_path):
                debug(f"[AniList] Bannière trouvée : {banner_path}")
                self.header_widget.set_background_image(banner_path)
                self.title_label.setStyleSheet(S.PAGE_TITLE_STYLE)
                self.path_label.setStyleSheet(S.FOLDER_PATH_STYLE)
                return
            # 2. Chercher une couverture AniList dans .anilist.json (fallback)
            anilist_file = os.path.join(self.folder_path, '.anilist.json')
            anilist_cover_path = None
            if os.path.exists(anilist_file):
                try:
                    import json
                    with open(anilist_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    cover_url = info.get('cover')
                    if cover_url:
                        thumb_dir = os.path.join(self.folder_path, '.thumbnails')
                        anilist_cover_path = os.path.join(thumb_dir, '_folder_thumb.png')
                        if os.path.exists(anilist_cover_path):
                            print(f"[AniList] Couverture trouvée : {anilist_cover_path}")
                            self.header_widget.set_background_image(anilist_cover_path)
                            self.title_label.setStyleSheet(S.PAGE_TITLE_STYLE)
                            self.path_label.setStyleSheet(S.FOLDER_PATH_STYLE)
                            return
                except Exception as e:
                    print(f"[AniList] Erreur lecture couverture : {e}")
            # 3. Sinon, image personnalisée
            custom_bg_path = os.path.join(self.folder_path, "_header_bg.png")
            debug(f"Recherche de l'image de fond personnalisée: {custom_bg_path}")
            if os.path.exists(custom_bg_path):
                print(f"Image personnalisée trouvée: {custom_bg_path}")
                self.header_widget.set_background_image(custom_bg_path)
                print("Image personnalisée appliquée au header")
                self.title_label.setStyleSheet(S.PAGE_TITLE_STYLE)
                self.path_label.setStyleSheet(S.FOLDER_PATH_STYLE)
            else:
                print(f"Image personnalisée non trouvée, utilisation de l'image par défaut")
                default_bg_path = "assets/images/header.png"
                if os.path.exists(default_bg_path):
                    self.header_widget.set_background_image(default_bg_path)
                    debug("Image par défaut appliquée au header")
                    self.title_label.setStyleSheet(S.PAGE_TITLE_STYLE)
                    self.path_label.setStyleSheet(S.FOLDER_PATH_STYLE)
                else:
                    print(f"Image par défaut non trouvée, utilisation du style par défaut (pas d'image)")
                    self.header_widget.set_background_image(None)
                    self.title_label.setStyleSheet(S.PAGE_TITLE_STYLE)
                    self.path_label.setStyleSheet("""
                        color: #666;
                        background: transparent;
                        border: none;
                        outline: none;
                        text-shadow: none;
                        box-shadow: none;
                        margin-top: 0px;
                    """)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image de fond du header: {e}")
            self.header_widget.set_background_image(None)
            self.title_label.setStyleSheet(S.PAGE_TITLE_STYLE)
            self.path_label.setStyleSheet("""
                color: #666;
                background: transparent;
                border: none;
                outline: none;
                text-shadow: none;
                box-shadow: none;
                margin-top: 0px;
            """)

    def set_header_background(self):
        """Permet à l'utilisateur de choisir une image de fond pour le header"""
        try:
            image_path, _ = QFileDialog.getOpenFileName(
                self,
                "Choisir une image de fond pour le header",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp)"
            )

            if image_path and os.path.exists(image_path):
                # Copier l'image dans le dossier avec le nom _header_bg.png
                custom_bg_path = os.path.join(self.folder_path, "_header_bg.png")
                
                try:
                    # Copier et redimensionner l'image pour qu'elle s'adapte au header
                    pixmap = QPixmap(image_path)
                    # Redimensionner à une résolution plus élevée pour une meilleure qualité
                    # Utiliser une largeur plus grande pour éviter la pixélisation
                    target_width = max(self.header_widget.width() * 2, 800)  # Minimum 800px de large
                    target_height = 80 * 2  # 160px de hauteur pour une meilleure qualité
                    
                    scaled_pixmap = pixmap.scaled(
                        target_width, target_height,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    scaled_pixmap.save(custom_bg_path, "PNG", quality=95)  # Qualité PNG maximale
                    
                    # Recharger l'image de fond
                    self.load_header_background()
                    
                    print(f"Nouvelle image de fond définie pour le header: {custom_bg_path}")
                except Exception as e:
                    print(f"Erreur lors de la définition de l'image de fond : {e}")
        except Exception as e:
            print(f"Erreur lors de la sélection de l'image de fond : {e}")

    def refresh_view(self):
        widgets = []
        try:
            all_items = sorted(os.listdir(self.folder_path))
            debug(f"[DEBUG] Contenu du dossier {self.folder_path} : {all_items}")
        except FileNotFoundError:
            self.grid_view.set_items([])
            debug(f"[DEBUG] Dossier introuvable : {self.folder_path}")
            return
        # Lire les alias du dossier courant
        import json
        alias_file = os.path.join(self.folder_path, '.alias.json')
        alias_map = {}
        if os.path.exists(alias_file):
            try:
                with open(alias_file, 'r', encoding='utf-8') as f:
                    alias_map = json.load(f)
            except Exception as e:
                alias_map = {}
        else:
            alias_map = {}
        fichiers_supportes = []
        languages = load_language_map(self.folder_path)
        for item_name in all_items:
            if item_name.startswith('.'):
                continue
            if item_name in self.session_hidden_files:
                continue
            item_path = os.path.join(self.folder_path, item_name)
            widget = None
            display_name = alias_map.get(item_name)
            if display_name is None:
                display_name = item_name
                # Un alias reste affiché tel quel : c'est un nom voulu, pas un
                # nom de fichier.
                if (settings.get("hide_extensions")
                        and item_name.lower().endswith(ARCHIVE_EXTENSIONS)):
                    display_name = os.path.splitext(item_name)[0]
            # Ajout case à cocher si mode sélection
            if self.selection_mode:
                from PySide6.QtWidgets import QCheckBox
                checkbox = QCheckBox()
                checkbox.setChecked(item_path in self.selected_items)
                checkbox.setStyleSheet("")
                checkbox.setFixedSize(24, 24)
                def on_state_changed(state, p=item_path):
                    if state:
                        self.selected_items.add(p)
                    else:
                        self.selected_items.discard(p)
                    # Mise à jour dynamique du bouton select_btn
                    if self.selected_items:
                        self.select_btn.setIcon(QIcon("assets/icons/trash-white.svg"))
                        self.select_btn.setToolTip("Supprimer la sélection")
                    else:
                        self.select_btn.setIcon(QIcon("assets/icons/check2-all-white.svg"))
                        self.select_btn.setToolTip("Sélectionner des fichiers")
                checkbox.stateChanged.connect(on_state_changed)
            else:
                checkbox = None
            # Cas 1: L'élément est un dossier
            if os.path.isdir(item_path):
                fichiers_supportes.append(item_name)
                thumb_path = ensure_folder_thumbnail(item_path)
                if not thumb_path:
                    thumb_path = (create_default_thumbnail() or 
                                  "assets/images/manga_sample.png")
                widget = ThumbnailWidget(
                    thumb_path, display_name, path=item_path, show_menu=True, checkbox=checkbox,
                    language=languages.get(item_name), count=count_chapters(item_path)
                )
                widget.clicked.connect(
                    functools.partial(self.on_item_clicked, item_path)
                )
                widget.alias_requested.connect(self.set_item_alias)
                widget.remove_requested.connect(self.remove_item)
                widget.language_requested.connect(self.set_item_language)
            # Cas 2: L'élément est un fichier supporté
            elif item_name.lower().endswith(ARCHIVE_EXTENSIONS):
                fichiers_supportes.append(item_name)
                base_name = os.path.splitext(item_name)[0]
                thumb_path = get_thumbnail_path(item_path)
                if not thumb_path:
                    thumb_path = (create_default_thumbnail() or 
                                  "assets/images/manga_sample.png")
                widget = ThumbnailWidget(
                    thumb_path, display_name, path=item_path, show_menu=True, checkbox=checkbox,
                    language=languages.get(item_name)
                )
                widget.clicked.connect(
                    functools.partial(self.on_item_clicked, item_path)
                )
                widget.alias_requested.connect(self.set_item_alias)
                widget.remove_requested.connect(self.remove_item)
                widget.language_requested.connect(self.set_item_language)
            if widget:
                widgets.append(widget)
        debug(f"[DEBUG] {len(fichiers_supportes)} éléments supportés trouvés")
        if not widgets:
            debug("[DEBUG] Aucun fichier ou dossier supporté trouvé dans ce dossier.")
        self.grid_view.set_items(widgets)
        # Mettre à jour l'icône du bouton après le refresh
        if self.selection_mode:
            if self.selected_items:
                self.select_btn.setIcon(QIcon("assets/icons/trash-white.svg"))
                self.select_btn.setToolTip("Supprimer la sélection")
            else:
                self.select_btn.setIcon(QIcon("assets/icons/check2-all-white.svg"))
                self.select_btn.setToolTip("Sélectionner des fichiers")
        else:
            self.select_btn.setIcon(QIcon("assets/icons/check2-all-white.svg"))
            self.select_btn.setToolTip("Sélectionner des fichiers")
        self.select_btn.setChecked(self.selection_mode)

    def on_item_clicked(self, path):
        """Gère le clic sur un élément dans la vue de dossier."""
        if os.path.isdir(path):
            try:
                files_in_folder = os.listdir(path)
                has_images = any(
                    f.lower().endswith(IMAGE_EXTENSIONS) for f in files_in_folder
                )
                has_archives = any(
                    f.lower().endswith(ARCHIVE_EXTENSIONS) for f in files_in_folder
                )
                has_subdirs = any(
                    os.path.isdir(os.path.join(path, f))
                    for f in files_in_folder
                    if f != '.thumbnails'
                )

                if has_images and not has_archives and not has_subdirs:
                    self.file_selected.emit(path)
                else:
                    self.path_stack.append(path)
                    self.set_folder(path, is_main_entry=False)
            except Exception as e:
                print(f"Erreur lors de l'accès au sous-dossier {path}: {e}")
        else:  # C'est un fichier
            self.file_selected.emit(path)

    def remove_item(self, path):
        """Masque un fichier (ou dossier) de la vue pour la session courante uniquement."""
        base_name = os.path.basename(path)
        self.session_hidden_files.add(base_name)
        self.refresh_view()

    def set_item_language(self, path, code):
        """Langue d'un élément du dossier, rangée à côté des alias."""
        save_item_language(path, code)
        self.refresh_view()

    def set_item_alias(self, path, current_name):
        """Renomme un fichier ou dossier (ajoute un alias dans un fichier caché .alias.json du dossier parent)"""
        import json
        from PySide6.QtWidgets import QInputDialog
        parent_dir = os.path.dirname(path)
        alias_file = os.path.join(parent_dir, '.alias.json')
        if os.path.exists(alias_file):
            try:
                with open(alias_file, 'r', encoding='utf-8') as f:
                    alias_map = json.load(f)
            except Exception:
                alias_map = {}
        else:
            alias_map = {}
        alias, ok = QInputDialog.getText(self, "Set alias", "Nouveau nom :", text=current_name)
        # Vérifier que l'utilisateur a cliqué sur OK et que le texte n'est pas vide
        if ok and alias and alias.strip():
            alias_map[os.path.basename(path)] = alias.strip()
            try:
                with open(alias_file, 'w', encoding='utf-8') as f:
                    json.dump(alias_map, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Erreur lors de l'écriture de l'alias : {e}")
        self.refresh_view()

    def refresh_folder(self):
        """Actualise le dossier en régénérant les vignettes et en affichant les nouveaux fichiers. Réinitialise aussi le masquage temporaire."""
        self.session_hidden_files = set()  # Réinitialise le masquage uniquement ici
        if hasattr(self, 'folder_path') and self.folder_path:
            # Afficher un popup de progression
            progress_dialog = ProgressDialog(self)
            progress_dialog.setWindowTitle("Actualisation du dossier")
            progress_dialog.show()
            def progress_callback(msg, value=None):
                progress_dialog.update_message(msg, value)
            # Régénérer toutes les vignettes du dossier
            generate_all_thumbnails_for_folder(self.folder_path, progress_callback)
            progress_dialog.close()
            # Actualiser l'affichage
            self.refresh_view()

    def resizeEvent(self, event):
        # Rendre le descriptif et les tags responsives
        if hasattr(self, 'anilist_desc_label'):
            margin = 40  # marge à gauche/droite
            new_width = max(200, self.width() - margin)
            self.anilist_desc_label.setMaximumWidth(new_width)
        if hasattr(self, 'anilist_tags_widget'):
            self.anilist_tags_widget.setMaximumWidth(self.width() - margin)
        super().resizeEvent(event)

    def toggle_selection_mode(self):
        if self.selection_mode and self.selected_items:
            # Suppression directe des fichiers/dossiers sélectionnés (masquage session)
            for p in list(self.selected_items):
                base_name = os.path.basename(p)
                self.session_hidden_files.add(base_name)
            self.selected_items.clear()
            self.selection_mode = False
            self.refresh_view()
            debug(f"[DEBUG] Fichiers/dossiers masqués : {self.session_hidden_files}")
        else:
            self.selection_mode = not self.selection_mode
            if not self.selection_mode:
                self.selected_items.clear()
            self.refresh_view()
            debug(f"[DEBUG] Mode sélection (vue dossier) : {self.selection_mode}")

# =====================================================================================
# LECTEUR DE FICHIERS (PDF et CBZ)
# =====================================================================================
class PageView(QScrollArea):
    """Zone de lecture : molette pour zoomer, clic gauche maintenu pour déplacer."""
    zoom_requested = Signal(float, QPoint)   # facteur multiplicatif, point vise

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pan_anchor = None
        self._pan_scroll = None
        # La bordure vient de la feuille de style : elle remplace le cadre par
        # defaut, qui detonnait avec les coins arrondis de la barre.
        self.setObjectName("readerView")
        self.setStyleSheet(S.READER_VIEW_STYLE)
        # Le clic ne doit pas voler le focus clavier à la page du lecteur.
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for bar in (self.horizontalScrollBar(), self.verticalScrollBar()):
            bar.rangeChanged.connect(lambda *_: self.update_cursor())
        self.update_cursor()

    def _scrollable(self):
        return (self.horizontalScrollBar().maximum() > 0
                or self.verticalScrollBar().maximum() > 0)

    def update_cursor(self):
        """Main ouverte seulement quand il y a de quoi se déplacer."""
        if self._pan_anchor is not None:
            return
        self.viewport().setCursor(Qt.CursorShape.OpenHandCursor if self._scrollable()
                                  else Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event):
        steps = event.angleDelta().y()
        if not steps:
            super().wheelEvent(event)
            return
        if settings.get("invert_wheel"):
            steps = -steps
        step = settings.wheel_zoom_factor()
        factor = step if steps > 0 else 1.0 / step
        self.zoom_requested.emit(factor, event.position().toPoint())
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._scrollable():
            self._pan_anchor = event.position().toPoint()
            self._pan_scroll = QPoint(self.horizontalScrollBar().value(),
                                      self.verticalScrollBar().value())
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_anchor is None:
            super().mouseMoveEvent(event)
            return
        moved = event.position().toPoint() - self._pan_anchor
        self.horizontalScrollBar().setValue(self._pan_scroll.x() - moved.x())
        self.verticalScrollBar().setValue(self._pan_scroll.y() - moved.y())
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._pan_anchor is not None and event.button() == Qt.MouseButton.LeftButton:
            self._pan_anchor = None
            self.update_cursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)


def make_reader_btn(icon_name, tooltip, callback):
    """Bouton icône de la barre du lecteur : plat, l'accent ne sort qu'au survol."""
    btn = QPushButton()
    btn.setIcon(QIcon(themed_icon(icon_name)))
    btn.setIconSize(QSize(17, 17))
    btn.setFixedSize(READER_BTN_SIZE, READER_BTN_SIZE)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(S.READER_ICON_BUTTON_STYLE)
    btn.setToolTip(tooltip)
    btn.clicked.connect(callback)
    return btn


def make_reader_group(*widgets):
    """Pilule claire qui réunit une famille d'actions du lecteur."""
    group = QWidget()
    group.setObjectName("readerGroup")
    group.setStyleSheet(S.READER_GROUP_STYLE)
    group.setFixedHeight(READER_GROUP_HEIGHT)
    row = QHBoxLayout(group)
    row.setContentsMargins(4, 0, 4, 0)
    row.setSpacing(2)
    for widget in widgets:
        row.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
    return group


class FileViewerPage(QWidget):
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.doc = None
        self.zip_file = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_factor = 1.0
        # Tant qu'il est vrai, chaque page est ajustée à la hauteur de la fenêtre ;
        # le premier zoom manuel le désactive et le facteur choisi est conservé.
        self.zoom_is_auto = True
        self.file_path = None
        self.file_type = None  # 'pdf' ou 'cbz'
        self.cbz_images = []  # Liste des images pour les CBZ
        self.rar_file = None
        # Sans politique de focus, le setFocus() de showEvent est sans effet et
        # aucune touche n'arrive jusqu'à keyPressEvent.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setup_ui()
        
        # Timer pour recalculer le zoom une fois la fenêtre affichée
        self.zoom_timer = QTimer()
        self.zoom_timer.setSingleShot(True)
        self.zoom_timer.timeout.connect(self.recalculate_zoom)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Barre du lecteur : retour à gauche, navigation au centre, zoom à
        # droite. Les raccourcis clavier sont rappelés dans les infobulles :
        # c'est le seul endroit où on peut les apprendre.
        bar = QWidget()
        bar.setObjectName("readerBar")
        bar.setStyleSheet(S.READER_BAR_STYLE)
        bar.setFixedHeight(READER_BAR_HEIGHT)
        nav_layout = QHBoxLayout(bar)
        nav_layout.setContentsMargins(10, 0, 10, 0)
        nav_layout.setSpacing(10)

        self.back_btn = make_reader_btn("arrow-back", "Retour (Échap)",
                                        self.back_clicked.emit)
        self.back_btn.setFixedSize(READER_GROUP_HEIGHT, READER_GROUP_HEIGHT)
        self.back_btn.setStyleSheet(S.READER_BACK_BUTTON_STYLE)
        self.back_btn.setIconSize(QSize(19, 19))

        self.prev_btn = make_reader_btn("chevron-left", "Page précédente (←)",
                                        self.previous_page)
        self.next_btn = make_reader_btn("chevron-right", "Page suivante (→)",
                                        self.next_page)
        self.page_label = QLabel()
        self.page_label.setStyleSheet(S.READER_PAGE_LABEL_STYLE)
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Largeur figée sur le pire des cas : sans cela la pilule se dilaterait
        # au passage de 9 à 10, puis de 99 à 100.
        self.page_label.setMinimumWidth(96)

        self.zoom_out_btn = make_reader_btn("zoom-out", "Zoom arrière (-)", self.zoom_out)
        self.zoom_in_btn = make_reader_btn("zoom-in", "Zoom avant (+)", self.zoom_in)
        # Le niveau de zoom est aussi le bouton qui rend la page à la fenêtre :
        # une fois zoomé à la main, plus rien ne ramenait à l'ajustement.
        self.zoom_label = QPushButton()
        self.zoom_label.setFixedHeight(30)
        self.zoom_label.setMinimumWidth(58)
        self.zoom_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_label.setStyleSheet(S.READER_ZOOM_LABEL_STYLE)
        self.zoom_label.setToolTip("Ajuster la page à la fenêtre")
        self.zoom_label.clicked.connect(self.fit_to_window)

        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(make_reader_group(self.prev_btn, self.page_label,
                                               self.next_btn))
        nav_layout.addStretch()
        nav_layout.addWidget(make_reader_group(self.zoom_out_btn, self.zoom_label,
                                               self.zoom_in_btn))

        self.update_page_label()

        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Le label couvre toute la zone : sans cela il intercepte le glisser.
        self.pdf_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        self.scroll_area = PageView()
        self.scroll_area.setWidget(self.pdf_label)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.zoom_requested.connect(self.zoom_at)

        # Boutons pilotés à la souris : ils ne doivent pas capter le clavier.
        for button in (self.back_btn, self.prev_btn, self.next_btn,
                       self.zoom_in_btn, self.zoom_out_btn, self.zoom_label):
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(bar)
        layout.addWidget(self.scroll_area)

    def calculate_optimal_zoom(self, page=None, image=None):
        """Calcule le facteur de zoom optimal pour afficher la page complète à la hauteur de la fenêtre"""
        # Obtenir la hauteur disponible de la fenêtre (en tenant compte de la barre de navigation)
        available_height = self.scroll_area.height() - 40  # 40px de marge pour la navigation
        
        if available_height <= 0:
            return 1.0
        
        if self.file_type == 'pdf' and page:
            # Pour les PDF
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
        elif (self.file_type == 'cbz' or self.file_type == 'image_folder') and image:
            # Pour les CBZ et dossiers d'images
            page_width = image.width()
            page_height = image.height()
        else:
            return 1.0
        
        # Calculer le facteur de zoom pour que la page s'adapte à la hauteur
        zoom_factor = available_height / page_height
        
        # Limiter le zoom entre 0.2 et 3.0 pour éviter les problèmes d'affichage
        return max(0.2, min(3.0, zoom_factor))

    def recalculate_zoom(self):
        """Re-ajuste la page après un redimensionnement de la fenêtre."""
        if self.total_pages > 0 and self.zoom_is_auto:
            self.display_page(self.current_page)

    def load_file(self, path):
        try:
            self.file_path = path
            if os.path.isdir(path):
                self.file_type = 'image_folder'
                image_files = [os.path.join(path, f) for f in os.listdir(path)
                               if f.lower().endswith(IMAGE_EXTENSIONS)]
                image_files.sort()
                self.cbz_images = image_files
                self.total_pages = len(self.cbz_images)
                self.doc = None
                self.zip_file = None
                self.rar_file = None
            elif path.lower().endswith('.pdf'):
                self.file_type = 'pdf'
                self.doc = fitz.open(path)
                self.total_pages = len(self.doc)
                self.zip_file = None
                self.rar_file = None
            elif path.lower().endswith('.cbz') or path.lower().endswith('.zip'):
                self.file_type = 'cbz'
                self.zip_file = zipfile.ZipFile(path, 'r')
                image_files = [f for f in self.zip_file.namelist() 
                              if f.lower().endswith(IMAGE_EXTENSIONS)]
                image_files.sort()
                self.cbz_images = image_files
                self.total_pages = len(self.cbz_images)
                self.doc = None
                self.rar_file = None
            elif path.lower().endswith('.rar'):
                self.file_type = 'rar'
                self.rar_file = rarfile.RarFile(path, 'r')
                image_files = [f for f in self.rar_file.namelist() 
                              if f.lower().endswith(IMAGE_EXTENSIONS)]
                image_files.sort()
                self.cbz_images = image_files
                self.total_pages = len(self.cbz_images)
                self.doc = None
                self.zip_file = None
            else:
                self.file_type = None
                self.doc = None
                self.zip_file = None
                self.rar_file = None
            # Nouveau fichier : on repart sur l'ajustement automatique
            self.zoom_is_auto = True
            self.display_page(0)
            # Programmer un recalcul du zoom après un court délai
            self.zoom_timer.start(100)  # 100ms de délai
        except Exception as e:
            self.pdf_label.setText(f"Erreur lors de l'ouverture du fichier: {e}")

    def showEvent(self, event):
        """Appelé quand la page devient visible"""
        super().showEvent(event)
        # Recalculer le zoom une fois que la page est affichée
        if ((self.doc and self.file_type == 'pdf') or 
            (self.zip_file and self.file_type == 'cbz') or 
            (self.rar_file and self.file_type == 'rar') or
            (self.file_type == 'image_folder')):
            self.zoom_timer.start(50)  # Délai plus court pour l'affichage
        # Donner le focus à cette page pour recevoir les événements clavier
        self.setFocus()

    def display_page(self, page_num):
        if not self.doc and not self.zip_file and not hasattr(self, 'rar_file') and self.file_type != 'image_folder':
            return
        self.current_page = page_num
        if self.file_type == 'pdf' and self.doc:
            if not (0 <= page_num < self.total_pages):
                return
            page = self.doc[page_num]
            if self.zoom_is_auto:
                self.zoom_factor = self.calculate_optimal_zoom(page=page)
            mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=mat)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            self.pdf_label.setPixmap(QPixmap.fromImage(img))
        elif self.file_type == 'image_folder':
            if not (0 <= page_num < self.total_pages):
                return
            image_path = self.cbz_images[page_num]
            qimage = QImage(image_path)
            if not qimage.isNull():
                self.pdf_label.setPixmap(self.scaled_page(qimage))
            else:
                self.pdf_label.setText(f"Impossible de charger l'image:\n{os.path.basename(image_path)}")
        elif self.file_type == 'cbz' and self.zip_file:
            if not (0 <= page_num < self.total_pages):
                return
            image_name = self.cbz_images[page_num]
            with self.zip_file.open(image_name) as image_file:
                image_data = image_file.read()
                qimage = QImage()
                if qimage.loadFromData(image_data):
                    self.pdf_label.setPixmap(self.scaled_page(qimage))
        elif self.file_type == 'rar' and hasattr(self, 'rar_file') and self.rar_file:
            if not (0 <= page_num < self.total_pages):
                return
            image_name = self.cbz_images[page_num]
            with self.rar_file.open(image_name) as image_file:
                image_data = image_file.read()
                qimage = QImage()
                if qimage.loadFromData(image_data):
                    self.pdf_label.setPixmap(self.scaled_page(qimage))
        self.update_page_label()

    def update_page_label(self):
        """Compteur, niveau de zoom et boutons de bout de course."""
        if self.total_pages:
            page, total = f"{self.current_page + 1}", f"{self.total_pages}"
        else:
            page, total = "-", "-"
        # La page courante ressort, le total reste en retrait : c'est le premier
        # chiffre que l'oeil vient chercher.
        self.page_label.setText(
            f'<span style="font-weight:bold;">{page}</span>'
            f'<span style="color:{theme_color("text_soft")};"> / {total}</span>')
        self.zoom_label.setText(f"{round(self.zoom_factor * 100)} %")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < self.total_pages - 1)

    def fit_to_window(self):
        """Rend la main à l'ajustement automatique, après un zoom manuel."""
        if self.total_pages:
            self.zoom_is_auto = True
            self.display_page(self.current_page)

    def scaled_page(self, qimage):
        """Image de page au zoom courant, ajustée à la fenêtre en mode automatique."""
        if self.zoom_is_auto:
            self.zoom_factor = self.calculate_optimal_zoom(image=qimage)
        return QPixmap.fromImage(qimage).scaled(
            max(1, int(qimage.width() * self.zoom_factor)),
            max(1, int(qimage.height() * self.zoom_factor)),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

    def zoom_at(self, factor, anchor):
        """Zoom multiplicatif gardant fixe le point de la page sous le curseur."""
        previous = self.zoom_factor
        self.zoom_factor = max(VIEWER_ZOOM_MIN, min(VIEWER_ZOOM_MAX, previous * factor))
        if abs(self.zoom_factor - previous) < 1e-6:
            return
        self.zoom_is_auto = False
        h = self.scroll_area.horizontalScrollBar()
        v = self.scroll_area.verticalScrollBar()
        target = QPoint(h.value() + anchor.x(), v.value() + anchor.y())
        ratio = self.zoom_factor / previous
        self.display_page(self.current_page)
        # Les barres n'ont leur nouvelle plage qu'après la mise en page : on
        # repositionne au tour de boucle suivant, sinon la valeur est écrêtée.
        QTimer.singleShot(0, lambda: (
            h.setValue(round(target.x() * ratio) - anchor.x()),
            v.setValue(round(target.y() * ratio) - anchor.y())))

    def go_to_page(self, page_num):
        """Changement de page demande par l'utilisateur.

        Le reglage « Conserver le zoom » decide si l'on repart de l'ajustement
        automatique ou si l'on garde le facteur choisi a la main.
        """
        if not settings.get("keep_zoom_between_pages"):
            self.zoom_is_auto = True
        self.display_page(page_num)

    def next_page(self):
        self.go_to_page(self.current_page + 1)

    def previous_page(self):
        self.go_to_page(self.current_page - 1)
        
    def zoom_in(self):
        self.zoom_is_auto = False
        self.zoom_factor = min(self.zoom_factor * 1.2, VIEWER_ZOOM_MAX)
        self.display_page(self.current_page)
        
    def zoom_out(self):
        self.zoom_is_auto = False
        self.zoom_factor = max(self.zoom_factor / 1.2, VIEWER_ZOOM_MIN)
        self.display_page(self.current_page)

    def keyPressEvent(self, event):
        """Gestion des touches clavier pour la navigation"""
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up, Qt.Key.Key_PageUp):
            # Flèche gauche/haut ou Page précédente : page précédente
            if self.current_page > 0:
                self.previous_page()
        elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_PageDown):
            # Flèche droite/bas ou Page suivante : page suivante
            if self.current_page < self.total_pages - 1:
                self.next_page()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            # Touche + ou = : zoom avant
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            # Touche - : zoom arrière
            self.zoom_out()
        elif event.key() == Qt.Key.Key_Home:
            # Touche Home : première page
            self.go_to_page(0)
        elif event.key() == Qt.Key.Key_End:
            # Touche End : dernière page
            self.go_to_page(self.total_pages - 1)
        elif event.key() == Qt.Key.Key_Escape:
            # Touche Échap : retour
            self.back_clicked.emit()
        else:
            # Pour les autres touches, appeler la méthode parent
            super().keyPressEvent(event)

    def close_file(self):
        """Ferme proprement les fichiers ouverts"""
        if self.doc:
            self.doc.close()
            self.doc = None
        if self.zip_file:
            self.zip_file.close()
            self.zip_file = None
        if hasattr(self, 'rar_file') and self.rar_file:
            self.rar_file.close()
            self.rar_file = None

    def closeEvent(self, event):
        """Appelé quand la fenêtre se ferme"""
        self.close_file()
        super().closeEvent(event)



# =====================================================================================
# PAGE CHAPITRES MANGA
# =====================================================================================
class MangaChaptersPage(QWidget):
    chapter_selected = Signal(str, str)  # chapter_id, chapter_title
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.manga_id = ""
        self.manga_title = ""
        self.chapters = []
        self.grid_view = ResponsiveGridView()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_widget = RoundedHeaderWidget()
        header_widget.radius = HEADER_RADIUS
        header_widget.setFixedHeight(HEADER_HEIGHT)
        header_widget.set_background_image(resource_path('assets/images/header.png'))
        header_widget.set_scrim()

        header = QHBoxLayout(header_widget)
        header.setContentsMargins(20, 20, 20, 20)

        # Titre du manga
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        self.title_label.setStyleSheet(S.PAGE_TITLE_STYLE_BOOKSHELF)
        header.addWidget(self.title_label)
        header.addStretch()

        # Bouton retour
        header.addWidget(make_back_btn(self.back_clicked.emit))
        header.addSpacing(20)
        
        layout.addWidget(header_widget)
        layout.addWidget(self.grid_view)

    def set_manga(self, manga_id, manga_title):
        """Définit le manga et charge ses chapitres"""
        self.manga_id = manga_id
        self.manga_title = manga_title
        self.title_label.setText(manga_title)
        self.load_chapters()

    def load_chapters(self):
        """Charge les chapitres du manga"""
        try:
            url = f'https://api.mangadex.org/manga/{self.manga_id}/feed'
            params = {
                'translatedLanguage[]': ['en', 'fr'],
                'order[chapter]': 'desc',
                'includes[]': ['scanlation_group']
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.chapters = data.get('data', [])
                self.display_chapters()
            else:
                print(f"Erreur chargement chapitres: {response.status_code}")
        except Exception as e:
            print(f"Erreur lors du chargement des chapitres: {e}")

    def display_chapters(self):
        """Affiche la liste des chapitres"""
        widgets = []
        
        for chapter in self.chapters:
            chapter_id = chapter['id']
            chapter_data = chapter['attributes']
            chapter_num = chapter_data.get('chapter', '0')
            chapter_title = chapter_data.get('title', '')
            
            # Créer le titre du chapitre
            if chapter_title:
                display_title = f"Chapitre {chapter_num} - {chapter_title}"
            else:
                display_title = f"Chapitre {chapter_num}"
            
            # Utiliser une vignette par défaut pour les chapitres
            default_path = create_default_thumbnail() or "assets/images/manga_sample.png"
            widget = ThumbnailWidget(default_path, display_title, path=chapter_id, show_menu=False)
            
            widget.clicked.connect(lambda checked, cid=chapter_id, ct=display_title: self.chapter_selected.emit(cid, ct))
            widgets.append(widget)
        
        self.grid_view.set_items(widgets)

# =====================================================================================
# PAGE TÉLÉCHARGEMENT CHAPITRE
# =====================================================================================
class ChapterDownloadPage(QWidget):
    download_complete = Signal(str)  # file_path
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.chapter_id = ""
        self.chapter_title = ""
        self.download_path = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_widget = RoundedHeaderWidget()
        header_widget.radius = HEADER_RADIUS
        header_widget.setFixedHeight(HEADER_HEIGHT)
        header_widget.set_background_image(resource_path('assets/images/header.png'))
        header_widget.set_scrim()

        header = QHBoxLayout(header_widget)
        header.setContentsMargins(20, 20, 20, 20)

        # Titre
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        self.title_label.setStyleSheet(S.PAGE_TITLE_STYLE_BOOKSHELF)
        header.addWidget(self.title_label)
        header.addStretch()

        # Bouton retour
        header.addWidget(make_back_btn(self.back_clicked.emit))
        header.addSpacing(20)
        
        layout.addWidget(header_widget)

        # Contenu central
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.setSpacing(30)

        # Message d'information
        info_label = QLabel("Téléchargement en cours...")
        info_label.setFont(QFont("Inter", 18))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(info_label)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        central_layout.addWidget(self.progress_bar)

        # Bouton d'ouverture
        self.open_btn = QPushButton("Ouvrir le fichier")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self.open_file)
        central_layout.addWidget(self.open_btn)

        layout.addWidget(central_widget)

    def set_chapter(self, chapter_id, chapter_title):
        """Définit le chapitre et commence le téléchargement"""
        self.chapter_id = chapter_id
        self.chapter_title = chapter_title
        self.title_label.setText(chapter_title)
        self.download_chapter()

    def download_chapter(self):
        """Télécharge le chapitre"""
        try:
            # Récupérer les pages du chapitre
            url = f'https://api.mangadex.org/at-home/server/{self.chapter_id}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                base_url = data['baseUrl']
                chapter_hash = data['chapter']['hash']
                
                # Créer le dossier de téléchargement
                download_dir = os.path.join(os.getcwd(), 'downloads')
                os.makedirs(download_dir, exist_ok=True)
                
                # Nom du fichier
                safe_title = "".join(c for c in self.chapter_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                self.download_path = os.path.join(download_dir, f"{safe_title}.cbz")
                
                # Télécharger les pages
                pages = data['chapter']['data']
                total_pages = len(pages)
                
                import zipfile
                with zipfile.ZipFile(self.download_path, 'w') as zip_file:
                    for i, page in enumerate(pages):
                        # Mettre à jour la progression
                        progress = int((i + 1) / total_pages * 100)
                        self.progress_bar.setValue(progress)
                        QApplication.processEvents()
                        
                        # Télécharger la page
                        page_url = f"{base_url}/data/{chapter_hash}/{page}"
                        page_response = requests.get(page_url, timeout=30)
                        
                        if page_response.status_code == 200:
                            # Déterminer l'extension
                            if page.endswith('.jpg') or page.endswith('.jpeg'):
                                ext = '.jpg'
                            elif page.endswith('.png'):
                                ext = '.png'
                            else:
                                ext = '.jpg'
                            
                            # Ajouter au ZIP
                            zip_file.writestr(f"{i+1:03d}{ext}", page_response.content)
                
                # Téléchargement terminé
                self.progress_bar.setValue(100)
                self.open_btn.setVisible(True)
                
                # Afficher un message de succès
                QMessageBox.information(self, "Succès", f"Chapitre téléchargé avec succès !\n{self.download_path}")
                
            else:
                QMessageBox.warning(self, "Erreur", f"Impossible de télécharger le chapitre (Erreur {response.status_code})")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du téléchargement : {e}")

    def open_file(self):
        """Ouvre le fichier téléchargé"""
        if self.download_path and os.path.exists(self.download_path):
            self.download_complete.emit(self.download_path)

# =====================================================================================
# FENETRE PRINCIPALE (Contrôleur de navigation)
# =====================================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAKU - Manga PDF Reader")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(S.APP_BACKGROUND_STYLE)
        self.setWindowIcon(QIcon(resource_path("assets/images/logo.png")))

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.settings_window = None
        self.build_pages()
        # Page d'ouverture choisie dans les paramètres.
        if settings.get("startup_page") == "bookshelf":
            self.show_bookshelf()
        else:
            self.show_home()

    def build_pages(self):
        """(Re)construit les quatre pages et rebranche leurs signaux.

        Les feuilles de style sont posées sur les widgets à leur construction :
        changer de thème passe donc par une reconstruction, pas par une simple
        mise à jour des couleurs.
        """
        self.home_page = HomePage()
        self.bookshelf_page = BookShelfPage()
        self.folder_view_page = FolderViewPage()
        self.pdf_viewer_page = FileViewerPage()
        for page in (self.home_page, self.bookshelf_page,
                     self.folder_view_page, self.pdf_viewer_page):
            self.stacked_widget.addWidget(page)
        self.connect_signals()

    def connect_signals(self):
        self.home_page.open_bookshelf.connect(self.show_bookshelf)
        self.home_page.open_file_dialog.connect(self.open_file)
        self.home_page.open_settings.connect(self.show_settings)
        self.home_page.toggle_theme.connect(self.toggle_theme)

        self.bookshelf_page.folder_selected.connect(self.show_folder_view)
        self.bookshelf_page.add_folder_clicked.connect(self.open_directory)
        self.bookshelf_page.back_clicked.connect(self.show_home)

        self.folder_view_page.file_selected.connect(self.show_pdf_viewer)
        self.folder_view_page.back_clicked.connect(self.show_bookshelf)

        self.pdf_viewer_page.back_clicked.connect(self.back_to_folder_view)



    def _reset_selection(self):
        """Sort les deux grilles du mode sélection, sans les reconstruire."""
        for page in (self.folder_view_page, self.bookshelf_page):
            page.selection_mode = False
            page.selected_items.clear()

    def show_home(self):
        # Chaque page reconstruit sa grille quand on l'affiche : le faire ici
        # revenait à recalculer les deux à chaque aller-retour.
        self._reset_selection()
        self.stacked_widget.setCurrentWidget(self.home_page)

    def show_bookshelf(self):
        self._reset_selection()
        self.bookshelf_page.refresh_shelf()
        self.stacked_widget.setCurrentWidget(self.bookshelf_page)

    def show_folder_view(self, path):
        debug(f"[DEBUG] show_folder_view: {path} (existe={os.path.exists(path)})")
        self.folder_view_page.set_folder(path, is_main_entry=True)
        self.stacked_widget.setCurrentWidget(self.folder_view_page)

    def show_pdf_viewer(self, path):
        self._reset_selection()
        self.pdf_viewer_page.load_file(path)
        self.stacked_widget.setCurrentWidget(self.pdf_viewer_page)

    def back_to_folder_view(self):
        """Retour du lecteur : la grille se remet à jour à ce moment-là."""
        self.folder_view_page.refresh_view()
        self.stacked_widget.setCurrentWidget(self.folder_view_page)

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier", "", "Fichiers supportés (*.pdf *.cbz *.zip *.rar);;PDF Files (*.pdf);;CBZ Files (*.cbz);;ZIP Files (*.zip);;RAR Files (*.rar)")
        if file:
            self.show_pdf_viewer(file)

    def open_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        self.bookshelf_page.add_folder(folder)

    def toggle_theme(self):
        """Bouton lune / soleil : bascule le thème et le retient."""
        new_theme = "light" if current_theme() == "dark" else "dark"
        settings.set("theme", new_theme)
        self.apply_theme()

    def apply_theme(self):
        """Applique le thème enregistré, en gardant l'utilisateur où il est."""
        set_theme(settings.get("theme"))
        apply_qt_palette(QApplication.instance())
        self.setStyleSheet(S.APP_BACKGROUND_STYLE)

        state = self.capture_state()
        old_pages = (self.home_page, self.bookshelf_page,
                     self.folder_view_page, self.pdf_viewer_page)
        self.build_pages()
        for page in old_pages:
            self.stacked_widget.removeWidget(page)
            page.deleteLater()
        self.restore_state(state)

        # La fenêtre de paramètres porte ses propres feuilles : elle se
        # reconstruit aussi, et se rouvre si elle était affichée.
        if self.settings_window is not None:
            was_visible = self.settings_window.isVisible()
            self.settings_window.close()
            self.settings_window.deleteLater()
            self.settings_window = None
            if was_visible:
                self.show_settings()

    def capture_state(self):
        """Ce qu'il faut savoir pour remettre l'utilisateur là où il était."""
        current = self.stacked_widget.currentWidget()
        viewer = self.pdf_viewer_page
        return {
            "page": ("viewer" if current is self.pdf_viewer_page else
                     "folder" if current is self.folder_view_page else
                     "bookshelf" if current is self.bookshelf_page else "home"),
            "folder_path": self.folder_view_page.folder_path,
            "path_stack": list(self.folder_view_page.path_stack),
            "hidden": set(self.folder_view_page.session_hidden_files),
            "file_path": viewer.file_path,
            "current_page": viewer.current_page,
            "zoom_factor": viewer.zoom_factor,
            "zoom_is_auto": viewer.zoom_is_auto,
        }

    def restore_state(self, state):
        folder = self.folder_view_page
        if state["folder_path"]:
            folder.session_hidden_files = state["hidden"]
            folder.set_folder(state["folder_path"], is_main_entry=True)
            folder.path_stack = state["path_stack"] or [state["folder_path"]]
        if state["page"] == "viewer" and state["file_path"]:
            viewer = self.pdf_viewer_page
            viewer.load_file(state["file_path"])
            viewer.zoom_factor = state["zoom_factor"]
            viewer.zoom_is_auto = state["zoom_is_auto"]
            viewer.display_page(state["current_page"])
            self.stacked_widget.setCurrentWidget(viewer)
        elif state["page"] == "folder" and state["folder_path"]:
            self.stacked_widget.setCurrentWidget(folder)
        elif state["page"] == "bookshelf":
            self.show_bookshelf()
        else:
            self.show_home()

    def show_settings(self):
        """Ouvre la fenêtre de paramètres, une seule instance réutilisée."""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(
                self,
                library_paths=lambda: [entry["path"] for entry in self.bookshelf_page.library])
            self.settings_window.settings_changed.connect(self.apply_setting)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def apply_setting(self, key):
        """Répercute un réglage sur les pages déjà construites.

        Les réglages lus au vol (molette, extensions masquées, traces) n'ont
        rien à faire ici : seuls ceux qui vivent dans des widgets déjà en place
        demandent une reconstruction.
        """
        if key in ("*", "theme"):
            # La bascule reconstruit les pages, y compris celle qui vient
            # d'émettre : on laisse d'abord le signal se dérouler.
            QTimer.singleShot(0, self.apply_theme)
            return
        rebuild = key in ("*", "thumbnail_size", "hide_extensions",
                          "thumbnail_cache_cleared")
        if key in ("*", "default_sort"):
            self.bookshelf_page.apply_sort(settings.get("default_sort") == "az",
                                           save=False)
            rebuild = True
        if not rebuild:
            return
        current = self.stacked_widget.currentWidget()
        if current is self.bookshelf_page:
            self.bookshelf_page.refresh_shelf()
        elif current is self.folder_view_page:
            self.folder_view_page.refresh_view()

def generate_all_thumbnails_for_folder(folder_path, progress_callback=None):
    """Génère toutes les vignettes PDF, CBZ, ZIP, RAR et CBR d'un dossier dans .thumbnails, avec callback de progression"""
    thumb_dir = os.path.join(folder_path, '.thumbnails')
    try:
        os.makedirs(thumb_dir, exist_ok=True)
    except OSError as e:
        print(f"Impossible de créer le dossier de vignettes : {thumb_dir}. Erreur : {e}")
        raise e
    index = load_thumb_cache_index(thumb_dir)
    files = sorted(f for f in os.listdir(folder_path) if f.lower().endswith(ARCHIVE_EXTENSIONS))
    total = len(files)
    for idx, file in enumerate(files):
        file_path = os.path.join(folder_path, file)
        if progress_callback:
            progress_callback(f"Chargement de l'image de la vignette : {file}", int((idx+1)/total*100))
        base = os.path.splitext(file)[0]
        thumb_path = os.path.join(thumb_dir, base + '.png')
        if thumbnail_needs_render(thumb_path, file_path, index):
            if write_cover_thumbnail(file_path, thumb_path):
                index[base + '.png'] = THUMB_CACHE_VERSION

    # Générer la vignette du dossier à partir du premier fichier trouvé (archive, PDF ou image)
    file_for_folder_thumb = folder_cover_source(folder_path)

    if file_for_folder_thumb:
        folder_thumb_path = os.path.join(thumb_dir, '_folder_thumb.png')
        if thumbnail_needs_render(folder_thumb_path, file_for_folder_thumb, index):
            if write_cover_thumbnail(file_for_folder_thumb, folder_thumb_path):
                index['_folder_thumb.png'] = THUMB_CACHE_VERSION

    save_thumb_cache_index(thumb_dir, index)

_CHILD_COUNT_CACHE = {}


def count_chapters(folder_path):
    """Nombre d'éléments lisibles d'un dossier : sous-dossiers et archives.

    Mis en cache sur la date de modification du dossier : la barre de recherche
    reconstruit la grille à chaque frappe, et un parcours par collection y
    coûterait cher sur un disque externe.
    """
    try:
        stamp = os.stat(folder_path).st_mtime_ns
    except OSError:
        return 0
    cached = _CHILD_COUNT_CACHE.get(folder_path)
    if cached and cached[0] == stamp:
        return cached[1]
    total = 0
    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.name.startswith('.'):
                    continue
                if entry.is_dir() or entry.name.lower().endswith(ARCHIVE_EXTENSIONS):
                    total += 1
    except OSError:
        total = 0
    _CHILD_COUNT_CACHE[folder_path] = (stamp, total)
    return total


def create_default_thumbnail():
    """Crée une image par défaut programmatiquement"""
    try:
        # Créer une image 200x280 avec un fond blanc et du texte
        pixmap = QPixmap(200, 280)
        pixmap.fill(QColor(255, 255, 255))  # Fond blanc
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(100, 100, 100))
        painter.drawText(
            pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No\nPreview\nAvailable"
        )
        painter.end()
        
        # Sauvegarder l'image par défaut
        default_path = "assets/images/manga_sample.png"
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        pixmap.save(default_path)
        return default_path
    except Exception as e:
        print(f"Erreur création image par défaut: {e}")
        return None

def get_thumbnail_path(file_path=None, folder_path=None):
    """Retourne le chemin de la vignette pour un fichier ou dossier"""
    try:
        if folder_path:
            thumb_dir = os.path.join(folder_path, '.thumbnails')
            thumb_path = os.path.join(thumb_dir, '_folder_thumb.png')
            debug(f"[DEBUG] Test vignette dossier: {thumb_path}")
            if os.path.exists(thumb_path):
                debug(f"[DEBUG] Vignette trouvée: {thumb_path}")
                return thumb_path
            debug(f"[DEBUG] Vignette non trouvée: {thumb_path}")
            return None
        else:
            base = os.path.splitext(os.path.basename(file_path))[0]
            thumb_dir = os.path.join(os.path.dirname(file_path), '.thumbnails')
            thumb_path = os.path.join(thumb_dir, base + '.png')
            debug(f"[DEBUG] Test vignette fichier: {thumb_path}")
            if os.path.exists(thumb_path):
                debug(f"[DEBUG] Vignette locale trouvée: {thumb_path}")
                return thumb_path
            folder_thumb = os.path.join(thumb_dir, '_folder_thumb.png')
            if os.path.exists(folder_thumb):
                debug(f"[DEBUG] Vignette dossier trouvée: {folder_thumb}")
                return folder_thumb
            debug(f"[DEBUG] Aucune vignette trouvée pour {file_path}")
            return None
    except Exception as e:
        print(f"Erreur get_thumbnail_path: {e}")
        return None

def regenerate_all_thumbnails():
    """Régénère toutes les vignettes de la bibliothèque existante (PDF et CBZ)"""
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
            library = json.load(f)
        
        print("Régénération de toutes les vignettes (PDF et CBZ)...")
        for entry in library:
            folder_path = entry["path"]
            if os.path.exists(folder_path):
                print(f"Génération des vignettes pour: {folder_path}")
                generate_all_thumbnails_for_folder(folder_path)
        print("Régénération terminée!")
    except Exception as e:
        print(f"Erreur lors de la régénération: {e}")

def fetch_anilist_info(manga_title):
    url = 'https://graphql.anilist.co'
    query = '''
    query ($search: String) {
      Media(search: $search, type: MANGA) {
        title { romaji english native }
        description(asHtml: false)
        tags { name }
        genres
        coverImage { large }
        bannerImage
      }
    }
    '''
    variables = {'search': manga_title}
    try:
        response = requests.post(url, json={'query': query, 'variables': variables},
                                 timeout=10)
        if response.status_code == 200:
            data = response.json()
            media = data.get('data', {}).get('Media')
            if media:
                return {
                    'title': media['title'],
                    'description': media['description'],
                    # AniList n'écrit qu'en anglais.
                    'descriptions': {'en': media['description'] or ''},
                    'tags': [tag['name'] for tag in media['tags']],
                    'genres': media['genres'],
                    'cover': media['coverImage']['large'],
                    'banner': media['bannerImage']
                }
    except Exception as e:
        print(f"Erreur AniList: {e}")
    return None

def fetch_mangadex_info(manga_title):
    """Recherche les informations d'un manga sur MangaDex"""
    url = 'https://api.mangadex.org/manga'
    params = {
        'title': manga_title,
        'limit': 5,
        'includes[]': ['cover_art']
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                # Préférer un titre identique à la recherche : sur des noms
                # courants, le premier résultat est souvent un doujinshi.
                def titles_of(entry):
                    attrs = entry.get('attributes', {})
                    values = list((attrs.get('title') or {}).values())
                    for alt in attrs.get('altTitles') or []:
                        values.extend(alt.values())
                    return [v.strip().lower() for v in values if isinstance(v, str)]

                wanted = manga_title.strip().lower()
                manga = next((e for e in data['data'] if wanted in titles_of(e)), data['data'][0])
                manga_id = manga['id']
                
                # Récupérer les détails complets du manga
                detail_url = f'https://api.mangadex.org/manga/{manga_id}'
                detail_response = requests.get(detail_url, timeout=10)
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    manga_detail = detail_data['data']
                    
                    # Récupérer la couverture avec vérification
                    cover_url = None
                    if 'relationships' in manga_detail:
                        for rel in manga_detail['relationships']:
                            if rel['type'] == 'cover_art':
                                cover_id = rel['id']
                                cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_id}.jpg"
                                
                                # Vérifier que l'URL de la couverture fonctionne
                                try:
                                    cover_response = requests.head(cover_url, timeout=5)
                                    if cover_response.status_code != 200:
                                        debug(f"[DEBUG MangaDex] URL couverture invalide: {cover_url}")
                                        cover_url = None
                                        continue
                                    else:
                                        debug(f"[DEBUG MangaDex] URL couverture valide: {cover_url}")
                                        break
                                except Exception as e:
                                    debug(f"[DEBUG MangaDex] Erreur vérification couverture: {e}")
                                    cover_url = None
                                    continue
                    
                    # Récupérer les tags
                    tags = []
                    if 'attributes' in manga_detail:
                        attrs = manga_detail['attributes']
                        if 'tags' in attrs:
                            tags = [tag['attributes']['name']['en'] for tag in attrs['tags']]
                    
                    # MangaDex publie un synopsis par langue : on les garde tous.
                    descriptions = manga_detail['attributes'].get('description') or {}
                    if not isinstance(descriptions, dict):
                        descriptions = {}
                    return {
                        'title': manga_detail['attributes']['title'].get('en', manga_title),
                        'description': descriptions.get('en', ''),
                        'descriptions': descriptions,
                        'tags': tags,
                        'genres': tags,  # MangaDex utilise des tags pour les genres
                        'cover': cover_url,
                        'banner': None  # MangaDex n'a pas de bannière
                    }
    except Exception as e:
        print(f"Erreur MangaDex: {e}")
    return None

def description_candidates(language):
    """Codes à essayer pour un synopsis, du plus précis au repli anglais."""
    if not language:
        return ("en",)
    if language == "es":
        # MangaDex publie souvent l'espagnol sous « es-la » (Amérique latine).
        return ("es", "es-la", "en")
    return (language, "en")


def pick_description(info, language):
    """Synopsis dans la langue demandée, sinon anglais, sinon n'importe laquelle."""
    descriptions = info.get('descriptions')
    if not isinstance(descriptions, dict) or not descriptions:
        descriptions = {'en': info.get('description') or ''}
    for code in description_candidates(language):
        if descriptions.get(code):
            return descriptions[code]
    return next((text for text in descriptions.values() if text), '')


def fetch_manga_info(manga_title, language=None):
    """Fiche d'un manga : AniList d'abord, MangaDex ensuite.

    MangaDex est aussi interrogé dès qu'une langue autre que l'anglais est
    demandée : c'est la seule des deux sources à fournir des synopsis traduits.
    """
    anilist = fetch_anilist_info(manga_title)
    needs_translation = bool(language) and language not in ("en",)
    mangadex = None
    if needs_translation or not (anilist and anilist.get('cover')):
        mangadex = fetch_mangadex_info(manga_title)
    if not anilist and not mangadex:
        debug(f"[DEBUG] Aucune fiche trouvée pour : {manga_title}")
        return None

    info = dict(anilist or mangadex)
    descriptions = {}
    for source in (mangadex, anilist):   # AniList prime sur la version anglaise
        if source:
            descriptions.update({k: v for k, v in (source.get('descriptions') or {}).items() if v})
    info['descriptions'] = descriptions
    if not info.get('cover') and mangadex:
        info['cover'] = mangadex.get('cover')
    return info


def refresh_manga_info(folder_path, title, language=None):
    """Ré-interroge les APIs pour ce dossier et met à jour son .anilist.json.

    Les synopsis déjà connus dans d'autres langues sont conservés : changer de
    langue n'efface pas ce qui a été récupéré auparavant.
    """
    info = fetch_manga_info(title, language=language)
    if not info:
        return None
    path = os.path.join(folder_path, '.anilist.json')
    known = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            previous = json.load(f)
        if isinstance(previous, dict) and isinstance(previous.get('descriptions'), dict):
            known = previous['descriptions']
    except (OSError, ValueError):
        pass
    merged = dict(known)
    merged.update(info.get('descriptions') or {})
    info['descriptions'] = merged
    info['title_query'] = title
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Erreur écriture .anilist.json : {e}")
    return info


def apply_qt_palette(app):
    """Teinte les fenêtres que Qt dessine lui-même.

    Les boîtes de dialogue, les menus des vignettes et la liste déroulante d'un
    QComboBox ne passent pas par nos feuilles de style : sans palette, elles
    resteraient blanches au milieu d'une application sombre.
    """
    if app is None:
        return
    palette = QPalette()
    if current_theme() == "dark":
        base = QColor(theme_color("surface"))
        alt = QColor(theme_color("surface_alt"))
        text = QColor(theme_color("text"))
        window = QColor(theme_color("bg"))
        for role, color in (
            (QPalette.ColorRole.Window, window),
            (QPalette.ColorRole.WindowText, text),
            (QPalette.ColorRole.Base, base),
            (QPalette.ColorRole.AlternateBase, alt),
            (QPalette.ColorRole.Text, text),
            (QPalette.ColorRole.Button, alt),
            (QPalette.ColorRole.ButtonText, text),
            (QPalette.ColorRole.ToolTipBase, base),
            (QPalette.ColorRole.ToolTipText, text),
            (QPalette.ColorRole.Highlight, QColor(ACCENT)),
            (QPalette.ColorRole.HighlightedText, QColor("#ffffff")),
            (QPalette.ColorRole.PlaceholderText, QColor(theme_color("text_muted"))),
        ):
            palette.setColor(role, color)
        disabled = QColor(theme_color("text_soft"))
        for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText,
                     QPalette.ColorRole.WindowText):
            palette.setColor(QPalette.ColorGroup.Disabled, role, disabled)
    app.setPalette(palette)


def main():
    # Certains chemins de la bibliothèque sortent du codepage de la console
    # (arabe, japonais) : sans cela, un simple print fait planter l'application.
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    # Mise à l'échelle fractionnaire : les vignettes sont rendues aux pixels
    # physiques de l'écran plutôt qu'à un facteur arrondi.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    # Régénérer toutes les vignettes au démarrage (désactivé pour accélérer le lancement)
    # regenerate_all_thumbnails()
    # Charger la police Inter
    font_path = os.path.join("assets", "fonts", "Inter-Regular.ttf")
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)
        app.setFont(QFont("Inter"))
    # Thème enregistré, posé avant la construction de la moindre page.
    set_theme(settings.get("theme"))
    apply_qt_palette(app)
    window = MainWindow()
    if settings.get("start_fullscreen"):
        window.showFullScreen()
    else:
        window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
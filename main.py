import sys
import os
import json
import functools
import zipfile
import fitz  # PyMuPDF
import rarfile
import requests

# === AJOUT : Fonction utilitaire pour les chemins d'assets compatible PyInstaller ===
def resource_path(relative_path):
    """Retourne le chemin absolu vers un fichier ressource, compatible PyInstaller et dev."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QGridLayout, QScrollArea,
    QFileDialog, QMenu, QInputDialog, QDialog, QProgressBar, QMessageBox,
    QGraphicsDropShadowEffect
)
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QImage, QFontDatabase, QPainter, QColor,
    QDesktopServices, QBrush, QPen
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QUrl  # imports nettoyés
from PySide6.QtSvg import QSvgRenderer

# Importer les styles
from styles.styles import (
    HOME_PAGE_BUTTON_STYLE, BMC_BUTTON_STYLE, THUMBNAIL_IMAGE_STYLE,
    THUMBNAIL_IMAGE_HOVER_STYLE, THUMBNAIL_MENU_BUTTON_STYLE,
    SCROLL_AREA_STYLE, BACK_BUTTON_STYLE,
    PAGE_TITLE_STYLE, FOLDER_PATH_STYLE,
    PAGE_TITLE_STYLE_BOOKSHELF
)

from ui.flowlayout import FlowLayout

LIBRARY_FILE = "library.json"
GENERATE_THUMBNAILS = True
VERSION = "1.0.0"
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
ARCHIVE_EXTENSIONS = ('.pdf', '.cbz', '.zip', '.rar', '.cbr')

os.environ["QT_STYLE_OVERRIDE"] = ""

# =====================================================================================
# LABEL AVEC COINS ARRONDIS
# =====================================================================================
class RoundedLabel(QLabel):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 10
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

# =====================================================================================
# HEADER AVEC COINS ARRONDIS
# =====================================================================================
class RoundedHeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 8
        self.background_image = None
    def set_background_image(self, image_path):
        if image_path and os.path.exists(image_path):
            self.background_image = image_path
            self.update()
        else:
            self.background_image = None
            self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.background_image and os.path.exists(self.background_image):
            pixmap = QPixmap(self.background_image)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.width(), self.height(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                x_offset = (scaled_pixmap.width() - self.width()) // 2
                y_offset = (scaled_pixmap.height() - self.height()) // 2
                mask = QPixmap(self.size())
                mask.fill(QColor('black'))
                mask_painter = QPainter(mask)
                mask_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                mask_painter.setBrush(QBrush(QColor('white')))
                mask_painter.setPen(QPen(Qt.PenStyle.NoPen))
                mask_painter.drawRoundedRect(
                    0, 0, self.width(), self.height(), self.radius, self.radius
                )
                mask_painter.end()
                scaled_pixmap.setMask(mask.createMaskFromColor(QColor('black')))
                painter.drawPixmap(-x_offset, -y_offset, scaled_pixmap)
            else:
                painter.fillRect(self.rect(), QColor("#f8f9fa"))
        else:
            painter.fillRect(self.rect(), QColor("#f8f9fa"))
        painter.setPen(QColor("#e9ecef"))
        painter.drawLine(0, self.height() - 2, self.width(), self.height() - 2)

# =====================================================================================
# PAGE D'ACCUEIL
# =====================================================================================
class HomePage(QWidget):
    open_bookshelf = Signal()
    open_file_dialog = Signal()
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
        subtitle.setFont(QFont("Inter", 14))
        subtitle.setStyleSheet("color: #444; margin-bottom: 20px;")
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        open_btn = QPushButton("OPEN FILE")
        open_btn.setFixedSize(200, 80)
        open_btn.setStyleSheet(HOME_PAGE_BUTTON_STYLE)
        open_btn.clicked.connect(self.open_file_dialog.emit)
        btn_layout.addWidget(open_btn)
        bookshelf_btn = QPushButton("BOOKSHELF")
        bookshelf_btn.setFixedSize(200, 80)
        bookshelf_btn.setStyleSheet(HOME_PAGE_BUTTON_STYLE)
        bookshelf_btn.clicked.connect(self.open_bookshelf.emit)
        btn_layout.addWidget(bookshelf_btn)
        layout.addLayout(btn_layout)
        bmc_btn = QPushButton('☕ Buy me a coffee')
        bmc_btn.setStyleSheet(BMC_BUTTON_STYLE)
        bmc_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://www.buymeacoffee.com/ezakaria')))
        layout.addWidget(bmc_btn, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

        # Ajout du bouton Paypal Me
        paypal_btn = QPushButton('💙 Paypal Me')
        paypal_btn.setStyleSheet('''
            QPushButton {
                background-color: #0070ba;
                color: #fff;
                border: none;
                border-radius: 10px;
                font-family: 'Inter';
                font-size: 18px;
                padding: 10px 30px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #1546a0;
            }
        ''')
        paypal_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://www.paypal.me/ZELORCHE')))
        layout.addWidget(paypal_btn, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

# =====================================================================================
# WIDGET VIGNETTE (Utilisé pour Dossiers et PDF)
# =====================================================================================
class ThumbnailWidget(QWidget):
    clicked = Signal()
    remove_requested = Signal(str)
    alias_requested = Signal(str, str)
    cover_requested = Signal(str)
    tags_requested = Signal(str)
    def __init__(self, thumb_path, title_text, path=None, width=200, height=280, show_menu=True, checkbox=None):
        super().__init__()
        self.thumb_path = thumb_path
        self.title_text = title_text
        self.path = path
        self.thumb_width = width
        self.thumb_height = height
        self.show_menu = show_menu
        self.checkbox = checkbox
        self.setObjectName("thumbnailWidget")
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setStyleSheet("")
        self.img_label = RoundedLabel()
        self.img_label.setContentsMargins(0, 0, 0, 0)
        self.update_image()
        self.img_label.setFixedSize(self.thumb_width, self.thumb_height)
        self.img_label.setStyleSheet(THUMBNAIL_IMAGE_STYLE)
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
            self.title_label.setStyleSheet(
                "font-size: 15px; color: #222; margin: 0px; padding: 0px;"
            )
            info_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignVCenter)
            info_layout.addStretch(1)
        else:
            self.title_label = QLabel(self.title_text)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_label.setWordWrap(True)
            self.title_label.setMinimumHeight(40)  # Hauteur minimale pour les titres longs
            self.title_label.setStyleSheet(
                "font-size: 15px; color: #222; margin: 0px; padding: 0px;"
            )
            info_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        info_widget.setLayout(info_layout)
        layout.addWidget(info_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        if self.show_menu and self.path:
            print(f"[DEBUG] Création du menu contextuel pour : {self.path}")
            menu_btn = QPushButton("⋯")
            menu_btn.setFixedSize(32, 32)
            menu_btn.setStyleSheet(THUMBNAIL_MENU_BUTTON_STYLE)
            layout.addWidget(menu_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            menu = QMenu()
            alias_action = menu.addAction("Set alias")
            alias_action.triggered.connect(lambda: self.alias_requested.emit(self.path, self.title_text))
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
                        os.makedirs(thumb_dir, exist_ok=True)
                        cover_path = os.path.join(thumb_dir, '_folder_thumb.png')
                        try:
                            if file_for_thumb.lower().endswith('.pdf'):
                                doc = fitz.open(file_for_thumb)
                                if len(doc) > 0:
                                    page = doc[0]
                                    pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                                    pix.save(cover_path)
                                doc.close()
                            elif file_for_thumb.lower().endswith(('.cbz', '.zip')):
                                with zipfile.ZipFile(file_for_thumb, 'r') as zip_file:
                                    image_files = [f for f in zip_file.namelist() if f.lower().endswith(IMAGE_EXTENSIONS)]
                                    if image_files:
                                        image_files.sort()
                                        first_image = image_files[0]
                                        with zip_file.open(first_image) as image_file:
                                            image_data = image_file.read()
                                            qimage = QImage()
                                            if qimage.loadFromData(image_data):
                                                pixmap = QPixmap.fromImage(qimage)
                                                scaled_pixmap = pixmap.scaled(400, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                                scaled_pixmap.save(cover_path)
                            elif file_for_thumb.lower().endswith('.rar'):
                                with rarfile.RarFile(file_for_thumb, 'r') as rar:
                                    image_files = [f for f in rar.namelist() if f.lower().endswith(IMAGE_EXTENSIONS)]
                                    if image_files:
                                        image_files.sort()
                                        first_image = image_files[0]
                                        with rar.open(first_image) as image_file:
                                            image_data = image_file.read()
                                            qimage = QImage()
                                            if qimage.loadFromData(image_data):
                                                pixmap = QPixmap.fromImage(qimage)
                                                scaled_pixmap = pixmap.scaled(400, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                                scaled_pixmap.save(cover_path)
                            elif file_for_thumb.lower().endswith(IMAGE_EXTENSIONS):
                                qimage = QImage(file_for_thumb)
                                if not qimage.isNull():
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                    scaled_pixmap.save(cover_path)
                            # Rafraîchir la vignette
                            self.update_thumbnail(cover_path)
                        except Exception as e:
                            print(f"Erreur lors de la génération de la couverture originale : {e}")
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
                
                print(f"[DEBUG] Tentative de téléchargement de couverture pour : {manga_name}")
                
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
                            print(f"[DEBUG] Couverture téléchargée : {cover_path}")
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
                                    print(f"[DEBUG] Informations API sauvegardées")
                                except Exception as e:
                                    print(f"[DEBUG] Erreur sauvegarde API : {e}")
                        else:
                            print(f"[DEBUG] Erreur téléchargement couverture : {resp.status_code}")
                            if resp.status_code == 404:
                                print(f"[DEBUG] Couverture introuvable sur le serveur : {cover_url}")
                            # Afficher un message d'erreur spécifique
                            from PySide6.QtWidgets import QMessageBox
                            if resp.status_code == 404:
                                QMessageBox.warning(None, "Couverture introuvable", f"La couverture pour {manga_name} n'est plus disponible sur le serveur")
                            else:
                                QMessageBox.warning(None, "Erreur de téléchargement", f"Impossible de télécharger la couverture pour {manga_name} (Erreur {resp.status_code})")
                    except Exception as e:
                        print(f"[DEBUG] Exception téléchargement couverture : {e}")
                        # Afficher un message d'erreur pour les exceptions réseau
                        from PySide6.QtWidgets import QMessageBox
                        QMessageBox.warning(None, "Erreur réseau", f"Erreur de connexion lors du téléchargement de la couverture pour {manga_name}")
                else:
                    print(f"[DEBUG] Aucune couverture trouvée pour : {manga_name}")
                    # Afficher un message d'erreur
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(None, "Aucune couverture trouvée", f"Aucune couverture trouvée pour {manga_name} sur AniList ou MangaDex")
            
            download_cover_action = menu.addAction("Download Cover")
            download_cover_action.triggered.connect(download_cover_from_anilist_for_all)
            
            explorer_action = menu.addAction("Open in Explorer")
            explorer_action.triggered.connect(lambda: self.open_in_explorer(self.path))
            remove_action = menu.addAction("Remove from bookshelf")
            remove_action.triggered.connect(lambda checked=False, p=self.path: self.remove_requested.emit(p))
            menu_btn.clicked.connect(lambda: menu.exec(menu_btn.mapToGlobal(menu_btn.rect().bottomLeft())))
    def update_image(self):
        try:
            print(f"Tentative de chargement de l'image: {self.thumb_path}")
            pixmap = QPixmap(self.thumb_path)
            if pixmap.isNull():
                print(f"Image nulle pour: {self.thumb_path}")
                default_pixmap = QPixmap(self.thumb_width, self.thumb_height)
                default_pixmap.fill(QColor(240, 240, 240))
                painter = QPainter(default_pixmap)
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(
                    default_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No\nPreview\nAvailable"
                )
                painter.end()
                scaled_pixmap = default_pixmap.scaled(
                    self.thumb_width, self.thumb_height, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.img_label.setPixmap(scaled_pixmap)
            else:
                print(f"Image chargée avec succès: {self.thumb_path}")
                scaled_pixmap = pixmap.scaled(self.thumb_width, self.thumb_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.img_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image {self.thumb_path}: {e}")
            try:
                error_pixmap = QPixmap(self.thumb_width, self.thumb_height)
                error_pixmap.fill(QColor(255, 200, 200))
                painter = QPainter(error_pixmap)
                painter.setPen(QColor(150, 0, 0))
                painter.drawText(error_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Error\nLoading\nImage")
                painter.end()
                self.img_label.setPixmap(error_pixmap)
            except Exception as e:
                self.img_label.setText("Error\nImage")
                self.img_label.setStyleSheet("border: 4px solid #111; "
                                             "border-radius: 14px; "
                                             "background: white; "
                                             "color: #666; "
                                             "font-size: 12px;")
                print(f"Erreur fatale lors de la création de l'image d'erreur: {e}")
    def update_thumbnail(self, new_thumb_path):
        try:
            self.thumb_path = new_thumb_path
            self.update_image()
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la vignette: {e}")
    def enterEvent(self, event):
        self.img_label.setStyleSheet(THUMBNAIL_IMAGE_HOVER_STYLE)
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.img_label.setStyleSheet(THUMBNAIL_IMAGE_STYLE)
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
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)  # centrer horizontalement
        grid_widget = QWidget()
        grid_widget.setLayout(self.grid_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(grid_widget)
        self.scroll_area.setStyleSheet(SCROLL_AREA_STYLE)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
        self._items = []

    def set_items(self, widgets):
        # Nettoyer les anciens widgets
        for widget in self._items:
            self.grid_layout.removeWidget(widget)
            widget.deleteLater()
        
        self._items = widgets
        self.refresh_grid()

    def refresh_grid(self):
        # Effacer les anciens widgets de la grille pour la reconstruire
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        vignette_w = 200 + 20
        n_col = max(1, self.width() // vignette_w if self.width() > 0 else 1)
        
        for i, widget in enumerate(self._items):
             self.grid_layout.addWidget(widget, i // n_col, i % n_col)
    
    def resizeEvent(self, event):
        self.refresh_grid()
        super().resizeEvent(event)

# =====================================================================================
# PAGE BIBLIOTHEQUE
# =====================================================================================
class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Génération des vignettes")
        self.setModal(True)
        self.setFixedSize(520, 120)
        layout = QVBoxLayout(self)
        self.label = QLabel("Préparation...")
        self.label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        layout.addWidget(self.label)
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)

    def update_message(self, msg, value=None):
        self.label.setText(msg)
        if value is not None:
            self.progress.setValue(value)
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
        self.refresh_shelf()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Création du header avec image de fond
        header_widget = RoundedHeaderWidget()
        header_widget.setFixedHeight(80)
        header_widget.set_background_image(resource_path('assets/images/header.png'))

        header = QHBoxLayout(header_widget)
        header.setContentsMargins(20, 20, 20, 20)

        # Affichage du titre Bookshelf (simple)
        title = QLabel("BookShelf")
        title.setFont(QFont("Inter", 32, QFont.Weight.Bold))
        title.setStyleSheet(PAGE_TITLE_STYLE_BOOKSHELF)
        header.addWidget(title)
        header.addStretch()

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        # Le bouton retour est le premier du groupe d'icônes à droite
        back_btn = make_header_btn(resource_path("assets/icons/arrow-left-white.png"), "Retour", self.back_clicked.emit)
        filter_bar.addWidget(back_btn)

        filter_btn = make_header_btn(resource_path("assets/icons/funnel-white.svg"), "Filtrer", lambda: None)
        filter_bar.addWidget(filter_btn)

        # Bouton Sélectionner (sélection multiple)
        self.select_btn = make_header_btn(resource_path("assets/icons/check2-all-white.svg"), "Sélectionner des fichiers", self.toggle_selection_mode)
        filter_bar.addWidget(self.select_btn)

        from PySide6.QtWidgets import QLineEdit
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Rechercher...")
        self.search_field.setFixedWidth(0)
        self.search_field.setVisible(False)
        self.search_field.textChanged.connect(self.refresh_shelf)
        filter_bar.addWidget(self.search_field)
        
        def toggle_search():
            if self.search_field.isVisible():
                self.search_field.setVisible(False)
                self.search_field.setFixedWidth(0)
                self.search_field.setText("")
            else:
                self.search_field.setVisible(True)
                self.search_field.setFixedWidth(200)
                self.search_field.setFocus()
        search_btn = make_header_btn(resource_path("assets/icons/search-white.svg"), "Rechercher", toggle_search)
        filter_bar.addWidget(search_btn)

        self.sort_az = True
        self.sort_btn = make_header_btn(resource_path("assets/icons/sort-alpha-down-white.svg"), "Trier A-Z", self.toggle_sort)
        filter_bar.addWidget(self.sort_btn)

        header.addLayout(filter_bar)

        add_btn = make_header_btn(resource_path("assets/icons/folder-plus-white.svg"), "Ajouter un dossier", self.add_folder_clicked.emit)
        header.addWidget(add_btn)
        header.addSpacing(20)
        
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
                generate_all_thumbnails_for_folder(folder_path, progress_callback)
                self.library.append({"path": folder_path})
                self.save_library()
                self.refresh_shelf()
                # --- Récupération automatique AniList/MangaDex ---
                manga_name = os.path.basename(folder_path)
                print(f"[DEBUG API] Tentative de récupération pour : {manga_name}")
                info = fetch_manga_info(manga_name)
                if info:
                    print(f"[DEBUG API] Succès, création de .anilist.json")
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
                                    print(f"[DEBUG API] Bannière téléchargée : {banner_path}")
                                else:
                                    print(f"[DEBUG API] Erreur téléchargement bannière : {resp.status_code}")
                            except Exception as e:
                                print(f"[DEBUG API] Exception téléchargement bannière : {e}")
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
                                    print(f"[DEBUG API] Vignette téléchargée : {thumb_path}")
                                else:
                                    print(f"[DEBUG API] Erreur téléchargement vignette : {resp.status_code}")
                            except Exception as e:
                                print(f"[DEBUG API] Exception téléchargement vignette : {e}")
                    except Exception as e:
                        print(f"[DEBUG API] Erreur lors de l'écriture du fichier : {e}")
                else:
                    print(f"[DEBUG API] Aucun résultat pour : {manga_name}")
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
                thumb_path = get_thumbnail_path(None, path)
                if thumb_path:
                    vignette = ThumbnailWidget(thumb_path, name, path=path)
                else:
                    default_path = create_default_thumbnail() or "assets/images/manga_sample.png"
                    vignette = ThumbnailWidget(default_path, name, path=path)
                def on_folder_selected(p=path):
                    print(f"[DEBUG] Signal folder_selected émis avec : {p}")
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
                    vignette = ThumbnailWidget(thumb_path, name, path=path, checkbox=checkbox)
                    vignette.clicked.connect(on_folder_selected)
                
                # Connecter les signaux une seule fois
                vignette.clicked.connect(on_folder_selected)
                vignette.remove_requested.connect(self.remove_folder)
                vignette.alias_requested.connect(self.set_folder_alias)
                vignette.cover_requested.connect(self.set_folder_cover)
                widgets.append(vignette)
            else:
                widgets.append(vignette)
            valid_library.append(entry)
        if len(valid_library) != len(self.library):
            self.library = valid_library
            self.save_library()
        print("[DEBUG] Aucun fichier ou dossier supporté trouvé dans ce dossier.")
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
                # Copier et redimensionner l'image pour qu'elle corresponde aux vignettes
                pixmap = QPixmap(image_path)
                scaled_pixmap = pixmap.scaled(400, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                scaled_pixmap.save(cover_path, "PNG")

                # Mettre à jour la date de modification pour éviter l'écrasement
                os.utime(cover_path, None)
                print(f"Nouvelle couverture définie pour {folder_path}")
                self.refresh_shelf()
            except Exception as e:
                print(f"Erreur lors de la définition de la couverture : {e}")

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
                # Optimisation : ne régénérer la vignette que si le dossier contient des fichiers supportés
                fichiers = [f for f in os.listdir(folder_path) if f.lower().endswith(ARCHIVE_EXTENSIONS)]
                if fichiers:
                    print(f"[DEBUG] Régénération de la vignette pour {folder_path} après changement d'alias.")
                    generate_all_thumbnails_for_folder(folder_path)
                else:
                    print(f"[DEBUG] Pas de fichiers supportés dans {folder_path}, pas de régénération de vignette.")
                # Vérification de la présence de .anilist.json
                anilist_file = os.path.join(folder_path, '.anilist.json')
                if not os.path.exists(anilist_file):
                    print(f"[DEBUG] Attention : .anilist.json absent dans {folder_path} après changement d'alias.")
                self.refresh_shelf()

    def toggle_sort(self):
        if self.sort_az:
            self.library.sort(key=lambda d: d.get("alias", os.path.basename(d["path"])).lower())
            self.sort_btn.setIcon(QIcon("assets/icons/sort-alpha-up-white.svg"))
            self.sort_btn.setToolTip("Trier Z-A")
        else:
            self.library.sort(key=lambda d: d.get("alias", os.path.basename(d["path"])).lower(), reverse=True)
            self.sort_btn.setIcon(QIcon("assets/icons/sort-alpha-down-white.svg"))
            self.sort_btn.setToolTip("Trier A-Z")
        self.sort_az = not self.sort_az
        self.save_library()
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
            print(f"[DEBUG] Dossiers supprimés : {self.selected_items}")
        else:
            self.selection_mode = not self.selection_mode
            if not self.selection_mode:
                self.selected_items.clear()
            self.refresh_shelf()
            print(f"[DEBUG] Mode sélection : {self.selection_mode}")

# === AJOUT : Fonction utilitaire globale pour les boutons d'icônes header ===
def make_header_btn(icon_path, tooltip, callback):
    btn = QPushButton()
    btn.setIcon(QIcon(icon_path))
    btn.setIconSize(QSize(32, 32))
    btn.setFixedSize(48, 48)
    btn.setStyleSheet(
        """
        QPushButton {
            background: rgba(0,0,0,0.45);
            border-radius: 24px;
            border: none;
        }
        QPushButton:hover {
            background: #95a5a6;
            color: #222;
        }
        """
    )
    btn.setToolTip(tooltip)
    btn.clicked.connect(callback)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(12)
    shadow.setColor(QColor(0, 0, 0, 200))
    shadow.setOffset(0, 3)
    btn.setGraphicsEffect(shadow)
    return btn

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

        # Colonne 2 : icônes alignées horizontalement au centre
        right_col = QHBoxLayout()
        right_col.setSpacing(18)
        right_col.setContentsMargins(0, 0, 0, 0)

        right_col.addWidget(make_header_btn(resource_path("assets/icons/arrow-left-white.png"), "Retour", self.navigate_back))
        right_col.addWidget(make_header_btn(resource_path("assets/icons/palette-white.svg"), "Changer la bannière", self.set_header_background))
        right_col.addWidget(make_header_btn(resource_path("assets/icons/arrow-clockwise-white.svg"), "Rafraîchir", self.refresh_folder))

        # Bouton unique de sélection/suppression
        self.select_btn = QPushButton()
        self.select_btn.setIcon(QIcon("assets/icons/check2-all-white.svg"))
        self.select_btn.setIconSize(QSize(32, 32))
        self.select_btn.setFixedSize(48, 48)
        self.select_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(0,0,0,0.45);
                border-radius: 24px;
                border: none;
            }
            QPushButton:hover {
                background: #95a5a6;
                color: #222;
            }
            """
        )
        self.select_btn.setToolTip("Sélectionner des fichiers")
        self.select_btn.clicked.connect(self.on_select_btn_clicked)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 3)
        self.select_btn.setGraphicsEffect(shadow)
        right_col.addWidget(self.select_btn)
        header_layout.addLayout(right_col)

        layout.addWidget(self.header_widget)

        # --- Layout central en deux colonnes (inchangé) ---
        central_layout = QHBoxLayout()
        central_layout.setSpacing(30)

        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        self.anilist_desc_label = QLabel()
        self.anilist_desc_label.setWordWrap(True)
        self.anilist_desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.anilist_desc_label.setStyleSheet("font-size: 15px; color: #444; margin-top: 10px;")
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
        print(f"[DEBUG] Appel de set_folder avec folder_path = '{folder_path}'")
        if is_main_entry:
            self.path_stack = [folder_path]
        self.folder_path = folder_path
        # Chercher l'alias dans la bibliothèque uniquement pour le dossier racine
        alias = None
        if len(self.path_stack) <= 1:
            try:
                if os.path.exists(LIBRARY_FILE):
                    with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                        library = json.load(f)
                    for entry in library:
                        if entry["path"] == folder_path:
                            alias = entry.get("alias")
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
                print(f"[DEBUG] .anilist.json trouvé : {anilist_file}")
                print(f"[DEBUG] Contenu .anilist.json : {info}")
                desc = info.get('description', '')
                tags_list = info.get('tags', [])
            except Exception as e:
                print(f"[DEBUG set_folder] Erreur lecture anilist.json: {e}")
        else:
            print(f"[DEBUG] .anilist.json absent dans : {folder_path}")
        self.anilist_desc_label.setText(desc)
        # Affichage des tags façon 'pills'
        # Nettoyer l'ancien contenu
        for i in reversed(range(self.anilist_tags_layout.count())):
            item = self.anilist_tags_layout.itemAt(i)
            if item is not None and item.widget() is not None:
                item.widget().setParent(None)
        for tag in tags_list:
            tag_label = QLabel(tag)
            tag_label.setStyleSheet(
                "background: #e6dca4; color: #444; border-radius: 12px; padding: 4px 14px; "
                "font-size: 13px; font-weight: bold; margin-bottom: 2px;"
            )
            self.anilist_tags_layout.addWidget(tag_label)
        self.refresh_view()

    def load_header_background(self):
        """Charge l'image de fond du header"""
        try:
            # 1. Chercher une bannière AniList téléchargée
            banner_path = os.path.join(self.folder_path, '.thumbnails', '_header_banner.png')
            if os.path.exists(banner_path):
                print(f"[AniList] Bannière trouvée : {banner_path}")
                self.header_widget.set_background_image(banner_path)
                self.title_label.setStyleSheet(PAGE_TITLE_STYLE)
                self.path_label.setStyleSheet(FOLDER_PATH_STYLE)
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
                            self.title_label.setStyleSheet(PAGE_TITLE_STYLE)
                            self.path_label.setStyleSheet(FOLDER_PATH_STYLE)
                            return
                except Exception as e:
                    print(f"[AniList] Erreur lecture couverture : {e}")
            # 3. Sinon, image personnalisée
            custom_bg_path = os.path.join(self.folder_path, "_header_bg.png")
            print(f"Recherche de l'image de fond personnalisée: {custom_bg_path}")
            if os.path.exists(custom_bg_path):
                print(f"Image personnalisée trouvée: {custom_bg_path}")
                self.header_widget.set_background_image(custom_bg_path)
                print("Image personnalisée appliquée au header")
                self.title_label.setStyleSheet(PAGE_TITLE_STYLE)
                self.path_label.setStyleSheet(FOLDER_PATH_STYLE)
            else:
                print(f"Image personnalisée non trouvée, utilisation de l'image par défaut")
                default_bg_path = "assets/images/header.png"
                if os.path.exists(default_bg_path):
                    self.header_widget.set_background_image(default_bg_path)
                    print("Image par défaut appliquée au header")
                    self.title_label.setStyleSheet(PAGE_TITLE_STYLE)
                    self.path_label.setStyleSheet(FOLDER_PATH_STYLE)
                else:
                    print(f"Image par défaut non trouvée, utilisation du style par défaut (pas d'image)")
                    self.header_widget.set_background_image(None)
                    self.title_label.setStyleSheet(PAGE_TITLE_STYLE)
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
            self.title_label.setStyleSheet(PAGE_TITLE_STYLE)
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
            print(f"[DEBUG] Contenu du dossier {self.folder_path} : {all_items}")
        except FileNotFoundError:
            self.grid_view.set_items([])
            print(f"[DEBUG] Dossier introuvable : {self.folder_path}")
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
        for item_name in all_items:
            if item_name.startswith('.'):
                continue
            if item_name in self.session_hidden_files:
                continue
            item_path = os.path.join(self.folder_path, item_name)
            widget = None
            display_name = alias_map.get(item_name, item_name)
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
                thumb_path = get_thumbnail_path(None, folder_path=item_path)
                if not thumb_path:
                    thumb_path = (create_default_thumbnail() or 
                                  "assets/images/manga_sample.png")
                widget = ThumbnailWidget(
                    thumb_path, display_name, path=item_path, show_menu=True, checkbox=checkbox
                )
                widget.clicked.connect(
                    functools.partial(self.on_item_clicked, item_path)
                )
                widget.alias_requested.connect(self.set_item_alias)
                widget.remove_requested.connect(self.remove_item)
            # Cas 2: L'élément est un fichier supporté
            elif item_name.lower().endswith(ARCHIVE_EXTENSIONS):
                fichiers_supportes.append(item_name)
                base_name = os.path.splitext(item_name)[0]
                thumb_path = get_thumbnail_path(item_path)
                if not thumb_path:
                    thumb_path = (create_default_thumbnail() or 
                                  "assets/images/manga_sample.png")
                widget = ThumbnailWidget(
                    thumb_path, display_name, path=item_path, show_menu=True, checkbox=checkbox
                )
                widget.clicked.connect(
                    functools.partial(self.on_item_clicked, item_path)
                )
                widget.alias_requested.connect(self.set_item_alias)
                widget.remove_requested.connect(self.remove_item)
            if widget:
                widgets.append(widget)
        print(f"[DEBUG] Fichiers/dossiers supportés trouvés : {fichiers_supportes}")
        if not widgets:
            print("[DEBUG] Aucun fichier ou dossier supporté trouvé dans ce dossier.")
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
            print(f"[DEBUG] Fichiers/dossiers masqués : {self.session_hidden_files}")
        else:
            self.selection_mode = not self.selection_mode
            if not self.selection_mode:
                self.selected_items.clear()
            self.refresh_view()
            print(f"[DEBUG] Mode sélection (vue dossier) : {self.selection_mode}")

# =====================================================================================
# LECTEUR DE FICHIERS (PDF et CBZ)
# =====================================================================================
class FileViewerPage(QWidget):
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.doc = None
        self.zip_file = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_factor = 1.0
        self.file_path = None
        self.file_type = None  # 'pdf' ou 'cbz'
        self.cbz_images = []  # Liste des images pour les CBZ
        self.rar_file = None
        self.setup_ui()
        
        # Timer pour recalculer le zoom une fois la fenêtre affichée
        self.zoom_timer = QTimer()
        self.zoom_timer.setSingleShot(True)
        self.zoom_timer.timeout.connect(self.recalculate_zoom)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        nav_layout = QHBoxLayout()
        
        # Boutons de navigation
        self.back_btn = QPushButton("←")
        self.back_btn.setToolTip("Retour à la vue précédente")
        self.back_btn.setStyleSheet(BACK_BUTTON_STYLE)
        self.back_btn.clicked.connect(self.back_clicked.emit)
        
        self.prev_btn = QPushButton("◀ Précédent")
        self.prev_btn.clicked.connect(self.previous_page)
        
        self.next_btn = QPushButton("Suivant ▶")
        self.next_btn.clicked.connect(self.next_page)

        self.page_label = QLabel("Page 0 / 0")
        
        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        
        self.zoom_out_btn = QPushButton("🔍-")
        self.zoom_out_btn.clicked.connect(self.zoom_out)

        # Ajout au layout de navigation
        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.zoom_out_btn)
        nav_layout.addWidget(self.zoom_in_btn)
        
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.pdf_label)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addLayout(nav_layout)
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
        """Recalcule le zoom optimal une fois que la fenêtre est affichée"""
        if self.doc and self.total_pages > 0 and self.file_type == 'pdf':
            current_page = self.doc[self.current_page]
            new_zoom = self.calculate_optimal_zoom(page=current_page)
            if abs(new_zoom - self.zoom_factor) > 0.1:  # Seulement si le changement est significatif
                self.zoom_factor = new_zoom
                self.display_page(self.current_page)
        elif self.zip_file and self.total_pages > 0 and self.file_type == 'cbz':
            # Pour les CBZ/ZIP, charger la première image pour calculer le zoom
            try:
                image_name = self.cbz_images[self.current_page]
                with self.zip_file.open(image_name) as image_file:
                    image_data = image_file.read()
                    qimage = QImage()
                    if qimage.loadFromData(image_data):
                        new_zoom = self.calculate_optimal_zoom(image=qimage)
                        if abs(new_zoom - self.zoom_factor) > 0.1:  # Seulement si le changement est significatif
                            self.zoom_factor = new_zoom
                            self.display_page(self.current_page)
            except Exception as e:
                print(f"Erreur lors du calcul du zoom CBZ: {e}")
        elif self.rar_file and self.total_pages > 0 and self.file_type == 'rar':
            # Pour les RAR, charger la première image pour calculer le zoom
            try:
                image_name = self.cbz_images[self.current_page]
                with self.rar_file.open(image_name) as image_file:
                    image_data = image_file.read()
                    qimage = QImage()
                    if qimage.loadFromData(image_data):
                        new_zoom = self.calculate_optimal_zoom(image=qimage)
                        if abs(new_zoom - self.zoom_factor) > 0.1:  # Seulement si le changement est significatif
                            self.zoom_factor = new_zoom
                            self.display_page(self.current_page)
            except Exception as e:
                print(f"Erreur lors du calcul du zoom RAR: {e}")
        elif self.file_type == 'image_folder' and self.total_pages > 0:
            try:
                image_path = self.cbz_images[self.current_page]
                qimage = QImage(image_path)
                if not qimage.isNull():
                    new_zoom = self.calculate_optimal_zoom(image=qimage)
                    if abs(new_zoom - self.zoom_factor) > 0.1:
                        self.zoom_factor = new_zoom
                        self.display_page(self.current_page)
            except Exception as e:
                print(f"Erreur lors du calcul du zoom pour le dossier d'images: {e}")

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
            # Afficher d'abord avec un zoom par défaut
            self.zoom_factor = 1.0
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
                scaled_pixmap = QPixmap.fromImage(qimage).scaled(
                    int(qimage.width() * self.zoom_factor),
                    int(qimage.height() * self.zoom_factor),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.pdf_label.setPixmap(scaled_pixmap)
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
                    new_zoom = self.calculate_optimal_zoom(image=qimage)
                    scaled_pixmap = QPixmap.fromImage(qimage).scaled(
                        int(qimage.width() * new_zoom),
                        int(qimage.height() * new_zoom),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.pdf_label.setPixmap(scaled_pixmap)
        elif self.file_type == 'rar' and hasattr(self, 'rar_file') and self.rar_file:
            if not (0 <= page_num < self.total_pages):
                return
            image_name = self.cbz_images[page_num]
            with self.rar_file.open(image_name) as image_file:
                image_data = image_file.read()
                qimage = QImage()
                if qimage.loadFromData(image_data):
                    new_zoom = self.calculate_optimal_zoom(image=qimage)
                    scaled_pixmap = QPixmap.fromImage(qimage).scaled(
                        int(qimage.width() * new_zoom),
                        int(qimage.height() * new_zoom),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.pdf_label.setPixmap(scaled_pixmap)
        self.page_label.setText(f"Page {self.current_page + 1} / {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < self.total_pages - 1)

    def next_page(self):
        self.display_page(self.current_page + 1)
        
    def previous_page(self):
        self.display_page(self.current_page - 1)
        
    def zoom_in(self):
        self.zoom_factor = min(self.zoom_factor * 1.2, 5.0)
        self.display_page(self.current_page)
        
    def zoom_out(self):
        self.zoom_factor = max(self.zoom_factor / 1.2, 0.2)
        self.display_page(self.current_page)

    def keyPressEvent(self, event):
        """Gestion des touches clavier pour la navigation"""
        if event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_Up:
            # Flèche gauche ou haut : page précédente
            if self.current_page > 0:
                self.previous_page()
        elif event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_Down:
            # Flèche droite ou bas : page suivante
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
            self.display_page(0)
        elif event.key() == Qt.Key.Key_End:
            # Touche End : dernière page
            self.display_page(self.total_pages - 1)
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
# FENETRE PRINCIPALE (Contrôleur de navigation)
# =====================================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAKU - Manga PDF Reader")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("background-color: #f6fafd;")
        self.setWindowIcon(QIcon(resource_path("assets/images/logo.png")))

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.home_page = HomePage()
        self.bookshelf_page = BookShelfPage()
        self.folder_view_page = FolderViewPage()
        self.pdf_viewer_page = FileViewerPage()

        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.bookshelf_page)
        self.stacked_widget.addWidget(self.folder_view_page)
        self.stacked_widget.addWidget(self.pdf_viewer_page)

        self.connect_signals()
        self.show_home()

    def connect_signals(self):
        self.home_page.open_bookshelf.connect(self.show_bookshelf)
        self.home_page.open_file_dialog.connect(self.open_file)

        self.bookshelf_page.folder_selected.connect(self.show_folder_view)
        self.bookshelf_page.add_folder_clicked.connect(self.open_directory)
        self.bookshelf_page.back_clicked.connect(self.show_home)

        self.folder_view_page.file_selected.connect(self.show_pdf_viewer)
        self.folder_view_page.back_clicked.connect(self.show_bookshelf)

        self.pdf_viewer_page.back_clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.folder_view_page))

    def show_home(self):
        self.folder_view_page.selection_mode = False
        self.folder_view_page.selected_items.clear()
        self.folder_view_page.refresh_view()
        self.bookshelf_page.selection_mode = False
        self.bookshelf_page.selected_items.clear()
        self.bookshelf_page.refresh_shelf()
        self.stacked_widget.setCurrentWidget(self.home_page)
    
    def show_bookshelf(self):
        self.folder_view_page.selection_mode = False
        self.folder_view_page.selected_items.clear()
        self.folder_view_page.refresh_view()
        self.bookshelf_page.selection_mode = False
        self.bookshelf_page.selected_items.clear()
        self.bookshelf_page.refresh_shelf()
        self.stacked_widget.setCurrentWidget(self.bookshelf_page)

    def show_folder_view(self, path):
        print(f"[DEBUG] show_folder_view appelé avec path: {path}")
        print(f"[DEBUG] Le dossier existe: {os.path.exists(path)}")
        if os.path.exists(path):
            print(f"[DEBUG] Contenu du dossier: {os.listdir(path)}")
        self.folder_view_page.set_folder(path, is_main_entry=True)
        self.stacked_widget.setCurrentWidget(self.folder_view_page)

    def show_pdf_viewer(self, path):
        self.folder_view_page.selection_mode = False
        self.folder_view_page.selected_items.clear()
        self.folder_view_page.refresh_view()
        self.pdf_viewer_page.load_file(path)
        self.stacked_widget.setCurrentWidget(self.pdf_viewer_page)

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier", "", "Fichiers supportés (*.pdf *.cbz *.zip *.rar);;PDF Files (*.pdf);;CBZ Files (*.cbz);;ZIP Files (*.zip);;RAR Files (*.rar)")
        if file:
            self.show_pdf_viewer(file)

    def open_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        self.bookshelf_page.add_folder(folder)

def generate_all_thumbnails_for_folder(folder_path, progress_callback=None):
    """Génère toutes les vignettes PDF, CBZ, ZIP et RAR d'un dossier dans .thumbnails, avec callback de progression"""
    thumb_dir = os.path.join(folder_path, '.thumbnails')
    try:
        os.makedirs(thumb_dir, exist_ok=True)
    except OSError as e:
        print(f"Impossible de créer le dossier de vignettes : {thumb_dir}. Erreur : {e}")
        raise e
    first_file_found = None
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(ARCHIVE_EXTENSIONS)]
    total = len(files)
    for idx, file in enumerate(files):
        file_lower = file.lower()
        file_path = os.path.join(folder_path, file)
        if progress_callback:
            progress_callback(f"Chargement de l'image de la vignette : {file}", int((idx+1)/total*100))
        base = os.path.splitext(file)[0]
        thumb_path = os.path.join(thumb_dir, base + '.png')
        anilist_thumb_path = os.path.join(thumb_dir, base + '_anilist.png')
        if not os.path.exists(thumb_path) or os.path.getmtime(thumb_path) < os.path.getmtime(file_path):
            try:
                if file_lower.endswith('.pdf'):
                    doc = fitz.open(file_path)
                    if len(doc) > 0:
                        page = doc[0]
                        pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                        pix.save(thumb_path)
                        if first_file_found is None:
                            first_file_found = file_path
                    doc.close()
                elif file_lower.endswith('.cbz') or file_lower.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_file:
                        image_files = [f for f in zip_file.namelist() 
                                      if f.lower().endswith(IMAGE_EXTENSIONS)]
                        if image_files:
                            image_files.sort()
                            first_image = image_files[0]
                            with zip_file.open(first_image) as image_file:
                                image_data = image_file.read()
                                qimage = QImage()
                                if qimage.loadFromData(image_data):
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                    scaled_pixmap.save(thumb_path)
                                    if first_file_found is None:
                                        first_file_found = file_path
                elif file_lower.endswith('.rar'):
                    with rarfile.RarFile(file_path, 'r') as rar:
                        image_files = [f for f in rar.namelist() if f.lower().endswith(IMAGE_EXTENSIONS)]
                        if image_files:
                            image_files.sort()
                            first_image = image_files[0]
                            with rar.open(first_image) as image_file:
                                image_data = image_file.read()
                                qimage = QImage()
                                if qimage.loadFromData(image_data):
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                    scaled_pixmap.save(thumb_path)
                                    if first_file_found is None:
                                        first_file_found = file_path
            except Exception as e:
                print(f"Erreur vignette {file_path}: {e}")
        # Récupération de la couverture depuis les APIs pour ce fichier
        if not os.path.exists(anilist_thumb_path):
            manga_name = os.path.splitext(file)[0]
            info = fetch_manga_info(manga_name)
            if info and info.get('cover'):
                cover_url = info['cover']
                try:
                    resp = requests.get(cover_url, timeout=10)
                    if resp.status_code == 200:
                        with open(anilist_thumb_path, 'wb') as imgf:
                            imgf.write(resp.content)
                        print(f"[DEBUG API] Vignette téléchargée pour {file}: {anilist_thumb_path}")
                    else:
                        print(f"[DEBUG API] Erreur téléchargement vignette fichier {file}: {resp.status_code}")
                except Exception as e:
                    print(f"[DEBUG API] Exception téléchargement vignette fichier {file}: {e}")

    # Générer la vignette du dossier à partir du premier fichier trouvé (archive, PDF ou image)
    file_for_folder_thumb = None
    
    if files:
        files.sort()
        first_file_found = os.path.join(folder_path, files[0])
    
    if first_file_found:
        file_for_folder_thumb = first_file_found
    else:
        # Si aucune archive/PDF n'est trouvé, chercher des images
        image_files = sorted([
            f for f in os.listdir(folder_path)
            if f.lower().endswith(IMAGE_EXTENSIONS)
        ])
        if image_files:
            file_for_folder_thumb = os.path.join(folder_path, image_files[0])

    if file_for_folder_thumb:
        folder_thumb_path = os.path.join(thumb_dir, '_folder_thumb.png')
        if not os.path.exists(folder_thumb_path) or os.path.getmtime(folder_thumb_path) < os.path.getmtime(file_for_folder_thumb):
            try:
                if file_for_folder_thumb.lower().endswith('.pdf'):
                    doc = fitz.open(file_for_folder_thumb)
                    if len(doc) > 0:
                        page = doc[0]
                        pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                        pix.save(folder_thumb_path)
                    doc.close()
                elif file_for_folder_thumb.lower().endswith(('.cbz', '.zip')):
                    with zipfile.ZipFile(file_for_folder_thumb, 'r') as zip_file:
                        image_files = [f for f in zip_file.namelist() 
                                      if f.lower().endswith(IMAGE_EXTENSIONS)]
                        if image_files:
                            image_files.sort()
                            first_image = image_files[0]
                            with zip_file.open(first_image) as image_file:
                                image_data = image_file.read()
                                qimage = QImage()
                                if qimage.loadFromData(image_data):
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                    scaled_pixmap.save(folder_thumb_path)
                elif file_for_folder_thumb.lower().endswith('.rar'):
                    with rarfile.RarFile(file_for_folder_thumb, 'r') as rar:
                        image_files = [f for f in rar.namelist() if f.lower().endswith(IMAGE_EXTENSIONS)]
                        if image_files:
                            image_files.sort()
                            first_image = image_files[0]
                            with rar.open(first_image) as image_file:
                                image_data = image_file.read()
                                qimage = QImage()
                                if qimage.loadFromData(image_data):
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                    scaled_pixmap.save(folder_thumb_path)
                elif file_for_folder_thumb.lower().endswith(IMAGE_EXTENSIONS):
                    qimage = QImage(file_for_folder_thumb)
                    if not qimage.isNull():
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                    scaled_pixmap.save(folder_thumb_path)
            except Exception as e:
                print(f"Erreur vignette dossier {folder_path}: {e}")

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
            print(f"[DEBUG] Test vignette dossier: {thumb_path}")
            if os.path.exists(thumb_path):
                print(f"[DEBUG] Vignette trouvée: {thumb_path}")
                return thumb_path
            print(f"[DEBUG] Vignette non trouvée: {thumb_path}")
            return None
        else:
            base = os.path.splitext(os.path.basename(file_path))[0]
            thumb_dir = os.path.join(os.path.dirname(file_path), '.thumbnails')
            thumb_path = os.path.join(thumb_dir, base + '.png')
            print(f"[DEBUG] Test vignette fichier: {thumb_path}")
            if os.path.exists(thumb_path):
                print(f"[DEBUG] Vignette locale trouvée: {thumb_path}")
                return thumb_path
            folder_thumb = os.path.join(thumb_dir, '_folder_thumb.png')
            if os.path.exists(folder_thumb):
                print(f"[DEBUG] Vignette dossier trouvée: {folder_thumb}")
                return folder_thumb
            print(f"[DEBUG] Aucune vignette trouvée pour {file_path}")
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
        response = requests.post(url, json={'query': query, 'variables': variables})
        if response.status_code == 200:
            data = response.json()
            media = data.get('data', {}).get('Media')
            if media:
                return {
                    'title': media['title'],
                    'description': media['description'],
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
                # Prendre le premier résultat
                manga = data['data'][0]
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
                                        print(f"[DEBUG MangaDex] URL couverture invalide: {cover_url}")
                                        cover_url = None
                                        continue
                                    else:
                                        print(f"[DEBUG MangaDex] URL couverture valide: {cover_url}")
                                        break
                                except Exception as e:
                                    print(f"[DEBUG MangaDex] Erreur vérification couverture: {e}")
                                    cover_url = None
                                    continue
                    
                    # Récupérer les tags
                    tags = []
                    if 'attributes' in manga_detail:
                        attrs = manga_detail['attributes']
                        if 'tags' in attrs:
                            tags = [tag['attributes']['name']['en'] for tag in attrs['tags']]
                    
                    return {
                        'title': manga_detail['attributes']['title'].get('en', manga_title),
                        'description': manga_detail['attributes'].get('description', {}).get('en', ''),
                        'tags': tags,
                        'genres': tags,  # MangaDex utilise des tags pour les genres
                        'cover': cover_url,
                        'banner': None  # MangaDex n'a pas de bannière
                    }
    except Exception as e:
        print(f"Erreur MangaDex: {e}")
    return None

def fetch_manga_info(manga_title):
    """Recherche les informations d'un manga sur AniList puis MangaDex si pas trouvé"""
    # Essayer d'abord AniList
    info = fetch_anilist_info(manga_title)
    if info and info.get('cover'):
        print(f"[DEBUG] Couverture trouvée sur AniList pour : {manga_title}")
        return info
    
    # Si pas trouvé sur AniList, essayer MangaDex
    print(f"[DEBUG] Pas trouvé sur AniList, essai MangaDex pour : {manga_title}")
    info = fetch_mangadex_info(manga_title)
    if info and info.get('cover'):
        print(f"[DEBUG] Couverture trouvée sur MangaDex pour : {manga_title}")
        return info
    
    print(f"[DEBUG] Aucune couverture trouvée pour : {manga_title}")
    return None

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    # Régénérer toutes les vignettes au démarrage (désactivé pour accélérer le lancement)
    # regenerate_all_thumbnails()
    # Charger la police Inter
    font_path = os.path.join("assets", "fonts", "Inter-Regular.ttf")
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)
        app.setFont(QFont("Inter"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
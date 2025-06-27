import sys
import os
import json
import functools
import zipfile
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QStackedWidget, QGridLayout, QScrollArea, 
                               QFileDialog, QMenu, QInputDialog, QDialog, QProgressBar)
from PySide6.QtGui import QFont, QPixmap, QIcon, QImage, QFontDatabase, QPainter, QColor, QDesktopServices
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QThread, QUrl
import fitz  # PyMuPDF
import rarfile

LIBRARY_FILE = "library.json"
GENERATE_THUMBNAILS = True  # Activer la génération de vignettes pour voir les couvertures des PDF

# =====================================================================================
# GÉNÉRATEUR DE VIGNETTES ASYNCHRONE
# =====================================================================================
class ThumbnailGenerator(QThread):
    thumbnail_ready = Signal(str, str)  # path, thumbnail_path
    
    def __init__(self):
        super().__init__()
        self.thumbnail_cache = {}
        self.pending_requests = set()
        self.is_running = False
    
    def generate_folder_thumbnail(self, folder_path):
        """Génère une vignette pour un dossier de manière asynchrone"""
        if folder_path in self.thumbnail_cache:
            self.thumbnail_ready.emit(folder_path, self.thumbnail_cache[folder_path])
            return
        
        if folder_path in self.pending_requests:
            return  # Déjà en cours de génération
            
        self.pending_requests.add(folder_path)
        if not self.is_running:
            self.start()
    
    def generate_cbz_thumbnail(self, cbz_path):
        """Génère une vignette pour un CBZ de manière asynchrone"""
        if cbz_path in self.thumbnail_cache:
            self.thumbnail_ready.emit(cbz_path, self.thumbnail_cache[cbz_path])
            return
        
        if cbz_path in self.pending_requests:
            return  # Déjà en cours de génération
            
        self.pending_requests.add(cbz_path)
        if not self.is_running:
            self.start()
    
    def generate_pdf_thumbnail(self, pdf_path):
        """Génère une vignette pour un PDF de manière asynchrone"""
        if pdf_path in self.thumbnail_cache:
            self.thumbnail_ready.emit(pdf_path, self.thumbnail_cache[pdf_path])
            return
        
        if pdf_path in self.pending_requests:
            return  # Déjà en cours de génération
            
        self.pending_requests.add(pdf_path)
        if not self.is_running:
            self.start()
    
    def run(self):
        """Méthode principale du thread"""
        self.is_running = True
        try:
            for path in list(self.pending_requests):
                try:
                    if path.lower().endswith('.pdf'):
                        thumb_path = self._generate_pdf_thumb(path)
                    elif path.lower().endswith('.cbz'):
                        thumb_path = self._generate_cbz_thumb(path)
                    else:
                        # Pour les dossiers
                        thumb_path = self._generate_folder_thumb(path)
                    
                    if thumb_path:
                        self.thumbnail_cache[path] = thumb_path
                        self.thumbnail_ready.emit(path, thumb_path)
                        
                except Exception:
                    # En cas d'erreur, utiliser l'image par défaut
                    default_thumb = create_default_thumbnail()
                    self.thumbnail_cache[path] = default_thumb
                    self.thumbnail_ready.emit(path, default_thumb)
                finally:
                    self.pending_requests.discard(path)
        finally:
            self.is_running = False
    
    def _generate_folder_thumb(self, folder_path):
        """Génère une vignette pour un dossier"""
        try:
            thumb_path = os.path.join(folder_path, "_folder_thumb.png")
            
            # Si la vignette existe déjà, l'utiliser
            if os.path.exists(thumb_path):
                return thumb_path
            
            # Chercher le premier fichier supporté dans le dossier
            try:
                files = os.listdir(folder_path)
                supported_files = [f for f in files if f.lower().endswith(('.pdf', '.cbz'))]
                
                if supported_files:
                    # Prendre le premier fichier trouvé
                    file_path = os.path.join(folder_path, supported_files[0])
                    if file_path.lower().endswith('.pdf'):
                        return self._generate_pdf_thumb(file_path, thumb_path)
                    else:
                        return self._generate_cbz_thumb(file_path, thumb_path)
            except Exception as e:
                print(f"Erreur lors de la recherche de fichiers dans {folder_path}: {e}")
        except Exception as e:
            print(f"Erreur lors de la génération de vignette pour {folder_path}: {e}")
        
        return "assets/images/manga_sample.png"
    
    def _generate_cbz_thumb(self, cbz_path, save_path=None):
        """Génère une vignette pour un fichier CBZ"""
        try:
            if save_path is None:
                save_path = cbz_path + "_thumb.png"
            
            # Si la vignette existe déjà, l'utiliser
            if os.path.exists(save_path):
                return save_path
            
            with zipfile.ZipFile(cbz_path, 'r') as zip_file:
                # Chercher la première image dans l'archive
                image_files = [f for f in zip_file.namelist() 
                              if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
                if image_files:
                    # Prendre la première image (trier pour avoir un ordre cohérent)
                    image_files.sort()
                    first_image = image_files[0]
                    
                    # Extraire et charger l'image
                    with zip_file.open(first_image) as image_file:
                        image_data = image_file.read()
                        qimage = QImage()
                        if qimage.loadFromData(image_data):
                            # Redimensionner et sauvegarder
                            pixmap = QPixmap.fromImage(qimage)
                            scaled_pixmap = pixmap.scaled(400, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            scaled_pixmap.save(save_path)
                            return save_path
        except Exception as e:
            print(f"Erreur lors de la génération de vignette CBZ {cbz_path}: {e}")
        
        return "assets/images/manga_sample.png"

    def _generate_pdf_thumb(self, pdf_path, save_path=None):
        """Génère une vignette pour un PDF"""
        try:
            if save_path is None:
                save_path = pdf_path + "_thumb.png"
            
            # Si la vignette existe déjà, l'utiliser
            if os.path.exists(save_path):
                return save_path
            
            doc = None
            try:
                doc = fitz.open(pdf_path)
                if len(doc) > 0:
                    page = doc[0]
                    # Utiliser une résolution très basse pour la performance
                    pix = page.get_pixmap(matrix=fitz.Matrix(0.15, 0.15))
                    pix.save(save_path)
                    return save_path
            except Exception as e:
                print(f"Erreur lors de la génération de vignette PDF {pdf_path}: {e}")
            finally:
                if doc:
                    doc.close()
        except Exception as e:
            print(f"Erreur générale lors de la génération de vignette PDF: {e}")
        
        return "assets/images/manga_sample.png"

# =====================================================================================
# LABEL AVEC COINS ARRONDIS
# =====================================================================================
class RoundedLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 10
        
    def setPixmap(self, pixmap):
        if pixmap:
            # Créer un masque arrondi
            mask = QPixmap(pixmap.size())
            mask.fill(Qt.black)
            
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            
            # Dessiner un rectangle arrondi blanc sur le masque noir
            painter.drawRoundedRect(0, 0, pixmap.width(), pixmap.height(), self.radius, self.radius)
            painter.end()
            
            # Appliquer le masque à la pixmap
            pixmap.setMask(mask.createMaskFromColor(Qt.black))
            
        super().setPixmap(pixmap)

# =====================================================================================
# HEADER AVEC COINS ARRONDIS
# =====================================================================================
class RoundedHeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 8
        self.background_image = None
        
    def set_background_image(self, image_path):
        """Définit l'image de fond avec coins arrondis"""
        if image_path and os.path.exists(image_path):
            self.background_image = image_path
            self.update()
        else:
            self.background_image = None
            self.update()
    
    def paintEvent(self, event):
        """Dessine le widget avec l'image de fond arrondie"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.background_image and os.path.exists(self.background_image):
            # Charger l'image de fond
            pixmap = QPixmap(self.background_image)
            if not pixmap.isNull():
                # Redimensionner l'image pour couvrir complètement le header
                # Utiliser KeepAspectRatioByExpanding pour remplir toute la surface
                scaled_pixmap = pixmap.scaled(
                    self.width(), self.height(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                
                # Calculer la position pour centrer l'image
                x_offset = (scaled_pixmap.width() - self.width()) // 2
                y_offset = (scaled_pixmap.height() - self.height()) // 2
                
                # Créer un masque arrondi à la taille du widget
                mask = QPixmap(self.size())
                mask.fill(Qt.black)
                
                mask_painter = QPainter(mask)
                mask_painter.setRenderHint(QPainter.Antialiasing)
                mask_painter.setBrush(Qt.white)
                mask_painter.setPen(Qt.NoPen)
                
                # Dessiner un rectangle arrondi blanc sur le masque noir
                mask_painter.drawRoundedRect(0, 0, self.width(), self.height(), self.radius, self.radius)
                mask_painter.end()
                
                # Appliquer le masque à la pixmap
                scaled_pixmap.setMask(mask.createMaskFromColor(Qt.black))
                
                # Dessiner l'image masquée en position centrée
                painter.drawPixmap(-x_offset, -y_offset, scaled_pixmap)
            else:
                # Fallback vers le style par défaut
                painter.fillRect(self.rect(), QColor("#f8f9fa"))
        else:
            # Style par défaut sans image
            painter.fillRect(self.rect(), QColor("#f8f9fa"))
        
        # Dessiner la bordure inférieure
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
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)

        # Ajout du logo au-dessus du titre
        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/images/logo.png")
        logo_label.setPixmap(logo_pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label, alignment=Qt.AlignCenter)

        subtitle = QLabel("Un Lecteur de Manga Offline")
        subtitle.setFont(QFont("Inter", 14))
        subtitle.setStyleSheet("color: #444; margin-bottom: 20px;")
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        style = """
            QPushButton {
                background-color: #fff;
                border: 4px solid #000;
                font-size: 22px;
                font-family: "Inter";
                border-radius: 20px;
            }
            QPushButton:hover { background-color: #eee; }
        """

        open_btn = QPushButton("OPEN FILE")
        open_btn.setFixedSize(200, 80)
        open_btn.setStyleSheet(style)
        open_btn.clicked.connect(self.open_file_dialog.emit)
        btn_layout.addWidget(open_btn)

        bookshelf_btn = QPushButton("BOOKSHELF")
        bookshelf_btn.setFixedSize(200, 80)
        bookshelf_btn.setStyleSheet(style)
        bookshelf_btn.clicked.connect(self.open_bookshelf.emit)
        btn_layout.addWidget(bookshelf_btn)
        
        layout.addLayout(btn_layout)

        # Ajout du bouton Buy me a coffee en bas
        bmc_btn = QPushButton('☕ Buy me a coffee')
        bmc_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFDD00;
                color: #000;
                border: 2px solid #000;
                border-radius: 10px;
                font-family: 'Inter';
                font-size: 18px;
                padding: 10px 30px;
                margin-top: 40px;
            }
            QPushButton:hover {
                background-color: #ffe066;
            }
        """)
        bmc_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://www.buymeacoffee.com/ezakaria')))
        layout.addWidget(bmc_btn, alignment=Qt.AlignHCenter | Qt.AlignBottom)

# =====================================================================================
# WIDGET VIGNETTE (Utilisé pour Dossiers et PDF)
# =====================================================================================
class ThumbnailWidget(QWidget):
    clicked = Signal()
    remove_requested = Signal(str)
    alias_requested = Signal(str, str)  # path, current_name
    cover_requested = Signal(str)

    def __init__(self, thumb_path, title_text, path=None, width=200, height=280, show_menu=True):
        super().__init__()
        self.thumb_path = thumb_path
        self.title_text = title_text
        self.path = path
        self.width = width
        self.height = height
        self.show_menu = show_menu
        self.setObjectName("thumbnailWidget")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Appliquer le style hover uniquement sur l'image
        self.setStyleSheet("")  # Pas de bordure sur le widget principal

        self.img_label = RoundedLabel()
        self.img_label.setContentsMargins(0, 0, 0, 0)
        self.update_image()
        self.img_label.setFixedSize(self.width, self.height)
        self.img_label.setStyleSheet("""
            border: 4px solid #111;
            border-radius: 14px;
            background: transparent;
            transition: border-color 0.2s;
        """)
        self.img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.img_label, alignment=Qt.AlignCenter)

        # Ajout du hover sur l'image
        self.img_label.setAttribute(Qt.WA_Hover, True)

        self.title_label = QLabel(self.title_text)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 15px; color: #222;")
        layout.addWidget(self.title_label)

        if self.show_menu and self.path:
            menu_btn = QPushButton("⋯")
            menu_btn.setFixedSize(32, 32)
            menu_btn.setStyleSheet("background: none; border: none; font-size: 22px; color: #444;")
            layout.addWidget(menu_btn, alignment=Qt.AlignCenter)
            menu = QMenu()
            
            # Action Set alias
            alias_action = menu.addAction("Set alias")
            alias_action.triggered.connect(lambda: self.alias_requested.emit(self.path, self.title_text))

            # Action "Add a Cover" (uniquement pour les dossiers)
            if os.path.isdir(self.path):
                cover_action = menu.addAction("Add a Cover")
                cover_action.triggered.connect(lambda: self.cover_requested.emit(self.path))
            
            menu.addAction("Open in Explorer")
            menu.addSeparator()
            remove_action = menu.addAction("Remove from bookshelf")
            remove_action.triggered.connect(lambda checked=False, p=self.path: self.remove_requested.emit(p))
            menu_btn.clicked.connect(lambda: menu.exec(menu_btn.mapToGlobal(menu_btn.rect().bottomLeft())))

    def update_image(self):
        """Met à jour l'image de la vignette"""
        try:
            print(f"Tentative de chargement de l'image: {self.thumb_path}")
            pixmap = QPixmap(self.thumb_path)
            if pixmap.isNull():
                print(f"Image nulle pour: {self.thumb_path}")
                # Créer une image par défaut programmatiquement
                default_pixmap = QPixmap(self.width, self.height)
                default_pixmap.fill(QColor(240, 240, 240))  # Fond gris clair
                
                painter = QPainter(default_pixmap)
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(default_pixmap.rect(), Qt.AlignCenter, "No\nPreview\nAvailable")
                painter.end()
                
                scaled_pixmap = default_pixmap.scaled(self.width, self.height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.img_label.setPixmap(scaled_pixmap)
            else:
                print(f"Image chargée avec succès: {self.thumb_path}")
                scaled_pixmap = pixmap.scaled(self.width, self.height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.img_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image {self.thumb_path}: {e}")
            # En cas d'erreur, créer une image par défaut
            try:
                error_pixmap = QPixmap(self.width, self.height)
                error_pixmap.fill(QColor(255, 200, 200))  # Fond rouge clair
                
                painter = QPainter(error_pixmap)
                painter.setPen(QColor(150, 0, 0))
                painter.drawText(error_pixmap.rect(), Qt.AlignCenter, "Error\nLoading\nImage")
                painter.end()
                
                self.img_label.setPixmap(error_pixmap)
            except:
                # En cas d'échec complet, afficher du texte
                self.img_label.setText("Error\nImage")
                self.img_label.setStyleSheet("border: 4px solid #111; border-radius: 14px; background: white; color: #666; font-size: 12px;")

    def update_thumbnail(self, new_thumb_path):
        """Met à jour la vignette avec une nouvelle image"""
        try:
            self.thumb_path = new_thumb_path
            self.update_image()
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la vignette: {e}")

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        # Appliquer le hover uniquement sur l'image
        self.img_label.setStyleSheet("""
            border: 4px solid #e74c3c;
            border-radius: 14px;
            background: transparent;
            transition: border-color 0.2s;
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.img_label.setStyleSheet("""
            border: 4px solid #111;
            border-radius: 14px;
            background: transparent;
            transition: border-color 0.2s;
        """)
        super().leaveEvent(event)

# =====================================================================================
# VUE RESPONSIVE (Grille pour dossiers ou PDFs)
# =====================================================================================
class ResponsiveGridView(QWidget):
    def __init__(self):
        super().__init__()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        
        # Aligner la grille en haut et au centre
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        grid_widget = QWidget()
        grid_widget.setLayout(self.grid_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(grid_widget)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent; width: 14px; margin: 4px 0 4px 0; border-radius: 7px;
            }
            QScrollBar::handle:vertical { background: #222; min-height: 40px; border-radius: 7px; }
            QScrollBar::handle:vertical:hover { background: #e74c3c; }
        """)
        
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
        self.thumbnail_generator = ThumbnailGenerator()
        self.thumbnail_generator.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.thumbnail_generator.start()
        self.pending_thumbnails = {}  # path -> widget
        self.load_library()
        self.setup_ui()
        self.refresh_shelf()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Création du header avec image de fond
        header_widget = RoundedHeaderWidget()
        header_widget.setFixedHeight(80)
        header_widget.set_background_image('assets/images/header.png')

        header = QHBoxLayout(header_widget)
        header.setContentsMargins(20, 20, 20, 20)
        
        back_btn = QPushButton("←")
        back_btn.setFixedSize(36, 36)
        back_btn.setStyleSheet("background: none; border: none; font-size: 28px;")
        back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(back_btn)

        title = QLabel("BookShelf")
        title.setFont(QFont("Inter", 32, QFont.Bold))
        title.setStyleSheet("color: #000000; background: transparent; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        filter_btn = QPushButton()
        filter_btn.setIcon(QIcon("assets/icons/funnel.svg"))
        filter_btn.setIconSize(QSize(28, 28))
        filter_btn.setStyleSheet("background: none; border: none;")
        filter_btn.setToolTip("Filtrer")
        filter_bar.addWidget(filter_btn)

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
        search_btn = QPushButton()
        search_btn.setIcon(QIcon("assets/icons/search.svg"))
        search_btn.setIconSize(QSize(28, 28))
        search_btn.setStyleSheet("background: none; border: none;")
        search_btn.setToolTip("Rechercher")
        search_btn.clicked.connect(toggle_search)
        filter_bar.addWidget(search_btn)

        self.sort_az = True
        self.sort_btn = QPushButton()
        self.sort_btn.setIcon(QIcon("assets/icons/sort-alpha-down.svg"))
        self.sort_btn.setIconSize(QSize(28, 28))
        self.sort_btn.setStyleSheet("background: none; border: none;")
        self.sort_btn.setToolTip("Trier A-Z")
        self.sort_btn.clicked.connect(self.toggle_sort)
        filter_bar.addWidget(self.sort_btn)

        header.addLayout(filter_bar)

        add_btn = QPushButton()
        add_btn.setIcon(QIcon("assets/icons/folder-plus.svg"))
        add_btn.setIconSize(QSize(32, 32))
        add_btn.setFixedSize(36, 36)
        add_btn.setStyleSheet('''
            QPushButton {
                background: none;
                border: none;
            }
            QPushButton:hover {
                background: #eee;
            }
        ''')
        add_btn.setToolTip("Ajouter un dossier")
        add_btn.clicked.connect(self.add_folder_clicked.emit)
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
            generate_all_thumbnails_for_folder(folder_path, progress_callback)
            progress_dialog.close()
            self.library.append({"path": folder_path})
            self.save_library()
            self.refresh_shelf()
    
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
                # Chercher la vignette pré-générée du dossier
                thumb_path = get_thumbnail_path(None, path)
                if thumb_path:
                    print(f"Utilisation vignette dossier: {thumb_path}")
                    vignette = ThumbnailWidget(thumb_path, name, path=path)
                else:
                    print(f"Pas de vignette pour le dossier: {path}")
                    # Créer l'image par défaut si elle n'existe pas
                    default_path = create_default_thumbnail() or "assets/images/manga_sample.png"
                    vignette = ThumbnailWidget(default_path, name, path=path)
                vignette.clicked.connect(functools.partial(self.folder_selected.emit, path))
                vignette.remove_requested.connect(self.remove_folder)
                vignette.alias_requested.connect(self.set_folder_alias)
                vignette.cover_requested.connect(self.set_folder_cover)
                widgets.append(vignette)
            valid_library.append(entry)
        # Met à jour la bibliothèque si des dossiers ont été supprimés
        if len(valid_library) != len(self.library):
            self.library = valid_library
            self.save_library()
        self.grid_view.set_items(widgets)

    def on_thumbnail_ready(self, path, thumbnail_path):
        """Appelé quand une vignette est prête"""
        try:
            if path in self.pending_thumbnails:
                widget = self.pending_thumbnails[path]
                # Pour les dossiers, forcer le rechargement du fichier _folder_thumb.png si c'est un dossier
                if os.path.isdir(path):
                    thumb_path = os.path.join(path, "_folder_thumb.png")
                    if os.path.exists(thumb_path):
                        widget.update_thumbnail(thumb_path)
                    else:
                        widget.update_thumbnail(thumbnail_path)
                else:
                    widget.update_thumbnail(thumbnail_path)
                del self.pending_thumbnails[path]
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la vignette: {e}")
            if path in self.pending_thumbnails:
                del self.pending_thumbnails[path]

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
            os.makedirs(thumb_dir, exist_ok=True)
            cover_path = os.path.join(thumb_dir, '_folder_thumb.png')

            try:
                # Copier et redimensionner l'image pour qu'elle corresponde aux vignettes
                pixmap = QPixmap(image_path)
                scaled_pixmap = pixmap.scaled(400, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
            
            if ok and new_alias.strip():
                # Mettre à jour l'alias
                entry["alias"] = new_alias.strip()
                self.save_library()
                self.refresh_shelf()

    def toggle_sort(self):
        if self.sort_az:
            self.library.sort(key=lambda d: d.get("alias", os.path.basename(d["path"])).lower())
            self.sort_btn.setIcon(QIcon("assets/icons/sort-alpha-up.svg"))
            self.sort_btn.setToolTip("Trier Z-A")
        else:
            self.library.sort(key=lambda d: d.get("alias", os.path.basename(d["path"])).lower(), reverse=True)
            self.sort_btn.setIcon(QIcon("assets/icons/sort-alpha-down.svg"))
            self.sort_btn.setToolTip("Trier A-Z")
        self.sort_az = not self.sort_az
        self.save_library()
        self.refresh_shelf()

# =====================================================================================
# PAGE DOSSIER (Vignettes PDF)
# =====================================================================================
class FolderViewPage(QWidget):
    file_selected = Signal(str)  # Changé de pdf_selected à file_selected
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.folder_path = ""
        self.grid_view = ResponsiveGridView()
        self.thumbnail_generator = ThumbnailGenerator()
        self.thumbnail_generator.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.thumbnail_generator.start()
        self.pending_thumbnails = {}  # path -> widget
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Création du header avec hauteur fixe
        self.header_widget = RoundedHeaderWidget()
        self.header_widget.setFixedHeight(80)
        
        header = QHBoxLayout(self.header_widget)
        header.setContentsMargins(20, 20, 20, 20)
        
        back_btn = QPushButton("←")
        back_btn.setFixedSize(36, 36)
        back_btn.setStyleSheet("background: none; border: none; font-size: 28px;")
        back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(back_btn)

        self.title_label = QLabel()
        self.title_label.setFont(QFont("Inter", 32, QFont.Bold))
        self.title_label.setStyleSheet("""
            color: #000000;
            background: transparent;
            border: none;
            outline: none;
            font-size: 32px;
            font-weight: bold;
            text-shadow: none;
            box-shadow: none;
            margin-bottom: 0px;
        """)
        self.path_label = QLabel()
        self.path_label.setFont(QFont("Arial", 11))
        self.path_label.setStyleSheet("""
            color: #000000;
            background: transparent;
            border: none;
            outline: none;
            text-shadow: none;
            box-shadow: none;
            margin-top: 0px;
        """)
        
        title_block = QVBoxLayout()
        title_block.setSpacing(0)  # Supprimer l'espace vertical
        title_block.setContentsMargins(0, 0, 0, 0)  # Supprimer les marges
        title_block.addWidget(self.title_label)
        title_block.addWidget(self.path_label)
        header.addLayout(title_block)
        header.addStretch()

        # Bouton pour définir l'image de fond du header
        bg_btn = QPushButton()
        bg_btn.setIcon(QIcon("assets/icons/palette.svg"))
        bg_btn.setIconSize(QSize(28, 28))
        bg_btn.setFixedSize(36, 36)
        bg_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
            }
            QPushButton:hover {
                color: #e74c3c;
                background: #f0f0f0;
                border-radius: 18px;
            }
        """)
        bg_btn.setToolTip("Définir l'image de fond du header")
        bg_btn.clicked.connect(self.set_header_background)
        header.addWidget(bg_btn)

        # Bouton de rafraîchissement
        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon("assets/icons/arrow-clockwise.svg"))
        refresh_btn.setIconSize(QSize(28, 28))
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
            }
            QPushButton:hover {
                color: #e74c3c;
                background: #f0f0f0;
                border-radius: 18px;
            }
        """)
        refresh_btn.setToolTip("Actualiser le dossier")
        refresh_btn.clicked.connect(self.refresh_folder)
        header.addWidget(refresh_btn)

        layout.addWidget(self.header_widget)
        layout.addWidget(self.grid_view)

    def set_folder(self, folder_path):
        self.folder_path = folder_path
        # Générer les vignettes à chaque accès au dossier
        generate_all_thumbnails_for_folder(folder_path)
        # Chercher l'alias dans la bibliothèque
        alias = None
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
        
        self.refresh_view()

    def load_header_background(self):
        """Charge l'image de fond du header"""
        try:
            # Chercher une image de fond personnalisée dans le dossier
            custom_bg_path = os.path.join(self.folder_path, "_header_bg.png")
            print(f"Recherche de l'image de fond personnalisée: {custom_bg_path}")
            
            if os.path.exists(custom_bg_path):
                print(f"Image personnalisée trouvée: {custom_bg_path}")
                # Utiliser l'image personnalisée
                self.header_widget.set_background_image(custom_bg_path)
                print("Image personnalisée appliquée au header")
                
                # Changer la couleur du titre et du chemin en blanc
                self.title_label.setStyleSheet("""
                    color: #000000;
                    background: transparent;
                    border: none;
                    outline: none;
                    font-size: 32px;
                    font-weight: bold;
                    text-shadow: none;
                    box-shadow: none;
                    margin-bottom: 0px;
                """)
                self.path_label.setStyleSheet("""
                    color: #000000;
                    background: transparent;
                    border: none;
                    outline: none;
                    text-shadow: none;
                    box-shadow: none;
                    margin-top: 0px;
                """)
            else:
                print(f"Image personnalisée non trouvée, utilisation de l'image par défaut")
                # Utiliser l'image par défaut
                default_bg_path = "assets/images/header.png"
                if os.path.exists(default_bg_path):
                    self.header_widget.set_background_image(default_bg_path)
                    print("Image par défaut appliquée au header")
                    
                    # Changer la couleur du titre et du chemin en blanc pour l'image par défaut aussi
                    self.title_label.setStyleSheet("""
                        color: #000000;
                        background: transparent;
                        border: none;
                        outline: none;
                        font-size: 32px;
                        font-weight: bold;
                        text-shadow: none;
                        box-shadow: none;
                        margin-bottom: 0px;
                    """)
                    self.path_label.setStyleSheet("""
                        color: #000000;
                        background: transparent;
                        border: none;
                        outline: none;
                        text-shadow: none;
                        box-shadow: none;
                        margin-top: 0px;
                    """)
                else:
                    print(f"Image par défaut non trouvée, utilisation du style par défaut")
                    # Fallback vers le style par défaut (pas d'image)
                    self.header_widget.set_background_image(None)
                    
                    # Remettre les couleurs par défaut
                    self.title_label.setStyleSheet("""
                        color: #000;
                        background: transparent;
                        border: none;
                        outline: none;
                        font-size: 32px;
                        font-weight: bold;
                        text-shadow: none;
                        box-shadow: none;
                        margin-bottom: 0px;
                    """)
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
            # Fallback vers le style par défaut
            self.header_widget.set_background_image(None)
            
            # Remettre les couleurs par défaut
            self.title_label.setStyleSheet("""
                color: #000;
                background: transparent;
                border: none;
                outline: none;
                font-size: 32px;
                font-weight: bold;
                text-shadow: none;
                box-shadow: none;
                margin-bottom: 0px;
            """)
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
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
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
        # Inclure les PDF, CBZ, ZIP et RAR
        supported_files = [f for f in os.listdir(self.folder_path) 
                          if f.lower().endswith(('.pdf', '.cbz', '.zip', '.rar'))]
        supported_files.sort()
        
        for file in supported_files:
            path = os.path.join(self.folder_path, file)
            base = os.path.splitext(file)[0]
            
            # Chercher la vignette pré-générée du fichier
            thumb_path = get_thumbnail_path(path)
            if thumb_path:
                print(f"Utilisation vignette fichier: {thumb_path}")
                vignette = ThumbnailWidget(thumb_path, base, path=path)
            else:
                print(f"Pas de vignette pour le fichier: {path}")
                # Créer l'image par défaut si elle n'existe pas
                default_path = create_default_thumbnail() or "assets/images/manga_sample.png"
                vignette = ThumbnailWidget(default_path, base, path=path)
            
            vignette.clicked.connect(functools.partial(self.file_selected.emit, path))
            vignette.remove_requested.connect(self.remove_file)
            widgets.append(vignette)
        self.grid_view.set_items(widgets)

    def on_thumbnail_ready(self, path, thumbnail_path):
        """Appelé quand une vignette est prête"""
        try:
            if path in self.pending_thumbnails:
                widget = self.pending_thumbnails[path]
                # Vérifier que le widget existe toujours
                if widget and not widget.isHidden():
                    widget.update_thumbnail(thumbnail_path)
                del self.pending_thumbnails[path]
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la vignette: {e}")
            # En cas d'erreur, supprimer de la liste des en attente
            if path in self.pending_thumbnails:
                del self.pending_thumbnails[path]

    def remove_file(self, file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
        self.refresh_view()

    def refresh_folder(self):
        """Actualise le dossier en régénérant les vignettes et en affichant les nouveaux fichiers"""
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
        self.back_btn.setStyleSheet("background: none; border: none; font-size: 24px;")
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
        self.pdf_label.setAlignment(Qt.AlignCenter)
        
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.pdf_label)
        self.scroll.setWidgetResizable(True)
        
        layout.addLayout(nav_layout)
        layout.addWidget(self.scroll)

    def calculate_optimal_zoom(self, page=None, image=None):
        """Calcule le facteur de zoom optimal pour afficher la page complète à la hauteur de la fenêtre"""
        # Obtenir la hauteur disponible de la fenêtre (en tenant compte de la barre de navigation)
        available_height = self.scroll.height() - 40  # 40px de marge pour la navigation
        
        if available_height <= 0:
            return 1.0
        
        if self.file_type == 'pdf' and page:
            # Pour les PDF
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
        elif self.file_type == 'cbz' and image:
            # Pour les CBZ
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

    def load_file(self, path):
        try:
            self.file_path = path
            if path.lower().endswith('.pdf'):
                self.file_type = 'pdf'
            elif path.lower().endswith('.cbz') or path.lower().endswith('.zip'):
                self.file_type = 'cbz'
            elif path.lower().endswith('.rar'):
                self.file_type = 'rar'
            else:
                self.file_type = None
            self.rar_file = None
            if self.file_type == 'pdf':
                self.doc = fitz.open(path)
                self.total_pages = len(self.doc)
                self.zip_file = None
            elif self.file_type == 'cbz':
                self.zip_file = zipfile.ZipFile(path, 'r')
                image_files = [f for f in self.zip_file.namelist() 
                              if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
                image_files.sort()
                self.cbz_images = image_files
                self.total_pages = len(self.cbz_images)
                self.doc = None
            elif self.file_type == 'rar':
                self.rar_file = rarfile.RarFile(path, 'r')
                image_files = [f for f in self.rar_file.namelist() 
                              if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
                image_files.sort()
                self.cbz_images = image_files
                self.total_pages = len(self.cbz_images)
                self.doc = None
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
        if (self.doc and self.file_type == 'pdf') or (self.zip_file and self.file_type == 'zip') or (self.rar_file and self.file_type == 'rar'):
            self.zoom_timer.start(50)  # Délai plus court pour l'affichage
        # Donner le focus à cette page pour recevoir les événements clavier
        self.setFocus()

    def display_page(self, page_num):
        if not self.doc and not self.zip_file and not hasattr(self, 'rar_file'):
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
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
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
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
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
        if event.key() == Qt.Key_Left or event.key() == Qt.Key_Up:
            # Flèche gauche ou haut : page précédente
            if self.current_page > 0:
                self.previous_page()
        elif event.key() == Qt.Key_Right or event.key() == Qt.Key_Down:
            # Flèche droite ou bas : page suivante
            if self.current_page < self.total_pages - 1:
                self.next_page()
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            # Touche + ou = : zoom avant
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            # Touche - : zoom arrière
            self.zoom_out()
        elif event.key() == Qt.Key_Home:
            # Touche Home : première page
            self.display_page(0)
        elif event.key() == Qt.Key_End:
            # Touche End : dernière page
            self.display_page(self.total_pages - 1)
        elif event.key() == Qt.Key_Escape:
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
        self.setWindowIcon(QIcon("assets/images/logo.png"))

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
        self.stacked_widget.setCurrentWidget(self.home_page)
    
    def show_bookshelf(self):
        self.bookshelf_page.refresh_shelf()
        self.stacked_widget.setCurrentWidget(self.bookshelf_page)

    def show_folder_view(self, path):
        self.folder_view_page.set_folder(path)
        self.stacked_widget.setCurrentWidget(self.folder_view_page)

    def show_pdf_viewer(self, path):
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
    os.makedirs(thumb_dir, exist_ok=True)
    first_file_found = None
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.cbz', '.zip', '.rar'))]
    total = len(files)
    for idx, file in enumerate(files):
        file_lower = file.lower()
        file_path = os.path.join(folder_path, file)
        if progress_callback:
            progress_callback(f"Chargement de l'image de la vignette : {file}", int((idx+1)/total*100))
        base = os.path.splitext(file)[0]
        thumb_path = os.path.join(thumb_dir, base + '.png')
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
                                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
                        if image_files:
                            image_files.sort()
                            first_image = image_files[0]
                            with zip_file.open(first_image) as image_file:
                                image_data = image_file.read()
                                qimage = QImage()
                                if qimage.loadFromData(image_data):
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                    scaled_pixmap.save(thumb_path)
                                    if first_file_found is None:
                                        first_file_found = file_path
                elif file_lower.endswith('.rar'):
                    with rarfile.RarFile(file_path, 'r') as rar:
                        image_files = [f for f in rar.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
                        if image_files:
                            image_files.sort()
                            first_image = image_files[0]
                            with rar.open(first_image) as image_file:
                                image_data = image_file.read()
                                qimage = QImage()
                                if qimage.loadFromData(image_data):
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                    scaled_pixmap.save(thumb_path)
                                    if first_file_found is None:
                                        first_file_found = file_path
            except Exception as e:
                print(f"Erreur vignette {file_path}: {e}")
    if first_file_found:
        folder_thumb_path = os.path.join(thumb_dir, '_folder_thumb.png')
        if not os.path.exists(folder_thumb_path) or os.path.getmtime(folder_thumb_path) < os.path.getmtime(first_file_found):
            try:
                if first_file_found.lower().endswith('.pdf'):
                    doc = fitz.open(first_file_found)
                    if len(doc) > 0:
                        page = doc[0]
                        pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                        pix.save(folder_thumb_path)
                    doc.close()
                elif first_file_found.lower().endswith('.cbz') or first_file_found.lower().endswith('.zip'):
                    with zipfile.ZipFile(first_file_found, 'r') as zip_file:
                        image_files = [f for f in zip_file.namelist() 
                                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
                        if image_files:
                            image_files.sort()
                            first_image = image_files[0]
                            with zip_file.open(first_image) as image_file:
                                image_data = image_file.read()
                                qimage = QImage()
                                if qimage.loadFromData(image_data):
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                    scaled_pixmap.save(folder_thumb_path)
                elif first_file_found.lower().endswith('.rar'):
                    with rarfile.RarFile(first_file_found, 'r') as rar:
                        image_files = [f for f in rar.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
                        if image_files:
                            image_files.sort()
                            first_image = image_files[0]
                            with rar.open(first_image) as image_file:
                                image_data = image_file.read()
                                qimage = QImage()
                                if qimage.loadFromData(image_data):
                                    pixmap = QPixmap.fromImage(qimage)
                                    scaled_pixmap = pixmap.scaled(400, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "File\nPreview\nNot\nAvailable")
        painter.end()
        
        # Sauvegarder l'image par défaut
        default_path = "assets/images/manga_sample.png"
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        pixmap.save(default_path)
        return default_path
    except Exception as e:
        print(f"Erreur création image par défaut: {e}")
        return None

def get_thumbnail_path(file_path, folder_path=None):
    """Retourne le chemin de la vignette pour un fichier ou dossier"""
    try:
        if folder_path:
            # Pour un dossier, chercher _folder_thumb.png
            thumb_dir = os.path.join(folder_path, '.thumbnails')
            thumb_path = os.path.join(thumb_dir, '_folder_thumb.png')
        else:
            # Pour un fichier (PDF ou CBZ), chercher nom_du_fichier.png
            base = os.path.splitext(os.path.basename(file_path))[0]
            thumb_dir = os.path.join(os.path.dirname(file_path), '.thumbnails')
            thumb_path = os.path.join(thumb_dir, base + '.png')
        
        if os.path.exists(thumb_path):
            print(f"Vignette trouvée: {thumb_path}")
            return thumb_path
        else:
            print(f"Vignette non trouvée: {thumb_path}")
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

def main():
    app = QApplication(sys.argv)
    
    # Régénérer toutes les vignettes au démarrage
    regenerate_all_thumbnails()
    
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
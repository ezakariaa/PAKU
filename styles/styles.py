"""
Fichier central pour les styles QSS de l'application.
"""

# =====================================================================================
# PAGE D'ACCUEIL
# =====================================================================================
# Même grammaire de pilules que les en-têtes, transposée sur fond clair.
# Qt ne dessine les coins arrondis que si le rayon ne dépasse pas la demi-hauteur
# du bloc peint : chaque bouton reçoit donc une hauteur fixe et le rayon qui va avec.
HOME_SUPPORT_HEIGHT = 40

# Action principale : entrer dans la bibliothèque.
HOME_PRIMARY_BUTTON_STYLE = """
    QPushButton {
        background: #e74c3c;
        border: none;
        border-radius: 27px;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        font-weight: bold;
    }
    QPushButton:hover   { background: #ef6152; }
    QPushButton:pressed { background: #c9402f; }
"""

# Action secondaire : ouvrir un fichier isolé.
HOME_SECONDARY_BUTTON_STYLE = """
    QPushButton {
        background: #ffffff;
        border: 2px solid #d9dde3;
        border-radius: 27px;
        color: #1b1f27;
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        font-weight: bold;
    }
    QPushButton:hover   { border-color: #e74c3c; color: #e74c3c; }
    QPushButton:pressed { background: #f2f4f6; }
"""

# Sous-titre sous le logo.
HOME_SUBTITLE_STYLE = "color: #5a6270; background: transparent; border: none;"

# Boutons de soutien : couleurs de marque conservées, forme alignée sur le reste.
BMC_BUTTON_STYLE = """
    QPushButton {
        background-color: #FFDD00;
        color: #1b1f27;
        border: none;
        border-radius: 20px;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: bold;
        padding: 0px 26px;
    }
    QPushButton:hover { background-color: #ffe74d; }
"""

PAYPAL_BUTTON_STYLE = """
    QPushButton {
        background-color: #0070ba;
        color: #ffffff;
        border: none;
        border-radius: 20px;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: bold;
        padding: 0px 26px;
    }
    QPushButton:hover { background-color: #0086dd; }
"""

# Style pour l'image de la vignette
THUMBNAIL_IMAGE_STYLE = """
    border: 4px solid #111;
    border-radius: 14px;
    background: transparent;
    transition: border-color 0.2s;
"""

# Style pour l'image de la vignette au survol
THUMBNAIL_IMAGE_HOVER_STYLE = """
    border: 4px solid #e74c3c;
    border-radius: 14px;
    background: transparent;
    transition: border-color 0.2s;
"""

# Style pour le menu de la vignette, posé sur le coin de la pochette
THUMBNAIL_MENU_BUTTON_STYLE = """
    QPushButton {
        background: rgba(17, 20, 27, 0.62);
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 14px;
    }
    QPushButton:hover   { background: #e74c3c; }
    QPushButton:pressed { background: #c9402f; }
"""

# =====================================================================================
# BOÎTE DE PROGRESSION
# =====================================================================================
# Carte sombre flottante, même matière que les en-têtes.
PROGRESS_CARD_STYLE = """
    QWidget#progressCard {
        background: #11141b;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 16px;
    }
"""

PROGRESS_TITLE_STYLE = "color: #ffffff; background: transparent; border: none;"
PROGRESS_PERCENT_STYLE = "color: #e74c3c; background: transparent; border: none;"
PROGRESS_MESSAGE_STYLE = "color: rgba(255, 255, 255, 0.60); background: transparent; border: none;"

# Barre fine : rayon = demi-hauteur, sinon Qt abandonne l'arrondi.
PROGRESS_BAR_STYLE = """
    QProgressBar {
        background: rgba(255, 255, 255, 0.12);
        border: none;
        border-radius: 4px;
    }
    QProgressBar::chunk {
        background: #e74c3c;
        border-radius: 4px;
    }
"""

# Style pour les zones de défilement
SCROLL_AREA_STYLE = """
    QScrollArea { background: transparent; border: none; }
    QScrollBar:vertical {
        background: transparent; width: 14px; margin: 4px 0 4px 0;
        border-radius: 7px;
    }
    QScrollBar::handle:vertical {
        background: #222; min-height: 40px; border-radius: 7px;
    }
    QScrollBar::handle:vertical:hover { background: #e74c3c; }
"""

# Style pour les boutons icônes simples (sans hover)
ICON_BUTTON_STYLE = "background: none; border: none;"

# Style pour le bouton d'ajout de la bibliothèque
BOOKSHELF_ADD_BUTTON_STYLE = """
    QPushButton {
        background: none;
        border: none;
    }
    QPushButton:hover {
        background: #eee;
    }
"""

# =====================================================================================
# BARRE D'EN-TETE DE LA BIBLIOTHEQUE
# =====================================================================================
# Accent de l'application, deja utilise par les vignettes et l'ascenseur.
ACCENT = "#e74c3c"
ACCENT_HOVER = "#ef6152"
ACCENT_PRESSED = "#c9402f"

# Titre : blanc, pose sur le voile sombre du header.
PAGE_TITLE_STYLE_BOOKSHELF = """
    color: #ffffff;
    background: transparent;
    border: none;
    outline: none;
"""

# Ligne secondaire sous le titre (nombre de collections).
HEADER_SUBTITLE_STYLE = """
    color: rgba(255, 255, 255, 0.60);
    background: transparent;
    border: none;
    outline: none;
"""

# Pilule translucide qui reunit les actions secondaires.
HEADER_TOOLBAR_STYLE = """
    QWidget#headerToolbar {
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 21px;
    }
"""

# Boutons icone de la pilule : plats au repos, l'accent ne sort qu'a l'etat actif.
HEADER_ICON_BUTTON_STYLE = """
    QPushButton {
        background: transparent;
        border: none;
        border-radius: 17px;
    }
    QPushButton:hover        { background: rgba(255, 255, 255, 0.18); }
    QPushButton:pressed      { background: rgba(255, 255, 255, 0.30); }
    QPushButton:checked      { background: #e74c3c; }
    QPushButton:checked:hover{ background: #ef6152; }
"""

# Bouton retour : detache de la pilule, mais meme matiere.
HEADER_BACK_BUTTON_STYLE = """
    QPushButton {
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 21px;
    }
    QPushButton:hover   { background: rgba(255, 255, 255, 0.20); }
    QPushButton:pressed { background: rgba(255, 255, 255, 0.30); }
"""

# Champ de recherche, integre a la pilule.
HEADER_SEARCH_STYLE = """
    QLineEdit {
        background: rgba(0, 0, 0, 0.32);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 16px;
        padding: 0px 14px;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        selection-background-color: #e74c3c;
    }
    QLineEdit:focus { border: 1px solid #e74c3c; }
"""

# Action principale : ajouter un dossier.
HEADER_PRIMARY_BUTTON_STYLE = """
    QPushButton {
        background: #e74c3c;
        border: none;
        border-radius: 21px;
        padding: 0px 20px 0px 16px;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover   { background: #ef6152; }
    QPushButton:pressed { background: #c9402f; }
"""

# Style pour les icônes du header Bookshelf
ICON_BUTTON_STYLE_BOOKSHELF = "background: none; border: none; color: #000;"

# Style pour le titre du header dossier
PAGE_TITLE_STYLE = """
    color: #fff;
    background: transparent;
    border: none;
    outline: none;
    font-size: 32px;
    font-family: 'Inter', sans-serif;
    font-weight: bold;
    text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.85);
    box-shadow: none;
    margin-bottom: 0px;
"""

# Style pour le chemin du header dossier
FOLDER_PATH_STYLE = """
    color: #fff;
    background: transparent;
    border: none;
    outline: none;
    font-family: 'Inter', sans-serif;
    text-shadow: 1px 1px 6px rgba(0, 0, 0, 0.8);
    box-shadow: none;
    margin-top: 0px;
"""

# Style pour les icônes du header dossier
ICON_BUTTON_STYLE_FOLDER = "background: none; border: none; color: #fff;"

# Style pour les boutons d'icônes avec effet de survol
HOVER_ICON_BUTTON_STYLE = """
    QPushButton {
        background: none;
        border: none;
    }
    QPushButton:hover {
        color: #e74c3c;
        background: #f0f0f0;
        border-radius: 18px;
    }
""" 

# =====================================================================================
# FENETRE DE PARAMETRES
# =====================================================================================
# Bouton engrenage de la page d'accueil : meme pilule que les actions voisines,
# mais carre-arrondi pour ne pas concurrencer les deux entrees principales.
HOME_ICON_BUTTON_STYLE = """
    QPushButton {
        background: #ffffff;
        border: 2px solid #d9dde3;
        border-radius: 27px;
    }
    QPushButton:hover   { border-color: #e74c3c; background: #fdf1ef; }
    QPushButton:pressed { background: #f2f4f6; }
"""

# Fond de la fenetre : le meme blanc casse que le reste de l'application.
SETTINGS_WINDOW_STYLE = """
    QDialog { background: #f6fafd; }
    QWidget#settingsBody { background: transparent; }
"""

SETTINGS_TITLE_STYLE = """
    color: #1b1f27;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 26px;
    font-weight: bold;
"""

SETTINGS_SUBTITLE_STYLE = """
    color: #6b7280;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
"""

# Onglets : plats, l'onglet actif est souligne par l'accent.
SETTINGS_TAB_BUTTON_STYLE = """
    QPushButton {
        background: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        padding: 8px 4px;
        color: #6b7280;
        font-family: 'Inter', sans-serif;
        font-size: 15px;
    }
    QPushButton:hover   { color: #1b1f27; }
    QPushButton:checked {
        color: #1b1f27;
        font-weight: bold;
        border-bottom: 3px solid #e74c3c;
    }
"""

# Titre de section, precede d'une barre d'accent dessinee par un QFrame.
SETTINGS_SECTION_TITLE_STYLE = """
    color: #1b1f27;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    font-weight: bold;
"""

SETTINGS_SECTION_BAR_STYLE = "background: #e74c3c; border: none; border-radius: 2px;"

# Carte blanche qui porte un reglage.
SETTINGS_ROW_STYLE = """
    QWidget#settingsRow {
        background: #ffffff;
        border: 1px solid #e6e9ee;
        border-radius: 12px;
    }
"""

SETTINGS_ROW_LABEL_STYLE = """
    color: #1b1f27;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: bold;
"""

SETTINGS_ROW_DESC_STYLE = """
    color: #6b7280;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
"""

SETTINGS_VALUE_STYLE = """
    color: #1b1f27;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: bold;
"""

SETTINGS_COMBO_STYLE = """
    QComboBox {
        background: #ffffff;
        border: 1px solid #d9dde3;
        border-radius: 8px;
        padding: 6px 12px;
        color: #1b1f27;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
    }
    QComboBox:hover { border-color: #e74c3c; }
    /* Pas de regle ::drop-down : la fleche reste celle du style Fusion. La
       redessiner demanderait une image, et un chemin en dur ne survit pas a
       l'empaquetage PyInstaller. */
    QComboBox QAbstractItemView {
        background: #ffffff;
        border: 1px solid #d9dde3;
        outline: none;
        selection-background-color: #e74c3c;
        selection-color: #ffffff;
    }
"""

SETTINGS_SLIDER_STYLE = """
    QSlider::groove:horizontal {
        height: 4px; background: #e6e9ee; border-radius: 2px;
    }
    QSlider::sub-page:horizontal {
        height: 4px; background: #e74c3c; border-radius: 2px;
    }
    QSlider::handle:horizontal {
        width: 16px; height: 16px; margin: -6px 0;
        background: #ffffff; border: 2px solid #e74c3c; border-radius: 8px;
    }
    QSlider::handle:horizontal:hover { background: #fdf1ef; }
"""

# Bouton d'action dans une carte (vider le cache, ouvrir un dossier...).
SETTINGS_ACTION_BUTTON_STYLE = """
    QPushButton {
        background: #ffffff;
        border: 2px solid #d9dde3;
        border-radius: 16px;
        padding: 0px 16px;
        color: #1b1f27;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover   { border-color: #e74c3c; color: #e74c3c; }
    QPushButton:pressed { background: #f2f4f6; }
"""

# Barre du bas : une action pleine a droite, une action discrete a gauche.
SETTINGS_PRIMARY_BUTTON_STYLE = """
    QPushButton {
        background: #e74c3c;
        border: none;
        border-radius: 18px;
        padding: 0px 22px;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover   { background: #ef6152; }
    QPushButton:pressed { background: #c9402f; }
"""

SETTINGS_LINK_BUTTON_STYLE = """
    QPushButton {
        background: transparent;
        border: none;
        color: #6b7280;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
    }
    QPushButton:hover { color: #e74c3c; }
"""

# Interrupteur : les couleurs sont peintes a la main, QSS ne sait pas dessiner
# un rail et sa pastille. Elles vivent ici pour rester avec le reste du theme.
SETTINGS_SWITCH_COLORS = {
    "track_off": "#d9dde3",
    "track_on": "#e74c3c",
    "track_off_hover": "#c9cfd8",
    "track_on_hover": "#ef6152",
    "knob": "#ffffff",
}


# =====================================================================================
# BARRE DU LECTEUR
# =====================================================================================
# Meme grammaire que les en-tetes de la bibliotheque - un retour detache, des
# actions reunies dans une pilule - mais transposee sur fond clair : ici c'est
# la page du manga qui doit tenir l'attention, pas la barre.
READER_BAR_HEIGHT = 56
READER_BTN_SIZE = 34
READER_GROUP_HEIGHT = 42

# Fond de la barre : une bande blanche posee sur le fond de l'application.
READER_BAR_STYLE = """
    QWidget#readerBar {
        background: #ffffff;
        border: 1px solid #e6e9ee;
        border-radius: 14px;
    }
"""

# Pilule claire qui reunit une famille d'actions (navigation, zoom).
READER_GROUP_STYLE = """
    QWidget#readerGroup {
        background: #f2f4f6;
        border: 1px solid #e6e9ee;
        border-radius: 21px;
    }
"""

# Boutons icone : plats au repos, l'accent n'apparait qu'au survol. Desactives,
# ils s'effacent au lieu de disparaitre, pour que la barre garde sa forme.
READER_ICON_BUTTON_STYLE = """
    QPushButton {
        background: transparent;
        border: none;
        border-radius: 17px;
    }
    QPushButton:hover    { background: rgba(231, 76, 60, 0.12); }
    QPushButton:pressed  { background: rgba(231, 76, 60, 0.22); }
    QPushButton:disabled { background: transparent; }
"""

# Retour : detache de la pilule, cercle blanc borde comme sur l'accueil.
READER_BACK_BUTTON_STYLE = """
    QPushButton {
        background: #ffffff;
        border: 2px solid #d9dde3;
        border-radius: 21px;
    }
    QPushButton:hover   { border-color: #e74c3c; background: #fdf1ef; }
    QPushButton:pressed { background: #f2f4f6; }
"""

# Compteur de pages : la page courante ressort, le total reste en retrait.
READER_PAGE_LABEL_STYLE = """
    color: #1b1f27;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
"""

# Niveau de zoom : c'est aussi le bouton qui rend la page a la fenetre.
READER_ZOOM_LABEL_STYLE = """
    QPushButton {
        background: transparent;
        border: none;
        border-radius: 15px;
        padding: 0px 8px;
        color: #5a6270;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover   { background: rgba(231, 76, 60, 0.12); color: #e74c3c; }
    QPushButton:pressed { background: rgba(231, 76, 60, 0.22); }
"""

# Zone de lecture : une seconde carte sous la barre, pour que la page soit
# posee sur quelque chose plutot que flottante sur le fond de l'application.
READER_VIEW_STYLE = """
    QScrollArea#readerView {
        background: transparent;
        border: 1px solid #e6e9ee;
        border-radius: 14px;
    }
    QScrollBar:vertical {
        background: transparent; width: 12px; margin: 6px 2px 6px 0;
        border-radius: 6px;
    }
    QScrollBar:horizontal {
        background: transparent; height: 12px; margin: 0 6px 2px 6px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical {
        background: #c2c9d3; min-height: 40px; border-radius: 6px;
    }
    QScrollBar::handle:horizontal {
        background: #c2c9d3; min-width: 40px; border-radius: 6px;
    }
    QScrollBar::handle:vertical:hover,
    QScrollBar::handle:horizontal:hover { background: #e74c3c; }
    /* Fleches de bout de barre : elles n'apportent rien a la lecture. */
    QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
    QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""

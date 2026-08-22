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

# Style pour le bouton retour
BACK_BUTTON_STYLE = "background: none; border: none; font-size: 28px;"

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
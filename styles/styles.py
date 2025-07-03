"""
Fichier central pour les styles QSS de l'application.
"""

# Style pour les boutons de la page d'accueil (Ouvrir / Bibliothèque)
HOME_PAGE_BUTTON_STYLE = """
    QPushButton {
        background-color: #fff;
        border: 4px solid #000;
        font-size: 22px;
        font-family: "Inter";
        border-radius: 20px;
    }
    QPushButton:hover { background-color: #eee; }
"""

# Style pour le bouton "Buy me a coffee"
BMC_BUTTON_STYLE = """
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

# Style pour le menu de la vignette
THUMBNAIL_MENU_BUTTON_STYLE = """
    background: none;
    border: none;
    font-size: 22px;
    color: #444;
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

# Style pour le titre du header Bookshelf
PAGE_TITLE_STYLE_BOOKSHELF = """
    color: #000;
    background: transparent;
    border: none;
    outline: none;
    font-size: 32px;
    font-family: 'Inter', sans-serif;
    font-weight: bold;
    text-shadow: none;
    box-shadow: none;
    margin-bottom: 0px;
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
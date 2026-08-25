"""
Fichier central pour les styles QSS de l'application.

Les couleurs qui changent avec le theme s'ecrivent en jetons - @surface, @text,
@border... - et sont resolues par `set_theme()`. Les modules lisent la feuille
resolue via l'objet `S` : `S.HOME_PRIMARY_BUTTON_STYLE`. Comme `S` est mute sur
place, une bascule de theme suffit a mettre tout le monde a jour ; il reste aux
pages a se reconstruire pour reposer leurs feuilles sur les widgets.

L'accent rouge, les en-tetes poses sur une image (voile sombre, texte blanc) et
la carte de progression ne dependent pas du theme : ils sont ecrits en dur.
"""

# =====================================================================================
# PALETTES
# =====================================================================================
PALETTES = {
    "light": {
        "bg": "#f6fafd",             # fond de l'application
        "surface": "#ffffff",        # cartes, barres, champs
        "surface_alt": "#f2f4f6",    # pilules et etats enfonces
        "border": "#e6e9ee",
        "border_strong": "#d9dde3",
        "border_hover": "#c9cfd8",
        "text": "#1b1f27",
        "text_muted": "#5a6270",
        "text_soft": "#8b94a3",      # le total de pages, a cote du numero courant
        "thumb_border": "#111111",
        "scroll_handle": "#b8c1cd",
        "accent_tint": "#fdf1ef",    # survol tres pale d'un bouton borde
        "accent_wash": "rgba(231, 76, 60, 0.12)",
        "accent_wash_strong": "rgba(231, 76, 60, 0.22)",
        "tag_bg": "#e6dca4",
        "tag_text": "#444444",
        "shadow": "#0b1220",
        "shadow_alpha": "135",
    },
    "dark": {
        "bg": "#14171d",
        "surface": "#1e222a",
        "surface_alt": "#272c35",
        "border": "#333a45",
        "border_strong": "#414a57",
        "border_hover": "#4d5766",
        "text": "#e8eaee",
        "text_muted": "#9aa3b0",
        "text_soft": "#6f7885",
        "thumb_border": "#39414d",
        "scroll_handle": "#49525f",
        "accent_tint": "#2b2024",
        "accent_wash": "rgba(231, 76, 60, 0.22)",
        "accent_wash_strong": "rgba(231, 76, 60, 0.34)",
        "tag_bg": "#3b3524",
        "tag_text": "#e6dca4",
        "shadow": "#000000",
        "shadow_alpha": "225",
    },
}

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
        background: @surface;
        border: 2px solid @border_strong;
        border-radius: 27px;
        color: @text;
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        font-weight: bold;
    }
    QPushButton:hover   { border-color: #e74c3c; color: #e74c3c; }
    QPushButton:pressed { background: @surface_alt; }
"""

# Sous-titre sous le logo.
HOME_SUBTITLE_STYLE = "color: @text_muted; background: transparent; border: none;"

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
    border: 4px solid @thumb_border;
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

# Ombre portée sous une pochette. QSS ne sait pas dessiner d'ombre : c'est un
# QGraphicsDropShadowEffect qui s'en charge, d'où des valeurs et non du style.
# Le flou et le décalage doivent rester dans la marge laissée par la vignette
# (THUMB_SHADOW_MARGINS dans main.py), sinon le bord de l'ombre est rogné.
THUMBNAIL_SHADOW_COLORS = {
    "color": "@shadow",
    "alpha": "@shadow_alpha",
    "blur": "30",
    # Ombre purement descendante : avec le cadre noir de la pochette, un decalage
    # lateral se lit comme un defaut d'alignement plutot que comme une ombre.
    "offset_x": "0",
    "offset_y": "9",
}

# Pastille de statut, juste au-dessus du nombre de chapitres. Ici la couleur
# porte le sens : elle ne suit donc pas le theme, seulement le statut.
THUMBNAIL_STATUS_COLORS = {
    "ongoing": "#2f6fb0",
    "finished": "#1f8a4c",
    "alpha": "235",
    "border": "#ffffff",
    # Contour plus franc que celui du compteur : sa couleur pouvant tomber sur
    # une pochette de la meme teinte, c'est le liseré qui detache la pastille.
    "border_alpha": "150",
    "text": "#ffffff",
}

# Pastille du nombre de chapitres, posée sur la pochette. Elle est peinte sur
# l'illustration, jamais sur le fond de l'application : ses couleurs ne suivent
# donc pas le thème, comme la pastille de menu juste au-dessus.
THUMBNAIL_BADGE_COLORS = {
    "background": "#11141b",
    "background_alpha": "190",
    "border": "#ffffff",
    "border_alpha": "56",
    "text": "#ffffff",
}

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

# Menu de la pastille ⋯ : une carte posee sur la grille, meme matiere que les
# autres surfaces du theme. Le fond translucide de la fenetre laisse les coins
# arrondis se decouper proprement (voir make_thumbnail_menu dans main.py).
THUMBNAIL_MENU_STYLE = """
    QMenu {
        background: @surface;
        border: 1px solid @border;
        border-radius: 12px;
        padding: 6px;
        color: @text;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
    }
    QMenu::item {
        padding: 8px 26px 8px 10px;
        margin: 1px 2px;
        border-radius: 8px;
    }
    QMenu::item:selected {
        background: @accent_wash;
        color: #e74c3c;
    }
    QMenu::item:disabled { color: @text_soft; }
    QMenu::icon { margin-left: 10px; }
    /* La coche d'une langue occupe la meme gouttiere que les icones. */
    QMenu::indicator {
        width: 16px; height: 16px;
        margin-left: 10px;
    }
    QMenu::separator {
        height: 1px;
        background: @border;
        margin: 6px 10px;
    }
    QMenu::right-arrow { width: 10px; height: 10px; margin-right: 10px; }
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

# Ascenseurs de toute l'application : fins, arrondis, sans les flèches de bout
# que Fusion dessine à sa façon et qui juraient avec le reste.
SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        background: transparent; width: 12px; margin: 6px 2px 6px 0;
        border-radius: 6px;
    }
    QScrollBar:horizontal {
        background: transparent; height: 12px; margin: 0 6px 2px 6px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical {
        background: @scroll_handle; min-height: 40px; border-radius: 6px;
    }
    QScrollBar::handle:horizontal {
        background: @scroll_handle; min-width: 40px; border-radius: 6px;
    }
    QScrollBar::handle:vertical:hover,
    QScrollBar::handle:horizontal:hover { background: #e74c3c; }
    QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
    QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""

# Style pour les zones de défilement
SCROLL_AREA_STYLE = """
    QScrollArea { background: transparent; border: none; }
""" + SCROLLBAR_STYLE

# Style pour les boutons icônes simples (sans hover)
ICON_BUTTON_STYLE = "background: none; border: none;"

# Style pour le bouton d'ajout de la bibliothèque
BOOKSHELF_ADD_BUTTON_STYLE = """
    QPushButton {
        background: none;
        border: none;
    }
    QPushButton:hover {
        background: @surface_alt;
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
ICON_BUTTON_STYLE_BOOKSHELF = "background: none; border: none; color: @text;"

# Style pour le titre du header dossier
PAGE_TITLE_STYLE = """
    color: #fff;
    background: transparent;
    border: none;
    outline: none;
    font-size: 42px;
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
        background: @surface_alt;
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
        background: @surface;
        border: 2px solid @border_strong;
        border-radius: 27px;
    }
    QPushButton:hover   { border-color: #e74c3c; background: @accent_tint; }
    QPushButton:pressed { background: @surface_alt; }
"""

# Fond de la fenetre : le meme blanc casse que le reste de l'application.
SETTINGS_WINDOW_STYLE = """
    QDialog { background: @bg; }
    QWidget#settingsBody { background: transparent; }
"""

SETTINGS_TITLE_STYLE = """
    color: @text;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 26px;
    font-weight: bold;
"""

SETTINGS_SUBTITLE_STYLE = """
    color: @text_muted;
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
        color: @text_muted;
        font-family: 'Inter', sans-serif;
        font-size: 15px;
    }
    QPushButton:hover   { color: @text; }
    QPushButton:checked {
        color: @text;
        font-weight: bold;
        border-bottom: 3px solid #e74c3c;
    }
"""

# Titre de section, precede d'une barre d'accent dessinee par un QFrame.
SETTINGS_SECTION_TITLE_STYLE = """
    color: @text;
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
        background: @surface;
        border: 1px solid @border;
        border-radius: 12px;
    }
"""

SETTINGS_ROW_LABEL_STYLE = """
    color: @text;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: bold;
"""

SETTINGS_ROW_DESC_STYLE = """
    color: @text_muted;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
"""

SETTINGS_VALUE_STYLE = """
    color: @text;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: bold;
"""

SETTINGS_COMBO_STYLE = """
    QComboBox {
        background: @surface;
        border: 1px solid @border_strong;
        border-radius: 8px;
        padding: 6px 12px;
        color: @text;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
    }
    QComboBox:hover { border-color: #e74c3c; }
    /* Pas de regle ::drop-down : la fleche reste celle du style Fusion. La
       redessiner demanderait une image, et un chemin en dur ne survit pas a
       l'empaquetage PyInstaller. */
    QComboBox QAbstractItemView {
        background: @surface;
        border: 1px solid @border_strong;
        outline: none;
        selection-background-color: #e74c3c;
        selection-color: #ffffff;
    }
"""

SETTINGS_SLIDER_STYLE = """
    QSlider::groove:horizontal {
        height: 4px; background: @border; border-radius: 2px;
    }
    QSlider::sub-page:horizontal {
        height: 4px; background: #e74c3c; border-radius: 2px;
    }
    QSlider::handle:horizontal {
        width: 16px; height: 16px; margin: -6px 0;
        background: @surface; border: 2px solid #e74c3c; border-radius: 8px;
    }
    QSlider::handle:horizontal:hover { background: @accent_tint; }
"""

# Bouton d'action dans une carte (vider le cache, ouvrir un dossier...).
SETTINGS_ACTION_BUTTON_STYLE = """
    QPushButton {
        background: @surface;
        border: 2px solid @border_strong;
        border-radius: 16px;
        padding: 0px 16px;
        color: @text;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover   { border-color: #e74c3c; color: #e74c3c; }
    QPushButton:pressed { background: @surface_alt; }
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
        color: @text_muted;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
    }
    QPushButton:hover { color: #e74c3c; }
"""

# Interrupteur : les couleurs sont peintes a la main, QSS ne sait pas dessiner
# un rail et sa pastille. Elles vivent ici pour rester avec le reste du theme.
SETTINGS_SWITCH_COLORS = {
    "track_off": "@border_strong",
    "track_on": "#e74c3c",
    "track_off_hover": "@border_hover",
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
        background: @surface;
        border: 1px solid @border;
        border-radius: 14px;
    }
"""

# Pilule claire qui reunit une famille d'actions (navigation, zoom).
READER_GROUP_STYLE = """
    QWidget#readerGroup {
        background: @surface_alt;
        border: 1px solid @border;
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
    QPushButton:hover    { background: @accent_wash; }
    QPushButton:pressed  { background: @accent_wash_strong; }
    QPushButton:disabled { background: transparent; }
"""

# Retour : detache de la pilule, cercle blanc borde comme sur l'accueil.
READER_BACK_BUTTON_STYLE = """
    QPushButton {
        background: @surface;
        border: 2px solid @border_strong;
        border-radius: 21px;
    }
    QPushButton:hover   { border-color: #e74c3c; background: @accent_tint; }
    QPushButton:pressed { background: @surface_alt; }
"""

# Compteur de pages : la page courante ressort, le total reste en retrait.
READER_PAGE_LABEL_STYLE = """
    color: @text;
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
        color: @text_muted;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover   { background: @accent_wash; color: #e74c3c; }
    QPushButton:pressed { background: @accent_wash_strong; }
"""

# Zone de lecture : une seconde carte sous la barre, pour que la page soit
# posee sur quelque chose plutot que flottante sur le fond de l'application.
READER_VIEW_STYLE = """
    QScrollArea#readerView {
        background: transparent;
        border: 1px solid @border;
        border-radius: 14px;
    }
""" + SCROLLBAR_STYLE


# =====================================================================================
# STYLES DEPENDANT DU THEME, POSES SUR LE FOND DE L'APPLICATION
# =====================================================================================
# Ces trois-la vivaient en clair dans main.py, ou le theme ne pouvait pas les
# atteindre.
APP_BACKGROUND_STYLE = "background-color: @bg;"

THUMBNAIL_TITLE_STYLE = "font-size: 15px; color: @text; margin: 0px; padding: 0px;"

# Sous-titre facultatif, sous le titre d'une pochette : plus petit et en
# retrait, pour rester une precision et non un second titre.
THUMBNAIL_SUBTITLE_STYLE = ("font-size: 12px; color: @text_muted; "
                            "margin: 0px; padding: 0px;")

# Synopsis AniList, sous la banniere de la vue dossier.
FOLDER_DESC_STYLE = "font-size: 15px; color: @text_muted; margin-top: 10px;"

# Tags AniList, en pastilles.
FOLDER_TAG_STYLE = """
    background: @tag_bg;
    color: @tag_text;
    border-radius: 12px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: bold;
    margin-bottom: 2px;
"""

# Filet horizontal, sous les onglets de la fenetre de parametres.
SETTINGS_RULE_STYLE = "background: @border; border: none;"


# =====================================================================================
# BOITE DE SAISIE
# =====================================================================================
# Renommage, sous-titre : une carte sans cadre systeme, comme la boite de
# progression, mais aux couleurs du theme puisqu'elle porte du texte saisi.
PROMPT_CARD_STYLE = """
    QWidget#promptCard {
        background: @surface;
        border: 1px solid @border;
        border-radius: 16px;
    }
"""

PROMPT_TITLE_STYLE = """
    color: @text;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    font-weight: bold;
"""

PROMPT_MESSAGE_STYLE = """
    color: @text_muted;
    background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
"""

PROMPT_INPUT_STYLE = """
    QLineEdit {
        background: @bg;
        border: 1px solid @border_strong;
        border-radius: 10px;
        padding: 9px 12px;
        color: @text;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        selection-background-color: #e74c3c;
        selection-color: #ffffff;
    }
    QLineEdit:focus { border: 1px solid #e74c3c; }
"""


# =====================================================================================
# MOTEUR DE THEMES
# =====================================================================================
class _Styles:
    """Feuilles resolues pour le theme courant.

    Les attributs sont remplaces a chaque bascule : les modules gardent leur
    reference a `S` et n'ont rien a reimporter.
    """


S = _Styles()

# Tout ce qui se termine par _STYLE ou _COLORS est une feuille a resoudre.
_TEMPLATES = {name: value for name, value in list(globals().items())
              if name.isupper() and ("_STYLE" in name or "_COLORS" in name)}

# Les jetons les plus longs d'abord : sans cela @border avalerait @border_strong.
_TOKENS = sorted(PALETTES["light"], key=len, reverse=True)

_THEME = "light"


def _render(text, palette):
    for token in _TOKENS:
        text = text.replace("@" + token, palette[token])
    return text


def set_theme(name):
    """Resout toutes les feuilles pour le theme demande. Retourne son nom."""
    global _THEME
    if name not in PALETTES:
        name = "light"
    _THEME = name
    palette = PALETTES[name]
    for key, template in _TEMPLATES.items():
        if isinstance(template, dict):
            setattr(S, key, {k: _render(v, palette) for k, v in template.items()})
        else:
            setattr(S, key, _render(template, palette))
    return name


def current_theme():
    return _THEME


def theme_color(token):
    """Couleur brute du theme courant, pour ce que QSS ne peut pas peindre."""
    return PALETTES[_THEME][token]


set_theme("light")


"""
Langue d'affichage de l'interface.

Le code est écrit en français : `tr("Ajouter")` renvoie la chaîne telle quelle
en français, et sa traduction quand une autre langue est choisie. Une chaîne
sans traduction retombe donc sur le français plutôt que sur une clé technique —
un oubli se voit, mais ne casse rien.

Les traces de mise au point et les messages de console ne passent pas par ici :
ils s'adressent au développeur, pas à l'utilisateur.
"""

# Langues proposées dans les paramètres.
UI_LANGUAGES = (
    ("fr", "Français"),
    ("en", "English"),
)

# français -> anglais. Les accolades des chaînes à trous sont conservées telles
# quelles : c'est l'appelant qui appelle .format().
TRANSLATIONS = {
    "en": {
        # --- Accueil ---
        "Un Lecteur de Manga Offline": "An Offline Manga Reader",
        "OUVRIR UN FICHIER": "OPEN FILE",
        "BIBLIOTHÈQUE": "BOOKSHELF",
        "Paramètres": "Settings",
        "Passer au thème sombre": "Switch to the dark theme",
        "Revenir au thème clair": "Back to the light theme",

        # --- Bibliothèque ---
        "Aucune collection": "No collection",
        "{count} collection": "{count} collection",
        "{count} collections": "{count} collections",
        "Filtrer": "Filter",
        "Rechercher": "Search",
        "Rechercher une collection": "Search a collection",
        "Sélectionner des dossiers": "Select folders",
        "Sélectionner des fichiers": "Select files",
        "Supprimer la sélection": "Delete the selection",
        "Trier A-Z": "Sort A-Z",
        "Trier Z-A": "Sort Z-A",
        "Ajouter": "Add",
        "Ajouter un dossier": "Add a folder",
        "Retour": "Back",

        # --- Vue dossier ---
        "Changer la bannière": "Change the banner",
        "Rafraîchir": "Refresh",
        "Masquer le synopsis": "Hide the synopsis",
        "Synopsis masqué partout par les paramètres":
            "Synopsis hidden everywhere by the settings",
        "Afficher le synopsis": "Show the synopsis",
        "Choisir une image de fond pour le header": "Choose a banner image",
        "Choisir une image de couverture": "Choose a cover image",
        "Choisir un dossier": "Choose a folder",
        "Ouvrir un fichier": "Open a file",

        # --- Menu d'une pochette ---
        "Renommer": "Rename",
        "Renommer…": "Rename…",
        "Sous-titre": "Subtitle",
        "Sous-titre…": "Subtitle…",
        "Langue": "Language",
        "Statut": "Status",
        "En cours": "Ongoing",
        "Terminé": "Finished",
        "Aucun": "None",
        "Aucune": "None",
        "Couverture d'origine": "Original cover",
        "Télécharger la couverture": "Download the cover",
        "Couverture depuis mon ordinateur": "Cover from my computer",
        "Ouvrir dans l'explorateur": "Open in the explorer",
        "Retirer de la bibliothèque": "Remove from the bookshelf",
        "Nom affiché à la place de « {name} ».": "Name shown instead of “{name}”.",
        "Petite ligne affichée sous le titre. Laissez vide pour l'enlever.":
            "Small line shown under the title. Leave empty to remove it.",
        "{count} chapitres": "{count} chapters",
        "1 chapitre": "1 chapter",

        # --- Langues d'un élément ---
        "Français": "French",
        "Anglais": "English",
        "Arabe": "Arabic",
        "Espagnol": "Spanish",
        "Allemand": "German",
        "Japonais": "Japanese",

        # --- Lecteur ---
        "Retour (Échap)": "Back (Esc)",
        "Page précédente (←)": "Previous page (←)",
        "Page suivante (→)": "Next page (→)",
        "Zoom arrière (-)": "Zoom out (-)",
        "Zoom avant (+)": "Zoom in (+)",
        "Ajuster la page à la fenêtre": "Fit the page to the window",

        # --- Boîtes et messages ---
        "Annuler": "Cancel",
        "Valider": "Confirm",
        "Génération des vignettes": "Generating covers",
        "Actualisation du dossier": "Refreshing the folder",
        "Préparation…": "Preparing…",
        "Chargement de l'image de la vignette : {file}": "Loading cover image: {file}",
        "Succès": "Done",
        "Erreur": "Error",
        "Erreur réseau": "Network error",
        "Erreur de téléchargement": "Download error",
        "Couverture introuvable": "Cover not found",
        "Aucune couverture trouvée": "No cover found",
        "Couverture personnalisée ajoutée avec succès": "Custom cover added",
        "Impossible de charger l'image sélectionnée": "The selected image could not be loaded",
        "Erreur d'accès au dossier": "Folder access error",
        "Téléchargement en cours...": "Downloading…",
        "Ouvrir le fichier": "Open the file",
        "PAKU - Manga PDF Reader": "PAKU - Manga PDF Reader",

        # --- Fenêtre de paramètres ---
        "PAKU - Paramètres": "PAKU - Settings",
        "Réglez le comportement de PAKU. Tout est enregistré à la volée.":
            "Tune how PAKU behaves. Everything is saved as you go.",
        "Réinitialiser les réglages": "Reset the settings",
        "Fermer": "Close",
        "Général": "General",
        "Bibliothèque": "Bookshelf",
        "Lecteur": "Reader",
        "Avancé": "Advanced",
        "Apparence": "Appearance",
        "Thème": "Theme",
        "Le même réglage que le bouton lune de la page d'accueil.":
            "The same setting as the moon button on the home page.",
        "Clair": "Light",
        "Sombre": "Dark",
        "Langue d'affichage": "Display language",
        "Langue de l'interface. Sans effet sur les synopsis, qui suivent la langue de chaque collection.":
            "Language of the interface. Synopses are unaffected: they follow each collection's own language.",
        "Démarrage": "Startup",
        "Page d'ouverture": "Opening page",
        "Écran affiché au lancement de l'application.": "Screen shown when the app starts.",
        "Accueil": "Home",
        "Démarrer en plein écran": "Start fullscreen",
        "Pris en compte au prochain lancement.": "Applied on the next launch.",
        "Affichage": "Display",
        "Taille des vignettes": "Cover size",
        "Largeur des pochettes dans la grille : la grille se réorganise aussitôt.":
            "Width of the covers in the grid; the grid reflows at once.",
        "Petite ({size} px)": "Small ({size} px)",
        "Moyenne ({size} px)": "Medium ({size} px)",
        "Grande ({size} px)": "Large ({size} px)",
        "Tri par défaut": "Default sort",
        "Ordre appliqué à la bibliothèque à l'ouverture.":
            "Order applied to the bookshelf when it opens.",
        "Masquer les extensions": "Hide extensions",
        "Affiche « Chapitre 12 » au lieu de « Chapitre 12.cbz ». Sans effet sur les éléments que vous avez renommés.":
            "Shows “Chapter 12” instead of “Chapter 12.cbz”. Items you renamed keep their name.",
        "Masquées": "Hidden",
        "Masqué": "Hidden",
        "Affiché": "Shown",
        "Affichées": "Shown",
        "Masquer le synopsis partout": "Hide every synopsis",
        "Retire le résumé et les tags de toutes les vues dossier. Un dossier peut aussi être masqué seul, depuis sa bannière.":
            "Removes the summary and tags from every folder view. A single folder can also be hidden from its own banner.",
        "Ajout d'un dossier": "Adding a folder",
        "Générer les vignettes à l'ajout": "Generate covers when adding",
        "Prépare toutes les pochettes d'un coup. Désactivé, elles sont créées au fil de l'affichage et l'ajout est immédiat.":
            "Prepares every cover in one go. Off, they are built as they are displayed and adding is instant.",
        "Récupérer les infos en ligne": "Fetch online info",
        "Synopsis, tags, bannière et couverture depuis AniList et MangaDex. Désactivé, l'ajout ne contacte aucun serveur.":
            "Synopsis, tags, banner and cover from AniList and MangaDex. Off, adding contacts no server at all.",
        "Oui": "Yes",
        "Non": "No",
        "Molette": "Wheel",
        "Pas de zoom": "Zoom step",
        "Zoom gagné ou perdu à chaque cran de molette.": "Zoom gained or lost per wheel notch.",
        "Inverser le sens": "Invert the direction",
        "Molette vers le haut pour dézoomer.": "Wheel up zooms out.",
        "Inversé": "Inverted",
        "Normal": "Normal",
        "Pages": "Pages",
        "Conserver le zoom": "Keep the zoom",
        "Garde votre niveau de zoom d'une page à l'autre. Désactivé, chaque page repart ajustée à la fenêtre.":
            "Keeps your zoom level from page to page. Off, every page starts fitted to the window again.",
        "Maintenance": "Maintenance",
        "Cache des vignettes": "Cover cache",
        "Supprime les dossiers « .thumbnails » de la bibliothèque. Les pochettes que vous avez choisies vous-même seront perdues, les autres seront régénérées.":
            "Deletes the “.thumbnails” folders of the bookshelf. Covers you picked yourself will be lost, the others are rebuilt.",
        "Vider": "Empty",
        "Fichiers de configuration": "Configuration files",
        "library.json et settings.json vivent dans {folder}.":
            "library.json and settings.json live in {folder}.",
        "Ouvrir le dossier": "Open the folder",
        "Diagnostic": "Diagnostics",
        "Traces de débogage": "Debug traces",
        "Écrit le détail des opérations dans la console. Utile pour signaler un problème, coûteux sur une grosse bibliothèque.":
            "Writes the details of every operation to the console. Useful to report a problem, costly on a large library.",
        "Activées": "On",
        "Silencieuses": "Silent",
        "Réinitialiser": "Reset",
        "Tous les réglages reviennent à leur valeur d'origine. Continuer ?":
            "Every setting goes back to its original value. Continue?",
        "Vider le cache des vignettes": "Empty the cover cache",
        "Aucun cache à supprimer.": "No cache to delete.",
        "{count} dossier(s) « {name} » vont être supprimés.":
            "{count} “{name}” folder(s) will be deleted.",
        "Les pochettes personnalisées et les bannières téléchargées seront perdues ; les autres seront régénérées à la prochaine ouverture.":
            "Custom covers and downloaded banners will be lost; the others are rebuilt the next time you open them.",
        "Continuer ?": "Continue?",
        "{count} dossier(s) supprimé(s).": "{count} folder(s) deleted.",
        "Échecs :": "Failures:",
        "Configuration": "Configuration",
        "Impossible d'ouvrir {folder} : {error}": "Could not open {folder}: {error}",
    },
}

_LANGUAGE = "fr"


def set_language(code):
    """Fixe la langue d'affichage. Retourne le code retenu."""
    global _LANGUAGE
    _LANGUAGE = code if code in dict(UI_LANGUAGES) else "fr"
    return _LANGUAGE


def current_language():
    return _LANGUAGE


def tr(text):
    """Traduit une chaîne d'interface. Le français est la source."""
    if _LANGUAGE == "fr":
        return text
    return TRANSLATIONS.get(_LANGUAGE, {}).get(text, text)

"""
Réglages système de l'application.

Un seul fichier JSON, `settings.json`, posé à côté de `library.json`. Le module
n'importe rien de `main` : c'est lui qui est importé, jamais l'inverse.
Chaque réglage a une valeur par défaut qui reproduit le comportement historique
de PAKU, de sorte qu'une installation existante ne change pas d'un poil tant
que l'utilisateur n'a touché à rien.
"""

import json
import os

SETTINGS_FILE = "settings.json"

# Valeurs par défaut = comportement de l'application avant l'arrivée des réglages.
DEFAULTS = {
    # --- Général ---
    "language": "fr",                # langue d'affichage : "fr" | "en"
    "theme": "light",                # "light" | "dark"
    "startup_page": "home",          # "home" | "bookshelf"
    "start_fullscreen": False,
    # --- Bibliothèque ---
    "default_sort": "az",            # "az" | "za"
    "thumbnail_size": "medium",      # "small" | "medium" | "large"
    "hide_extensions": False,
    "hide_description": False,       # synopsis et tags, dans toutes les vues dossier
    "auto_thumbnails": True,         # générer les vignettes à l'ajout d'un dossier
    "fetch_online_info": True,       # AniList / MangaDex à l'ajout d'un dossier
    # --- Lecteur ---
    "wheel_zoom_step": 15,           # pourcentage de zoom par cran de molette
    "invert_wheel": False,
    "keep_zoom_between_pages": True,
    # --- Avancé ---
    "debug_traces": False,
}

# Tailles de vignette proposées, en pixels logiques.
THUMBNAIL_SIZES = {
    "small": (150, 210),
    "medium": (200, 280),
    "large": (260, 364),
}


class AppSettings:
    """Dictionnaire de réglages persistant, tolérant à un fichier absent ou abîmé."""

    def __init__(self, path=SETTINGS_FILE):
        self._path = path
        self._values = dict(DEFAULTS)
        self.load()

    # -- persistance ------------------------------------------------------
    def load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                stored = json.load(f)
        except (OSError, ValueError):
            return
        if not isinstance(stored, dict):
            return
        # Les clés inconnues sont ignorées : un fichier écrit par une version
        # plus récente ne doit pas injecter de réglages que le code ne gère pas.
        for key, value in stored.items():
            if key in DEFAULTS and isinstance(value, type(DEFAULTS[key])):
                self._values[key] = value

    def save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._values, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"Impossible d'écrire {self._path} : {e}")

    # -- accès ------------------------------------------------------------
    def get(self, key):
        return self._values.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        """Écrit le réglage et retourne True s'il a réellement changé."""
        if key not in DEFAULTS:
            raise KeyError(f"Réglage inconnu : {key}")
        if self._values.get(key) == value:
            return False
        self._values[key] = value
        self.save()
        return True

    def reset(self):
        self._values = dict(DEFAULTS)
        self.save()

    def as_dict(self):
        return dict(self._values)

    # -- dérivés ----------------------------------------------------------
    def thumbnail_pixel_size(self):
        return THUMBNAIL_SIZES.get(self.get("thumbnail_size"), THUMBNAIL_SIZES["medium"])

    def wheel_zoom_factor(self):
        """Facteur multiplicatif d'un cran de molette (1.15 pour 15 %)."""
        return 1.0 + max(1, min(50, int(self.get("wheel_zoom_step")))) / 100.0

    def config_dir(self):
        return os.path.dirname(os.path.abspath(self._path))


# Instance partagée par toute l'application.
settings = AppSettings()

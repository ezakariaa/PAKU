"""
Fenêtre de paramètres : une fenêtre à part, ouverte depuis l'engrenage de la
page d'accueil.

Chaque contrôle écrit son réglage immédiatement — il n'y a pas de bouton
« Appliquer » à oublier — et prévient la fenêtre principale via
`settings_changed`, qui relaie la clé modifiée.

Le module ne connaît que `app_settings` et les styles : il peut donc être
importé par `main` sans boucle d'import.
"""

import os
import shutil
import subprocess
import sys

from PySide6.QtCore import (Property, QEasingCurve, QPropertyAnimation, QRectF,
                            QSize, Qt, Signal)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import (QAbstractButton, QComboBox, QDialog, QFrame,
                               QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QScrollArea, QSlider, QStackedWidget,
                               QVBoxLayout, QWidget)

from app_settings import THUMBNAIL_SIZES, settings
from i18n import tr, UI_LANGUAGES
from styles.styles import S

THUMB_CACHE_DIRNAME = ".thumbnails"


# =====================================================================================
# INTERRUPTEUR
# =====================================================================================
class ToggleSwitch(QAbstractButton):
    """Interrupteur à bascule : QSS ne sait pas dessiner un rail et sa pastille."""

    TRACK_WIDTH = 46
    TRACK_HEIGHT = 26
    KNOB_MARGIN = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(self.TRACK_WIDTH, self.TRACK_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._offset = 0.0
        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(140)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._slide)

    # Position de la pastille, de 0 (éteint) à 1 (allumé).
    def _get_offset(self):
        return self._offset

    def _set_offset(self, value):
        self._offset = value
        self.update()

    offset = Property(float, _get_offset, _set_offset)

    def _slide(self, checked):
        target = 1.0 if checked else 0.0
        # Hors écran, l'animation ne serait jamais peinte : on saute à la valeur.
        self._animation.stop()
        if not self.isVisible():
            self._set_offset(target)
            return
        self._animation.setStartValue(self._offset)
        self._animation.setEndValue(target)
        self._animation.start()

    def sizeHint(self):
        return QSize(self.TRACK_WIDTH, self.TRACK_HEIGHT)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        hovered = self.underMouse()
        if self.isChecked():
            key = "track_on_hover" if hovered else "track_on"
        else:
            key = "track_off_hover" if hovered else "track_off"
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(S.SETTINGS_SWITCH_COLORS[key]))
        radius = self.TRACK_HEIGHT / 2
        painter.drawRoundedRect(QRectF(self.rect()), radius, radius)

        diameter = self.TRACK_HEIGHT - 2 * self.KNOB_MARGIN
        travel = self.TRACK_WIDTH - 2 * self.KNOB_MARGIN - diameter
        x = self.KNOB_MARGIN + travel * self._offset
        painter.setBrush(QColor(S.SETTINGS_SWITCH_COLORS["knob"]))
        painter.drawEllipse(QRectF(x, self.KNOB_MARGIN, diameter, diameter))


# =====================================================================================
# FENETRE
# =====================================================================================
class SettingsWindow(QDialog):
    """Réglages système. Non modale : on peut la laisser ouverte en naviguant."""

    settings_changed = Signal(str)   # clé du réglage qui vient de changer

    def __init__(self, parent=None, library_paths=None):
        # Qt.Window : une vraie fenêtre, avec sa barre de titre et son entrée
        # dans la barre des tâches, plutôt qu'une boîte collée à la principale.
        super().__init__(parent, Qt.WindowType.Window)
        self._library_paths = library_paths or (lambda: [])
        # Rechargeurs appelés après une réinitialisation, un par contrôle.
        self._reloaders = []
        self.setWindowTitle(tr("PAKU - Paramètres"))
        self.setStyleSheet(S.SETTINGS_WINDOW_STYLE)
        self.setMinimumSize(720, 560)
        self.resize(820, 640)
        self.setup_ui()

    # -- construction -----------------------------------------------------
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 18)
        layout.setSpacing(0)

        title = QLabel(tr("Paramètres"))
        title.setStyleSheet(S.SETTINGS_TITLE_STYLE)
        layout.addWidget(title)

        subtitle = QLabel(tr("Réglez le comportement de PAKU. Tout est enregistré à la volée."))
        subtitle.setStyleSheet(S.SETTINGS_SUBTITLE_STYLE)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        self.pages = QStackedWidget()
        tab_bar = QHBoxLayout()
        tab_bar.setContentsMargins(0, 0, 0, 0)
        tab_bar.setSpacing(24)
        self._tab_buttons = []
        for index, name in enumerate((tr("Général"), tr("Bibliothèque"), tr("Lecteur"), tr("Avancé"))):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(S.SETTINGS_TAB_BUTTON_STYLE)
            # L'onglet actif passe en gras : sans cette reserve, le libelle
            # serait rogne au moment de la selection.
            bold = QFont(button.font())
            bold.setBold(True)
            button.setMinimumWidth(QFontMetrics(bold).horizontalAdvance(name) + 14)
            button.setChecked(index == 0)
            button.clicked.connect(lambda _checked, i=index: self.show_tab(i))
            tab_bar.addWidget(button)
            self._tab_buttons.append(button)
        tab_bar.addStretch()
        layout.addLayout(tab_bar)

        rule = QFrame()
        rule.setFixedHeight(1)
        rule.setStyleSheet(S.SETTINGS_RULE_STYLE)
        layout.addWidget(rule)
        layout.addSpacing(14)

        for builder in (self.build_general, self.build_library,
                        self.build_reader, self.build_advanced):
            self.pages.addWidget(self.wrap_in_scroll(builder()))
        layout.addWidget(self.pages, 1)

        layout.addSpacing(14)
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        reset_btn = QPushButton(tr("Réinitialiser les réglages"))
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(S.SETTINGS_LINK_BUTTON_STYLE)
        reset_btn.clicked.connect(self.reset_settings)
        footer.addWidget(reset_btn)
        footer.addStretch()
        close_btn = QPushButton(tr("Fermer"))
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(S.SETTINGS_PRIMARY_BUTTON_STYLE)
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)
        layout.addLayout(footer)

    def wrap_in_scroll(self, content):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setStyleSheet(S.SCROLL_AREA_STYLE)
        area.setFrameShape(QFrame.Shape.NoFrame)
        content.setObjectName("settingsBody")
        area.setWidget(content)
        return area

    def show_tab(self, index):
        self.pages.setCurrentIndex(index)
        for position, button in enumerate(self._tab_buttons):
            button.setChecked(position == index)

    # -- briques de mise en page ------------------------------------------
    @staticmethod
    def new_page():
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 14, 8)
        layout.setSpacing(10)
        return page, layout

    @staticmethod
    def section(layout, title):
        if layout.count():
            layout.addSpacing(12)
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        bar = QFrame()
        bar.setFixedSize(4, 18)
        bar.setStyleSheet(S.SETTINGS_SECTION_BAR_STYLE)
        row.addWidget(bar)
        label = QLabel(title)
        label.setStyleSheet(S.SETTINGS_SECTION_TITLE_STYLE)
        row.addWidget(label)
        row.addStretch()
        layout.addWidget(holder)

    @staticmethod
    def row(layout, title, description):
        """Carte blanche : libellé et explication à gauche, contrôle à droite."""
        card = QWidget()
        card.setObjectName("settingsRow")
        card.setStyleSheet(S.SETTINGS_ROW_STYLE)
        box = QHBoxLayout(card)
        box.setContentsMargins(16, 12, 16, 12)
        box.setSpacing(16)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)
        label = QLabel(title)
        label.setStyleSheet(S.SETTINGS_ROW_LABEL_STYLE)
        text.addWidget(label)
        if description:
            hint = QLabel(description)
            hint.setWordWrap(True)
            hint.setStyleSheet(S.SETTINGS_ROW_DESC_STYLE)
            text.addWidget(hint)
        box.addLayout(text, 1)
        layout.addWidget(card)
        return box

    # -- contrôles --------------------------------------------------------
    def add_toggle(self, layout, key, title, description,
                   on_text="Activé", off_text="Désactivé"):
        box = self.row(layout, title, description)
        state = QLabel()
        state.setStyleSheet(S.SETTINGS_VALUE_STYLE)
        state.setMinimumWidth(88)
        switch = ToggleSwitch()

        def refresh_label(checked):
            state.setText(on_text if checked else off_text)

        def changed(checked):
            refresh_label(checked)
            if settings.set(key, bool(checked)):
                self.settings_changed.emit(key)

        switch.setChecked(bool(settings.get(key)))
        refresh_label(switch.isChecked())
        switch.toggled.connect(changed)
        box.addWidget(switch, 0, Qt.AlignmentFlag.AlignVCenter)
        box.addWidget(state, 0, Qt.AlignmentFlag.AlignVCenter)

        def reload():
            switch.blockSignals(True)
            switch.setChecked(bool(settings.get(key)))
            switch.blockSignals(False)
            switch._slide(switch.isChecked())
            refresh_label(switch.isChecked())

        self._reloaders.append(reload)
        return switch

    def add_combo(self, layout, key, title, description, options):
        """`options` : liste de couples (valeur stockée, libellé affiché)."""
        box = self.row(layout, title, description)
        combo = QComboBox()
        combo.setCursor(Qt.CursorShape.PointingHandCursor)
        combo.setStyleSheet(S.SETTINGS_COMBO_STYLE)
        combo.setMinimumWidth(190)
        for value, label in options:
            combo.addItem(label, value)

        def select_current():
            index = combo.findData(settings.get(key))
            combo.setCurrentIndex(max(0, index))

        def changed(_index):
            if settings.set(key, combo.currentData()):
                self.settings_changed.emit(key)

        select_current()
        combo.currentIndexChanged.connect(changed)
        box.addWidget(combo, 0, Qt.AlignmentFlag.AlignVCenter)

        def reload():
            combo.blockSignals(True)
            select_current()
            combo.blockSignals(False)

        self._reloaders.append(reload)
        return combo

    def add_slider(self, layout, key, title, description, minimum, maximum, suffix=""):
        box = self.row(layout, title, description)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setStyleSheet(S.SETTINGS_SLIDER_STYLE)
        slider.setRange(minimum, maximum)
        slider.setFixedWidth(190)
        value_label = QLabel()
        value_label.setStyleSheet(S.SETTINGS_VALUE_STYLE)
        value_label.setMinimumWidth(52)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        def changed(value):
            value_label.setText(f"{value}{suffix}")
            if settings.set(key, int(value)):
                self.settings_changed.emit(key)

        slider.setValue(int(settings.get(key)))
        value_label.setText(f"{slider.value()}{suffix}")
        slider.valueChanged.connect(changed)
        box.addWidget(slider, 0, Qt.AlignmentFlag.AlignVCenter)
        box.addWidget(value_label, 0, Qt.AlignmentFlag.AlignVCenter)

        def reload():
            slider.blockSignals(True)
            slider.setValue(int(settings.get(key)))
            slider.blockSignals(False)
            value_label.setText(f"{slider.value()}{suffix}")

        self._reloaders.append(reload)
        return slider

    def add_action(self, layout, title, description, button_text, callback):
        box = self.row(layout, title, description)
        button = QPushButton(button_text)
        button.setFixedHeight(32)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(S.SETTINGS_ACTION_BUTTON_STYLE)
        button.clicked.connect(callback)
        box.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        return button

    # -- pages ------------------------------------------------------------
    def build_general(self):
        page, layout = self.new_page()
        self.section(layout, tr("Apparence"))
        self.add_combo(layout, "theme", tr("Thème"),
                       tr("Le même réglage que le bouton lune de la page d'accueil."),
                       [("light", tr("Clair")), ("dark", tr("Sombre"))])
        self.add_combo(layout, "language", tr("Langue d'affichage"),
                       tr("Langue de l'interface. Sans effet sur les synopsis, qui "
                          "suivent la langue de chaque collection."),
                       list(UI_LANGUAGES))

        self.section(layout, tr("Démarrage"))
        self.add_combo(layout, "startup_page", tr("Page d'ouverture"),
                       tr("Écran affiché au lancement de l'application."),
                       [("home", tr("Accueil")), ("bookshelf", tr("Bibliothèque"))])
        self.add_toggle(layout, "start_fullscreen", tr("Démarrer en plein écran"),
                        tr("Pris en compte au prochain lancement."),
                        on_text=tr("Oui"), off_text=tr("Non"))
        layout.addStretch()
        return page

    def build_library(self):
        page, layout = self.new_page()
        self.section(layout, tr("Affichage"))
        thumb_options = [
            ("small", tr("Petite ({size} px)").format(size=THUMBNAIL_SIZES["small"][0])),
            ("medium", tr("Moyenne ({size} px)").format(size=THUMBNAIL_SIZES["medium"][0])),
            ("large", tr("Grande ({size} px)").format(size=THUMBNAIL_SIZES["large"][0])),
        ]
        self.add_combo(layout, "thumbnail_size", tr("Taille des vignettes"),
                       tr("Largeur des pochettes dans la grille : la grille se "
                       "réorganise aussitôt."), thumb_options)
        self.add_combo(layout, "default_sort", tr("Tri par défaut"),
                       tr("Ordre appliqué à la bibliothèque à l'ouverture."),
                       [("az", "A → Z"), ("za", "Z → A")])
        self.add_toggle(layout, "hide_extensions", tr("Masquer les extensions"),
                        tr("Affiche « Chapitre 12 » au lieu de « Chapitre 12.cbz ». "
                        "Sans effet sur les éléments que vous avez renommés."),
                        on_text=tr("Masquées"), off_text=tr("Affichées"))
        self.add_toggle(layout, "hide_description", tr("Masquer le synopsis partout"),
                        tr("Retire le résumé et les tags de toutes les vues dossier. "
                           "Un dossier peut aussi être masqué seul, depuis sa bannière."),
                        on_text=tr("Masqué"), off_text=tr("Affiché"))

        self.section(layout, tr("Ajout d'un dossier"))
        self.add_toggle(layout, "auto_thumbnails", tr("Générer les vignettes à l'ajout"),
                        tr("Prépare toutes les pochettes d'un coup. Désactivé, elles "
                        "sont créées au fil de l'affichage et l'ajout est immédiat."),
                        on_text=tr("Oui"), off_text=tr("Non"))
        self.add_toggle(layout, "fetch_online_info", tr("Récupérer les infos en ligne"),
                        tr("Synopsis, tags, bannière et couverture depuis AniList et "
                        "MangaDex. Désactivé, l'ajout ne contacte aucun serveur."),
                        on_text=tr("Oui"), off_text=tr("Non"))
        layout.addStretch()
        return page

    def build_reader(self):
        page, layout = self.new_page()
        self.section(layout, tr("Molette"))
        self.add_slider(layout, "wheel_zoom_step", tr("Pas de zoom"),
                        tr("Zoom gagné ou perdu à chaque cran de molette."),
                        5, 50, " %")
        self.add_toggle(layout, "invert_wheel", tr("Inverser le sens"),
                        tr("Molette vers le haut pour dézoomer."),
                        on_text=tr("Inversé"), off_text=tr("Normal"))

        self.section(layout, tr("Pages"))
        self.add_toggle(layout, "keep_zoom_between_pages", tr("Conserver le zoom"),
                        tr("Garde votre niveau de zoom d'une page à l'autre. Désactivé, "
                        "chaque page repart ajustée à la fenêtre."),
                        on_text=tr("Oui"), off_text=tr("Non"))
        layout.addStretch()
        return page

    def build_advanced(self):
        page, layout = self.new_page()
        self.section(layout, tr("Maintenance"))
        self.add_action(layout, tr("Cache des vignettes"),
                        tr("Supprime les dossiers « .thumbnails » de la bibliothèque. "
                        "Les pochettes que vous avez choisies vous-même seront "
                        "perdues, les autres seront régénérées."),
                        tr("Vider"), self.clear_thumbnail_cache)
        self.add_action(layout, tr("Fichiers de configuration"),
                        tr("library.json et settings.json vivent dans {folder}.")
                        .format(folder=settings.config_dir()),
                        tr("Ouvrir le dossier"), self.open_config_dir)

        self.section(layout, tr("Diagnostic"))
        self.add_toggle(layout, "debug_traces", tr("Traces de débogage"),
                        tr("Écrit le détail des opérations dans la console. Utile pour "
                        "signaler un problème, coûteux sur une grosse bibliothèque."),
                        on_text=tr("Activées"), off_text=tr("Silencieuses"))
        layout.addStretch()
        return page

    # -- actions ----------------------------------------------------------
    def clear_thumbnail_cache(self):
        caches = []
        for root_path in self._library_paths():
            if not os.path.isdir(root_path):
                continue
            for current, dirs, _files in os.walk(root_path):
                if THUMB_CACHE_DIRNAME in dirs:
                    caches.append(os.path.join(current, THUMB_CACHE_DIRNAME))
                    # Inutile de descendre dans un cache que l'on va supprimer.
                    dirs.remove(THUMB_CACHE_DIRNAME)
        if not caches:
            QMessageBox.information(self, tr("Cache des vignettes"),
                                    tr("Aucun cache à supprimer."))
            return
        answer = QMessageBox.question(
            self, tr("Vider le cache des vignettes"),
            tr("{count} dossier(s) « {name} » vont être supprimés.")
            .format(count=len(caches), name=THUMB_CACHE_DIRNAME) + "\n\n"
            + tr("Les pochettes personnalisées et les bannières téléchargées seront "
                 "perdues ; les autres seront régénérées à la prochaine ouverture.")
            + "\n\n" + tr("Continuer ?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        removed, failed = 0, []
        for cache in caches:
            try:
                shutil.rmtree(cache)
                removed += 1
            except OSError as e:
                failed.append(f"{cache} : {e}")
        if failed:
            QMessageBox.warning(self, tr("Cache des vignettes"),
                                tr("{count} dossier(s) supprimé(s).").format(count=removed)
                                + "\n\n" + tr("Échecs :") + "\n"
                                + "\n".join(failed[:5]))
        else:
            QMessageBox.information(self, tr("Cache des vignettes"),
                                    tr("{count} dossier(s) supprimé(s).").format(count=removed))
        self.settings_changed.emit("thumbnail_cache_cleared")

    def open_config_dir(self):
        directory = settings.config_dir()
        try:
            if sys.platform.startswith("win"):
                os.startfile(directory)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", directory])
            else:
                subprocess.Popen(["xdg-open", directory])
        except OSError as e:
            QMessageBox.warning(self, tr("Configuration"),
                                tr("Impossible d'ouvrir {folder} : {error}")
                                .format(folder=directory, error=e))

    def reset_settings(self):
        answer = QMessageBox.question(
            self, tr("Réinitialiser"),
            tr("Tous les réglages reviennent à leur valeur d'origine. Continuer ?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        settings.reset()
        for reload in self._reloaders:
            reload()
        # Une seule notification : la fenêtre principale reconstruit tout.
        self.settings_changed.emit("*")

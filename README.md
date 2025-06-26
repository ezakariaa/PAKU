# MangaPDFReader

Un lecteur de PDF avec une interface inspirée des lecteurs de manga modernes.

## Structure du projet

- `main.py` : Point d'entrée de l'application.
- `ui/` : Fichiers d'interface graphique (créés avec Qt Designer).
- `assets/images/` : Images, fonds, icônes.
- `assets/fonts/` : Polices personnalisées.
- `requirements.txt` : Dépendances Python.

## Lancement

1. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
2. Lancez l'application :
   ```bash
   python main.py
   ```

## Fonctionnalités

### ✅ Fonctionnalités implémentées
- **Page d'accueil stylisée** : Interface manga moderne avec design "RULIA"
- **Ouverture de PDF** : Sélection et chargement de fichiers PDF
- **Lecteur PDF complet** : Affichage des pages avec PyMuPDF
- **Navigation** : Boutons précédent/suivant, première/dernière page
- **Zoom** : Contrôles de zoom avec boutons et raccourcis clavier
- **Raccourcis clavier** : Navigation rapide avec le clavier
- **Interface responsive** : Design moderne et intuitif

### 🎮 Raccourcis clavier
- **Flèches gauche/droite** : Navigation entre les pages
- **Home/End** : Aller à la première/dernière page
- **Ctrl +** : Zoom avant
- **Ctrl -** : Zoom arrière
- **Ctrl 0** : Reset du zoom

### 🎨 Interface
- Design inspiré des lecteurs de manga modernes
- Couleurs et typographie appropriées
- Boutons stylisés avec effets hover
- Zone de lecture avec scroll automatique
- Barre de navigation complète

## Dépendances

- **PySide6** : Interface graphique Qt
- **PyMuPDF** : Lecture et rendu des PDF

## Développement futur

- 🔄 Mode plein écran
- 🔄 Rotation des pages
- 🔄 Extraction de texte
- 🔄 Historique des fichiers récents
- 🔄 Thèmes personnalisables
- 🔄 Support des formats CBZ/CBR 
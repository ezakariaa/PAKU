import flet as ft
import os

def main(page: ft.Page):
    # Configuration de la page (fenêtre)
    page.title = "PAKU - Bibliothèque de Merveilles"
    page.window_width = 800
    page.window_height = 600
    page.padding = 0

    # --- Gestionnaire de sélection de fichiers ---
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            # Pour l'instant, on affiche juste le chemin du premier fichier sélectionné
            print(f"Fichier sélectionné : {e.files[0].path}")
        else:
            print("Aucun fichier sélectionné.")

    file_picker = ft.FilePicker(on_result=on_file_picked)
    # Le FilePicker doit être dans l'overlay pour s'afficher par-dessus l'UI
    page.overlay.append(file_picker)

    # --- Interface Utilisateur ---

    # Création du header avec une image de fond
    header = ft.Container(
        content=ft.Image(src="assets/images/header.png", fit=ft.ImageFit.COVER),
        height=150,
        border_radius=ft.border_radius.all(8)
    )

    # Création du logo
    logo = ft.Image(src="assets/images/logo.png", width=120, height=120)

    # Boutons d'action
    library_button = ft.ElevatedButton(
        text="Bibliothèque",
        icon=ft.Icons.FOLDER,
        width=200,
        height=50
    )

    open_file_button = ft.ElevatedButton(
        text="Ouvrir un fichier",
        icon=ft.Icons.FILE_OPEN,
        width=200,
        height=50,
        # On connecte le clic à l'ouverture du dialogue de sélection
        on_click=lambda _: file_picker.pick_files(
            dialog_title="Ouvrir un fichier",
            allowed_extensions=["pdf", "cbz", "cbr", "rar"]
        )
    )
    
    # Conteneur principal de la page
    # On utilise une Colonne pour empiler les éléments verticalement
    page.add(
        ft.Column(
            [
                header,
                ft.Column(
                    [
                        logo,
                        ft.Row(
                            [library_button, open_file_button],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20
                        ),
                    ],
                    # Ce alignment pousse le contenu vers le centre de l'espace restant
                    alignment=ft.MainAxisAlignment.CENTER, 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=30,
                    expand=True # Pour que cette colonne prenne tout l'espace vertical restant
                )
            ],
            expand=True
        )
    )
    page.update()

# Lancement de l'application
ft.app(target=main, assets_dir="assets") 
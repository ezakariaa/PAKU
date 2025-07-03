# Script pour corriger l'indentation dans main.py
with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Corriger complètement la fonction get_thumbnail_path
lines[1826] = '            else:\n'
lines[1827] = '                print(f"Vignette non trouvée: {thumb_path}")\n'
lines[1828] = '                return None\n'
lines[1829] = '        else:\n'
lines[1830] = '            # Pour un fichier (PDF ou CBZ), chercher nom_du_fichier.png, sinon vignette du dossier\n'
lines[1831] = '            base = os.path.splitext(os.path.basename(file_path))[0]\n'
lines[1832] = '            thumb_dir = os.path.join(os.path.dirname(file_path), \'.thumbnails\')\n'
lines[1833] = '            thumb_path = os.path.join(thumb_dir, base + \'.png\')\n'
lines[1834] = '            if os.path.exists(thumb_path):\n'
lines[1835] = '                print(f"Vignette locale trouvée: {thumb_path}")\n'
lines[1836] = '                return thumb_path\n'
lines[1837] = '            else:\n'
lines[1838] = '                # En dernier recours, retourner la vignette du dossier si elle existe\n'
lines[1839] = '                folder_thumb = os.path.join(thumb_dir, \'_folder_thumb.png\')\n'
lines[1840] = '                if os.path.exists(folder_thumb):\n'
lines[1841] = '                    print(f"Vignette dossier trouvée: {folder_thumb}")\n'
lines[1842] = '                    return folder_thumb\n'
lines[1843] = '                print(f"Aucune vignette trouvée pour {file_path}")\n'
lines[1844] = '                return None\n'

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Correction terminée!") 
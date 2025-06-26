@echo off
REM Script d'installation automatique des dépendances pour MangaPDFReader

REM Active l'environnement virtuel s'il existe
IF EXIST venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Installe les dépendances du projet
pip install --upgrade pip
pip install -r requirements.txt

REM Installe les dépendances système pour PyMuPDF et rarfile si besoin
REM (PyMuPDF et rarfile ne nécessitent pas de dépendances système sous Windows en général)

REM Message de fin
ECHO Installation terminée. Si vous voyez des erreurs, copiez-les ici pour obtenir de l'aide.
pause 
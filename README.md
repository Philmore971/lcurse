lcurse
======

08/07/2019 Mises à jour catalogue et Addons sont fonctionnelles.
Nouvelle structure du site https://www.curseforge.com/wow/addons

### Version tout en français de "lcurse". Utilitaire en Python compatible linux de "curse".
Branche principale et de référence du projet :
https://github.com/ephraim/lcurse/

Étant donné que l'application considère que l'installation par défaut sera dans le répertoire " ~/.wine/drive_c/Program Files (x86)/World of Warcraft/ ", votre installation n’est peut être pas structuré de la même façon, vous devrez probablement créer un lien par « ln -s source destination » entre les deux dossiers wow/Interface/Addons.

Pour exemple dans mon cas personnel, installation wow via Lutris, j'ai créer un lien symbolique vers le dossier d'installation standard de Wow :

ln -s '/home/philmore/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Interface/AddOns' '/home/philmore/.wine/drive_c/Program Files (x86)/World of Warcraft/_retail_/Interface/AddOns'

lcurse supporte les dépôts git aussi.
Comme les dépôts git ne sont pas structurés de façon identique, vous devrez probablement créer un nouveau lien via
"ln -s source destination" à l'intérieur du répertoire wow/Interface/Addons folder.
Mais au moins la mise à jour se fait alors par la voie habituelle.

### Pré-requis
* python 3.6 ou 3.7
* pipenv
* PyQt5
* bs4
* lxml

### Installation des pré-requis :
```bash
pipenv install
```
### Lancement du programme
```bash
pipenv run ./lcurse
```
### Mode mise à jour addons, sans interface

Vous pouvez lancer `lcurse` en "Mode sans surveillance" une fois que vous avez mis en place les réglages de base.
Ceci mettra à jour tous vos addons et quittera.
```bash
pipenv run ./lcurse --auto-update
```

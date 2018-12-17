lcurse
======

Version tout en français de "lcurse". Utilitaire en Python compatible linux de "curse".
Branche principale et de référence du projet :
https://github.com/ephraim/lcurse/

Remarque : Il est possible d'utiliser l'installation par défaut de Python de son système sans créer un environnement "pipenv"
Dans la fenêtre d'un terminal, utiliser la commande :
~/lcurse-master/lcurse

Étant donné que l'application considère que l'installation par défaut sera dans le répertoire " ~/.wine/drive_c/Program Files (x86)/World of Warcraft/ ", votre installation n’est peut être pas structuré de la même façon, vous devrez probablement créer un lien par « ln -s source destination » entre les deux dossiers wow/Interface/Addons.

Pour exemple dans mon cas personnel, installation wow via Lutris, j'ai créer un lien symbolique vers le dossier d'installation standard de Wow :

ln -s '/home/philmore/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Interface/AddOns' '/home/philmore/.wine/drive_c/Program Files (x86)/World of Warcraft/_retail_/Interface/AddOns'

lcurse nowadays supports git repositories too.
As git repos aren't structured the same, you will most probably need to create an link via "ln -s source destination" inside the wow/Interface/Addons folder.
But at least the update is then done via the usuall lcurse way.

### Requirements
* python 3.6 ou 3.7
* pipenv
* PyQt5
* bs4
* lxml

All requirements can be installed with:
```bash
pipenv install
```

## Running

Simply:
```bash
pipenv run ./lcurse
```

### Unattended mode

You may also run `lcurse` in "unattended mode" once you have set it up. This
will update all your addons and then exit. Use
```bash
pipenv run ./lcurse --auto-update
```

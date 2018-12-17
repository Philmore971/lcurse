lcurse
======

Version tout en français de "lcurse". Utilitaire en Python compatible linux de "curse".
Branche principale et de référence du projet :
https://github.com/ephraim/lcurse/

Remarque : Il est possible d'utiliser l'installation par défaut de Python de son système sans créer un environnement "pipenv"
Dans la fenêtre d'un terminal, utiliser la commande :
~/lcurse-master/lcurse

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

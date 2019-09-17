from PyQt5 import Qt

WOW_FOLDER_KEY = "Préférences / répertoire Wow\n"
WOW_TOC_KEY = "Préférences / Toc Courant"
WOW_FOLDER_DEFAULT = "{}/.wine/drive_c/Program Files (x86)/World of Warcraft".format(Qt.QDir.homePath())
WOW_VERSION_DEFAULT = "retail"

LCURSE_FOLDER = "{}/.lcurse".format(Qt.QDir.homePath())
LCURSE_ADDONS = LCURSE_FOLDER + "/addons.json"
LCURSE_ADDONS_BASE = LCURSE_FOLDER + "/addons_{}.json"
LCURSE_ADDON_CATALOG = LCURSE_FOLDER + "/addon-catalog.json"
LCURSE_ADDON_TOCS_CACHE = LCURSE_FOLDER + "/tocs.json"

LCURSE_MAXTHREADS_KEY = "Préférences / Tâches maxi"
LCURSE_MAXTHREADS_DEFAULT = 50
LCURSE_DBVERSION = 1
TOC = "80200"
print("Répertoire par défaut :",WOW_FOLDER_KEY,WOW_FOLDER_DEFAULT)
# with open(toc, encoding="utf8", errors='replace') as f:
#     line = f.readline()
#     while line != "":
#         print(line)
# sys.exit(42)

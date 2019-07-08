from PyQt5 import Qt
from bs4 import BeautifulSoup
import urllib.request
from urllib.request import build_opener, HTTPCookieProcessor, HTTPError
from http import cookiejar
import zipfile
from modules import defines
import os
import re
import time
import tempfile
from _thread import start_new_thread
from threading import Lock
from subprocess import check_output, check_call
import hashlib
import json

opener = build_opener(HTTPCookieProcessor(cookiejar.CookieJar()))

# default User-Agent ('Python-urllib/2.6') will *not* work
opener.addheaders = [('User-Agent', 'Mozilla/5.0'), ]

# Debug helper: caches html page to not hammer server while testing/debugging/coding    
class CachedResponse:
    data = ""
    def __init__(self,data):
        self.data=data
        
    def read(self):
        return self.data

# Debug helper: caches html page to not hammer server while testing/debugging/coding    
class CacheDecorator(object):
    cachePrefix = '/tmp/urlcache_'
    def __init__(self,fun):
        self.fun=fun
        
    def __call__(self, url):
        md5 = hashlib.md5()
        md5.update(bytes(url,'utf8'))
        hash=md5.hexdigest()
        try:
            return self.ReadFromCache(hash)
        except:
            response = self.fun(url)
            f = open(self.cachePrefix +  hash, "w")
            f.write(str(response.read()))
            f.close()
            return response            
            
    def ReadFromCache(self, hash): 
        return CachedResponse(open(self.cachePrefix + hash,'r').read())

# Enable CacheDecorator in order to cache html pages retrieved from curse
# WARNING only for html parsing, disable when you are testing downloading zips
#@CacheDecorator
def OpenWithRetry(url):
    count = 0
    maxcount = 5
    
    # Retry 5 times
    while count < maxcount:
        try:
            response = opener.open(urllib.parse.urlparse(urllib.parse.quote(url, ':/?=')).geturl())

            return response

        except Exception as e:
            print("Ne peut ouvrir '{}', réessayé... ({})".format(url, count))

            count = count + 1
            time.sleep(1)

            if count >= maxcount:
                raise


class CheckDlg(Qt.QDialog):
    checkFinished = Qt.pyqtSignal(Qt.QVariant, bool, Qt.QVariant)
    closeSignal = Qt.pyqtSignal()
    print('Contrôle de la présence d\'un catalogue')

    def __init__(self, parent, addons):
        super(CheckDlg, self).__init__(parent)
        settings = Qt.QSettings()
        layout = Qt.QVBoxLayout(self)
        if len(addons) == 1:
            layout.addWidget(Qt.QLabel(self.tr("Vérifiez si cet Addon nécessite une mise à jour...")))
        else:
            layout.addWidget(Qt.QLabel(self.tr("Vérifiez si ces Addons nécessitent une mise à jour...")))
        self.progress = Qt.QProgressBar(self)
        self.progress.setRange(0, len(addons))
        self.progress.setValue(0)
        self.progress.setFormat("%v / %m | %p%")
        layout.addWidget(self.progress)
        cancelBox = Qt.QHBoxLayout()
        cancelBox.addStretch()
        self.cancelButton = Qt.QPushButton(self.tr("Cancel"), self)
        self.cancelButton.clicked.connect(self.onCancel)
        cancelBox.addWidget(self.cancelButton)
        cancelBox.addStretch()
        layout.addLayout(cancelBox)
        self.addons = addons
        self.maxThreads = int(settings.value(defines.LCURSE_MAXTHREADS_KEY, defines.LCURSE_MAXTHREADS_DEFAULT))
        self.sem = Qt.QSemaphore(self.maxThreads)

        # safe to use without a mutex because reading and writing are independent of each other,
        # and GIL will make these atomic operations.
        self.cancelled = False

        # protected with self.progressMutex
        self.progressMutex = Lock()
        self.progressOrAborted = 0

        self.closeSignal.connect(self.close)

    def closeEvent(self, event):
        with self.progressMutex:
            if self.progressOrAborted < self.progress.maximum():
                # if we aren't ready to close, the user pressed the close button - set the cancel flag so we can stop
                # si nous ne sommes pas prêts à fermer, l’utilisateur a appuyé sur le bouton Fermer
                # - définir l’indicateur d’annulation pour que nous puissions arrêter
                self.cancelled = True
                event.ignore()

    def startWorkerThreads(self):
        print('Démarrage tâche (thread)')
        self.threads = []
        for addon in self.addons:
            self.sem.acquire()
            if not self.cancelled:
                thread = CheckWorker(addon)
                thread.checkFinished.connect(self.onCheckFinished)
                thread.start()
                self.threads.append(thread)
            else:
                self.onCancelOrFinish(False)

    def exec_(self):
#        print('démarrage nouveau thread')
        start_new_thread(self.startWorkerThreads, ())
        super(CheckDlg, self).exec_()

    def onCancelOrFinish(self, updateProgress):
#        print('Action terminée ou stoppée par l\'utilisateur')
        self.sem.release()
        shouldClose = False
        if updateProgress:
            self.progress.setValue(self.progress.value() + 1)
        with self.progressMutex:
            self.progressOrAborted += 1
            if self.progressOrAborted == self.progress.maximum():
                shouldClose = True
        if shouldClose:
            # emit this as a signal so that it will be processed on the main thread.
            # Otherwise, this will try to do cleanup from a worker thread, which is a /bad/ idea.
            self.closeSignal.emit()

    @Qt.pyqtSlot(Qt.QVariant, bool, Qt.QVariant)
    def onCheckFinished(self, addon, needsUpdate, updateData):
        self.checkFinished.emit(addon, needsUpdate, updateData)
        self.onCancelOrFinish(True)

    def onCancel(self):
        self.cancelled = True


class CheckWorker(Qt.QThread):
    checkFinished = Qt.pyqtSignal(Qt.QVariant, bool, Qt.QVariant)

    def __init__(self, addon):
        super(CheckWorker, self).__init__()
        self.addon = addon

    def needsUpdateGit(self):
        try:
            settings = Qt.QSettings()
            dest = "{}/_retail_/Interface/AddOns/{}".format(
                settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT),
                os.path.basename(str(self.addon[2])[:-4]))
            originCurrent = str(check_output(["git", "ls-remote", str(self.addon[2]), "HEAD"]), "utf-8").split()[0]
            localCurrent = self.addon[3]
            if localCurrent != originCurrent:
                return (True, (originCurrent, ""))
            return (False, ("", ""))
        except Exception as e:
            print("Git Update Exception",e)
        return (False, None)

    def needsUpdateCurse(self):
        try:
            pattern = re.compile("-nolib$")
            url = self.addon[2] + '/files'
            response = OpenWithRetry(url)
            html = response.read()
            soup = BeautifulSoup(html, "lxml")
            beta=self.addon[4]
#            lis = soup.findAll("tr","project-file-list__item")
            lis = soup.findAll("tr")
            if lis:
#                versionIdx = 0
                versionIdx = 1
                isOk=False
                while True:
#                    isOk= beta or lis[versionIdx].td.span.attrs['title']=='Release'
                    isOk= beta or lis[versionIdx].td.div.span.string=='R'
                    if isOk:
                        break
                    versionIdx=versionIdx+1
                row=lis[versionIdx]
#                version=row.find("span","table__content file__name").string
                elem=row.find("a",attrs={"data-action":"file-link"})
                version=elem.string
                if str(self.addon[3]) != version:
                    addonid=elem.attrs['href'].split('/')[-1]
                    addonname=elem.attrs['href'].split('/')[-3]
#                    downloadLink="https://www.curseforge.com"+ row.find("a").attrs['href'] + '/file'
                    downloadLink = "https://www.curseforge.com/wow/addons/" + addonname + "/download/" + addonid + "/file"
                    return (True, (version, downloadLink))
            return (False, ("", ""))
            
        except HTTPError as e:
            print("Curse Update Exception",e)
        except Exception as e:
            print(e)
        return (False, None)

    def run(self):
        result = None;
        if "curseforge.com" in self.addon[2]:
            result = self.needsUpdateCurse()
        elif self.addon[2].endswith(".git"):
            result = self.needsUpdateGit()

        if result:
            self.checkFinished.emit(self.addon, result[0], result[1])
        else:
            self.checkFinished.emit(self.addon, False, False)


class UpdateDlg(Qt.QDialog):
    updateFinished = Qt.pyqtSignal(Qt.QVariant, bool)

    def __init__(self, parent, addons):
        super(UpdateDlg, self).__init__(parent)
        settings = Qt.QSettings()
        layout = Qt.QVBoxLayout(self)
        if len(addons) == 1:
            layout.addWidget(Qt.QLabel(self.tr("Mise à jour Addon...")))
        else:
            layout.addWidget(Qt.QLabel(self.tr("Mise à jour des addons...")))
        self.progress = Qt.QProgressBar(self)
        self.progress.setRange(0, len(addons))
        self.progress.setValue(0)
        self.progress.setFormat("%v / %m | %p%")
        layout.addWidget(self.progress)
        self.addons = addons
        self.maxThreads = int(settings.value(defines.LCURSE_MAXTHREADS_KEY, defines.LCURSE_MAXTHREADS_DEFAULT))
        self.sem = Qt.QSemaphore(self.maxThreads)

    def startWorkerThreads(self):
        self.threads = []
        print('Génération des tâches (threads)')
        for addon in self.addons:
            self.sem.acquire()
            thread = UpdateWorker(addon)
            thread.updateFinished.connect(self.onUpdateFinished)
            thread.start()
            self.threads.append(thread)

    def exec_(self):
        start_new_thread(self.startWorkerThreads, ())
        super(UpdateDlg, self).exec_()

    @Qt.pyqtSlot(Qt.QVariant, bool)
    def onUpdateFinished(self, addon, result):
        self.sem.release()
        value = self.progress.value() + 1
        self.progress.setValue(value)
        self.updateFinished.emit(addon, result)
        if value == self.progress.maximum():
            self.close()


class UpdateWorker(Qt.QThread):
    updateFinished = Qt.pyqtSignal(Qt.QVariant, bool)

    def __init__(self, addon):
        super(UpdateWorker, self).__init__()
        self.addon = addon

    def doUpdateGit(self):
        try:
            settings = Qt.QSettings()
            dest = "{}/_retail_/Interface/AddOns/{}".format(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT))
            destAddon = "{}/{}".format(dest, os.path.basename(str(self.addon[2]))[:-4])
            if not os.path.exists(destAddon):
                os.chdir(dest)
                check_call(["git", "clone", self.addon[2]])
            else:
                os.chdir(destAddon)
                check_call(["git", "pull"])
            return True
        except Exception as e:
            print("DoGitUpdate",e)
        return False

    def doUpdateCurse(self):
        try:
            settings = Qt.QSettings()
            response = OpenWithRetry(self.addon[5][1])
            dest = "{}/_retail_/Interface/AddOns/".format(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT))

            with tempfile.NamedTemporaryFile('w+b') as zipped:
                zipped.write(response.read())
                zipped.seek(0)
                with zipfile.ZipFile(zipped, 'r') as z:
                    r=re.compile(".*\.toc$")
                    r2=re.compile("[\\/]")
                    tocs=filter(r.match,z.namelist())
                    for nome in list(tocs):
                        t=r2.split(nome)
                        if len(t) == 2:
                            break
                    toc="{}/_retail_/Interface/AddOns/{}".format(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT),nome)
                    z.extractall(dest)
            return True, toc
        except Exception as e:
            print("DoCurseUpdate",e)
            raise e
        return False

    def run(self):
        if "curseforge.com" in self.addon[2]:
            result,toc = self.doUpdateCurse()
        elif self.addon[2].endswith(".git"):
            result,toc = self.doUpdateGit()
        else:
            result=False
            toc="n/a"
        self.updateFinished.emit(self.addon + (toc,), result)


class UpdateCatalogDlg(Qt.QDialog):
    updateCatalogFinished = Qt.pyqtSignal(Qt.QVariant)
    print('Lecture catalogue')

    def __init__(self, parent):
        super(UpdateCatalogDlg, self).__init__(parent)
        layout = Qt.QVBoxLayout(self)
        layout.addWidget(Qt.QLabel(self.tr("Mise à jour de la liste des Addons disponible ...")))
        self.progress = Qt.QProgressBar(self)
        self.progress.setRange(0, 0)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

    def exec_(self):
        self.thread = UpdateCatalogWorker()
        self.thread.updateCatalogFinished.connect(self.onUpdateCatalogFinished)
        self.thread.retrievedLastpage.connect(self.setMaxProgress)
        self.thread.progress.connect(self.onProgress)
        self.thread.start()
        super(UpdateCatalogDlg, self).exec_()

    @Qt.pyqtSlot(int)
    def setMaxProgress(self, maxval):
        self.progress.setRange(0, maxval)

    @Qt.pyqtSlot(int)
    def onProgress(self, foundAddons):
        value = self.progress.value() + 1
        self.progress.setValue(value)
        self.progress.setFormat(self.tr("%p% - Addons trouvés : {}").format(foundAddons))

    @Qt.pyqtSlot(Qt.QVariant)
    def onUpdateCatalogFinished(self, addons):
        self.updateCatalogFinished.emit(addons)
        self.close()


class UpdateCatalogWorker(Qt.QThread):
    updateCatalogFinished = Qt.pyqtSignal(Qt.QVariant)
    retrievedLastpage = Qt.pyqtSignal(int)
    progress = Qt.pyqtSignal(int)

    def __init__(self):
        super(UpdateCatalogWorker, self).__init__()
        settings = Qt.QSettings()
        self.addons = []
        self.addonsMutex = Qt.QMutex()
        self.maxThreads = int(settings.value(defines.LCURSE_MAXTHREADS_KEY, defines.LCURSE_MAXTHREADS_DEFAULT))
        self.sem = Qt.QSemaphore(self.maxThreads)
        self.lastpage = 1
        print("Initialisation")

    def retrievePartialListOfAddons(self, page):
        # response va contenir la page de l'URL en cours, fonction du numéro de page
        response = OpenWithRetry("https://www.curseforge.com/wow/addons?page={}".format(page))
        # la variable soup va contenir la transformation de la page en un arbre hiérarchisé via l'analyseur XML
        # Analyseur XML (analyseur = parser en anglais. lxml est l'analyseur le plus rapide) 
        soup = BeautifulSoup(response.read(), "lxml")

        # Le nombre de page est contenu dans la ligne
        # <a class="pagination-item" href="/wow/addons?page=345"><span class="text-primary-500">345</span></a>

        # Traitement origine erreur serveur conservé
        # Curse returns a soft-500
        if soup.find_all("h2", string="Error"):
            print("Erreur coté serveur pendant la création de la liste des addons.")

        # Initialisation à la page 1
        lastpage = 1
        # traitement particulier de la page 1 pour extraire le nombre de page à aspirer
        if page == 1:
        # lignes origine
#            pager = soup.select("ul.b-pagination-list.paging-list.j-tablesorter-pager.j-listing-pagination li")
#            lastpage = int(pager[len(pager) - 2].contents[0].contents[0])

        ####### Rechercher le nombre de page
        # Variable pager contient tous les class="pagination-item"
            pager = soup.select("a.pagination-item")
        # Si la variable pager existe (n'est pas vide), extraire le nombre de page à lire pour construire le catalogue
            if pager:
            # ligne d'origine
#                lastpage = int(pager[len(pager) - 2].contents[0].contents[0])

            # extraction du deuxième élément de la liste -> indice 1, puisque que la prmière indexation est 0 -> attribut "href"
            # on obtient une chaine de caractères
                NbrPage = pager[len(pager)-1]["href"]
                longueur=len(NbrPage)
                position_egal = NbrPage.rfind("=")+1
            # transtypage de la chaine resultante en entier après l'avoir découpée
                lastpage = int(NbrPage[NbrPage.rfind("=")+1:len(NbrPage)])
                print('Nbr de page à traiter : ', lastpage)

        ####### Traitement d'extraction des informations des addons effectué sur chaque page (dont la page 1)

        # ligne origine
#        projects = soup.select("li.project-list-item")  # li .title h4 a")

        # balise "a", attribut class="my-auto"
        projects = soup.find_all("a", "my-auto")
        NbrElementListe = len(projects)-1
        self.addonsMutex.lock()
        for index, Element in enumerate(projects):
            if (index % 2) == 0:
                    nome=str(Element.text).strip()
                    URL=str(Element.get('href').strip())
                    href="https://www.curseforge.com{}".format(URL)
                    self.addons.append([nome, href])
            else:
                    pass

        # Python Multithreading Lock objects
        self.progress.emit(len(self.addons))
        self.addonsMutex.unlock()
        self.sem.release()
        return lastpage

    def retrieveListOfAddons(self):
        page = 1
        lastpage = 1
        print("Chercher liste des ADDONS")
        self.sem.acquire()
        lastpage = self.retrievePartialListOfAddons(page)
        page += 1
        self.retrievedLastpage.emit(lastpage)
        # Tant que la page en cours de traitement est inférieure ou égal au nombre de page à extraire
        while page <= lastpage:
            self.sem.acquire()
            start_new_thread(self.retrievePartialListOfAddons, (page,))
            page += 1

    def run(self):
        self.retrieveListOfAddons()
        # wait until all worker are done
        # attendre que tous les threads aient terminé
        self.sem.acquire(self.maxThreads)
        self.updateCatalogFinished.emit(self.addons)

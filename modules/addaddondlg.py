from PyQt5 import Qt


class AddAddonDlg(Qt.QDialog):
    def __init__(self, parent, availableAddons):
        super(AddAddonDlg, self).__init__(parent)
        box = Qt.QVBoxLayout(self)
        box.addWidget(Qt.QLabel(self.tr("Donnez le nom ou l'URL de l'addon que vous souhaitez ajouter :"), self))
        self.input = Qt.QLineEdit(self)
        box.addWidget(self.input)
        btnBox = Qt.QDialogButtonBox(Qt.QDialogButtonBox.Ok | Qt.QDialogButtonBox.Cancel)
        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)
        box.addWidget(btnBox)
        self.show()
        if availableAddons:
            self.completer = Qt.QCompleter([addon[0] for addon in availableAddons], self)
            self.completer.setFilterMode(Qt.Qt.MatchContains)
            self.completer.setCaseSensitivity(Qt.Qt.CaseInsensitive)
            self.input.setCompleter(self.completer)
        else:
            Qt.QMessageBox.information(self, self.tr("Catalogue des addons absent"), self.tr(
                "Vous n'avez pas mis à jour le catalogue des addons disponibles, "
                "donnez l'URL de l'addon que vous souhaitez ajouter."))

    def getText(self):
        return self.input.text()

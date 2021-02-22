import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic

form_class = uic.loadUiType("BITCompare.ui")[0]

class App(QDialog, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(645,960)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    Main = App()
    Main.show()
    app.exec_()
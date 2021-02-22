import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox, QLineEdit,\
                            QCheckBox, QRadioButton,QProgressBar,QGroupBox,QFileDialog,QTableWidget,QSpinBox, \
                            QListWidget, QTabWidget, QTableWidgetItem


class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self):
        btn_ok = QPushButton('OK')
        btn_cancel = QPushButton('Cancel')
        btn_ok.clicked.connect(self.on_click)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(btn_ok)
        hbox.addWidget(btn_cancel)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addStretch(2)
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        self.setLayout(vbox)

        self.setWindowTitle('Box Layout')
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def on_click(self):
        QMessageBox.question(self, 'Message', "Do you like Python?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
#!/usr/bin/env python3

config = [
    {'name': 'Serve', 'btns': ['Serve', 'ClearCache', 'ClearCookie', 'Quit']},
    {'name': 'Utils', 'btns': ['build', 'minify', 'inline', 'base64', 'getqr']}
]

import os
import sys
import importlib

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class MainWindow(QMainWindow):

    rows = 4

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)

        tabs = QTabWidget()

        for tabconfig in config:

            tab = QWidget()
            tablayout = QGridLayout()

            btns = tabconfig['btns']
            for i, btn in enumerate(btns):

                if os.path.isfile(btn+'.py'):
                    # load button handler from seperate files
                    try:
                        m = importlib.import_module(btn)
                        action = m.Action()
                        title = action.title
                        handle = action.handle
                    except:
                        title = btn
                        handle = lambda: ...

                    qbtn = QPushButton(title)
                    qbtn.clicked.connect(handle)
                else:
                    qbtn = QPushButton(btn)
                    if btn == 'Quit':
                        qbtn.clicked.connect(lambda: app.quit())

                tablayout.addWidget(qbtn, i%self.rows, int(i/self.rows))
                    

            # btn = QPushButton(QIcon('config.gif'), 'btn4')
            # btn.setToolButtonStyle(ToolButtonTextUnderIcon)
            tab.setLayout(tablayout)

            # this seems of no use
            # tabs.setTabIcon(0, QIcon('config.gif'))

            tabs.addTab(tab, tabconfig['name'])

        # tabs.setTabShape(QTabWidget.Triangular)
        layout.addWidget(tabs)
        self.setCentralWidget(central)
        self.setStyleSheet(r'''
            QTabWidget{
                margin:10px;
            }
            QPushButton{
                width:60px;
                height:40px;
                padding:10px;
            }
            QTabWidget{
                font-size:16px;
                color:red;
            }
        ''')


if __name__ == '__main__':

    # get all styles
    # print(QStyleFactory.keys())
    # QApplication.setStyle(QStyleFactory.create('Fusion'))

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())



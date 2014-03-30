from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTabWidget, QVBoxLayout, QWidget, QTextEdit


class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        tabs = QTabWidget()

        tab = QWidget()
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Status", "URL", "Action"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        tab.setLayout(layout)
        tabs.addTab(tab, 'Serve')

        tab = QWidget()
        self.edit = QTextEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.edit)
        tab.setLayout(layout)
        tabs.addTab(tab, 'Serve')

        layout = QVBoxLayout()
        layout.addWidget(tabs)
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)
        self.statusBar().showMessage('haha', 5000)


class Action():
    '''
    Action class define what will be shown in the main window
    the icon, wording, and handler
    '''
    title = 'Serve'

    def handle(self):

        if 'dialog' not in globals():
            global window
            window = Window()

        window.show()

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())

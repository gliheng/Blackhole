from PyQt5.QtCore import pyqtSignal, QMimeData, Qt
from PyQt5.QtGui import QPixmap, QPalette
from PyQt5.QtWidgets import QDialog, QLabel, QFrame, QVBoxLayout


class Dropsite(QLabel):
    dropped = pyqtSignal(QMimeData)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setPixmap(QPixmap('./img/dropzone.ico'))
        self.setScaledContents(True)

        self.setFrameStyle(QFrame.Sunken | QFrame.StyledPanel)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setAutoFillBackground(True)

    def dragEnterEvent(self, evt):
        evt.acceptProposedAction()
        self.setBackgroundRole(QPalette.Highlight)

    def dragMoveEvent(self, evt):
        pass

    def dragLeaveEvent(self, evt):
        self.setBackgroundRole(QPalette.Dark)
        
    def dropEvent(self, evt):
        self.setBackgroundRole(QPalette.Dark)
        self.dropped.emit(evt.mimeData())



class Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()

        label = QLabel('Drop your files here!')
        label.setAlignment(Qt.AlignCenter)

        dropsite = Dropsite()
        dropsite.dropped.connect(self.onDrop)

        layout.addWidget(label)
        layout.addWidget(dropsite)

        self.setLayout(layout)

    def onDrop(self, mimeData=None):
        print(mimeData)
        


class Action():
    '''
    Action class define what will be shown in the main window
    the icon, wording, and handler
    '''
    title = 'Minify'

    def handle(self):

        if 'dialog' not in globals():
            global dialog
            dialog = Dialog()

        dialog.show()

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    d = Dialog()
    d.show()
    sys.exit(app.exec_())

from PyQt5.QtWidgets import QLineEdit, QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QImage, QPixmap

class Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.lineedit = QLineEdit()
        self.lineedit.setPlaceholderText('Type url here')
        self.lineedit.setFocus()

        # self.lineedit.editingFinished.connect(self.drawQrcode)
        self.lineedit.textChanged.connect(self.drawQrcode)

        self.image = QLabel()
        self.image.setScaledContents(True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.lineedit)
        layout.addWidget(self.image)

        self.setStyleSheet(r'''
            QLineEdit{
                padding:10px;
            }
        ''')

    def drawQrcode(self):
        import qrcode
        import tempfile
        import os

        temp_dir = os.path.join(tempfile.gettempdir(), 'blackhole')
        if not os.path.isdir(temp_dir):
            os.mkdir(temp_dir)

        imgpath = os.path.join(temp_dir, 'qrcode.png')

        string = self.lineedit.text()
        qrcode.make(string).save(imgpath)

        img = QImage()
        img.load(imgpath)

        self.image.setPixmap(QPixmap.fromImage(img))

class Action():
    title = 'Qrcode'

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

import sys
import cv2
import threading
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLabel
from PyQt6.QtGui import QPalette, QColor, QIcon, QPixmap, QImage
from PyQt6.QtCore import Qt

from save_send_network_tables import *


class Color(QWidget):
    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)


class MainWindow(QMainWindow):
    bot_active = False
    auto_bot = None
    window_message = ""
    mode = 0
    tries = 0

    def __init__(self):
        super(MainWindow, self).__init__()  # *args, **kwargs)
        #  
        self.setWindowTitle("Smarter Dashboard")
        self.setWindowIcon(QIcon("GUI/4829logo.png"))

        layout = QGridLayout()

        # first row
        layout.addWidget(Color('white'), 0, 0)
        layout.addWidget(Color('white'), 0, 1)
        layout.addWidget(Color('white'), 0, 2)
        layout.addWidget(Color('white'), 0, 3)
        layout.addWidget(Color('white'), 0, 4)
        # second row

        # display the playing field map on the screen
        self.field_image = QPixmap(cv2.imread("GUI/rapid-react-field-red.png"))  # for blue alliance, use "GUI/rapid-react-field-blue.png"
        playingfieldmap = QLabel()
        pixmap = self.convert_cv_qt(self.field_image)
        playingfieldmap.setPixmap(pixmap)
        layout.addWidget(playingfieldmap, 1, 0, 4, 1)

        layout.addWidget(Color('white'), 1, 1)
        layout.addWidget(Color('white'), 1, 2)
        layout.addWidget(Color('white'), 1, 3)
        layout.addWidget(Color('white'), 1, 4)
        # third row
        layout.addWidget(Color('white'), 2, 1)
        layout.addWidget(Color('white'), 2, 2)
        layout.addWidget(Color('white'), 2, 3)
        layout.addWidget(Color('white'), 2, 4)
        # fourth row
        layout.addWidget(Color('white'), 3, 1)
        layout.addWidget(Color('white'), 3, 2)
        layout.addWidget(Color('white'), 3, 3)
        layout.addWidget(Color('white'), 3, 4)
        # fifth row
        layout.addWidget(Color('white'), 4, 1)
        layout.addWidget(Color('white'), 4, 2)
        layout.addWidget(Color('white'), 4, 3)
        layout.addWidget(Color('white'), 4, 4)
        # sixth row
        layout.addWidget(Color('white'), 5, 0)
        layout.addWidget(Color('white'), 5, 1)
        layout.addWidget(Color('white'), 5, 2)
        layout.addWidget(Color('white'), 5, 3)
        layout.addWidget(Color('white'), 5, 4)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def convert_cv_qt(self, cv_img) -> QPixmap:
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(int(self.width()), int(self.height()), Qt.AspectRatioMode.KeepAspectRatio)
        return QPixmap.fromImage(p)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()



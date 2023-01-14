import sys
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt
from GUI.main_window_ui import *
import cv2
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle("Smarter Dashboard")
        self.setWindowIcon(QtGui.QIcon("GUI/4829logo.png"))
        self.setFocus()



    def convert_cv_qt(self, cv_img) -> QtGui.QPixmap:
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(int(self.width() * 1.125), int(self.height() * 1.125), Qt.AspectRatioMode.KeepAspectRatio)
        return QtGui.QPixmap.fromImage(p)

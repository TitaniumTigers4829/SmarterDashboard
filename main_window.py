from PyQt6 import QtWidgets
import threading
import logging
import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from scoretracker import ScoreTracker
from GUI.main_window_ui import *
from score_updater import *


class MainWindow(QtWidgets.QMainWindow, ScoreTracker):


    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
       # self.scoreTracker()
        self.setWindowTitle("Smarter Dashboard")
        self.setWindowIcon(QtGui.QIcon("GUI/4829logo.png"))
        self.setFocus()
        self.field_image = cv2.imread("GUI/charged-up-field-red.png")
        self.playingfield.setPixmap(self.convert_cv_qt(self.field_image))
       # self.scoreUpdater()

    def convert_cv_qt(self, cv_img) -> QPixmap:
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(int(self.width() * 1.125), int(self.height() * 1.125), Qt.AspectRatioMode.KeepAspectRatio)
        return QPixmap.fromImage(p)

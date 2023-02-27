from PyQt6 import QtWidgets
import threading
import logging
import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from GUI.main_window_ui import *

class ScoreTracker(Ui_MainWindow):
    
    def scoreTracker(self):
        self.lowerterminal1.setStyleSheet("background-color: green")
        
from PyQt6 import QtWidgets
import threading
import logging
import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


from GUI.main_window_ui import *
from save_send_network_tables import *


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    bot_active = False
    auto_bot = None
    window_message = ""
    mode = 0
    tries = 0

    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle("Smarter Dashboard")
        self.setWindowIcon(QtGui.QIcon("GUI/4829logo.png"))
        self.setFocus()
        self.field_image = cv2.imread("GUI/rapid-react-field-red.png")
        self.label_2.setPixmap(self.convert_cv_qt(self.field_image))

    def establish_network_table_connection(self):
        cond = threading.Condition()
        notified = [False]

        def connectionListener(connected, info):
            print(info, '; Connected=%s' % connected)
            with cond:
                notified[0] = True
                cond.notify()

        logging.basicConfig(level=logging.DEBUG)
        NetworkTables.startClientTeam(4829)
        NetworkTables.addConnectionListener(connectionListener, immediateNotify=True)

        with cond:
            print("Waiting")
            if not notified[0]:
                cond.wait()
                self.connected_to_network_table = False

        # This is reached once it is connected to the network table
        self.connected_to_network_table = True
        nt = NetworkTables.getTable("climbZerosTable")
        self.nt = nt
        print("Connected")

    def save_climb_zeroes(self):
        if self.nt is not None:
            self.label.setText("Connected")
            # This starts a thread that will run until climb values are saved
            t2 = threading.Thread(target=receive_climb_values, args=[self.nt])
            t2.start()
            self.button1.setStyleSheet("background-color: green")
        else:
            self.label.setText("Cannot establish connection")

    def send_button_clicked(self):
        if self.nt is not None:
            self.label.setText("Connected")
            self.sending_climb_zeroes = not self.sending_climb_zeroes
            if self.sending_climb_zeroes:
                self.button2.setText("Stop Sending")
                self.button1.setStyleSheet("")
                self.button1.setDisabled(True)
                t3 = threading.Thread(target=send_climb_values, args=[self.nt])
                t3.start()
            else:
                self.button2.setText("Send")
                self.button1.setEnabled(True)
        else:
            self.label.setText("Cannot establish connection")

    def convert_cv_qt(self, cv_img) -> QPixmap:
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(int(self.width() / 2), int(self.height() / 2), Qt.AspectRatioMode.KeepAspectRatio)
        return QPixmap.fromImage(p)

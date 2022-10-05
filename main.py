import sys

from PyQt6.QtWidgets import QApplication

from main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

#!/usr/bin/python3

import sys, os

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QFile, QIODevice, Slot

from ament_index_python.packages import get_package_share_directory


class URGui(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.app = QApplication()
        ui_file_name = os.path.join(get_package_share_directory("drt_ur_gui"), "ui", "drt_ur_gui.ui")
        ui_file = QFile(ui_file_name)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
            sys.exit(-1)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        if not self.window:
            print(loader.errorString())
            sys.exit(-1)
        self.window.pushButton.clicked.connect(self.button_clicked)
        self.window.show()
        
    @Slot()
    def button_clicked(self):
        print("button clicked!!!")
        return

if __name__ == "__main__":
    app = QApplication()
    ur_gui = URGui()
    ur_gui.window.show()
    sys.exit(app.exec())
    

# @Slot()
# def button_clicked(self):
#     print("button clicked!!!!")
#     return

# if __name__ == "__main__":
#     app = QApplication(sys.argv)

#     ui_file_name = os.path.join(get_package_share_directory("drt_ur_gui"), "ui", "drt_ur_gui.ui")
#     ui_file = QFile(ui_file_name)
#     if not ui_file.open(QIODevice.ReadOnly):
#         print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
#         sys.exit(-1)
#     loader = QUiLoader()
#     window = loader.load(ui_file)
#     ui_file.close()
#     if not window:
#         print(loader.errorString())
#         sys.exit(-1)
    
#     window.pushButton.clicked.connect(button_clicked)
    
#     window.show()

#     sys.exit(app.exec())
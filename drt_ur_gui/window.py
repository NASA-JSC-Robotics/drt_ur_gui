
import os, sys
from python_qt_binding.QtWidgets import QMainWindow
from python_qt_binding.QtCore import QFile, QIODevice, Slot
from python_qt_binding import loadUi

from ament_index_python.packages import get_package_share_directory

from drt_ur_gui.node import RemoteURCmdr

class URGui(QMainWindow, RemoteURCmdr):
    def __init__(self):
        super().__init__()
        ui_file_name = os.path.join(get_package_share_directory("drt_ur_gui"), "ui", "drt_ur_gui.ui")
        ui_file = QFile(ui_file_name)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
            sys.exit(-1)
        # loader = QUiLoader()
        # self.window = loader.load(ui_file)
        loadUi(ui_file, self)
        ui_file.close()
        # if not self.window:
        #     print(loader.errorString())
        #     sys.exit(-1)
        self.srvButton.clicked.connect(self.srv_button_clicked)
        self.pushButton2.clicked.connect(self.button2_clicked)
        self.pushButton3.clicked.connect(self.button3_clicked)
        self.pushButton4.clicked.connect(self.button4_clicked)
        
    @Slot()
    def srv_button_clicked(self):
        print("srv button clicked!!!")
        response = self.send_request()
        print(response)
        return

    @Slot()
    def button2_clicked(self):
        print("button 2 clicked!!!")
        return
    
    @Slot()
    def button3_clicked(self):
        print("button 3 clicked!!!")
        return

    @Slot()
    def button4_clicked(self):
        print("button 4 clicked!!!")
        return
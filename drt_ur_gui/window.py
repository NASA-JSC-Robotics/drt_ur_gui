
import os, sys
from python_qt_binding.QtWidgets import QMainWindow
from python_qt_binding.QtCore import QFile, QIODevice, Slot, QTimer
from python_qt_binding import loadUi

from ament_index_python.packages import get_package_share_directory

# from drt_ur_gui.node import RemoteURCmdr

class URGui(QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.be = backend
        ui_file_name = os.path.join(get_package_share_directory("drt_ur_gui"), "ui", "drt_ur.ui")
        ui_file = QFile(ui_file_name)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
            sys.exit(-1)
        loadUi(ui_file, self)
        ui_file.close()
        
        timer1 = QTimer(self)
        timer1.timeout.connect(self.status_0)
        timer1.start(2000)
        timer2 = QTimer(self)
        timer2.timeout.connect(self.status_1)
        timer2.start(2000)
        timer3 = QTimer(self)
        timer3.timeout.connect(self.status_2)
        timer3.start(2000)
        
        
        # stat_timer_0 = self.create_timer(2.0, self.status_0, callback_group=self.r_cbg)
        # stat_timer_1 = self.create_timer(2.0, self.status_1, callback_group=self.r_cbg)
        # stat_timer_2 = self.create_timer(2.0, self.status_2, callback_group=self.r_cbg)

        self.pushButton.clicked.connect(self.button_clicked)
        self.pushButton_1.clicked.connect(self.button1_clicked)
        self.pushButton_2.clicked.connect(self.button2_clicked)
        self.pushButton_3.clicked.connect(self.button3_clicked)
        
    @Slot()
    def button_clicked(self):
        print("Button 0 clicked!!!")
        response = self.be.send_request_0()
        print(response)
        return

    @Slot()
    def button1_clicked(self):
        print("Button 1 clicked!!!")
        response = self.be.send_request_1()
        print(response)
        return
    
    @Slot()
    def button2_clicked(self):
        print("button 2 clicked!!!")
        response = self.be.send_request_2()
        print(response)
        return

    @Slot()
    def button3_clicked(self):
        print("button 3 clicked!!!")
        response = self.be.send_request_3()
        print(response)
        return
    
    def status_0(self):
        print("Requesting status 0")
        response = self.be.send_request_4()
        print(response)
        return
    
    def status_1(self):
        print("Requesting status 1")
        response = self.be.send_request_5()
        print(response)
        return
    
    def status_2(self):
        print("Requesting status 2")
        response = self.be.send_request_6()
        print(response)
        return
    

import os, sys
from python_qt_binding.QtWidgets import QMainWindow, QTableWidgetItem
from python_qt_binding.QtCore import QFile, QIODevice, Slot, QTimer
from python_qt_binding.QtGui import QTextCharFormat
from python_qt_binding import loadUi

from ament_index_python.packages import get_package_share_directory

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
        
        
        # Status timers
        self.tableWidget.setRowCount(3)
        timer1 = QTimer(self)
        timer1.timeout.connect(self.status_0)
        self.setCell(0, 0, "request 1")
        timer1.start(2000)
        timer2 = QTimer(self)
        timer2.timeout.connect(self.status_1)
        self.setCell(1, 0, "request 2")
        timer2.start(2000)
        timer3 = QTimer(self)
        timer3.timeout.connect(self.status_2)
        self.setCell(2, 0, "request 3")
        timer3.start(2000)
        self.status_0()
        self.status_1()
        self.status_2()
        
        self.textEditor.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #000000;
                color:            #FFFFFF;
                font-family:      monospace;
                font-size:        12pt;
                }
            """)
        
        # Button connections
        self.pushButton.clicked.connect(self.button_clicked)
        self.pushButton_1.clicked.connect(self.button1_clicked)
        self.pushButton_2.clicked.connect(self.button2_clicked)
        self.pushButton_3.clicked.connect(self.button3_clicked)
        

        
        
    def setCell(self, row, column, data):
        item = QTableWidgetItem(str(data))
        self.tableWidget.setItem(row, column, item)
        return
        
    
    @Slot()
    def button_clicked(self):
        self.textEditor.clear()
        print("Button 0 requested, calling...")
        self.textEditor.insertPlainText("Button 0 requested, calling...\n")
        response = self.be.send_request_0()
        print(response)
        self.textEditor.insertPlainText(f"Button 0 response: {str(response)}")
        return

    @Slot()
    def button1_clicked(self):
        print("Button 1 clicked!!!")
        self.textEditor.clear()
        response = self.be.send_request_1()
        print(response)
        self.textEditor.insertPlainText(f"Button 1 response: {str(response)}")
        return
    
    @Slot()
    def button2_clicked(self):
        print("button 2 clicked!!!")
        self.textEditor.clear()
        response = self.be.send_request_2()
        print(response)
        self.textEditor.insertPlainText(f"Button 2 response: {str(response)}")
        return

    @Slot()
    def button3_clicked(self):
        print("button 3 clicked!!!")
        self.textEditor.clear()
        response = self.be.send_request_3()
        print(response)
        self.textEditor.insertPlainText(f"Button 3 response: {str(response)}")
        return
    
    def status_0(self):
        print("Requesting status 0")
        response = self.be.send_request_4()
        self.setCell(0, 1, str(response))
        print(response)
        return
    
    def status_1(self):
        print("Requesting status 1")
        response = self.be.send_request_5()
        self.setCell(1, 1, str(response))
        print(response)
        return
    
    def status_2(self):
        print("Requesting status 2")
        response = self.be.send_request_6()
        self.setCell(2, 1, str(response))
        print(response)
        return
    
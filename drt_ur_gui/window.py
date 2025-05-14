
import os, sys
from datetime import datetime
from python_qt_binding.QtWidgets import QMainWindow, QTableWidgetItem
from python_qt_binding.QtCore import QFile, QIODevice, Slot, QTimer
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
        self.setCell(0, 0, "Robot mode:")
        self.setCell(1, 0, "Safety mode:")
        self.setCell(2, 0, "Program state:")

        timer_robot_mode = QTimer(self)
        timer_robot_mode.timeout.connect(self.status_robot_mode)
        timer_robot_mode.start(2000)

        timer_safety_mode = QTimer(self)
        timer_safety_mode.timeout.connect(self.status_safety_mode)
        timer_safety_mode.start(2000)

        timer_program_state = QTimer(self)
        timer_program_state.timeout.connect(self.status_program_state)
        timer_program_state.start(2000)

        self.status_robot_mode()
        self.status_safety_mode()
        self.status_program_state()
        
        self.textEditor.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #000000;
                color:            #FFFFFF;
                font-family:      monospace;
                font-size:        10pt;
                }
            """)
        
        # Button connections
        self.b_brakeRelease.clicked.connect(self.brake_release_clicked)
        self.b_play.clicked.connect(self.play_clicked)
        self.b_connect.clicked.connect(self.connect_clicked)
        self.b_unlockPStop.clicked.connect(self.unlock_pstop_clicked)
        self.b_restartSafety.clicked.connect(self.restart_safety_clicked)
        
    def setCell(self, row, column, data):
        item = QTableWidgetItem(str(data))
        self.tableWidget.setItem(row, column, item)
        return
    
    def addText(self, data):
        self.textEditor.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}]")
        self.textEditor.appendPlainText(str(data))
        scrollbar = self.textEditor.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        return
    
    @Slot()
    def brake_release_clicked(self): # TODO
        # print("Button 0 requested, calling...")
        self.addText("Button 0 requested, calling...\n")
        response = self.be.send_brake_release()
        # print(response)
        self.addText(f"Button 0 response: {str(response)}\n\n")
        return

    @Slot()
    def play_clicked(self):
        # print("Button 1 clicked!!!")
        self.addText("Button 1 requested, calling...\n")
        response = self.be.send_play()
        # print(response)
        self.addText(f"Button 1 response: {str(response)}\n\n")
        return
    
    @Slot()
    def connect_clicked(self):
        # print("button 2 clicked!!!")
        self.addText("Button 2 requested, calling...\n")
        response = self.be.send_connect()
        # print(response)
        self.addText(f"Button 2 response: {str(response)}\n\n")
        return

    @Slot()
    def unlock_pstop_clicked(self):
        # print("button 3 clicked!!!")
        self.addText("Button 3 requested, calling...\n")
        response = self.be.send_unlock_pstop()
        # print(response)
        self.addText(f"Button 3 response: {str(response)}\n\n")
        return
    
    @Slot()
    def restart_safety_clicked(self):
        # print("button 3 clicked!!!")
        self.addText("Button 3 requested, calling...\n")
        response = self.be.send_restart_safety()
        # print(response)
        self.addText(f"Button 3 response: {str(response)}\n\n")
        return

    def status_robot_mode(self):
        # print("Requesting status 0")
        response = self.be.send_robot_mode_req()
        self.setCell(0, 1, str(response[0])) # TODO: process the other response items (answer, success)
        # print(response)
        return
    
    def status_safety_mode(self):
        # print("Requesting status 1")
        response = self.be.send_safety_mode_req()
        self.setCell(1, 1, str(response[0])) # TODO: process the other response items (answer, success)
        # print(response)
        return
    
    def status_program_state(self):
        # print("Requesting status 2")
        response = self.be.send_program_state_req()
        self.setCell(2, 1, str(response[0])) # TODO: process the other response items (program_name, answer, success)
        # print(response)
        return
    
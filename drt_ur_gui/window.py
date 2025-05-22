
import os, sys, queue
from datetime import datetime
from python_qt_binding.QtWidgets import QMainWindow, QTableWidgetItem
from python_qt_binding.QtCore import QFile, QIODevice, Slot, QTimer
from python_qt_binding import loadUi

from ament_index_python.packages import get_package_share_directory

from ur_dashboard_msgs.srv import (
    Popup, AddToLog, GetRobotMode,
    Load, IsProgramSaved, RawRequest,
    GetLoadedProgram, IsProgramRunning,
    GetProgramState, GetSafetyMode
)
from ur_dashboard_msgs.msg import ProgramState, RobotMode, SafetyMode


def denumerate_ros_msg_type(msg_type):
    return {getattr(msg_type, name): name for name in dir(msg_type) if not name.startswith('_') and isinstance(getattr(msg_type, name), int)}

ROBOT_MODES = denumerate_ros_msg_type(RobotMode)
SAFETY_MODES = denumerate_ros_msg_type(SafetyMode)


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
        
        timer_queue = QTimer(self)
        timer_queue.timeout.connect(self._consume_queue)
        timer_queue.start(50) # 20 hz

        timer_robot_mode = QTimer(self)
        timer_robot_mode.timeout.connect(self.status_robot_mode)
        timer_robot_mode.start(2000) # 0.5 hz

        timer_safety_mode = QTimer(self)
        timer_safety_mode.timeout.connect(self.status_safety_mode)
        timer_safety_mode.start(2000) # 0.5 hz

        timer_program_state = QTimer(self)
        timer_program_state.timeout.connect(self.status_program_state)
        timer_program_state.start(2000) # 0.5 hz

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
    

    
    def _consume_queue(self):
        try:
            response = self.be.response_queue.get(timeout=0.1) # we can only wait as long as our timer period, right?
            service_name = response['service_name']
            res_content = response['content']
            if service_name == 'dashboard_client/get_robot_mode':
                robot_mode = ROBOT_MODES[res_content.robot_mode.mode]
                self.show_robot_mode(robot_mode)
            elif service_name == 'dashboard_client/get_safety_mode':
                safety_mode = SAFETY_MODES[res_content.safety_mode.mode]
                self.show_safety_mode(safety_mode)
            elif service_name == 'dashboard_client/program_state':
                program_state = res_content.state.state
                self.show_program_state(program_state)
            else: # if response is not from a status service
                display_txt = []
                display_txt.append(response['message']) # TODO: process success as color highlight? Or prefix?
                res_fields = response['service_type'].Response.get_fields_and_field_types()
                for field in res_fields.keys():
                    display_txt.append(f"\v{field}: {getattr(res_content, field)}")
                display_txt = ''.join(display_txt)
                self.addText(display_txt)
        except queue.Empty:
            pass
        except Exception as e:
            self.be.get_logger().error(f'Exception {e} encountered while processing response queue')
            return
        return
        
    
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
    def brake_release_clicked(self):
        self.addText("Brake release requested, calling...\n")
        self.be.send_service_request('dashboard_client/brake_release')
        return

    @Slot()
    def play_clicked(self):
        self.addText("Program play requested, calling...\n")
        self.be.send_service_request('dashboard_client/play')
        return
    
    @Slot()
    def connect_clicked(self):
        self.addText("Dashboard connect requested, calling...\n")
        self.be.send_service_request('dashboard_client/connect')
        return

    @Slot()
    def unlock_pstop_clicked(self):
        self.addText("Button 3 requested, calling...\n")
        self.be.send_service_request('dashboard_client/unlock_protective_stop')
        return
    
    @Slot()
    def restart_safety_clicked(self):
        self.addText("Button 3 requested, calling...\n")
        self.be.send_service_request('dashboard_client/restart_safety')
        return

    def status_robot_mode(self):
        self.be.send_service_request('dashboard_client/get_robot_mode')
        return
    
    def status_safety_mode(self):
        self.be.send_service_request('dashboard_client/get_safety_mode')
        return

    def status_program_state(self):
        self.be.send_service_request('dashboard_client/program_state')
        return

    def show_robot_mode(self, mode: str):
        self.setCell(0, 1, mode)
        return
    
    def show_safety_mode(self, mode: str):
        self.setCell(1, 1, mode)
        return    
    
    def show_program_state(self, state: str):
        self.setCell(2, 1, state)
        return
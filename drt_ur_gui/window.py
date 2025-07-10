
import os, sys, queue
from datetime import datetime
from python_qt_binding.QtWidgets import QMainWindow, QTableWidgetItem, QTreeWidgetItem
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

from drt_ur_gui import ROBOT_MODES, SAFETY_MODES, SERVICES

class URGui(QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.be = backend
        self.all_services = {self.be.get_full_service_name(item['name']):item['type'] for item in SERVICES}

        ui_file_path = os.path.join(get_package_share_directory("drt_ur_gui"), "ui", "drt_ur.ui")
        self._load_ui(ui_file_path)
        self._init_text_editor()
        self._init_status_table()
        self._init_queue_consumer()
        self._connect_buttons()
        self._init_service_selector()
        self._init_service_tree()
    
    def _load_ui(self, ui_file_path: str):
        ui_file = QFile(ui_file_path)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_path}: {ui_file.errorString()}")
            sys.exit(-1)
        loadUi(ui_file, self)
        ui_file.close()
        return
    
    def _init_status_table(self):
        self.watchTable.setRowCount(3)
        self.setCell(0, 0, "Robot mode:")
        self.setCell(1, 0, "Safety mode:")
        self.setCell(2, 0, "Program state:")
        timer_robot_mode = QTimer(self)
        timer_robot_mode.timeout.connect(self.status_robot_mode)
        timer_robot_mode.start(2000) # 0.5 hz
        timer_safety_mode = QTimer(self)
        timer_safety_mode.timeout.connect(self.status_safety_mode)
        timer_safety_mode.start(2000) # 0.5 hz
        timer_program_state = QTimer(self)
        timer_program_state.timeout.connect(self.status_program_state)
        timer_program_state.start(2000) # 0.5 hz
        return

    def _init_queue_consumer(self):
        timer_queue = QTimer(self)
        timer_queue.timeout.connect(self._consume_queue)
        timer_queue.start(50) # 20 hz
        return

    def _init_text_editor(self):
        self.addText('Welcome to the Dexterous Robotics Remote UR GUI!')
        return
    

    
    def _connect_buttons(self):
        self.b_brakeRelease.clicked.connect(self.brake_release_clicked)
        self.b_play.clicked.connect(self.play_clicked)
        self.b_connect.clicked.connect(self.connect_clicked)
        self.b_unlockPStop.clicked.connect(self.unlock_pstop_clicked)
        self.b_restartSafety.clicked.connect(self.restart_safety_clicked)
        return

    def _init_service_selector(self):
        taken_services = [
            'brake_release',
            'play',
            'connect',
            'unlock_protective_stop',
            'restart_safety',
            'get_robot_mode',
            'get_safety_mode',
            'program_state',
            ]
        taken_services = [self.be.get_full_service_name(srv) for srv in taken_services]
        selector_services = list(set(self.all_services.keys()) - set(taken_services))
        if len(selector_services) == 0:
            return # no services to add to service selector
        else:
            self.serviceSelector.addItems(selector_services)
        # NOTE: textActivated should signal "when the user chooses an item in the combobox. The item's text is passed"
        #       "If you need to know when the choice actually changes, use signal currentIndexChanged() or currentTextChanged()"
        #       https://doc.qt.io/qtforpython-6.5/PySide6/QtWidgets/QComboBox.html#PySide6.QtWidgets.PySide6.QtWidgets.QComboBox.textActivated
        self.serviceSelector.currentTextChanged.connect(self._serviceSelected)
        return
    
    def _init_service_tree(self):
        self.serviceTree.setColumnCount(3)
        self.serviceTree.setHeaderLabels(["Name", "Type", "Data"])
        # TODO: Get serviceSelector initial selection and populate on start
        # TODO: Separate out serviceTree populator from _serviceSelected slot
        # TODO: Auto expand tree on service selection
        # TODO: Make datafield fillable for lowest level service tree items
        # TODO: Get user input and send service request on correct button press
        # TODO: Clear user input on button press
        # TODO: Add service request to watch table on button press
    
    @Slot(str)
    def _serviceSelected(self, srv_name):
        # get service full name (for free, from srv_name)
        self.be.get_logger().info('\n' + srv_name + '\n') # if we're running from a launch file using simple print won't work here
        # get service type
        srv_type = self.all_services[srv_name]
        self.be.get_logger().info('\n' + f'{srv_type}' + '\n')
        # breakdown service type content into QTreeWidgetItem
        # add QTreeWidgetItem to QTreeWidget called serviceTree
        # TODO: need error catches here
        # TODO: needs a recursive function to handle arbitrary message structure depth
        self.serviceTree.clear()
        fields = srv_type.Request.get_fields_and_field_types()
        tree_item = QTreeWidgetItem([srv_name])
        for field_name, field_type in fields.items():
            tree_item.addChild(QTreeWidgetItem([field_name, field_type]))
        self.serviceTree.insertTopLevelItems(0, [tree_item])
            
        return # TODO: populate serviceTree with fields and description on textActivated from serviceSelector

    def _consume_queue(self):
        try:
            response = self.be.response_queue.get(timeout=0.1) # we can only wait as long as our timer period, right?
            service_name = response['service_name']
            res_content = response['content']
            if service_name == self.be.get_full_service_name('get_robot_mode'):
                self.be.get_logger().info("Robot mode response pulled from queue, updating...")
                robot_mode = ROBOT_MODES[res_content.robot_mode.mode]
                self.show_robot_mode(robot_mode)
            elif service_name == self.be.get_full_service_name('get_safety_mode'):
                self.be.get_logger().info("Safety mode response pulled from queue, updating...")
                safety_mode = SAFETY_MODES[res_content.safety_mode.mode]
                self.show_safety_mode(safety_mode)
            elif service_name == self.be.get_full_service_name('program_state'):
                self.be.get_logger().info("Program state response pulled from queue, updating...")
                program_state = res_content.state.state
                self.show_program_state(program_state)
            else: # if response is not from a status service
                self.be.get_logger().info(f"{service_name} response pulled from queue, processing...")
                display_txt = []
                display_txt.append(response['message']) # TODO: process success as color highlight? Or prefix?
                res_fields = response['service_type'].Response.get_fields_and_field_types()
                for field in res_fields.keys():
                    display_txt.append(f"\n\t\t└── {field}: {getattr(res_content, field)}")
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
        self.watchTable.setItem(row, column, item)
        return
    
    def addText(self, data):
        timestamp = f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}]"
        display_txt = ': '.join([timestamp, str(data)])
        self.serviceMonitor.appendPlainText(display_txt)
        scrollbar = self.serviceMonitor.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        return
    
    @Slot()
    def brake_release_clicked(self):
        self.addText("Brake release requested, calling...")
        self.be.send_service_request(self.be.get_full_service_name('brake_release'))
        return

    @Slot()
    def play_clicked(self):
        self.addText("Program play requested, calling...")
        self.be.send_service_request(self.be.get_full_service_name('play'))
        return
    
    @Slot()
    def connect_clicked(self):
        self.addText("Dashboard connect requested, calling...")
        self.be.send_service_request(self.be.get_full_service_name('connect'))
        return

    @Slot()
    def unlock_pstop_clicked(self):
        self.addText("Unlock protective stop requested, calling...")
        self.be.send_service_request(self.be.get_full_service_name('unlock_protective_stop'))
        return
    
    @Slot()
    def restart_safety_clicked(self):
        self.addText("Restart safety requested, calling...")
        self.be.send_service_request(self.be.get_full_service_name('restart_safety'))
        return

    def status_robot_mode(self):
        self.be.send_service_request(self.be.get_full_service_name('get_robot_mode'))
        return
    
    def status_safety_mode(self):
        self.be.send_service_request(self.be.get_full_service_name('get_safety_mode'))
        return

    def status_program_state(self):
        self.be.send_service_request(self.be.get_full_service_name('program_state'))
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
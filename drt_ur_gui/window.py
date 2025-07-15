
import os, sys, queue
from datetime import datetime
from python_qt_binding.QtWidgets import QMainWindow, QTableWidgetItem, QTreeWidgetItem, QLineEdit
from python_qt_binding.QtCore import QFile, QIODevice, Slot, QTimer, Qt
from python_qt_binding.QtGui import QPixmap, QColor
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
        share_path = get_package_share_directory("drt_ur_gui")
        ui_file_path = os.path.join(share_path, "ui", "drt_ur.ui")
        self.resources_path = os.path.join(share_path, "resources")
        self._load_ui(ui_file_path)
        self._init_window()
        self._init_logo()
        self._init_robot_label()
        self._init_arm_label()
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
    
    def _init_window(self):
        self.setWindowTitle(self.be.get_parameter('window.name').get_parameter_value().string_value)
        window_stylesheet = self.be.get_parameter('window.stylesheet').get_parameter_value().string_value
        if window_stylesheet != '':
            self.setStyleSheet(window_stylesheet)
        return
    def _init_logo(self):
        logo_filename = self.be.get_parameter('logo_file_name').get_parameter_value().string_value
        if logo_filename != '':
            logo = QPixmap(os.path.join(self.resources_path, 'iMetro_full.png'))
            self.label_logo.setPixmap(logo)
        return
    
    def _init_robot_label(self):
        self.label_robot.setText(self.be.get_parameter('robot.name').get_parameter_value().string_value)
        robot_stylesheet = self.be.get_parameter('robot.stylesheet').get_parameter_value().string_value
        if robot_stylesheet != '':
            self.label_robot.setStyleSheet(robot_stylesheet)
        return
    
    def _init_arm_label(self):
        self.label_arm.setText(self.be.get_parameter('arm.name').get_parameter_value().string_value)
        arm_stylesheet = self.be.get_parameter('arm.stylesheet').get_parameter_value().string_value
        if arm_stylesheet != '':
            self.label_arm.setStyleSheet(arm_stylesheet)
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
        self.b_clearService.clicked.connect(self.clear_service_clicked)
        self.b_send.clicked.connect(self.send_service_clicked)
        #TODO: self.b_watch.clicked.connect(
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
        selector_services.sort()
        if len(selector_services) == 0:
            return # no services to add to service selector
        else:
            self.serviceSelector.addItems(selector_services)
        # NOTE: textActivated should signal "when the user chooses an item in the combobox. The item's text is passed"
        #       "If you need to know when the choice actually changes, use signal currentIndexChanged() or currentTextChanged()"
        #       https://doc.qt.io/qtforpython-6.5/PySide6/QtWidgets/QComboBox.html#PySide6.QtWidgets.PySide6.QtWidgets.QComboBox.textActivated
        self.serviceSelector.currentTextChanged.connect(self._serviceSelected)
        self._serviceSelected(self.serviceSelector.currentText())
        return
    
    def _init_service_tree(self):
        self.serviceTree.setColumnCount(3)
        self.serviceTree.setHeaderLabels(["Name", "Type", "Data"])
        # self.serviceTree.itemDoubleClicked.connect(self._service_tree_item_double_clicked)
        # TODO: Get serviceSelector initial selection and populate on start
        # TODO: Separate out serviceTree populator from _serviceSelected slot
        # TODO: Get user input and send service request on correct button press
        # TODO: Clear user input on button press
        # TODO: Add service request to watch table on button press
    
    @Slot(str)
    def _serviceSelected(self, srv_name):
        # get service full name (for free, from srv_name)
        self.be.get_logger().debug('\n' + srv_name + '\n') # if we're running from a launch file using simple print won't work here
        # get service type
        srv_type = self.all_services[srv_name]
        self.be.get_logger().debug('\n' + f'{srv_type}' + '\n')
        # TODO: need error catches here
        # TODO: needs a recursive function to handle arbitrary message structure depth
        self.serviceTree.clear()
        fields = srv_type.Request.get_fields_and_field_types()
        pretty_srv_type = str(srv_type.__module__.split('.')[0]) + '/srv/' + str(srv_type.__name__)
        srv_tree_item = QTreeWidgetItem(self.serviceTree, [srv_name, pretty_srv_type, ''])
        for field_name, field_type in fields.items():
            field_tree_item = QTreeWidgetItem(srv_tree_item, [field_name, field_type])
            field_input_widget = QLineEdit()
            if 'load_program' in srv_name:
                field_input_widget.setText(self.be.get_parameter('program').get_parameter_value().string_value)
            self.serviceTree.setItemWidget(field_tree_item, 2, field_input_widget)
        self.serviceTree.expandAll()
        for col in range(self.serviceTree.columnCount()):
            self.serviceTree.resizeColumnToContents(col)
        return

    def _consume_queue(self):
        try:
            response = self.be.response_queue.get(timeout=0.1) # we can only wait as long as our timer period, right?
            service_name = response['service_name']
            res_content = response['content']
            if service_name == self.be.get_full_service_name('get_robot_mode'):
                self.be.get_logger().debug("Robot mode response pulled from queue, updating...")
                robot_mode = ROBOT_MODES[res_content.robot_mode.mode]
                self.show_robot_mode(robot_mode)
            elif service_name == self.be.get_full_service_name('get_safety_mode'):
                self.be.get_logger().debug("Safety mode response pulled from queue, updating...")
                safety_mode = SAFETY_MODES[res_content.safety_mode.mode]
                self.show_safety_mode(safety_mode)
            elif service_name == self.be.get_full_service_name('program_state'):
                self.be.get_logger().debug("Program state response pulled from queue, updating...")
                program_state = res_content.state.state
                self.show_program_state(program_state)
            else: # if response is not from a status service
                self.be.get_logger().debug(f"{service_name} response pulled from queue, processing...")
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
        

    def setCell(self, row, column, data, color:str = None):
        item = QTableWidgetItem(str(data))
        if color:
            item.setBackground(QColor(color))
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
    def clear_service_clicked(self):
        top_item = self.serviceTree.topLevelItem(0)
        for child_idx in range(top_item.childCount()):
            child = top_item.child(child_idx)
            editor = self.serviceTree.itemWidget(child, 2)
            if isinstance(editor, QLineEdit):
                editor.clear()

    @Slot()
    def send_service_clicked(self):
        srv_item = self.serviceTree.topLevelItem(0)
        srv_name = srv_item.text(0)
        srv_type = srv_item.text(1)
        req_data = {}
        for child_idx in range(srv_item.childCount()):
            field_item = srv_item.child(child_idx)
            field_name = field_item.text(0)
            editor = self.serviceTree.itemWidget(field_item, 2)
            data = editor.text()
            req_data[field_name] = data
        self.be.send_service_request(srv_name, content=req_data)
        
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
        # TODO: Needs a better way to spec color, maybe a dict member?
        red_modes = ['DISCONNECTED', 'CONFIRM_SAFETY', 'BOOTING', 'POWER_OFF']
        yellow_modes = ['POWER_ON', 'IDLE', 'BACKDRIVE']
        green_modes = ['RUNNING']
        blue_modes = ['UPDATING_FIRMWARE', 'FREEDRIVE'] # TODO: Do these ever actually show up, is FREEDRIVE correct?
        if mode in red_modes:
            color = "red"
        elif mode in yellow_modes:
            color = "yellow"
        elif mode in green_modes:
            color = "green"
        elif mode in blue_modes:
            color = "blue"
        else:
            color = None
        self.setCell(0, 1, mode, color)
        return

    def show_safety_mode(self, mode: str):
        green_modes = ['NORMAL']
        if mode not in green_modes:
            color = "red"
        else:
            color = "green"
        self.setCell(1, 1, mode, color)
        return    
    
    def show_program_state(self, state: str):
        ['STOPPED', 'PAUSED', 'PLAYING']
        if state == 'STOPPED':
            color = "red"
        elif state == 'PAUSED':
            color = "yellow"
        elif state == 'PLAYING':
            color = "green"
        else:
            color = None
        self.setCell(2, 1, state, color)
        return
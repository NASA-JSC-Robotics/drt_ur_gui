import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup


from std_srvs.srv import Trigger
from ur_dashboard_msgs.msg import RobotMode, SafetyMode, ProgramState
from ur_dashboard_msgs.srv import (
    AddToLog,
    GetRobotMode,
    Load,
    GetSafetyMode,
    IsProgramRunning,
    GetProgramState,
    Popup,
    RawRequest,
    GetLoadedProgram,
    IsProgramSaved,
    )


class FakeClass():
    def __init__(self):
        self.init_stuff()
    def init_stuff(self):
        print("it works")



class FakeDashboardClient(Node):
    def __init__(self):
        super().__init__('dashboard_client') 
        
        self.r_cbg = ReentrantCallbackGroup()
        self.init_srvs()
        
    def init_srvs(self):
        
        self.s_addtolog = self.create_service(
            AddToLog, 
            'dashboard_client/add_to_log', 
            self.cb_AddToLog, 
            callback_group=self.r_cbg)
        
        self.s_brakerelease = self.create_service(
            Trigger, 
            'dashboard_client/brake_release', 
            self.cb_BrakeRelease, 
            callback_group=self.r_cbg)

        self.s_clearopmode = self.create_service(
            Trigger, 
            'dashboard_client/clear_operational_mode', 
            self.cb_ClearOpMode, 
            callback_group=self.r_cbg)

        self.s_closepopup = self.create_service(
            Trigger, 
            'dashboard_client/close_popup', 
            self.cb_ClosePopup, 
            callback_group=self.r_cbg)

        self.s_closesafetypopup = self.create_service(
            Trigger, 
            'dashboard_client/close_safety_popup', 
            self.cb_CloseSafetyPopup, 
            callback_group=self.r_cbg)

        self.s_connect = self.create_service(
            Trigger, 
            'dashboard_client/connect', 
            self.cb_Connect, 
            callback_group=self.r_cbg)

        self.s_getloadedprogram = self.create_service(
            GetLoadedProgram, 
            'dashboard_client/get_loaded_program', 
            self.cb_GetLoadedProgram, 
            callback_group=self.r_cbg)

        self.s_getrobotmode = self.create_service(
            GetRobotMode, 
            'dashboard_client/get_robot_mode', 
            self.cb_GetRobotMode, 
            callback_group=self.r_cbg)

        self.s_getsafetymode = self.create_service(
            GetSafetyMode, 
            'dashboard_client/get_safety_mode', 
            self.cb_GetSafetyMode, 
            callback_group=self.r_cbg)

        self.s_loadinstallation = self.create_service(
            Load, 
            'dashboard_client/load_installation', 
            self.cb_LoadInstallation, 
            callback_group=self.r_cbg)

        self.s_loadprogram = self.create_service(
            Load, 
            'dashboard_client/load_program', 
            self.cb_LoadProgram, 
            callback_group=self.r_cbg)

        self.s_pause = self.create_service(
            Trigger, 
            'dashboard_client/pause', 
            self.cb_Pause, 
            callback_group=self.r_cbg)

        self.s_play = self.create_service(
            Trigger, 
            'dashboard_client/play', 
            self.cb_Play, 
            callback_group=self.r_cbg)

        self.s_popup = self.create_service(
            Popup, 
            'dashboard_client/popup', 
            self.cb_Popup, 
            callback_group=self.r_cbg)

        self.s_poweroff = self.create_service(
            Trigger, 
            'dashboard_client/power_off', 
            self.cb_PowerOff, 
            callback_group=self.r_cbg)

        self.s_poweron = self.create_service(
            Trigger, 
            'dashboard_client/power_on', 
            self.cb_PowerOn, 
            callback_group=self.r_cbg)

        self.s_programrunning = self.create_service(
            IsProgramRunning, 
            'dashboard_client/program_running', 
            self.cb_ProgramRunning, 
            callback_group=self.r_cbg)

        self.s_programsaved = self.create_service(
            IsProgramSaved, 
            'dashboard_client/program_saved', 
            self.cb_ProgramSaved, 
            callback_group=self.r_cbg)

        self.s_programstate = self.create_service(
            GetProgramState, 
            'dashboard_client/program_state', 
            self.cb_ProgramState, 
            callback_group=self.r_cbg)

        self.s_quit = self.create_service(
            GetLoadedProgram, # seems wrong but this is what the doc says the type is, probably is Trigger ir, callback_group=self.r_cbgl 
            'dashboard_client/quit', 
            self.cb_Quit) 

        self.s_rawrequest = self.create_service(
            RawRequest, 
            'dashboard_client/raw_request', 
            self.cb_RawRequest, 
            callback_group=self.r_cbg)

        self.s_restartsafety = self.create_service(
            Trigger, 
            'dashboard_client/restart_safety', 
            self.cb_RestartSafety, 
            callback_group=self.r_cbg)

        self.s_shutdown = self.create_service(
            Trigger, 
            'dashboard_client/shutdown', 
            self.cb_Shutdown, 
            callback_group=self.r_cbg)

        self.s_stop = self.create_service(
            Trigger, 
            'dashboard_client/stop', 
            self.cb_Stop, 
            callback_group=self.r_cbg)

        self.s_unlockpstop = self.create_service(
            Trigger, 
            'dashboard_client/unlock_protective_stop', 
            self.cb_UnlockPStop, 
            callback_group=self.r_cbg)

    def cb_AddToLog(self, req, res):

        self.get_logger().info(f'Incoming request \n add_to_log: {req.message}')
        res.answer = 'added to log'
        res.success = True
        return res
    
    def cb_BrakeRelease(self, req, res):
        req
        self.get_logger().info('Incoming request \n brake_release')
        res.success = True
        res.message = 'brakes releasing'
        return res
    
    def cb_ClearOpMode(self, req, res):
        req
        self.get_logger().info('Incoming request \n clear_operational_mode')
        res.success = True
        res.message = 'operational mode cleared'
        return res
    
    def cb_ClosePopup(self, req, res):
        req
        self.get_logger().info('Incoming request \n close_popup')
        res.success = True
        res.message = 'popup closed'
        return res
    
    def cb_CloseSafetyPopup(self, req, res):
        req
        self.get_logger().info('Incoming request \n close_safety_popup')
        res.success = True
        res.message = 'safety popup closed'
        return res
    
    def cb_Connect(self, req, res):
        req
        self.get_logger().info('Incoming request \n connect')
        res.success = True
        res.message = 'connected'
        return res
    
    def cb_GetLoadedProgram(self, req, res):
        req
        self.get_logger().info('Incoming request \n get_loaded_program')
        res.answer = 'program loaded'
        res.program_name = 'program.urp'
        res.success = True
        return res
    
    '''
    quick blurb on digesting RobotMode for back lookup
    
    for name, value in RobotMode.__dict__.items():
        print(f"name: {name} \n value: {value}")
        if isinstance(value, int) and name.isupper():
            test[value] = name
    __dict__: meta attribute that contains all of the attribute of the object to which the __dict__ attribute belongs
    In python, everything is an object
    '''
    
    def cb_GetRobotMode(self, req, res):
        req
        self.get_logger().info('Incoming request \n get_robot_mode')
        res.robot_mode = RobotMode()
        res.robot_mode.mode = 7
        res.answer = "answer"
        res.success = True
        return res
    
    def cb_GetSafetyMode(self, req, res):
        req
        self.get_logger().info('Incoming request \n get_safety_mode')
        res.safety_mode = SafetyMode()
        res.safety_mode.mode = 1
        res.answer = "answer"
        res.success = True
        return res
    
    def cb_LoadInstallation(self, req, res):
        self.get_logger().info(f'Incoming request \n load_installation:{req.filename}')
        res.answer("installation loaded")
        res.success = True
        return res
    
    def cb_LoadProgram(self, req, res):
        self.get_logger().info(f'Incoming request \n load_program:{req.filename}')
        res.answer("program loaded")
        res.success = True
        return res
    
    def cb_Pause(self, req ,res):
        req
        self.get_logger().info('Incoming request \n pause')
        res.success = True
        res.message = "program paused"
        return res
    
    def cb_Play(self, req, res):
        self.get_logger().info('Incoming request \n play')
        res.success = True
        res.message = "program playing"
        while True: # blocking statement to test threading
            continue
        return res
    
    def cb_Popup(self, req, res):
        self.get_logger().info(f'Incoming request \n popup:{req.message}')
        res.answer = "pop up opened"
        res.success = True
        return res
    
    def cb_PowerOff(self, req, res):
        req
        self.get_logger().info('Incoming request \n power_off')
        res.success = True
        res.message = "robot powered off"
        return res
    
    def cb_PowerOn(self, req, res):
        req
        self.get_logger().info('Incoming request \n power_on')
        res.success = True
        res.message = "robot powered on"
        return res
    
    def cb_ProgramRunning(self, req, res):
        req
        self.get_logger().info('Incoming request \n program_running')
        res.program_running = True
        res.success = True
        return res
    
    def cb_ProgramSaved(self, req, res):
        req
        self.get_logger().info('Incoming request \n program_saved')
        res.program_name = 'program.urp'
        res.program_saved = True
        res.success = True
        return res
    
    def cb_ProgramState(self, req, res):
        req
        self.get_logger().info('Incoming request \n program_state')
        res.state = ProgramState()
        res.state.state = 'PLAYING' # So stupid that I can't just directly set the state as a string, hopefully I'm just not smart enough to understand the reasoning here, I guess to restrict responses?
        res.program_name = 'program.urp'
        res.answer = 'answer'
        res.success = True
        return res
    
    def cb_Quit(self, req, res):
        req
        self.get_logger().info('Incoming request \n quit')
        res.answer = "quitting program"
        res.program_name = "program.urp"
        res.success = True
        return res
    
    def cb_RawRequest(self, req, res):
        self.get_logger().info(f'Incoming request \n raw_request:{req.query}')
        res.answer = "raw request response"
        return res
    
    def cb_RestartSafety(self, req, res):
        req
        self.get_logger().info('Incoming request \n restart_safety')
        res.success = True
        res.message = 'restarting safety'
        return res
    
    def cb_Shutdown(self, req, res):
        req
        self.get_logger().info('Incoming request \n shutdown')
        res.success = True
        res.message = "shutting down"
        return res
    
    def cb_Stop(self, req, res):
        req
        self.get_logger().info('Incoming request \n stop')
        res.success = True
        res.message = "stopping program"
        return res
    
    def cb_UnlockPStop(self, req, res):
        self.get_logger().info('Incoming request \n unlock_protective_stop')
        res.success = True
        res.message = "unlocking protective stop"
        return res
    
        
        
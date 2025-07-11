import itertools, threading
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

from drt_ur_gui.window import ROBOT_MODES, SAFETY_MODES

class FakeDashboardClient(Node):
    def __init__(self):
        super().__init__('dashboard_client')
        self.r_cbg = ReentrantCallbackGroup()
        self._initStates()
        self._initSrvs()
        
    def _initStates(self):
        self.robot_mode = RobotMode()
        self.robot_mode.mode = RobotMode.POWER_OFF # = 3
        self.program_state = ProgramState()
        self.program_state.state = 'STOPPED'
        self.safety_mode = SafetyMode()
        self.safety_mode.mode = SafetyMode.NORMAL # = 1
        self.program_name = "<unnamed>.urp"
        return
        
    def _changeRobotMode(self, target_mode: int):
        mode_rate = self.create_rate(0.25)
        init_mode = self.robot_mode.mode
        if target_mode == init_mode: # if robot is already in target mode
            self.get_logger().warning(f"Mode change to {ROBOT_MODES[target_mode]} was requested, but robot is already in that mode, skipping...")
            return
        elif target_mode > init_mode: # Target mode is elevated wrt current mode
            iter_modes = itertools.filterfalse(
                            lambda x: x[0] < init_mode or
                                        x[0] == RobotMode.BACKDRIVE or
                                        x[0] > target_mode,
                                        sorted(ROBOT_MODES.items())
            )
        else: # Target mode is degraded wrt current mode
            iter_modes = itertools.filterfalse(
                            lambda x: x[0] > init_mode or
                                        x[0] == RobotMode.BACKDRIVE or
                                        x[0] < target_mode,
                                        sorted(ROBOT_MODES.items(), reverse=True)
            )
        for num, mode in iter_modes:
            self.get_logger().debug(f'num = {num}')
            self.get_logger().debug(f'mode = {mode}')
            mode_rate.sleep()
            self.robot_mode.mode = num
            self.get_logger().debug(f'Robot mode changed to {ROBOT_MODES[num]}')
        mode_rate.destroy()
        return
    
    def _changeProgramState(self, target_state: str):
        allowed_states = ['STOPPED', 'PAUSED', 'PLAYING']
        if target_state not in allowed_states:
            self.get_logger().warning(f"Requested target program state {target_state} is not allowed, skipping...")
            return
        else:
            self.program_state.state = target_state
        return
        
    def _initSrvs(self):
        
        self.s_addtolog = self.create_service(
            AddToLog, 
            '~/add_to_log', 
            self.cb_AddToLog, 
            callback_group=self.r_cbg)
        
        self.s_brakerelease = self.create_service(
            Trigger, 
            '~/brake_release', 
            self.cb_BrakeRelease, 
            callback_group=self.r_cbg)

        self.s_clearopmode = self.create_service(
            Trigger, 
            '~/clear_operational_mode', 
            self.cb_ClearOpMode, 
            callback_group=self.r_cbg)

        self.s_closepopup = self.create_service(
            Trigger, 
            '~/close_popup', 
            self.cb_ClosePopup, 
            callback_group=self.r_cbg)

        self.s_closesafetypopup = self.create_service(
            Trigger, 
            '~/close_safety_popup', 
            self.cb_CloseSafetyPopup, 
            callback_group=self.r_cbg)

        self.s_connect = self.create_service(
            Trigger, 
            '~/connect', 
            self.cb_Connect, 
            callback_group=self.r_cbg)

        self.s_getloadedprogram = self.create_service(
            GetLoadedProgram, 
            '~/get_loaded_program', 
            self.cb_GetLoadedProgram, 
            callback_group=self.r_cbg)

        self.s_getrobotmode = self.create_service(
            GetRobotMode, 
            '~/get_robot_mode', 
            self.cb_GetRobotMode, 
            callback_group=self.r_cbg)

        self.s_getsafetymode = self.create_service(
            GetSafetyMode, 
            '~/get_safety_mode', 
            self.cb_GetSafetyMode, 
            callback_group=self.r_cbg)

        self.s_loadinstallation = self.create_service(
            Load, 
            '~/load_installation', 
            self.cb_LoadInstallation, 
            callback_group=self.r_cbg)

        self.s_loadprogram = self.create_service(
            Load, 
            '~/load_program', 
            self.cb_LoadProgram, 
            callback_group=self.r_cbg)

        self.s_pause = self.create_service(
            Trigger, 
            '~/pause', 
            self.cb_Pause, 
            callback_group=self.r_cbg)

        self.s_play = self.create_service(
            Trigger, 
            '~/play', 
            self.cb_Play, 
            callback_group=self.r_cbg)

        self.s_popup = self.create_service(
            Popup, 
            '~/popup', 
            self.cb_Popup, 
            callback_group=self.r_cbg)

        self.s_poweroff = self.create_service(
            Trigger, 
            '~/power_off', 
            self.cb_PowerOff, 
            callback_group=self.r_cbg)

        self.s_poweron = self.create_service(
            Trigger, 
            '~/power_on', 
            self.cb_PowerOn, 
            callback_group=self.r_cbg)

        self.s_programrunning = self.create_service(
            IsProgramRunning, 
            '~/program_running', 
            self.cb_ProgramRunning, 
            callback_group=self.r_cbg)

        self.s_programsaved = self.create_service(
            IsProgramSaved, 
            '~/program_saved', 
            self.cb_ProgramSaved, 
            callback_group=self.r_cbg)

        self.s_programstate = self.create_service(
            GetProgramState, 
            '~/program_state', 
            self.cb_ProgramState, 
            callback_group=self.r_cbg)

        self.s_quit = self.create_service(
            GetLoadedProgram, # seems wrong but this is what the doc says the type is, probably is Trigger ir, callback_group=self.r_cbgl 
            '~/quit', 
            self.cb_Quit) 

        self.s_rawrequest = self.create_service(
            RawRequest, 
            '~/raw_request', 
            self.cb_RawRequest, 
            callback_group=self.r_cbg)

        self.s_restartsafety = self.create_service(
            Trigger, 
            '~/restart_safety', 
            self.cb_RestartSafety, 
            callback_group=self.r_cbg)

        self.s_shutdown = self.create_service(
            Trigger, 
            '~/shutdown', 
            self.cb_Shutdown, 
            callback_group=self.r_cbg)

        self.s_stop = self.create_service(
            Trigger, 
            '~/stop', 
            self.cb_Stop, 
            callback_group=self.r_cbg)

        self.s_unlockpstop = self.create_service(
            Trigger, 
            '~/unlock_protective_stop', 
            self.cb_UnlockPStop, 
            callback_group=self.r_cbg)

    def cb_AddToLog(self, req, res):

        self.get_logger().debug(f'Incoming request: add_to_log: {req.message}')
        res.answer = 'added to log'
        res.success = True
        return res
    
    def cb_BrakeRelease(self, req, res):
        req
        self.get_logger().debug('Incoming request: brake_release')
        br_T = threading.Thread(target = self._changeRobotMode, args=(7,), daemon = True)
        br_T.start()
        res.success = True
        res.message = 'brakes releasing'
        return res
    
    def cb_ClearOpMode(self, req, res):
        req
        self.get_logger().debug('Incoming request: clear_operational_mode')
        res.success = True
        res.message = 'operational mode cleared'
        return res
    
    def cb_ClosePopup(self, req, res):
        req
        self.get_logger().debug('Incoming request: close_popup')
        res.success = True
        res.message = 'popup closed'
        return res
    
    def cb_CloseSafetyPopup(self, req, res):
        req
        self.get_logger().debug('Incoming request: close_safety_popup')
        res.success = True
        res.message = 'safety popup closed'
        return res
    
    def cb_Connect(self, req, res):
        req
        self.get_logger().debug('Incoming request: connect')
        res.success = True
        res.message = 'connected'
        return res
    
    def cb_GetLoadedProgram(self, req, res):
        req
        self.get_logger().debug('Incoming request: get_loaded_program')
        res.answer = 'program loaded'
        res.program_name = 'program.urp'
        res.success = True
        return res
    
    def cb_GetRobotMode(self, req, res):
        req
        self.get_logger().debug('Incoming request: get_robot_mode')
        res.robot_mode = self.robot_mode
        res.answer = "answer"
        res.success = True
        return res
    
    def cb_GetSafetyMode(self, req, res):
        req
        self.get_logger().debug('Incoming request: get_safety_mode')
        res.safety_mode = self.safety_mode
        res.answer = "answer"
        res.success = True
        return res
    
    def cb_LoadInstallation(self, req, res):
        self.get_logger().debug(f'Incoming request: load_installation:{req.filename}')
        res.answer("installation loaded")
        res.success = True
        return res
    
    def cb_LoadProgram(self, req, res):
        self.get_logger().debug(f'Incoming request: load_program:{req.filename}')
        res.answer("program loaded")
        res.success = True
        return res
    
    def cb_Pause(self, req ,res):
        self.get_logger().debug('Incoming request: pause')
        self._changeProgramState('PAUSED')
        res.success = True
        res.message = "program paused"
        return res
    
    def cb_Play(self, req, res):
        self.get_logger().debug('Incoming request: play')
        self._changeProgramState('PLAYING')
        res.success = True
        res.message = "program playing"
        return res
    
    def cb_Popup(self, req, res):
        self.get_logger().debug(f'Incoming request: popup:{req.message}')
        res.answer = "pop up opened"
        res.success = True
        return res
    
    def cb_PowerOff(self, req, res):
        req
        self.get_logger().debug('Incoming request: power_off')
        res.success = True
        res.message = "robot powered off"
        return res
    
    def cb_PowerOn(self, req, res):
        req
        self.get_logger().debug('Incoming request: power_on')
        res.success = True
        res.message = "robot powered on"
        return res
    
    def cb_ProgramRunning(self, req, res):
        req
        self.get_logger().debug('Incoming request: program_running')
        res.program_running = True
        res.success = True
        return res
    
    def cb_ProgramSaved(self, req, res):
        req
        self.get_logger().debug('Incoming request: program_saved')
        res.program_name = 'program.urp'
        res.program_saved = True
        res.success = True
        return res
    
    def cb_ProgramState(self, req, res):
        req
        self.get_logger().debug('Incoming request: program_state')
        res.state = self.program_state
        res.program_name = self.program_name
        res.answer = 'answer'
        res.success = True
        return res
    
    def cb_Quit(self, req, res):
        req
        self.get_logger().debug('Incoming request: quit')
        res.answer = "quitting program"
        res.program_name = "program.urp"
        res.success = True
        return res
    
    def cb_RawRequest(self, req, res):
        self.get_logger().debug(f'Incoming request: raw_request:{req.query}')
        res.answer = "raw request response"
        return res
    
    def cb_RestartSafety(self, req, res):
        req
        self.get_logger().debug('Incoming request: restart_safety')
        res.success = True
        res.message = 'restarting safety'
        return res
    
    def cb_Shutdown(self, req, res):
        req
        self.get_logger().debug('Incoming request: shutdown')
        res.success = True
        res.message = "shutting down"
        return res
    
    def cb_Stop(self, req, res):
        self.get_logger().debug('Incoming request: stop')
        self._changeProgramState('STOPPED')
        res.success = True
        res.message = "stopping program"
        return res
    
    def cb_UnlockPStop(self, req, res):
        self.get_logger().debug('Incoming request: unlock_protective_stop')
        res.success = True
        res.message = "unlocking protective stop"
        return res
    
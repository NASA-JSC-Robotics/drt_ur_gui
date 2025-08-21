from ur_dashboard_msgs.msg import ProgramState, RobotMode, SafetyMode
from ur_dashboard_msgs.srv import AddToLog, GetLoadedProgram, GetRobotMode, GetSafetyMode, Load, Popup, IsProgramRunning, IsProgramRunning, IsProgramSaved, GetProgramState, RawRequest
from std_srvs.srv import Trigger


# class ServiceWrapper:


def denumerate_ros_msg_type(msg_type):
    """Converts enumerated ROS 2 message types to {integer_value:name} dictonaries

    Arguments:
        msg_type (ROS 2 Message Class): The enumerated message type to denumerate
    
    Returns:
        dict: {integer_value:name} reverse-enumerated (numbered) dictonary of named interger constants defined in the ROS 2 message type
    
    RobotMode, SafetyMode, and other ROS 2 messages contain named integer constants. Unfortunately these constants are stored as object attributes and
    aren't actually associated with the message field. There's no easy way to look up a constant's name by that constant's integer value, despite the field
    only storing the integer value. This function attempts to solve that issue by returning a dict that's keyed by the integer values.

    Works by filtering the message type's attribute list to attributes that return integers.
    """
    return {getattr(msg_type, name): name for name in dir(msg_type) if not name.startswith('_') and isinstance(getattr(msg_type, name), int)}

# ROBOT_MODES
# 0: 'DISCONNECTED'
# 1: 'CONFIRM_SAFETY'
# 2: 'BOOTING'
# 3: 'POWER_OFF'
# 4: 'POWER_ON'
# 5: 'IDLE'
# 6: 'BACKDRIVE'
# 7: 'RUNNING'
# 8: UPDATING_FIRMWARE
ROBOT_MODES = denumerate_ros_msg_type(RobotMode)

# SAFETY_MODES
# 1: 'NORMAL'
# 2: 'REDUCED'
# 3: 'PROTECTIVE_STOP'
# 4: 'RECOVERY'
# 5: 'SAFEGUARD_STOP'
# 6: 'SYSTEM_EMERGENCY_STOP'
# 7: 'ROBOT_EMERGENCY_STOP'
# 8: 'VIOLATION'
# 9: 'FAULT'
# 10: 'VALIDATE_JOINT_ID'
# 11: 'UNDEFINED_SAFETY_MODE'
# 12: 'AUTOMATIC_MODE_SAFEGUARD_STOP'
# 13: 'SYSTEM_THREE_POSITION_ENABLING_STOP'
SAFETY_MODES = denumerate_ros_msg_type(SafetyMode)

# TODO: Convert SERVICES list to config/services.yaml
SERVICES= [
            {
                'name':'add_to_log',
                'type':AddToLog
            },
            {
                'name':'brake_release',
                'type':Trigger
            },
            {
                'name':'clear_operational_mode',
                'type':Trigger
            },
            {
                'name':'close_popup',
                'type':Trigger
            },
            {
                'name':'close_safety_popup',
                'type':Trigger
            },
            {
                'name':'connect',
                'type':Trigger
            },
            {
                'name':'get_loaded_program',
                'type':GetLoadedProgram
            },
            {
                'name':'get_robot_mode',
                'type':GetRobotMode
            },
            {
                'name':'get_safety_mode',
                'type':GetSafetyMode
            },
            {
                'name':'load_installation',
                'type':Load
            },
            {
                'name':'load_program',
                'type':Load
            },
            {
                'name':'pause',
                'type':Trigger
            },
            {
                'name':'play',
                'type':Trigger
            },
            {
                'name':'popup',
                'type':Popup
            },
            {
                'name':'power_off',
                'type':Trigger
            },
            {
                'name':'power_on',
                'type':Trigger
            },
            {
                'name':'program_running',
                'type':IsProgramRunning
            },
            {
                'name':'program_saved',
                'type':IsProgramSaved
            },
            {
                'name':'program_state',
                'type':GetProgramState
            },
            {
                'name':'quit',
                'type':GetLoadedProgram
            },
            {
                'name':'raw_request',
                'type':RawRequest
            },
            {
                'name':'restart_safety',
                'type':Trigger
            },
            {
                'name':'shutdown',
                'type':Trigger
            },
            {
                'name':'stop',
                'type':Trigger
            },
            {
                'name':'unlock_protective_stop',
                'type':Trigger
            }
        ]
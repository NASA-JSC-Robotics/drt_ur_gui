
import sys

# from example_interfaces.srv import AddTwoInts
from ur_dashboard_msgs.srv import GetRobotMode, GetSafetyMode, GetProgramState
from std_srvs.srv import Trigger
import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup

class RemoteURCmdr(Node):
    def __init__(self):
        super().__init__('remote_ur_commander')
        
        self.r_cbg = ReentrantCallbackGroup()
        
        self.client_brake_release = self.create_client(Trigger, 'dashboard_client/brake_release', callback_group=self.r_cbg)
        self.client_play = self.create_client(Trigger, 'dashboard_client/play', callback_group=self.r_cbg)
        self.client_connect = self.create_client(Trigger, 'dashboard_client/connect', callback_group=self.r_cbg)
        self.client_unlock_pstop = self.create_client(Trigger, 'dashboard_client/unlock_protective_stop', callback_group=self.r_cbg)
        self.client_restart_safety = self.create_client(Trigger, 'dashboard_client/restart_safety', callback_group=self.r_cbg)

        self.client_robot_mode = self.create_client(GetRobotMode, 'dashboard_client/get_robot_mode', callback_group=self.r_cbg)
        self.client_safety_mode = self.create_client(GetSafetyMode, 'dashboard_client/get_safety_mode', callback_group=self.r_cbg)
        self.client_program_state = self.create_client(GetProgramState, 'dashboard_client/program_state', callback_group=self.r_cbg)
        

        while not (
                    self.client_brake_release.wait_for_service(timeout_sec=1.0)
                and self.client_play.wait_for_service(timeout_sec=1.0)
                and self.client_connect.wait_for_service(timeout_sec=1.0)
                and self.client_unlock_pstop.wait_for_service(timeout_sec=1.0)
                and self.client_robot_mode.wait_for_service(timeout_sec=1.0)
                and self.client_safety_mode.wait_for_service(timeout_sec=1.0)
                and self.client_program_state.wait_for_service(timeout_sec=1.0)
                and self.client_restart_safety.wait_for_service(timeout_sec=1.0)):
            self.get_logger().info('service not available, waiting again...')
    
    def send_brake_release(self):
        req = Trigger.Request()
        future = self.client_brake_release.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return [
            response.success,
            response.message,
        ]

    def send_play(self):
        req = Trigger.Request()
        future = self.client_play.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return [
            response.success,
            response.message,
        ]

    def send_connect(self):
        req = Trigger.Request()
        future = self.client_connect.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return [
            response.success,
            response.message,
        ]
    
    def send_unlock_pstop(self):
        req = Trigger.Request()
        future = self.client_unlock_pstop.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return [
            response.success,
            response.message,
        ]
    
    def send_restart_safety(self):
        req = Trigger.Request()
        future = self.client_restart_safety.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return [
            response.success,
            response.message,
        ]
    
    def send_robot_mode_req(self):
        req = GetRobotMode.Request()
        future = self.client_robot_mode.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return [
            response.robot_mode, # TODO: RobotMode is an enum, we should be able to process it here
            response.answer,
            response.success,
        ]
    
    def send_safety_mode_req(self):
        req = GetSafetyMode.Request()
        future = self.client_safety_mode.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return [
            response.safety_mode, # TODO: SafetyMode is an enum, we should be able to process it here
            response.answer,
            response.success,
        ]
    
    def send_program_state_req(self):
        req = GetProgramState.Request()
        future = self.client_program_state.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return [
            response.state, # TODO: ProgramState is some string enum thing, but we can still process it here
            response.program_name,
            response.answer,
            response.success,
        ]
    
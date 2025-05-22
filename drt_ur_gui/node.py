
import functools
import queue

# from example_interfaces.srv import AddTwoInts
from ur_dashboard_msgs.srv import (
    Popup, AddToLog, GetRobotMode,
    Load, IsProgramSaved, RawRequest,
    GetLoadedProgram, IsProgramRunning,
    GetProgramState, GetSafetyMode
)    
from std_srvs.srv import Trigger
import rclpy
from rclpy.node import Node

class RemoteURCmdr(Node):
    def __init__(self):
        super().__init__('remote_ur_commander')
        self.get_logger().info("Starting remote_ur_commander node...")
        self.service_list = [
            { # brake release
                'name': 'dashboard_client/brake_release',
                'type': Trigger,
            },
            { # play
                'name': 'dashboard_client/play',
                'type': Trigger,
            },
            { # connect
                'name': 'dashboard_client/connect',
                'type': Trigger,
            },
            { # unlock protective stop
                'name': 'dashboard_client/unlock_protective_stop',
                'type': Trigger,
            },
            { # restart safety
                'name': 'dashboard_client/restart_safety',
                'type': Trigger,
            },
            { # get robot mode
                'name': 'dashboard_client/get_robot_mode',
                'type': GetRobotMode,
            },
            { # get safety mode
                'name': 'dashboard_client/get_safety_mode',
                'type': GetSafetyMode,
            },
            { # program state
                'name': 'dashboard_client/program_state',
                'type': GetProgramState,
            }
        ]
        self.service_clients = {}
        self.callbacks = {}
        self.response_queue = queue.Queue()
        
        # self.generate_services_statically()
        self.generate_services_dynamically()
                
            

    def generate_services_dynamically(self):
        self.get_logger().info("Generating services clients...")
        for service in self.service_list:
            service_name = service['name']
            service_type = service['type']
            client = self.create_client(service_type, service_name)
            self.service_clients[service_name] = client
            self.callbacks[service_name] = functools.partial(self._process_response,
                                                             service_name=service_name,
                                                             service_type=service_type)
            self.get_logger().info(f"Service client {service_name} created.")

    def send_service_request(self, name: str, content: dict = None):
        # Place holder bad response for queue
        bad_response = {
            'service_name': name,
            'success': False,
            'message': '',
            'response_content': None
            
        }
        # is the service known?
        if name not in self.service_clients.keys():
            self.get_logger().error(f'service {name} requested is unavailable!')
            bad_response['message'] = f"Service client for '{name}' not found."
            self.response_queue.put(bad_response)
            return
        client = self.service_clients[name]
        # is the service ready?
        if not client.service_is_ready():
            self.get_logger().warn(f"Service '{name}' is not ready, skipping request.")
            bad_response['message'] = f"Service '{name}' is not ready."
            self.response_queue.put(bad_response)
            return
        req_type = client.srv_type.Request
        req = req_type()
        # populate service request from content dictionary
        if content:
            for field, value in content.items():
                if hasattr(req, field): # check to verify that content is valid
                    try:
                        setattr(req, field, value) # populates request field-by-field, setattr for dynamic field naming
                    except TypeError as e:
                        self.get_logger().error(
                            f"Type error setting '{field}' for service request to '{name}': {e}. "
                            f"Expected type: {type(getattr(req, field))}, Got: {type(value)}"
                        )
                        bad_response['message'] = f"Type mismatch for '{field}' in service '{name}' request: {e}"
                        self.response_queue.put(bad_response)
                        return
                else: # req does not have 'field' attribute
                    self.get_logger().warn(
                        f"Request field '{field}' not found in service '{name}' request message. "
                         "Skipping this argument."
                    )
                    continue
        self.get_logger().info(f"Sending service request to '{name}")
        if content: self.get_logger().info(f"with content: {content}")
        future = client.call_async(req)
        future.add_done_callback(self.callbacks[name])
        return


    def _process_response(self, future, service_name: str, service_type):
        output = {
            'service_name': service_name,
            'service_type': service_type,
            'success': False,
            'message': 'Service call failed',
            'content': None
        }
        
        try:
            res = future.result()
            output['content'] = res
            output['success'] = True
            output['message'] = f"Received response from {service_name}"
        except Exception as e:
            output['message'] = f"Exception during service call {service_name}: {e}"
            self.get_logger().info(f'Exception {e} while processing response for {service_name}')
        
        self.response_queue.put(output)
        return

    ''' single service request senders
    def generate_services_statically(self):
        # TODO: set function for callback instead of just waiting there
        self.client_brake_release = self.create_client(Trigger, 'dashboard_client/brake_release')
        self.client_play = self.create_client(Trigger, 'dashboard_client/play')
        self.client_connect = self.create_client(Trigger, 'dashboard_client/connect')
        self.client_unlock_pstop = self.create_client(Trigger, 'dashboard_client/unlock_protective_stop')
        self.client_restart_safety = self.create_client(Trigger, 'dashboard_client/restart_safety')

        self.client_robot_mode = self.create_client(GetRobotMode, 'dashboard_client/get_robot_mode')
        self.client_safety_mode = self.create_client(GetSafetyMode, 'dashboard_client/get_safety_mode')
        self.client_program_state = self.create_client(GetProgramState, 'dashboard_client/program_state')
        

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
        future.add_done_callback(functools.partial(
                                        self._process_response,
                                        service_name='dashboard_client/brake_release',
                                        service_type=Trigger))

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
    
    '''
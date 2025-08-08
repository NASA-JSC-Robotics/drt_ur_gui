
# TODO: change filename to something more descriptive

import functools
import queue

# from example_interfaces.srv import AddTwoInts
from ur_dashboard_msgs.srv import  (AddToLog,
                                    GetLoadedProgram,
                                    GetProgramState,
                                    GetRobotMode,
                                    GetSafetyMode,
                                    IsProgramRunning,
                                    IsProgramSaved,
                                    Load,
                                    Popup,
                                    RawRequest,
)    
from std_srvs.srv import Trigger
import rclpy
from rclpy.node import Node

from drt_ur_gui import SERVICES

class RemoteURCmdr(Node):
    # TODO: Docstring
    # TODO: shutdown or __del__ cleanup function
    def __init__(self):
        super().__init__('drt_ur_gui')
        self.get_logger().info("Starting drt_ur_gui node...")
        self._init_params()
        self.service_list = SERVICES
        self.service_clients = {}
        self.callbacks = {}
        self.response_queue = queue.Queue()
        self.generate_services_dynamically()

    def _init_params(self):
        self.declare_parameters(
            namespace = '',
            parameters = [
                ('dashboard_client_name', 'dashboard_client'),
                ('window.name', 'DRT Remote Commander'),
                ('window.stylesheet', ''),
                ('robot.name', 'UR Arm'),
                ('robot.stylesheet', ''),
                ('arm.name', 'Arm 0'),
                ('arm.stylesheet', ''),
                ('program', 'default.urp'),
                ('logo_file_name', '')
            ]
        )
        self.dashboard_client_name = self.get_parameter('dashboard_client_name').get_parameter_value().string_value
    
    def get_full_service_name(self, srv):
        # TODO: pathlib or os.path.join here
        return '/'.join([self.dashboard_client_name, srv])

    def generate_services_dynamically(self):
        self.get_logger().info("Generating services clients...")
        for service in self.service_list:
            service_name = self.get_full_service_name(service['name'])
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
        # TODO: req = client.srv_type.Request()
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
                    # TODO: warn -> ERROR
                    self.get_logger().warn(
                        f"Request field '{field}' not found in service '{name}' request message. "
                         "Skipping this argument."
                    )
                    continue
        self.get_logger().debug(f"Sending service request to '{name}")
        if content: self.get_logger().debug(f"with content: {content}")
        # TODO: Set async call timeout
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
        self.get_logger().debug(f"Received response from {service_name}")
        try:
            res = future.result()
            output['content'] = res
            output['success'] = True
            output['message'] = f"Received response from {service_name}"
        except Exception as e:
            output['message'] = f"Exception during service call {service_name}: {e}"
            self.get_logger().debug(f'Exception {e} while processing response for {service_name}')
        
        self.get_logger().debug(f"Response from {service_name} added to queue")
        self.response_queue.put(output)
        return

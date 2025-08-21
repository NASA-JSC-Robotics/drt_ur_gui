
# TODO: change filename to something more descriptive

import functools
import queue
import os
import sys
import yaml


from ur_dashboard_msgs.srv import  (
    AddToLog, GetLoadedProgram, GetProgramState,
    GetRobotMode, GetSafetyMode, IsProgramRunning,
    IsProgramSaved, Load, Popup, RawRequest,
)

from std_srvs.srv import ( 
    Trigger
)

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

class Service(object):


class RemoteURCmdr(Node):
    """Backend node for Dexterous Robotics Remote UR Arm Commander GUI
    
    Provides service clients and handles responses for service requests
    Service clients are generated from services provided in this package's services list (config/services.yaml)
    Services are called from the send_service_request method. 
    Service request responses get processed and placed on a queue object shared with the Qt GUI thread as they are received.

    Parameters:
    -----------
    dashboard_client_name: The name of the UR Dashboard Client node, used to resolve service names
    service_list_path: The path to the yaml list of services
            File format must follow:
                    -name: <service_name>
                    type: <service_type>
    window.name: Window name to be displayed in the title bar of the GUI window
    window.stylesheet: CSS stylesheet for GUI window
    robot.name: Robot name to be displayed in main GUI window area
    arm.name: Arm name to be displayed next to robot.name, used as a label when running multiple arms at once
    program: Name of URScript program to be filled out when load_program is selected in the GUI, typically ext_ctrl.urp or external_control.urp
    logo_file_name: The path to the logo that will be displayed in the GUI window

    Attributes:
    -----------
    service_list: YAML safe_load list of file at service_list_path
                        list item format: ['name': '<service_name>', 'type':<service_type>]
    service_clients: Dict used to store service clients, keyed by service name
    callbacks: Dist used to store service callbacks, keyed by service name
    response_queue: Queue object used to pass service responses from ROS 2 thread to the GUI's Qt thread
    dashboard_client_name: Stores the parameter of the same name
    service_list_path: Stores the parameter of the same name
    
    Methods:
    --------
    _init_params: Initializes (declares) parameters and defaults
    load_service_list: Loads the service list from the provided service_list_path
    get_full_service_name: Appends the dashboard_client_name to a dashboard_client service name to correctly target the client node
    generate_services_dynamically: Generates service clients and callbacks from the service list yaml at service_list_path
    send_service_request: Sends services requests
        Arguments:
            name (str): the name of the service that is being requested
            content (dict): the content of the service request, provided as a {field: value} dict
    _process_response: Queues incoming service request responses for GUI thread
    
    """
    # TODO: shutdown or __del__ cleanup function
    def __init__(self):
        super().__init__('drt_ur_gui')
        self.get_logger().info("Starting drt_ur_gui node...")
        self._init_params()
        self.dashboard_client_name = self.get_parameter('dashboard_client_name').get_parameter_value().string_value
        self.service_list_path = self.get_parameter('service_list_path').get_parameter_value().string_value
        self.service_list = self.load_service_list(self.service_list_path) # [{'name':'{self.dashboard_client_name}/service_name', 'type': service_type_class}]
        self.services = self.generate_services()
        self.callbacks = {}
        self.response_queue = queue.Queue()
        self.generate_services_dynamically()

    def _init_params(self):
        self.declare_parameters(
            namespace = '',
            parameters = [
                ('dashboard_client_name', 'dashboard_client'),
                ('service_list_path', os.path.join(get_package_share_directory('drt_ur_gui'), 'config', 'services.yaml')),
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
    
    def load_service_list(self, list_path):
        self.get_logger().info("Loading service list...")
        services = []
        with open(list_path, 'r') as service_list_contents:
            str_service_list = yaml.safe_load(service_list_contents)
        for service in str_service_list:
            try: # Attempt to match service type to imported modules
                service_type = getattr(sys.modules[__name__], service["type"])
            except AttributeError: # If we can't find the service type, inform and skip
                self.get_logger().error(
                    f"Error while loading services from {self.service_list_path}: "
                    f"Service '{service_name}' type {service['type']} not recognized, skipping..."
                )
                continue
            service_name = self.get_full_service_name(service['name'])
            services.append({'name': service_name, 'type': service_type})
        return services
            
        
    def get_full_service_name(self, srv):
        # TODO: pathlib or os.path.join here
        return '/'.join([self.dashboard_client_name, srv])

    # TODO: convert layered dict 'services' to class
    def generate_services(self):
        self.get_logger().info("Generating service clients...")
        services = {}
        for service in self.service_list:
            client = self.create_client(service_type, service_name)
            callback = functools.partial(self._process_response,
                                            service_name=service_name,
                                            service_type=service_type)
            services[service_name]['client'] = client
            services[service_name]['callback'] = callback
            self.get_logger().info(f"Service client {service_name} created.")
        return services

    # NEXT: adapt send_service_request to 
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

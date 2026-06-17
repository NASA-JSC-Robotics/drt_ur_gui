#!/usr/bin/env python3
#
# Copyright (c) 2025, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
#
# All rights reserved.
#
# This software is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# TODO: change filename to something more descriptive

import functools
import queue
import os
import sys
import yaml
from random import random
import time

from ur_dashboard_msgs.srv import (
    AddToLog,
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

from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

# Import the capabilities for socket and threading
import socket
import threading
import struct
from std_msgs.msg import String

# Import ROS2 controller manager capabilities
from controller_manager_msgs.srv import SwitchController
from controller_manager_msgs.srv import ListControllers
from std_msgs.msg import Bool


_KNOWN_SRV_TYPES = [
    AddToLog,
    GetLoadedProgram,
    GetProgramState,
    GetRobotMode,
    GetSafetyMode,
    IsProgramRunning,
    IsProgramSaved,
    Load,
    Popup,
    RawRequest,
    Trigger,
]


class RemoteURCmdr(Node):
    """Backend node for Dexterous Robotics Remote UR Arm Commander GUI

    Provides service clients and handles responses for service requests
    Service clients are generated from services provided in this package's services list (config/services.yaml)
    Services are called from the send_service_request method.
    Service request responses get processed and placed on a queue object shared with the Qt GUI thread as they are
    received.

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
    program: Name of URScript program to be filled out when load_program is selected in the GUI, typically ext_ctrl.urp
                or external_control.urp
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
    get_full_service_name: Appends the dashboard_client_name to a dashboard_client service name to correctly target the
                            client node
    generate_services_dynamically: Generates service clients and callbacks from the service list yaml at
                                    service_list_path
    send_service_request: Sends services requests
        Arguments:
            name (str): the name of the service that is being requested
            content (dict): the content of the service request, provided as a {field: value} dict
    _process_response: Queues incoming service request responses for GUI thread

    """

    # TODO: shutdown or __del__ cleanup function
    def __init__(self):
        super().__init__("drt_ur_gui")
        self.get_logger().info("Starting drt_ur_gui node...")
        self.service_request_timeout = 5.0  # seconds # TODO: Param self.service_request_timeout
        self.active_service_requests = {}  # used to store and ID async service requests for timeout handling
        self._init_params()
        self.dashboard_client_name = self.get_parameter("dashboard_client_name").get_parameter_value().string_value
        self.service_list_path = self.get_parameter("service_list_path").get_parameter_value().string_value
        self.service_list = self.load_service_list(
            self.service_list_path
        )  # [{'name':'<self.dashboard_client_name>/<service_name>', 'type': <service_type_class>}]
        self.loaded_services = self.generate_services()
        self.callbacks = {}
        self.response_queue = queue.Queue()

        ## Initialize the socket structure
        self.robot_ip = self.get_parameter("robot_ip").get_parameter_value().string_value

        self.script_command_topic = (
            self.declare_parameter("script_command_topic", "/script_command").get_parameter_value().string_value
        )
        self.script_command_pub = self.create_publisher(String, self.script_command_topic, 10)  # QoS queue depth
        self.get_logger().info(f"Script command publisher created on topic: {self.script_command_topic}")

        # Primary Interface Sockets and Threads
        # self.primary_socket = None
        self.rtde_socket = None
        self.rtde_running = False

        self.telemetry_lock = threading.Lock()
        self.latest_telemetry = {
            "timestamp": 0.0,
            "actual_q": [0.0] * 6,
            "actual_qd": [0.0] * 6,
            # "output_double_register_0": 0.0,
        }

        # Connect Primary and RTDE Interfaces
        # self.connect_primary_interface()
        self.connect_rtde_interface()

        ## Adding ROS2 service client and publisher
        self.switch_client = self.create_client(SwitchController, "/controller_manager/switch_controller")
        self.control_list_client = self.create_client(ListControllers, "/controller_manager/list_controllers")

        # Call the list of active controllers because we are not booting the robot in freedrive mode
        # while not self.control_list_client.wait_for_service(timeout_sec=1.0):
        #     self.get_logger().info("Service not available, waiting...")

        self.control_request = ListControllers.Request()

        self.freedrive_pub = self.create_publisher(Bool, "/freedrive_mode_controller/enable_freedrive_mode", 10)

        self.freedrive_active = False
        self.heartbeat_timer = self.create_timer(0.5, self._run_freedrive_heartbeat)  # Publish freedrive message at 2Hz

        self.current_controllers = []
        self.freedrive_controller = ["freedrive_mode_controller"]

    def _init_params(self):
        self.declare_parameters(
            namespace="",
            parameters=[
                ("dashboard_client_name", "dashboard_client"),
                (
                    "service_list_path",
                    os.path.join(get_package_share_directory("drt_ur_gui"), "config", "services.yaml"),
                ),
                ("window.name", "DRT Remote Commander"),
                ("window.stylesheet", ""),
                ("robot.name", "UR Arm"),
                ("robot.stylesheet", ""),
                ("arm.name", "Arm 0"),
                ("arm.stylesheet", ""),
                ("program", "default.urp"),
                ("logo_file_name", ""),
                # Add a declaration for robot's IP
                (
                    "robot_ip",
                    "192.168.1.102",
                ),  # <--------- This is a static IP address assignment, do we want this to be dynamic? Can it be dynamic?
            ],
        )

    def load_service_list(self, list_path):
        self.get_logger().info("Loading service list...")
        services = []
        with open(list_path) as service_list_contents:
            str_service_list = yaml.safe_load(service_list_contents)
        for service in str_service_list:
            service_name = self.get_full_service_name(service["name"])
            try:  # Attempt to match service type to imported modules
                service_type = getattr(sys.modules[__name__], service["type"])
            except AttributeError:  # If we can't find the service type, inform and skip
                self.get_logger().error(
                    f"Error while loading services from {self.service_list_path}: "
                    f"Service '{service_name}' type {service['type']} not recognized, skipping..."
                )
                continue
            services.append({"name": service_name, "type": service_type})
        return services

    def get_full_service_name(self, srv):
        return "/".join([self.dashboard_client_name, srv])

    # TODO: convert layered dict 'services' to class
    def generate_services(self):
        self.get_logger().info("Generating service clients...")
        services = {}
        for service in self.service_list:
            service_name, service_type = service["name"], service["type"]
            client = self.create_client(service_type, service_name)
            callback = functools.partial(self._process_response, service_name=service_name, service_type=service_type)
            services[service_name] = {"client": client, "callback": callback, "type": service_type}
            self.get_logger().info(f"Service client {service_name} created.")
        return services

    def send_service_request(self, name: str, content: dict = None):
        # Place holder bad response for queue
        self.get_logger().debug(f"SERVICE REQUEST: {name} {content}")
        bad_response = {"service_name": name, "success": False, "message": "", "response_content": None}
        # is the service known?
        if name not in self.loaded_services.keys():
            response_message = f"Service {name} requested is unavailable!"
            self.get_logger().error(response_message)
            bad_response["message"] = response_message
            self.response_queue.put(bad_response)
            return
        client = self.loaded_services[name]["client"]
        # is the service ready?
        if not client.service_is_ready():
            response_message = f"Service {name} is not ready, skipping request."
            self.get_logger().error(response_message)
            bad_response["message"] = response_message
            self.response_queue.put(bad_response)
            return
        req = client.srv_type.Request()
        # populate service request from content dictionary
        if content:
            for field, value in content.items():
                if hasattr(req, field):  # check to verify that content is valid
                    try:
                        setattr(req, field, value)  # populates request field-by-field
                    # if a field value is of the wrong type, send error and return
                    except TypeError as e:
                        response_message = (
                            f"Service request failed: Type error setting {field} for service request to {name}: {e}. "
                            f"Expected type: {type(getattr(req, field))}, Got: {type(value)}"
                        )
                        self.get_logger().error(response_message)
                        bad_response["message"] = response_message
                        self.response_queue.put(bad_response)
                        return
                else:  # if a message field does not exist, send error and return
                    response_message = (
                        f"Service request failed: Request field {field} not found in service {name} request message."
                        f"Available fields and types are {req.get_fields_and_field_types()}"
                    )
                    self.get_logger().error(response_message)
                    bad_response["message"] = response_message
                    return
        self.get_logger().debug(f"Sending service request to {name}")
        if content:
            self.get_logger().debug(f"with content: {content}")
        request_id = int(random() * 1e6)
        self.get_logger().debug(f"{name} ID: {request_id}")
        self.active_service_requests[request_id] = {}
        self.active_service_requests[request_id]["name"] = name
        self.active_service_requests[request_id]["timer"] = self.create_timer(
            self.service_request_timeout, functools.partial(self._process_request_timeout, request_id)
        )
        self.active_service_requests[request_id]["future"] = client.call_async(req)
        self.active_service_requests[request_id]["future"].add_done_callback(
            functools.partial(self._process_request_done, request_id)
        )
        return

    def _process_request_timeout(self, request_id):
        if request_id in self.active_service_requests:
            request = self.active_service_requests.pop(request_id)
            request["timer"].cancel()
            service_name = request["name"]
            service_type = self.loaded_services[service_name]["type"]
            output = {
                "service_name": service_name,
                "service_type": service_type,
                "success": False,
                "message": f"Service call timed out, (timeout={self.service_request_timeout})",
                "content": None,
            }
            self.get_logger().error(
                f"Service call to {service_name} timed out, timeout is set to {self.service_request_timeout}"
            )
            self.response_queue.put(output)
        else:  # request_id is not registered in self.active_service_requests
            self.get_logger().error(f"Service request id {request_id} not found in active requests id list")
        return

    def _process_request_done(self, request_id, future):
        if request_id in self.active_service_requests:
            request = self.active_service_requests.pop(request_id)
            request["timer"].cancel()
            self.loaded_services[request["name"]]["callback"](future)
        else:
            self.get_logger().error(f"Received response from unknown request ID {request_id}")
        return

    def _process_response(self, future, service_name: str, service_type):
        output = {
            "service_name": service_name,
            "service_type": service_type,
            "success": False,
            "message": "Service call failed",
            "content": None,
        }
        self.get_logger().debug(f"Received response from {service_name}")
        try:
            res = future.result()
            output["content"] = res
            output["success"] = True
            output["message"] = f"Received response from {service_name}"
        except Exception as e:
            output["message"] = f"Exception during service call {service_name}: {e}"
            self.get_logger().debug(f"Exception {e} while processing response for {service_name}")

        self.get_logger().debug(f"Response from {service_name} added to queue")
        self.response_queue.put(output)
        return

    # Primary and RTDE Interface Functions
    # TL;DR Direct Port calls are not in use
    """These are direct UR Arm Port calls, but they don't work. The front end works, but connecting to the actual robot does not.
    I'm leaving the skeleton of this code in tact, in case we need direct port calls in the future. &y"""

    # def connect_primary_interface(self):
    #     try:
    #         self.primary_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         self.primary_socket.settimeout(2.0)
    #         self.primary_socket.connect((self.robot_ip, 30001))
    #         self.get_logger.info().info("Successfully connected to Primary Interface")
    #     except Exception as e:
    #         self.get_logger().error(f"Failed to connect to Primary Interface: {e}")
    #         self.primary_socket = None

    def send_urscript(self, script_string: str):
        output = {
            "service_name": "script_command/send_script",
            "service_type": "std_msgs/msg/String",
            "success": False,
            "message": "",
            "content": None,
        }

        try:
            clean_script = script_string.strip()

            if not clean_script:
                output["message"] = "Empty script, nothing sent."
                self.response_queue.put(output)
                return

            if "\n" in clean_script:
                if not clean_script.startswith("def") and not clean_script.startswith("sec"):
                    formatted_script = "def gui_program():\n"
                    for line in clean_script.splitlines():
                        stripped = line.rstrip()
                        if stripped:
                            formatted_script += f"  {stripped}\n"
                    formatted_script += "end\n"
                else:
                    formatted_script = clean_script
                    if not formatted_script.endswith("\n"):
                        formatted_script += "\n"
            else:
                formatted_script = clean_script
                if not formatted_script.endswith("\n"):
                    formatted_script += "\n"

            msg = String()
            msg.data = formatted_script
            self.script_command_pub.publish(msg)

            output["success"] = True
            output["message"] = "URScript published to script_command topic."
            self.get_logger().info("Published URScript.")

        except Exception as e:
            output["message"] = f"Failed to publish URScript:{e}"
            self.get_logger().error(output["message"])

        self.response_queue.put(output)

    def connect_rtde_interface(self):
        try:
            self.rtde_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rtde_socket.settimeout(2.0)
            self.rtde_socket.connect((self.robot_ip, 30004))

            proto_request = struct.pack("!HBH", 5, 0x56, 2)
            self.rtde_socket.sendall(proto_request)
            ptype, payload = self._rtde_recv_packet()
            if ptype != 0x76:
                self.get_logger().warning("Unexpected RDE version response: 0x{ptype:02x}")

            output_recipe = "timestamp, actual_q, actual_qd"
            output_recipe_bytes = output_recipe.encode("utf-8")
            output_msg = struct.pack("!HB", 3 + len(output_recipe_bytes), 0x4F) + output_recipe_bytes
            self.rtde_socket.sendall(output_msg)
            ptpe, payload = self._rtde_recv_packet()
            if ptype == 0x4F and len(payload) > 0:
                self.rtde_output_recipe_id = payload[0]
                self.get_logger().info("RTDE output recipe ID: {self.rtde_output_recipe_id}")
            else:
                self.get_logger().error("Failed to setup RTDE output recipe.")
                self.rtde_socket.close()
                self.rtde_socket = None
                return

            input_recipe = "input_double_register_0"
            input_recipe_bytes = input_recipe.encode("utf-8")
            input_msg = struct.pack("!HB", 3 + len(input_recipe_bytes), 0x49) + input_recipe_bytes
            self.rtde_socket.sendall(input_msg)
            ptype, payload = self._rtde_recv_packet()
            if ptype == 0x49 and len(payload) > 0:
                self.rtde_input_recipe_id = payload[0]
                self.get_logger().info("RTDE input recipe ID: {self.rtde_input_recipe_id}")
            else:
                self.get_logger().warning("Failed to setup RTDE input recipe. Input writing disabled.")
                self.rtde_input_recipe_id = None

            start_msg = struct.pack("!HB", 3, 0x53)
            self.rtde_socket_sendall(start_msg)
            ptype, payload = self._rtde_recv_packet()
            if ptype == 0x53 and len(payload) > 0 and payload[0] == 1:
                self.get_logger().info("RTDE synchronization started successfully.")
            else:
                self.get_logger().error("RTDE synchronization start rejected.")
                self.rtde_socket.close()
                self.rtde_socket = None
                return

            self.rtde_running = True
            self.rtde_thread = threading.Thread(target=self._rtde_loop, daemon=True)
            self.rtde_thread.start()
            self.get_logger().info("RTDE telemetry thread started for {self.robo_ip}:30004")
        except Exception as e:
            e
            self.get_logger().error("Failed to connect to RTDE interface: {e}")
            self.rtde_socket = None

    def _rtde_recv_packet(self):
        header = self._recv_exact(3)
        packet_len = struct.unpack("!H", header[0:2])[0]
        packet_type = header[2]
        payload = b""
        if packet_len > 3:
            payload = self._recv_exact(packet_len - 3)
        return packet_type, payload

    def _recv_exact(self, num_bytes):
        data = b""
        while len(data) < num_bytes:
            chunk = self.rtde_socket.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionError("RTDE connection closed by remote host.")
            data += chunk
        return data

    def _rtde_loop(self):
        # RTDE requires a continuous read command after setup to start synchronization
        # try:
        #     self.rtde_socket.sendall(b"\x00\x03S")
        # except Exception as e:
        #     self.get_logger().error(f"RTDE Start exception: {e}")
        #     return

        while self.rtde_running:
            try:
                header = self._recv_exact(3)
                packet_len = struct.unpack("!H", header[0:2])[0]
                packet_type = header[2]

                payload = b""
                if packet_len > 3:
                    payload = self._recv_exact(packet_len - 3)

                if packet_type == 0x55 and len(payload) > 1:
                    recipe_id = payload[0]
                    recipe_id
                    data = payload[1:]
                    data

                    if len(payload) >= 104:
                        timestamp = struct.unpack("!d", payload[0:8])[0]
                        actual_q = list(struct.unpack("!6d", payload[8:56]))
                        actual_qd = list(struct.unpack("!6d", payload[56:104]))

                        with self.telemetry_lock:
                            self.latest_telemetry["timestamp"] = timestamp
                            self.latest_telemetry["actual_q"] = actual_q
                            self.latest_telemetry["actual_qd"] = actual_qd

            except socket.timeout:
                continue
            except Exception as e:
                self.get_logger().error(f"RTDE Loop execution error: {e}")
                break

        self.get_logger().warning("RTDE telemetry loop has exited.")

    def send_rtde_input(self, value: float):
        if not self.rtde_socket:
            self.get_logger().warning("RTDE socket not connected.")
            return False

        if not hasattr(self, "rtde_input_recipe_id") or self.rtde_input_recipe_id is None:
            self.get_logger().warning("RTDE input recipe not configured.")
            return False

        try:
            payload = struct.pack("!Bd", self.rtde_input_recipe_id, value)
            header = struct.pack("!HB", 3 + len(payload), 0x55)
            self.rtde_socket.sendall(header + payload)
            return True
        except Exception as e:
            self.get_logger().error(f"Failed to transmit RTDE input filed: {e}")
            return False

    ## ROS2 Controller Manager functions
    # self.control_request = ListControllers.Request() --> here for referencing, delete l8r
    def _get_active_controllers(self):

        self.current_controllers.clear()

        if not self.switch_client.service_is_ready():
            self.get_logger().error("Controller manager service unavailable. (-1)")
            return False

        controller_call = self.control_list_client.call_async(self.control_request)
        controller_call.add_done_callback(self._enable_control_done_callback)

    def _enable_control_done_callback(self, controller_call):
        controller_response = controller_call.result()
        if controller_response is None:
            self.get_logger().error("Failed to retrieve list of active controllers.")

        for controller in controller_response.controller:
            if controller.state == "active":
                if controller.required_command_interfaces:
                    self.current_controllers.append(controller.name)

        if not self.current_controllers:
            self.get_logger().error("No controllers registered as active.")

    def _run_freedrive_heartbeat(self):
        if self.freedrive_active:
            msg = Bool()
            msg.data = True
            self.freedrive_pub.publish(msg)

    def enable_ros2_freedrive(self):
        if not self.switch_client.service_is_ready():
            self.get_logger().error("Controller manager service unavailable.")
            return False

        req = SwitchController.Request()
        self._get_active_controllers()
        ctr = 0

        while not self.current_controllers:
            time.sleep(0.5)
            ctr += 1

            if ctr == 20:
                self.get_logger().error("No controllers registered as active. (-1)")
                return

        req.deactivate_controllers = self.current_controllers
        req.activate_controllers = self.freedrive_controller

        req.strictness = SwitchController.Request.STRICT

        future = self.switch_client.call_async(req)
        future.add_done_callback(self._enable_switch_done_callback)

    def _enable_switch_done_callback(self, future):
        res = future.result()
        if res.ok:
            self.get_logger().info("Successfully paused tracking. Starting freedrive.")
            self.freedrive_active = True
        else:
            self.get_logger().error("Failed to switch controllers.")

    def disable_ros2_freedrive(self):
        if not self.switch_client.service_is_ready():
            self.get_logger().error("Controller manager service unavailable.")
            return False

        req = SwitchController.Request()
        req.deactivate_controllers = self.freedrive_controller
        req.activate_controllers = self.current_controllers

        req.strictness = SwitchController.Request.STRICT

        future = self.switch_client.call_async(
            req
        )  # if there is no set in active controllers, then the console will error out. safeguard?
        future.add_done_callback(self._disable_switch_done_callback)

    def _disable_switch_done_callback(self, future):
        res = future.result()
        if res.ok:
            self.get_logger().info("Freedrive mode disabled.")
            self.freedrive_active = False
        else:
            self.get_logger().error("Failed to restore previous controllers.")

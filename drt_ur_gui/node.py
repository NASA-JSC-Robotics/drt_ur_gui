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
# test

import functools
import queue
import os
import sys
import yaml
from random import random

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

    (&& Freedrive Mode Related Attributes &&)
    switch_client: Service client to switch the state of controllers
    control_list_client: For retrieving the list of all controllers (both active and inactive) on the robot
    freedrive_pub: Publisher to keep freedrive mode active when enabled
    active_controllers: For storing the list of currently active controllers
    freedrive_controller: Stores the freedrive mode controller

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

    (&& Freedrive Mode Related Methods &&)
    _run_freedrive_heartbeat: Keepalive message for freedrive mode
    enable_ros2_freedrive: Turns freedrive mode on and de-activates the current controllers
    disable_ros2_freedrive: Turns freedrive mode off and re-activates the previous controllers
    _switch_to_freedrive: Acquires the list of all controllers, stores the currently active controllers
                          and the safety monitoring controllers
    _process_switch_controllers: Actives and de-activates the requested controllers
    _successful_controller_switch: Checks for the successful de/activation of controllers

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

        ## For freedrive mode
        self.freedrive_direction = self.get_parameter("freedrive_direction").get_parameter_value().string_value
        self.switch_client = self.create_client(SwitchController, "/controller_manager/switch_controller")
        self.control_list_client = self.create_client(ListControllers, "/controller_manager/list_controllers")
        self.control_request = ListControllers.Request()
        self.freedrive_pub = self.create_publisher(
            Bool, f"/{self.freedrive_direction}freedrive_mode_controller/enable_freedrive_mode", 10
        )
        self.freedrive_active = False
        self.active_controllers = []
        self.freedrive_controller = [
            f"{self.freedrive_direction}freedrive_mode_controller"
        ]

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
                ("freedrive_direction", ""),
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

    ## ROS2 Controller Manager functions
    """ Unlike the above services that run through UR's dashboard client, Freedrive mode is backed by ROS2's Controller Manager.
    Freedrive mode is not a currently native feature of UR's dashboard client. """

    def _run_freedrive_heartbeat(self):
        # To keep the freedrive mode active
        if self.freedrive_active:
            msg = Bool()
            msg.data = True
            self.freedrive_pub.publish(msg)

    def enable_ros2_freedrive(self):
        # Check if the controller and switch controller managers are available
        if not self.switch_client.service_is_ready():
            self.get_logger().error("Switch Controller manager service unavailable.")
            return False

        if not self.control_list_client.service_is_ready():
            self.get_logger().error("Controller manager service unavailable.")
            return False

        # Get the list of currently active controllers, store them, and switch to freedrive mode
        self.active_controllers.clear()
        self.freedrive_active = True
        get_all_controllers = self.control_list_client.call_async(self.control_request)
        get_all_controllers.add_done_callback(self._switch_to_freedrive)

    def disable_ros2_freedrive(self):
        # Check if the switch controller manager is available
        if not self.switch_client.service_is_ready():
            self.get_logger().error("Switch Controller manager service unavailable.")
            return False

        # Bring the previously active controllers back online
        # if not self.active_controllers:
        #     self.get_logger().error("List of active controllers is empty.")
        #     return
        # else:
        self.freedrive_active = False
        self._process_switch_controllers(turn_ON=self.active_controllers, turn_OFF=self.freedrive_controller)
        self.destroy_timer(self.heartbeat_timer)

    def _switch_to_freedrive(self, get_all_controllers):
        # Controller request to get the list of active controllers before freedrive mode is enabled
        controller_response = get_all_controllers.result()
        if controller_response is None:
            self.get_logger().error("Failed to retrieve list of all controllers.")
            return
        else:
            self.get_logger().info("List of controllers received.")
            for controller in controller_response.controller:
                if controller.state == "active":
                    if (
                        controller.required_command_interfaces
                        and not (controller.type == "ur_controllers/GPIOController" or controller.type == "ur_controllers/FreedriveModeController")
                    ):  # white listed the io and status controller for e-stop monitoring
                        self.active_controllers.append(controller.name)

        # if not self.active_controllers:
        self.get_logger().error("No controllers registered as active.")
    #     return
    # else:
        self._process_switch_controllers(turn_ON=self.freedrive_controller, turn_OFF=self.active_controllers)

        # Start the freedrive heartbeat @ 2Hz
        self.heartbeat_timer = self.create_timer(0.5, self._run_freedrive_heartbeat)

    def _process_switch_controllers(self, turn_ON, turn_OFF):
        # if not turn_ON or not turn_OFF:
        #     self.get_logger().error("One of the controller lists is empty.")
        #     return
        # else:
        req = SwitchController.Request()
        req.deactivate_controllers = turn_OFF
        req.activate_controllers = turn_ON

        req.strictness = SwitchController.Request.STRICT

        future = self.switch_client.call_async(req)
        future.add_done_callback(self._successful_controller_switch)

    def _successful_controller_switch(self, future):
        res = future.result()
        state = self.freedrive_active

        if res.ok and state is True:
            self.get_logger().info("Successfully paused tracking. Starting freedrive.")
        elif res.ok and state is False:
            self.get_logger().info("Freedrive mode disabled.")
        elif not res.ok and state is True:
            self.get_logger().error("Failed to switch controllers.")
        elif not res.ok and state is False:
            self.get_logger().error("Failed to restore previous controllers.")

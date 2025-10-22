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

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_fake_hardware",
            default_value="false",
            choices=["true", "false"],
            description="Start robot with simulated hardware mirroring command to its states",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "connect_lag",
            default_value="false",
            choices=["true", "false"],
            description="Force service timeouts by adding lag to the 'connect' service in the \
                            mock Dashboard Client node (only works with use_fake_hardware=true)",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument("ns", default_value="", description="Namespace for the hardware robot")
    )

    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    connect_lag = LaunchConfiguration("connect_lag")
    ns = LaunchConfiguration("ns")

    config = os.path.join(get_package_share_directory("drt_ur_gui"), "config", "one_arm.yaml")

    gui_node = Node(
        package="drt_ur_gui",
        executable="run_gui.py",
        output="screen",
        namespace=ns,
        parameters=[config],
        sigterm_timeout="0",
    )
    mock_dbc_node = Node(
        package="drt_ur_gui",
        executable="run_mock_dbc.py",
        output="screen",
        namespace=ns,
        parameters=[
            {
                "connect_lag": connect_lag,
            }
        ],
        condition=IfCondition(use_fake_hardware),
        sigterm_timeout="0",
    )

    return LaunchDescription(declared_arguments + [gui_node, mock_dbc_node])

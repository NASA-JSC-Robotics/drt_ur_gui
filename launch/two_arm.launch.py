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
            "mock_dashboard",
            default_value="false",
            choices=["true", "false"],
            description="Launch the mock dashboard node to simulated UR commands and state",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument("ns", default_value="", description="Namespace for the hardware robot")
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "right_arm_config_path",
            default_value=os.path.join(get_package_share_directory("drt_ur_gui"), "config", "two_arm_right.yaml"),
            description="Full filepath to the parameters yaml that will be applied to the right arm GUI window",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "left_arm_config_path",
            default_value=os.path.join(get_package_share_directory("drt_ur_gui"), "config", "two_arm_left.yaml"),
            description="Full filepath to the parameters yaml that will be applied to the left arm GUI window",
        )
    )

    mock_dashboard = LaunchConfiguration("mock_dashboard")
    ns = LaunchConfiguration("ns")
    config_right = LaunchConfiguration("right_arm_config_path")
    config_left = LaunchConfiguration("left_arm_config_path")

    right_arm_nodes = [
        Node(
            package="drt_ur_gui",
            executable="run_gui.py",
            name="right_drt_ur_gui",
            output="screen",
            namespace=ns,
            parameters=[config_right],
            sigterm_timeout="0",
        ),
        Node(
            package="drt_ur_gui",
            executable="run_mock_dbc.py",
            name="right_dashboard_client",  # must match dashboard_client_name in config/two_arm_right.yaml
            output="screen",
            namespace=ns,
            condition=IfCondition(mock_dashboard),
            sigterm_timeout="0",
        ),
    ]

    left_arm_nodes = [
        Node(
            package="drt_ur_gui",
            executable="run_gui.py",
            name="left_drt_ur_gui",
            output="screen",
            namespace=ns,
            parameters=[config_left],
            sigterm_timeout="0",
        ),
        Node(
            package="drt_ur_gui",
            executable="run_mock_dbc.py",
            name="left_dashboard_client",
            output="screen",
            namespace=ns,
            condition=IfCondition(mock_dashboard),
            sigterm_timeout="0",
        ),
    ]

    return LaunchDescription(declared_arguments + left_arm_nodes + right_arm_nodes)

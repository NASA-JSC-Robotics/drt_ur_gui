import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

from drt_ur_gui import SERVICES

def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_fake_hardware",
            default_value="false",
            choices=['true', 'false'],
            description="Start robot with simulated hardware mirroring command to its states"
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the hardware robot"
        )
    )
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    ns = LaunchConfiguration("ns")

    
    config = os.path.join(
        get_package_share_directory('drt_ur_gui'),
        'config',
        'pb.yaml'
    )
    
    right_gui_node = Node(
        package = "drt_ur_gui",
        executable="run_gui.py",
        name="right_drt_ur_gui",
        output='screen',
        namespace = ns,
        parameters = [config]
    )
    left_gui_node = Node(
        package = "drt_ur_gui",
        executable="run_gui.py",
        name="left_drt_ur_gui",
        output='screen',
        namespace = ns,
        parameters = [config]
    )
    right_mock_dbc_node = Node(
        package= "drt_ur_gui",
        executable="run_mock_dbc.py",
        name="right_dashboard_client",
        output='screen',
        namespace = ns,
        condition=IfCondition(use_fake_hardware)
    )
    left_mock_dbc_node = Node(
        package= "drt_ur_gui",
        executable="run_mock_dbc.py",
        name="left_dashboard_client",
        output='screen',
        namespace = ns,
        condition=IfCondition(use_fake_hardware)
    )
    return LaunchDescription(declared_arguments + [right_gui_node, left_gui_node, right_mock_dbc_node, left_mock_dbc_node])

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, NotSubstitution
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
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_ip",
            default_value="192.168.1.102",
            description="IP address by which the robot can be reached.")
    )

    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    ns = LaunchConfiguration("ns")
    robot_ip = LaunchConfiguration("robot_ip")

    
    config = os.path.join(
        get_package_share_directory('drt_ur_gui'),
        'config',
        'clr.yaml'
    )
    
    gui_node = Node(
        package = "drt_ur_gui",
        executable="run_gui.py",
        output='screen',
        namespace = ns,
        parameters = [config]
    )
    dashboard_client_node = Node(
        package="ur_robot_driver",
        condition=IfCondition(NotSubstitution(use_fake_hardware)),
        executable="dashboard_client",
        name="dashboard_client",
        output="screen",
        emulate_tty=True,
        parameters=[{"robot_ip": robot_ip}],
    )
    mock_dbc_node = Node(
        package= "drt_ur_gui",
        executable="run_mock_dbc.py",
        output='screen',
        namespace = ns,
        condition=IfCondition(use_fake_hardware)
    )
    return LaunchDescription(declared_arguments + [gui_node, dashboard_client_node, mock_dbc_node])

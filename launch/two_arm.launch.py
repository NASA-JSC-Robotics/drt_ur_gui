from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from drt_ur_gui import SERVICES


def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "dashboard_client_one_name",
            default_value="right_dashboard_client",
            description="Name of the first dashboard client node"
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "dashboard_client_two_name",
            default_value="left_dashboard_client",
            description="Name of the second dashboard client node"
        )
    )
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
    
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
    
def launch_setup(context, *args, **kwargs):
    dashboard_client_one_name = LaunchConfiguration("dashboard_client_one_name").perform(context)
    dashboard_client_two_name = LaunchConfiguration("dashboard_client_two_name").perform(context)
    
    use_fake_hardware = LaunchConfiguration("use_fake_hardware").perform(context)
    ns = LaunchConfiguration("ns").perform(context)
    
    arm_one_nodes = [
        Node(
            package = "drt_ur_gui",
            executable="run_gui.py",
            name="right_remote_ur_commander",
            output='screen',
            namespace = ns,
            parameters=[
                {'dashboard_client_name': dashboard_client_one_name}
            ],
        ),
        Node(
            package = "drt_ur_gui",
            executable = "run_mock_dbc.py",
            name = dashboard_client_one_name,
            output = 'screen',
            namespace = ns,
            condition = IfCondition(use_fake_hardware)
        )
    ]
    
    arm_two_nodes = [
        Node(
            package = "drt_ur_gui",
            executable = "run_gui.py",
            name = "left_remote_ur_commander",
            output = 'screen',
            namespace = ns,
            parameters=[
                {'dashboard_client_name': dashboard_client_two_name}
            ]
        ),
        Node(
            package = "drt_ur_gui",
            executable = "run_mock_dbc.py",
            name = dashboard_client_two_name,
            output = 'screen',
            namespace = ns,
            condition = IfCondition(use_fake_hardware)
        )
    ]
    return arm_one_nodes + arm_two_nodes

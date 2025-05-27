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
            "dashboard_client_name",
            default_value="dashboard_client",
            description="Name of the dashboard client node"
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
    dashboard_client_name = LaunchConfiguration("dashboard_client_name").perform(context)
    use_fake_hardware = LaunchConfiguration("use_fake_hardware").perform(context)
    ns = LaunchConfiguration("ns").perform(context)
    gui_node = Node(
        package = "drt_ur_gui",
        executable="run_gui.py",
        output='screen',
        namespace = ns,
        parameters = [
            {'dashboard_client_name': dashboard_client_name}
        ]
    )
    mock_dbc_node = Node(
        package= "drt_ur_gui",
        executable="run_mock_dbc.py",
        output='screen',
        namespace = ns,
        name = dashboard_client_name,
        condition=IfCondition(use_fake_hardware)
    )
    return [gui_node, mock_dbc_node]



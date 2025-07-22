import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, NotSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the hardware robot"
        )
    )
    ns = LaunchConfiguration("ns")    
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
    return LaunchDescription(declared_arguments + [gui_node])

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
    
    config_right = os.path.join(
        get_package_share_directory('drt_ur_gui'),
        'config',
        'two_arm_right.yaml'
    )

    config_left = os.path.join(
        get_package_share_directory('drt_ur_gui'),
        'config',
        'two_arm_left.yaml'
    )

    right_arm_nodes = [
        Node(
            package = "drt_ur_gui",
            executable="run_gui.py",
            name="right_remote_ur_commander",
            output='screen',
            namespace = ns,
            parameters=[config_right],
        ),
        Node(
            package = "drt_ur_gui",
            executable = "run_mock_dbc.py",
            name = "left_dashboard_client", # must match dashboard_client_name in config/two_arm_right.yaml
            output = 'screen',
            namespace = ns,
            condition = IfCondition(use_fake_hardware)
        )
    ]
    
    left_arm_nodes = [
        Node(
            package = "drt_ur_gui",
            executable = "run_gui.py",
            name = "left_remote_ur_commander",
            output = 'screen',
            namespace = ns,
            parameters=[config_left]
        ),
        Node(
            package = "drt_ur_gui",
            executable = "run_mock_dbc.py",
            name = "right_dashboard_client",
            output = 'screen',
            namespace = ns,
            condition = IfCondition(use_fake_hardware)
        )
    ]
    
    nodes = [
        left_arm_nodes +
        right_arm_nodes
        ]
    
    return LaunchDescription(declared_arguments + nodes)

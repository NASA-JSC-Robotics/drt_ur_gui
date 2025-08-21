#!/usr/bin/python3

import rclpy
from rclpy.executors import MultiThreadedExecutor

from drt_ur_gui.mock_dashboard_client import MockDashboardClient

def main(args=None):
    rclpy.init(args=args)
    multithread_exec = MultiThreadedExecutor()
    mock_dbc = MockDashboardClient()
    multithread_exec.add_node(mock_dbc)
    try:
        multithread_exec.spin()
    except Exception as e:
        mock_dbc.get_logger().info(f"Executor spin error: {e}")
    finally:
        multithread_exec.shutdown()
        mock_dbc.get_logger().info('Shutting down...')
    
if __name__ == "__main__":
    main()
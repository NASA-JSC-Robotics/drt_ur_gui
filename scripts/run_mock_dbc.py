#!/usr/bin/python3

import rclpy
from rclpy.executors import MultiThreadedExecutor

from drt_ur_gui.mock_dashboard_client import FakeDashboardClient

def main(args=None):
    rclpy.init(args=args)
    mtexec = MultiThreadedExecutor()
    mock_dbc = FakeDashboardClient()
    mtexec.add_node(mock_dbc)
    try:
        mtexec.spin()
    except Exception as e:
        mock_dbc.get_logger().info(f"Executor spin error: {e}")
    finally:
        mtexec.shutdown()
        mock_dbc.get_logger().info('Shutting down...')
    
        
        
    
    
if __name__ == "__main__":
    main()
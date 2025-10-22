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
    except KeyboardInterrupt:
        pass
    except Exception as e:
        mock_dbc.get_logger().info(f"Executor spin error: {e}")
    finally:
        mock_dbc.get_logger().info("Cleaning up mock dashboard client...")
        mock_dbc.destroy_node()
        rclpy.try_shutdown()
        print("[MockDashboardClient Executable]: Completed cleanup, exiting...")


if __name__ == "__main__":
    main()

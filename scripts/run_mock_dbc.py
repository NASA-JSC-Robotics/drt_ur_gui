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

import sys
from functools import partial
import signal
import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.signals import SignalHandlerOptions

from drt_ur_gui.mock_dashboard_client import MockDashboardClient


def sigterm_handler(executor, node, sig, frame):
    """
    Handler for SIGTERM signals. Triggers try_shutdown event on executor, forcing spin to stop.
    """
    node.get_logger().warn("Received SIGTERM, shutting down mock dashboard client...")
    executor.context.try_shutdown()


def main(args=None):
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # block incoming SIGINT signals
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)  # tell ros2 to let us handle all signals
    multithread_exec = MultiThreadedExecutor()
    mock_dbc = MockDashboardClient()
    multithread_exec.add_node(mock_dbc)
    signal_handler = partial(sigterm_handler, multithread_exec, mock_dbc)  # set up signal handler lambda function
    signal.signal(signal.SIGTERM, signal_handler)  # set SIGTERM signals to trigger the signal handler function
    try:
        multithread_exec.spin()
    except Exception as e:
        mock_dbc.get_logger().info(f"Executor spin error: {e}")
    finally:
        mock_dbc.get_logger().info("Cleaning up mock dashboard client...")
        # Normally we wait for executor shutdown here, but we're relying on sys.exit(0)
        # to kill running threads faster to avoid a SIGKILL escalation
        mock_dbc.destroy_node()
        rclpy.try_shutdown()
        print("[MockDashboardClient Executable]: Completed cleanup, exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()

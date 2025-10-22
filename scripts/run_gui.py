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

import signal
import sys
from functools import partial
import rclpy
from rclpy.executors import MultiThreadedExecutor
from python_qt_binding.QtWidgets import QApplication
from python_qt_binding.QtCore import QTimer
from rclpy.signals import SignalHandlerOptions

from drt_ur_gui.window import URGui
from drt_ur_gui.node import RemoteURCmdr


def cleanup_ros2(node, multithread_exec):
    """
    Cleanup function for the GUI backend node.
    """
    node.get_logger().info("Starting cleanup on shutdown...")
    multithread_exec.remove_node(node)
    node.destroy_node()
    multithread_exec.shutdown()
    rclpy.try_shutdown()


def main(args=None):
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # block incoming SIGINT signals
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)  # tell ros2 to let us handle all signals
    app = QApplication(sys.argv)  # Create Qt application
    ur_cmdr = RemoteURCmdr()  # GUI backend node
    ur_gui = URGui(ur_cmdr)  # GUI Node with backend node arg

    mtexec = MultiThreadedExecutor()
    mtexec.add_node(ur_cmdr)

    def sigterm_handler(sig, frame):
        """
        Handler for SIGTERM signals. Commands Qt App to quit, triggering sys.exit() in main().
        """
        ur_cmdr.get_logger().info("Received SIGTERM, shutting down gui...")
        app.quit()

    signal.signal(signal.SIGTERM, sigterm_handler)  # set SIGTERM signals to trigger sigterm_handler function

    # Running the Qt App through a QTimer to allow for graceful exit through app.quit() in sigterm_handler function
    timer = QTimer()
    timer.timeout.connect(partial(mtexec.spin_once, timeout_sec=0))
    timer.start(10)  # 10ms, 100Hz refresh rate

    cleanup_function = partial(cleanup_ros2, ur_cmdr, mtexec)  # partial function/lambda for backend node clean up
    app.aboutToQuit.connect(cleanup_function)  # Triggers cleanup_function on GUI window close

    try:
        ur_gui.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        cleanup_ros2(ur_cmdr, mtexec)  # Trigger cleanup on unexpected exceptions
        sys.exit(1)


if __name__ == "__main__":
    main()

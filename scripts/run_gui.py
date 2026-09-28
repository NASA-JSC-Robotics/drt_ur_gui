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
from python_qt_binding.QtWidgets import QApplication, QMainWindow
from python_qt_binding.QtCore import QTimer, Qt

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
    from pathlib import Path
    import yaml
    from pprint import pprint
    raw_args = sys.argv[1:] 
    print(f"Remaining command line arguments: {raw_args}")
    indx = raw_args.index("--ros-args")
    print(raw_args[:indx])
    for file_path in raw_args[:indx]:
      if Path(file_path).is_file():
        print("The file exists.")
        # Open the YAML file and parse it into a dictionary
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)

        for key, val in data.items():
          print(key)
          ur_cmdr = RemoteURCmdr(node_name=key)
        # pprint(data)
        # print(data.keys()[0])

        # print(type(data))  # <class 'dict'>
      else:
          print("The file does not exist.")



    quit()
    
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # block incoming SIGINT signals
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)  # tell ros2 to let us handle all signals
    
    
    print(args)
    quit()
    
    app = QApplication(sys.argv)  # Create Qt application
    ur_cmdr = RemoteURCmdr()  # GUI backend node
    ur_cmdr2 = RemoteURCmdr()  # GUI backend node
    main_window = QMainWindow()
    
    ur_gui = URGui(ur_cmdr)  # GUI Node with backend node arg
    ur_gui.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
    ur_gui2 = URGui(ur_cmdr2)  # GUI Node with backend node arg
    ur_gui2.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
    
    main_window.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, ur_gui)
    main_window.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, ur_gui2)

    mtexec = MultiThreadedExecutor()
    mtexec.add_node(ur_cmdr)
    mtexec.add_node(ur_cmdr2)

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
    cleanup_function2 = partial(cleanup_ros2, ur_cmdr2, mtexec)  # partial function/lambda for backend node clean up
    app.aboutToQuit.connect(cleanup_function)  # Triggers cleanup_function on GUI window close
    app.aboutToQuit.connect(cleanup_function2)  # Triggers cleanup_function on GUI window close

    try:
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        cleanup_ros2(ur_cmdr, mtexec)  # Trigger cleanup on unexpected exceptions
        cleanup_ros2(ur_cmdr2, mtexec)  # Trigger cleanup on unexpected exceptions
        sys.exit(1)


if __name__ == "__main__":
    main()

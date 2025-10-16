#!/usr/bin/python3

import threading, sys
import rclpy
from rclpy.executors import MultiThreadedExecutor
from python_qt_binding.QtWidgets import QApplication

from drt_ur_gui.window import URGui
from drt_ur_gui.node import RemoteURCmdr


def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    ur_cmdr = RemoteURCmdr()
    mtexec = MultiThreadedExecutor()
    mtexec.add_node(ur_cmdr)
    mtexec_Thread = threading.Thread(target = mtexec.spin, daemon = True)
    mtexec_Thread.start()
    
    
    ur_gui = URGui(ur_cmdr)
    ur_gui.show()
    
    app.exec_()
    ur_cmdr.response_queue.join()
    ur_cmdr.destroy_node()
    rclpy.shutdown()
    mtexec.shutdown()
    mtexec_Thread.join()
    

if __name__ == "__main__":
    main()


# # Erik suggests:
# def main(args=None):
#     rclpy.init(args=args)

#     app = QApplication(sys.argv)
#     ur_cmdr = RemoteURCmdr()
#     ur_gui = URGui(ur_cmdr)

#     mtexec = MultiThreadedExecutor()
#     mtexec.add_node(ur_cmdr)
#     mtexec_T = threading.Thread(target = mtexec.spin)
#     mtexec_T.start()

#     def signal_handler(sig, frame):
#         print(f"Program received signal: {sig}, terminating...")
#         app.quit()
#         ur_cmdr.response_queue.join()
#         ur_cmdr.destroy_node()
#         mtexec.shutdown()
#         mtexec_T.join()

#     signal.signal(signal.SIGINT, signal_handler)
#     signal.signal(signal.SIGTERM, signal_handler)

#     try:
#         ur_gui.show()
#         app.exec_()
#     except KeyboardInterrupt:
#         pass
#     finally:
#         rclpy.try_shutdown()

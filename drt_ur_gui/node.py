
import sys

from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node

class RemoteURCmdr(Node):
    def __init__(self):
        super().__init__('remote_ur_commander')
        self.add_client = self.create_client(AddTwoInts, 'add_two_ints')
        while not self.add_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = AddTwoInts.Request()
    
    def send_request(self):
        self.req.a = 1
        self.req.b = 2
        future = self.add_client.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response.sum
    
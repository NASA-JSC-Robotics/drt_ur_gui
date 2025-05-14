
import sys

from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup

class RemoteURCmdr(Node):
    def __init__(self):
        super().__init__('remote_ur_commander')
        
        self.r_cbg = ReentrantCallbackGroup()
        
        self.client_0 = self.create_client(AddTwoInts, 'add_two_ints', callback_group=self.r_cbg)
        self.client_1 = self.create_client(AddTwoInts, 'add_two_ints', callback_group=self.r_cbg)
        self.client_2 = self.create_client(AddTwoInts, 'add_two_ints', callback_group=self.r_cbg)
        self.client_3 = self.create_client(AddTwoInts, 'add_two_ints', callback_group=self.r_cbg)
        self.client_4 = self.create_client(AddTwoInts, 'add_two_ints', callback_group=self.r_cbg)
        self.client_5 = self.create_client(AddTwoInts, 'add_two_ints', callback_group=self.r_cbg)
        self.client_6 = self.create_client(AddTwoInts, 'add_two_ints', callback_group=self.r_cbg)
        self.client_7 = self.create_client(AddTwoInts, 'add_two_ints', callback_group=self.r_cbg)

        while not (self.client_0.wait_for_service(timeout_sec=1.0)
                    and self.client_1.wait_for_service(timeout_sec=1.0)
                    and self.client_2.wait_for_service(timeout_sec=1.0)
                    and self.client_3.wait_for_service(timeout_sec=1.0)
                    and self.client_4.wait_for_service(timeout_sec=1.0)
                    and self.client_5.wait_for_service(timeout_sec=1.0)
                    and self.client_6.wait_for_service(timeout_sec=1.0)
                    and self.client_7.wait_for_service(timeout_sec=1.0)):
            self.get_logger().info('service not available, waiting again...')
        self.req = AddTwoInts.Request()
    
    def send_request_0(self):
        self.req.a = 0
        self.req.b = 0
        future = self.client_0.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response.sum

    def send_request_1(self):
        self.req.a = 1
        self.req.b = 0
        future = self.client_1.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response.sum

    def send_request_2(self):
        self.req.a = 0
        self.req.b = 2
        future = self.client_2.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response.sum
    
    def send_request_3(self):
        self.req.a = 1
        self.req.b = 2
        future = self.client_3.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response.sum
    
    def send_request_4(self):
        self.req.a = 2
        self.req.b = 2
        future = self.client_4.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response.sum
    
    def send_request_5(self):
        self.req.a = 3
        self.req.b = 2
        future = self.client_5.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response.sum
    
    def send_request_6(self):
        self.req.a = 4
        self.req.b = 2
        future = self.client_6.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response.sum
    
    def send_request_7(self):
        self.req.a = 3
        self.req.b = 4
        future = self.client_7.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response.sum
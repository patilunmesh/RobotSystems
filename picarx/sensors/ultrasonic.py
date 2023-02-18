import sys
try:
    sys.path.append('..')
    from picarx import Picarx
    from robot_hat import *
except ImportError:
    print("ImportError: not Raspberry Pi.")
    from picarx_improved import Picarx
    from sim_robot_hat import *

class Ultrsonic:
    
    def __init__(self,
                 pin1: Pin,
                 pin2: Pin,
                 threshold) -> None:

        self.car = Picarx()
        self.pin1 = pin1
        self.pin2 = pin2
        self.threshold = threshold

    def read(self):
        print("Ultrsonic fetching values.")
        return Ultrasonic(self.pin1, self.pin2).read()

    def process(self, sensor_value):
        if sensor_value < self.threshold:
            return True
        return False

    def control(self, processed_value):
        if processed_value:
            print("stopping car")
            self.car.stop()

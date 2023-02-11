import numpy as np
from enum import IntEnum
from typing import List
from busses import DataBus
import sys
try:
    sys.path.append('/home/hlab/RobotSystems/picarx')
    from picarx import Picarx
    from robot_hat import *
except ImportError:
    print("ImportError: not Raspberry Pi.")
    from picarx_improved import Picarx
    from sim_robot_hat import *

SensorOutput = List[int]


class Sensor:
    def __init__(self, adc_channels, bus: DataBus) -> None:
        self.channels = [ADC(channel) for channel in adc_channels]
        self.bus = bus

    def read(self) -> SensorOutput:
        sensor_values = [adc.read() for adc in self.channels]
        self.bus.write({'adc': sensor_values})
        print("Grayscale::sensor read")
        return sensor_values


class Polarity(IntEnum):
    Dark = -1
    Light = +1


class Interpreter:

    def __init__(self,
                 sensitivity: float = 1e-0,
                 polarity: Polarity = Polarity.Dark) -> None:

        self.sensitivity = sensitivity
        self.polarity = polarity

    def process(self, sensor_values: SensorOutput) -> float:
        mid = len(sensor_values) // 2
        diff = np.array(sensor_values[:mid+1]) - np.array(sensor_values[mid:]) * self.polarity
        diff[mid:] *= -1   
        return np.clip(np.mean(diff) * self.sensitivity, -1, 1)


class Controller:

    def __init__(self, bus: DataBus, scale: float = 1.0, *args, **kwargs) -> None:
        self.bus = bus
        self.car = Picarx()
        self.interpreter = Interpreter(*args, **kwargs)

    def update(self):
        values = self.bus.read()['adc']
        values = self.interpreter.process(values)
        self.steer(values)
        print("Grayscale::Controller::update() updated steering angle.")

    def steer(self, grayscale_out) -> float:
        car.set_dir_servo_angle(angle)

    

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


class GSSensor:
    def __init__(self, bus: DataBus) -> None:
        self.chn_0 = ADC('A0')
        self.chn_1 = ADC('A1')
        self.chn_2 = ADC('A2')
        self.bus = bus

    def read(self) -> SensorOutput:
        adc_value_list = []
        adc_value_list.append(self.chn_0.read())
        adc_value_list.append(self.chn_1.read())
        adc_value_list.append(self.chn_2.read())
        self.bus.write({'adc': adc_value_list})
        print("Grayscale::sensor read")
        return sensor_values


class Polarity(IntEnum):
    Dark = -1
    Light = +1


class GSInterpreter:

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


class GSController:

    def __init__(self, bus: DataBus, scale: float = 1.0, *args, **kwargs) -> None:
        self.bus = bus
        self.car = Picarx()
        self.interpreter = GSInterpreter(*args, **kwargs)

    def update(self):
        values = self.bus.read()['adc']
        values = self.interpreter.process(values)
        self.steer(values)
        print("Grayscale::Controller::update() updated steering angle.")

    def steer(self, grayscale_out) -> float:
        car.set_dir_servo_angle(angle)

    

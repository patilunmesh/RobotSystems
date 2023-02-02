from robot_hat import *
import numpy as np
from enum import IntEnum
from typing import List
from picarx import Picarx
from time import sleep

SensorOutput = List[int]
PERIOD = 4095
PRESCALER = 10

class Sensor(object):
    def __init__(self, pin0, pin1, pin2):
        self.chn_0 = ADC(pin0)
        self.chn_1 = ADC(pin1)
        self.chn_2 = ADC(pin2)

    def get_grayscale_data(self):
        adc_value_list = []
        adc_value_list.append(self.chn_0.read())
        adc_value_list.append(self.chn_1.read())
        adc_value_list.append(self.chn_2.read())
        return adc_value_list

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

        # caluclate difference
        mid = len(sensor_values) // 2
        delta = np.array(sensor_values[:mid+1]) - np.array(sensor_values[mid:]) * self.polarity
        delta[mid:] *= -1  
        return np.clip(np.mean(delta) * self.sensitivity, -1, 1)

class Controller:

    def __init__(self, *args, **kwargs) -> None:
        self.scale = scale
        self.car = Picarx()
        self.values = [0, 0, 0]

    def steer(self, values) -> float:
        print("Grayscale::Controller::steer() steering.")
        self.car.set_angle(self.scale * grayscale_out)

    

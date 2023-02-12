import futures3
from readerwriterlock import rwlock
from grayscale import GSSensor, GSInterpreter, GSController
from camera import CamSensor, CamInterpreter, CamController
from ultrasonic import Ultrsonic
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


class Executor():
    def __init__(self):
        self.car = Picarx()
        # initialize all the busses
        self.gs_bus = DataBus()
        self.ultrasonic_bus = DataBus()
        self.cam_bus = DataBus()
        self.inter_bus = DataBus()
        #greyscale units
        self.gray_sensor = GSSensor(self.gs_bus)
        self.gray_interp = GSInterpreter()
        self.gray_control = GSController(None, self.car)
        #camera units
        self.camera = CamSensor()
        self.cmera_proc = CamInterpreter()
        self.cam_control = CamController()
        #Ultrasonic
        self.ultrasonic = Ultrsonic(Pin('D0'),Pin('D1'),75)

    def execute(self):
        delay = 0.1

        while True:
            with futures3.ThreadPoolExecutor() as executor:
                eGrayscale = executor.submit(self.gray_sensor, self.gs_bus, delay)
                eUltra = executor.submit(self.ultrasonic, self.ultrasonic_bus, delay)
                eCamera = executor.submit(self.camera, self.cam_bus, delay)
                eInterpreter = executor.submit(self.gray_interp, self.gs_bus, self.inter_bus, delay)
                eController = executor.submit(self.gray_control, self.interp_bus, delay)

            eGrayscale.result()
            eUltra.result()
            eCamera.result()
            eInterpreter.result()
            eController.result()

if __name__ == "__main__":
    exe = Executor()
    #exe.execute()
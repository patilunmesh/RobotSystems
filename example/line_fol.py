from picarx import Picarx
from greyscale import Sensor, Interpreter, Controller
from time import sleep
if __name__ == '__main__':

    print("\ntesting grayscale sensor.")

    # test car
    car = Picarx()

    # grayscale sensor, interpreter and controller
    sensor = Sensor('A0', 'A1', 'A2')
    interpreter = Interpreter()
    controller = Controller(None, car)

    while (True):
        data  = sensor.get_grayscale_data()
        print(data)
        ret = interpreter.process(data)
        print(ret)
        sleep(1)
        controller.steer(ret)
        car.forward(10)
    car.stop()

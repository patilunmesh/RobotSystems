from picarx import Picarx
import Picarx.sensors.grayscale as Grayscale

if __name__ == '__main__':

    print("\ntesting grayscale sensor. Using ultrasonic sensor for breaks.")

    # test car
    car = Picarx()

    # grayscale sensor, interpreter and controller
    sensor = Grayscale.Sensor(['A0', 'A1', 'A2'])
    interpreter = Grayscale.Interpreter()
    controller = Grayscale.Controller(None, car)

    
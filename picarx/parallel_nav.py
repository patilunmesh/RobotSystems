import sys
sys.path.append('')
try:
    from picarx import Picarx
    from robot_hat import *
except ImportError:
    print("ImportError: not Raspberry Pi.")
    from picarx_improved import Picarx
    from sim_robot_hat import *

import sensors.grayscale as Grayscale
import sensors.ultrasonic as Ultrasonic

from rossros.rossros import Bus, Producer, ConsumerProducer, Consumer, runConcurrently, Timer


if __name__ == '__main__':

    print("grayscale sensor for line folloing and ultrasonic sensor for breaks.")
    car = Picarx()

    ########################## Timer for killing threads #########################################
    
    timeout = Bus(initial_message= False, name="timeout")
    killingTimer = Timer(output_buses = timeout,  # buses that receive the countdown value
                         duration=5,  # how many seconds the timer should run for (0 is forever)
                         delay=0,  # how many seconds to sleep for between checking time
                         termination_buses=Bus(False, "Default timer termination bus"),
                         name="killbus")


    ########################## Sensor bus generation section #############################

    # creating grayscale sensor, interpreter and controller and busses
    sensor = Grayscale.GSSensor(None)
    interpreter = Grayscale.GSInterpreter()
    controller = Grayscale.GSController(None)
    gray_input_bus = Bus(initial_message=[0, 0, 0], name="gray_input_bus")
    gray_output_bus = Bus(initial_message=0.0, name="gray_output_bus")

    # ultrasonic sensor reader and busses
    ultrasonic = Ultrasonic.Ultrsonic(Pin('D0'),Pin('D1'),75)
    ultrasonic_input = Bus(initial_message=80, name="ultrasonic_input")
    ultrasonic_output = Bus(initial_message=False, name="ultrasonic_output")


    ############################ Producers, consumers and controllers #######################

    # grayscale producer, control and consumer
    grayscale_producer = Producer(sensor.read, output_busses=gray_input_bus,delay=0.5,name="grayscale_producer")
    grayscale_control = ConsumerProducer(interpreter.process,
                                         input_busses=gray_in_bus,output_busses=gray_out_bus,
                                         delay=1.0,
                                         termination_buses = timeout,
                                         name="grayscale_control"
                                         )
    grayscale_consumer = Consumer(controller.steer,
                                  input_busses=gray_out_bus, 
                                  delay=1.0,
                                  termination_buses = timeout,
                                  name="grayscale_consumer")

    
    
    ultrasonic_producer = Producer(ultrasonic.read,
                                   output_busses=ultrasonic_input,
                                   delay=0.3,
                                   termination_buses = timeout,
                                   name="ultrasonic_producer")

    ultrasonic_control = ConsumerProducer(ultrasonic.process,
                                          input_busses=ultrasonic_input,
                                          output_busses=ultrasonic_output, 
                                          delay=0.5,
                                          termination_buses = timeout,
                                          name="ultrasonic_control")
    ultrasonic_consumer = Consumer(ultrasonic.control,
                                   input_busses=ultrasonic_output, 
                                   delay=0.5,
                                   termination_buses = timeout,
                                   name="ultrasonic_consumer")

    ############################################### Concurrent execution ########################

    runConcurrently([
        # grayscale
        grayscale_producer,
        grayscale_control,
        grayscale_consumer,

        # ultrasonic
        ultrasonic_producer,
        ultrasonic_control,
        ultrasonic_consumer]
    )

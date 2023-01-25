try:
    from robot_hat import Pin, PWM, Servo
except ImportError:
    print("using sim functions")
    from sim_robot_hat import Pin, PWM, Servo
import atexit

class Motors(object):
    
    def __init__(self):

        self.dir_servo_pin ='P2' 
        self.motor_pins =['D4', 'D5', 'P12', 'P13']
        self.PERIOD = 4095
        self.PRESCALER = 10
        self.TIMEOUT = 0.02

        # dir servo
        self.dir_servo_pin = Servo(PWM(self.dir_servo_pin)) 
        self.dir_cal_value = -3
        self.dir_servo_pin.angle(self.dir_cal_value)
        
        # motors
        self.left_dir_pin = Pin(self.motor_pins[0])
        self.right_dir_pin = Pin(self.motor_pins[1])
        self.left_pwm_pin = PWM(self.motor_pins[2])
        self.right_pwm_pin = PWM(self.motor_pins[3])
        self.motor_direction_pins = [self.left_dir_pin, self.right_dir_pin]
        self.motor_speed_pins = [self.left_pwm_pin, self.right_pwm_pin]
        self.cali_dir_value = [1, 1]
        self.cali_speed_value = [0, 0]
        self.dir_current_angle = 0
        for pin in self.motor_speed_pins:
            pin.period(self.PERIOD)
            pin.prescaler(self.PRESCALER)
        atexit.register(self.clear)
    
    def motor_speed_calibration(self,value):
        self.cali_speed_value = value
        if value < 0:
            self.cali_speed_value[0] = 0
            self.cali_speed_value[1] = abs(self.cali_speed_value)
        else:
            self.cali_speed_value[0] = abs(self.cali_speed_value)
            self.cali_speed_value[1] = 0

    def motor_direction_calibration(self, motor, value):
        motor -= 1
        if value == 1:
            self.cali_dir_value[motor] = 1
        elif value == -1:
            self.cali_dir_value[motor] = -1

    def dir_servo_angle_calibration(self,value):
        self.dir_cal_value = value
        self.dir_servo_pin.angle(value)
    
    def set_motor_speed(self, motor,speed):
        motor -= 1
        if speed >= 0:
            direction = 1 * self.cali_dir_value[motor]
        elif speed < 0:
            direction = -1 * self.cali_dir_value[motor]
        speed = abs(speed)
        if speed != 0:
            speed = int(speed /2 ) + 50
        speed = speed - self.cali_speed_value[motor]
        if direction < 0:
            self.motor_direction_pins[motor].high()
            self.motor_speed_pins[motor].pulse_width_percent(speed)
        else:
            self.motor_direction_pins[motor].low()
            self.motor_speed_pins[motor].pulse_width_percent(speed)

    def set_dir_servo_angle(self,value):
        self.dir_current_angle = value
        angle_value  = value + self.dir_cal_value
        self.dir_servo_pin.angle(angle_value)

    def forward(self,speed):
        current_angle = self.dir_current_angle
        abs_current_angle = abs(current_angle)
        if abs_current_angle > 40:  abs_current_angle = 39
        factor = abs_current_angle * (3.14/180) * self.Rw *(10.5 - abs_current_angle/1.3)
        print(factor, speed)
        if current_angle >= 0:
            self.set_motor_speed(1, speed+factor)
            self.set_motor_speed(2, -speed+factor) 
        else:
            self.set_motor_speed(1, speed-factor)
            self.set_motor_speed(2, -1*(speed+factor))

    def backward(self,speed):
        current_angle = self.dir_current_angle
        abs_current_angle = abs(current_angle)
        if abs_current_angle > 40:  abs_current_angle = 39
        factor = abs_current_angle * (3.14/180) * self.Rw *(10.5 - abs_current_angle/1.3)
        print(factor, speed)
        if current_angle >= 0:
            self.set_motor_speed(2, speed+factor)
            self.set_motor_speed(1, -speed+factor) 
        else:
            self.set_motor_speed(2, speed-factor)
            self.set_motor_speed(1, -1*(speed+factor))

    def stop(self):
        self.set_motor_speed(1, 0)
        self.set_motor_speed(2, 0)

    def clear(self):
        self.stop()
        self.set_dir_servo_angle(0)
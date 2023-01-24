#!/usr/bin/python3

from picarx import Picarx
import time

def delay(t):
	t = t/1000
	time.sleep(t)

class Manuver():
	def __init__(self):
		self.picar = Picarx()

	def emergency_stop(self):
		self.picar.stop()

	def delay_stop(self):
		delay(1000)
		self.picar.stop()
		self.picar.set_dir_servo_angle(0)

	def Moveit(self, order = "forward"):
		if order == "forward":
			self.picar.always_forward(75)
			self.delay_stop()
		elif order == "backward":
			self.picar.always_backward(75)
			self.delay_stop()
		elif order == "forward left":
			self.picar.set_dir_servo_angle(-30)
			self.picar.forward(75)
			self.delay_stop()
		elif order == "forward right":
			self.picar.set_dir_servo_angle(30)
			self.picar.forward(75)
			self.delay_stop()
		elif order == "backward left":
			self.picar.set_dir_servo_angle(-30)
			self.picar.backward(75)
			self.delay_stop()
		elif order == "backward right":
			self.picar.set_dir_servo_angle(30)
			self.picar.backward(75)
			self.delay_stop()
		elif order == 'stop':
			self.picar.stop()


	def parallel_park(self, order = "left"):
		if order == "left":
			self.picar.set_dir_servo_angle(0)
			self.picar.forward(75)
			self.picar.set_dir_servo_angle(-30)
			delay(1000)
			self.picar.set_dir_servo_angle(30)
			self.delay_stop()

		elif order == "right":
			self.picar.set_dir_servo_angle(0)
			self.picar.forward(75)
			self.picar.set_dir_servo_angle(30)
			delay(1000)
			self.picar.set_dir_servo_angle(-30)
			self.delay_stop()

	def kturning(self, order="left"):
		if order == "left":
			self.Moveit("forward left")

			self.picar.set_dir_servo_angle(30)
			self.picar.backward(50)
			self.delay_stop()

			self.picar.set_dir_servo_angle(-20)
			self.picar.forward(75)
			delay(1000)
			self.picar.set_dir_servo_angle(0)
			self.delay_stop()

		elif order == "right":
			self.Moveit("forward right")

			self.picar.set_dir_servo_angle(-30)
			self.picar.backward(50)
			self.delay_stop()

			self.picar.set_dir_servo_angle(20)
			self.picar.forward(75)
			delay(1000)
			self.picar.set_dir_servo_angle(0)
			self.delay_stop()

if __name__ == "__main__":
	manuver = Manuver()
	actions = ["forward right", "backward right", "forward left", "backward left","forward", "backward"]
	dirs = ["left", "right"]
	while True:
		usr_input = int(input("Choose maneuver: \n1] move in direction \n2] park in direction \n3] k-turn \n4] stop \n5] exit \n"))
		manuver.emergency_stop()
		if usr_input == 1:
			print("choose: forward right, backward right, forward left, backward left, forward")
			inp = input("direction to move: ")
			if inp in actions:
				manuver.Moveit(inp)
			else:
				continue

		elif usr_input == 2:
			inp = input("Parallel park left or right:")
			if inp in dirs:
				manuver.parallel_park(inp)
			else:
				continue

		elif usr_input == 3:
			inp = input("k-turning left or right: ")
			if inp in dirs:
				manuver.kturning(inp)
			else:
				continue

		elif usr_input == 4:
			manuver.emergency_stop()

		elif usr_input == 5:
			manuver.emergency_stop()
			break
		else:
			print("Choose an action...: ")

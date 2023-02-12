import numpy as np
from busses import DataBus
import threading
import cv2
import time
import logging
import sys

try:
    sys.path.append('/home/hlab/RobotSystems/picarx')
    from picarx import Picarx
    from robot_hat import *
    from picamera import PiCamera
except ImportError:
    print("ImportError: not Raspberry Pi.")
    from picarx_improved import Picarx
    from sim_robot_hat import PiCamera

SensorOutput = np.array

class CamSensor:
    def __init__(self):
        self.cam = PiCamera()
        self.out = np.empty(
            (self.cam.resolution.height,
             self.cam.resolution.width, 3),
            dtype=np.uint8)

    def read(self, bus: DataBus, event: threading.Event):
        while not event.is_set():
            self.cam.capture(self.out, "bgr")
            #writing in bus
            if event.is_set(): 
                return
            bus.write_data({'frame': self.out})
    
    def cam_read(self):
        self.cam.capture(self.out, "bgr")
        return self.out

class CamInterpreter:

    def __init__(self) -> None:
        self.stop_now = False
        self.curr_steering_angle = 90
        
    def detect_lane(self, frame):
        edges = self.detect_edges(frame)
        line_segments = self.detect_line_segments(edges)
        lane_lines = self.average_slope_intercept(frame, line_segments)
        theta = self.steer(lane_lines, frame)
        return theta, self.stop_now

    def steer(self, lane_lines, frame):
        if len(lane_lines) == 0:
            logging.error('No lane lines detected, nothing to do.')
            self.stop_now = True
            return 90
        new_steering_angle = self.compute_steering_angle(frame, lane_lines)
        self.curr_steering_angle = self.stabilize_steering_angle(self.curr_steering_angle, new_steering_angle, len(lane_lines))
        return curr_steering_angle

    def detect_edges(self, frame):
        # filter for blue lane lines #sorted
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([85, 210, 60])
        upper_blue = np.array([110, 255, 170])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        edges = cv2.Canny(mask, 250, 300)
        return edges

    def detect_line_segments(self, cropped_edges):
        # tuning min_threshold, minLineLength, maxLineGap is a trial and error process by hand
        rho = 1  # precision in pixel, i.e. 1 pixel
        angle = np.pi / 180  # degree in radian, i.e. 1 degree
        min_threshold = 10  # minimal of votes
        line_segments = cv2.HoughLinesP(cropped_edges, rho, angle, min_threshold, np.array([]), minLineLength=8,
                                        maxLineGap=4)

        return line_segments


    def average_slope_intercept(self, frame, line_segments):
        lane_lines = []
        if line_segments is None:
            logging.info('No line_segment segments detected')
            return lane_lines
        height, width, _ = frame.shape
        left_fit = []
        right_fit = []

        boundary = 1/3
        left_region_boundary = width * (1 - boundary)  # left lane line segment should be on left 2/3 of the screen
        right_region_boundary = width * boundary # right lane line segment should be on left 2/3 of the screen

        for line_segment in line_segments:
            for x1, y1, x2, y2 in line_segment:
                if x1 == x2:
                    logging.info('skipping vertical line segment (slope=inf): %s' % line_segment)
                    continue
                fit = np.polyfit((x1, x2), (y1, y2), 1)
                slope = fit[0]
                intercept = fit[1]
                if slope < 0:
                    if x1 < left_region_boundary and x2 < left_region_boundary:
                        left_fit.append((slope, intercept))
                else:
                    if x1 > right_region_boundary and x2 > right_region_boundary:
                        right_fit.append((slope, intercept))

        left_fit_average = np.average(left_fit, axis=0)
        if len(left_fit) > 0:
            lane_lines.append(make_points(frame, left_fit_average))

        right_fit_average = np.average(right_fit, axis=0)
        if len(right_fit) > 0:
            lane_lines.append(make_points(frame, right_fit_average))

        return lane_lines


    def compute_steering_angle(self, frame, lane_lines):
        """ Find the steering angle based on lane line coordinate
            We assume that camera is calibrated to point to dead center
        """
        if len(lane_lines) == 0:
            logging.info('No lane lines detected, do nothing')
            return -90

        height, width, _ = frame.shape
        if len(lane_lines) == 1:
            x1, _, x2, _ = lane_lines[0][0]
            x_offset = x2 - x1
        else:
            _, _, left_x2, _ = lane_lines[0][0]
            _, _, right_x2, _ = lane_lines[1][0]
            camera_mid_offset_percent = 0.02 # 0.0 means car pointing to center, -0.03: car is centered to left, +0.03 means car pointing to right
            mid = int(width / 2 * (1 + camera_mid_offset_percent))
            x_offset = (left_x2 + right_x2) / 2 - mid

        # find the steering angle, which is angle between navigation direction to end of center line
        y_offset = int(height / 2)

        angle_to_mid_radian = math.atan(x_offset / y_offset)  # angle (in radian) to center vertical line
        angle_to_mid_deg = int(angle_to_mid_radian * 180.0 / math.pi)  # angle (in degrees) to center vertical line
        steering_angle = angle_to_mid_deg + 90  # this is the steering angle needed by picar front wheel

        logging.debug('new steering angle: %s' % steering_angle)
        return steering_angle


    def stabilize_steering_angle(self, curr_steering_angle, new_steering_angle, num_of_lane_lines, max_angle_deviation_two_lines=5, max_angle_deviation_one_lane=1):
        """
        Using last steering angle to stabilize the steering angle
        This can be improved to use last N angles, etc
        if new angle is too different from current angle, only turn by max_angle_deviation degrees
        """
        if num_of_lane_lines == 2 :
            # if both lane lines detected, then we can deviate more
            max_angle_deviation = max_angle_deviation_two_lines
        else :
            # if only one lane detected, don't deviate too much
            max_angle_deviation = max_angle_deviation_one_lane
        
        angle_deviation = new_steering_angle - curr_steering_angle
        if abs(angle_deviation) > max_angle_deviation:
            stabilized_steering_angle = int(curr_steering_angle
                                            + max_angle_deviation * angle_deviation / abs(angle_deviation))
        else:
            stabilized_steering_angle = new_steering_angle
        return stabilized_steering_angle



class CamController:

    def __init__(self, scale: float = 1.0) -> None:
        self.car = Picarx()
        self.scale = 1.3
        self.interpreter = CamInterpreter()

    def update(self, bus: DataBus, event: threading.Event):
        while not event.is_set() or not bus.length() == 0:
            frame = bus.read()['frame']
            print ("Controller:: calculating steering angle.")
            # get angle from frame
            angle, stopper = self.interpreter.detect_lane(frame)
            # transform and steer
            car.forward(0.5)
            if stopper: car.stop()
            car.set_dir_servo_angle(self.scale*angle)
    
    def steer(self, angle):
        print("Controller:: steering.")
        car.set_dir_servo_angle(self.scale*angle)
#!/usr/bin/python3
# coding=utf8


import sys
sys.path.append('/home/pi/ArmPi/')
import cv2
import time
import Camera
import threading
from LABConfig import *
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *
import atexit

import concurrent.futures
from readerwriterlock import rwlock

#Global setup
coordinate = {
    'red':   (-15 + 0.5, 12 - 0.5, 1.5),
    'green': (-15 + 0.5, 6 - 0.5,  1.5),
    'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
} 
pos = [0,0,0]
chosenColor = 'None'  
roia = False 
start = False
z_r = coordinate['red'][2]


class ColorSensing():

    def __init__(self):
        self.count = 0
        self.center_list = []
        self.start_count_t1 = True
        self.t1 = 0
        #Camera setup
        self.my_camera = Camera.Camera()
        self.second_camera = Camera.Camera()
        self.my_camera.camera_open(2)
        self.second_camera.camera_open(0)
        atexit.register(self.cleanup)
        
        #Size of camera view
        self.resolution = (640, 480)

        self.roi = ()
        self.last_x, self.last_y = 0, 0
        self.get_roi = False
        self.target_color = ('red', 'blue', 'green')
        self.detect_color = ""
        self.range_rgb = {
            'red': (0, 0, 255),
            'blue': (255, 0, 0),
            'green': (0, 255, 0),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
        }
        self.color_list = []
        
    
    def processImage(self, img):
        global roia 
        global start
        
        img_copy = img.copy()
        img_h, img_w = img.shape[:2]
        cv2.line(img, (0, int(img_h / 2)), (img_w, int(img_h / 2)), (0, 0, 200), 1)
        cv2.line(img, (int(img_w / 2), 0), (int(img_w / 2), img_h), (0, 0, 200), 1)
        frame_resize = cv2.resize(img_copy, self.resolution, interpolation=cv2.INTER_NEAREST)
        frame_gb = cv2.GaussianBlur(frame_resize, (11, 11), 11)
        #If a recognized object is detected in an area, the area is detected until there is no
        self.get_roi = roia
        start_pickup = start
        if self.get_roi and not start_pickup:
            self.get_roi = False
            roia = self.get_roi
            frame_gb = getMaskROI(frame_gb, self.roi, self.resolution)     
        frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # Convert image to LAB space
        return frame_lab
   
        
    def getMaxValidAreas(self, frame_lab):
        global chosenColor 
        self.color_area_max = None
        max_area = 0
        area_max = 0
        areaMaxContour = 0
        areaMaxContour_max = 0
        for i in color_range:
            if i in self.target_color:
                self.detect_color = i
                chosenColor = self.detect_color
                frame_mask = cv2.inRange(frame_lab, color_range[self.detect_color][0], color_range[self.detect_color][1])  #Perform bitwise operations on original image and mask
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((6, 6), np.uint8))  # Open operation
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((6, 6), np.uint8))  # Close operation
                contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  #Find the outline
                areaMaxContour, area_max = self.getAreaMaxContour(contours)  # Find the largest contour
                if areaMaxContour is not None:
                    if area_max > max_area:#find the largest area
                        max_area = area_max
                        self.color_area_max = i
                        areaMaxContour_max = areaMaxContour 
                   
        return areaMaxContour_max, max_area
    
    
    def getLocation(self, areaMaxContour_max, max_area, img):
        if max_area > 2500:  # Have found the largest area
            self.rect = cv2.minAreaRect(areaMaxContour_max)
            box = np.int0(cv2.boxPoints(self.rect))
            roi = getROI(box) #Get roi area
            get_roi = True
            img_centerx, img_centery = getCenter(self.rect, roi, self.resolution, square_length)  # Get the coordinates of the center of the block
            self.world_x, self.world_y = convertCoordinate(img_centerx, img_centery, self.resolution) #Convert to real world coordinates
        
            cv2.drawContours(img, [box], -1, self.range_rgb[self.color_area_max], 2)
            cv2.putText(img, '(' + str(self.world_x) + ',' + str(self.world_y) + ')', (min(box[0, 0], box[2, 0]), box[2, 1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.range_rgb[self.color_area_max], 1) #draw center point
            self.decisionMaking()
            #track = True
        return img
    
    
    def main_color(self):
        if self.color_area_max == 'red':  #红色最大
            color = 1
        elif self.color_area_max == 'green':  #绿色最大
            color = 2
        elif self.color_area_max == 'blue':  #蓝色最大
            color = 3
        else:
            color = 0
        return color
    
    
    def decisionMaking(self):
        global chosenColor
        global start
        global pos
        
        self.last_x, self.last_y = self.world_x, self.world_y
        distance = math.sqrt(pow(self.world_x - self.last_x, 2) + pow(self.world_y - self.last_y, 2)) #Compare the last coordinates to determine whether to move
            
        color = self.main_color()
        self.color_list.append(color)

        if distance < 0.5:
            self.count += 1
            self.center_list.extend((self.world_x, self.world_y))
            if self.start_count_t1:
                self.start_count_t1 = False
                self.t1 = time.time()
            if time.time() - self.t1 > 1:
                self.rotation_angle = self.rect[2] 
                self.start_count_t1 = True
                self.world_X, self.world_Y = np.mean(np.array(self.center_list).reshape(self.count, 2), axis=0)
                self.center_list = []
                self.count = 0
                self.start_pick_up = True
                pos = [self.world_X, self.world_Y, self.rotation_angle]
                start = self.start_pick_up
        else:
            self.t1 = time.time()
            self.start_count_t1 = True
            self.center_list = []
            self.count = 0

        if len(self.color_list) == 3:  #If there are multiple colors on the board
            # take the average
            color = int(round(np.mean(np.array(self.color_list))))
            self.color_list = []
            if color == 1:
                self.detect_color = 'red'
                self.draw_color = self.range_rgb["red"]
                chosenColor = self.detect_color
            elif color == 2:
                self.detect_color = 'green'
                self.draw_color = self.range_rgb["green"]
                chosenColor = self.detect_color
            elif color == 3:
                self.detect_color = 'blue'
                self.draw_color = self.range_rgb["blue"]
                chosenColor = self.detect_color
            else:
                self.detect_color = 'None'
                self.draw_color = self.range_rgb["black"]
                chosenColor = self.detect_color
        else:
            self.draw_color = (0, 0, 0)
            self.detect_color = "None" 
            chosenColor = self.detect_color
         
    
    def run(self, img):
        frame_lab = self.processImage(img)
        areaMaxContour, area_max = self.getMaxValidAreas(frame_lab)
        return self.getLocation(areaMaxContour, area_max, img)
        
        
    def start(self):
        while True:
            img = self.my_camera.frame
            second_img = self.second_camera.frame
            #print(img.shape)
            
            #frame_gb = cv2.GaussianBlur(frame_resize, (11, 11), 11)
            if img is not None and second_img is not None:
                frame_resize = cv2.resize(second_img, self.resolution, interpolation=cv2.INTER_NEAREST)
                frame = img.copy()
                Frame = self.run(frame)           
                cv2.imshow('Top', Frame)

                cv2.imshow('Bottom', frame_resize)
                key = cv2.waitKey(1)
                if key == 27:
                    break
        self.cleanup()
     
            
    def cleanup(self):  
        self.my_camera.camera_close()
        cv2.destroyAllWindows()
    
        
    def getAreaMaxContour(self, contours):
        contour_area_temp = 0
        contour_area_max = 0
        area_max_contour = None

        for c in contours: 
            contour_area_temp = math.fabs(cv2.contourArea(c))  
            if contour_area_temp > contour_area_max:
                contour_area_max = contour_area_temp
                if contour_area_temp > 300:  
                    area_max_contour = c

        return area_max_contour, contour_area_max 


class ArmMove():
    def __init__(self) -> None:

        #Initializing move servos and position
        self.servo1 = 500
        self.AK = ArmIK()
        self.dz = 2.5

        self.unreachable = False 
        atexit.register(self.cleanup)


    def colorPalletizing(self):
        #Get targets from Bus
        global pos
        global chosenColor
        global start
        global roia
        global z_r 
        
        coordinate = {
            'red':   (-15 + 0.5, 12 - 0.5, 1.5),
            'green': (-15 + 0.5, 6 - 0.5,  1.5),
            'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
        }
        
        while True:    
            global pos
            global chosenColor
            global start
            global roia
            global z_r
            
            #Get targets from Bus
            world_X = pos[0]
            world_Y = pos[1]
            
            #Get color from Bus
            detect_color = chosenColor
            
            start_pick_up = start 
          
            
            if detect_color != 'None' and start_pick_up:  
                self.set_rgb(detect_color)
                self.setBuzzer(0.1)
                z = z_r
                z_r += self.dz
                if z == 2 * self.dz + coordinate['red'][2]:
                    z_r = coordinate['red'][2]
                if z == coordinate['red'][2]:  
                    move_square = True
                    time.sleep(3)
                    move_square = False
                result = self.AK.setPitchRangeMoving((world_X, world_Y, 7), -90, -90, 0)  
                if result == False:
                    unreachable = True
                else:
                    unreachable = False
                    time.sleep(result[2]/1000)

                    self.pickUp()
                    
                    self.dropOffStack(z)

                    self.initMove() 
                    time.sleep(1.5)

                    detect_color = 'None'
                    get_roi = False
                    roia = get_roi
                    start_pick_up = False
                    start = start_pick_up
                    chosenColor = detect_color
                    self.set_rgb(detect_color)


    #Picks up the cube
    def pickUp(self):
        global pos
        world_X = pos[0]
        world_Y = pos[1]
        rotation_angle = pos[2]
        
        servo2_angle = getAngle(world_X, world_Y, rotation_angle) 
        Board.setBusServoPulse(1, self.servo1 - 280, 500)  
        Board.setBusServoPulse(2, servo2_angle, 500)
        time.sleep(0.5)

        self.AK.setPitchRangeMoving((world_X, world_Y, 1.5), -90, -90, 0, 1000)
        time.sleep(1.5)

        Board.setBusServoPulse(1, self.servo1, 500)  
        time.sleep(0.8)

        Board.setBusServoPulse(2, 500, 500)
        self.AK.setPitchRangeMoving((world_X, world_Y, 12), -90, -90, 0, 1000)  
        time.sleep(0.5)
        
     #Drops off cube   
    
    #Drop off cube
    def dropOff(self):
        global chosenColor
        detect_color = chosenColor
        
        result = self.AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0)   
        time.sleep(result[2]/1000)
                            
        servo2_angle = getAngle(coordinate[detect_color][0], coordinate[detect_color][1], -90)
        Board.setBusServoPulse(2, servo2_angle, 500)
        time.sleep(0.5)

        self.AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], coordinate[detect_color][2] + 3), -90, -90, 0, 500)
        time.sleep(0.5)
                            
        self.AK.setPitchRangeMoving((coordinate[detect_color]), -90, -90, 0, 1000)
        time.sleep(0.8)

        Board.setBusServoPulse(1, self.servo1 - 200, 500)  #Open gripper
        time.sleep(0.8)

        self.AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0, 800)
        time.sleep(0.8)
   
    #Drop Off in Stack
    def dropOffStack(self, z):
        global chosenColor
        detect_color = chosenColor
        
        self.AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0, 1500) 
        time.sleep(1.5)
                            
        servo2_angle = getAngle(coordinate[detect_color][0], coordinate[detect_color][1], -90)
        Board.setBusServoPulse(2, servo2_angle, 500)
        time.sleep(0.5)

        self.AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], z + 3), -90, -90, 0, 500)
        time.sleep(0.5)
                        
        self.AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], z), -90, -90, 0, 1000)
        time.sleep(0.8)

        Board.setBusServoPulse(1, self.servo1 - 200, 500)  
        time.sleep(1)

        self.AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0, 800)
        time.sleep(0.8)

    #Runs color sorting code
    def colorSort(self):
        #Get targets from Bus
        global pos
        global chosenColor
        global start
        global roia
        
        coordinate = {
            'red':   (-15 + 0.5, 12 - 0.5, 1.5),
            'green': (-15 + 0.5, 6 - 0.5,  1.5),
            'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
        }
        
        while True:    
            global pos
            global chosenColor
            global start
            global roia
            #Get targets from Bus
            world_X = pos[0]
            world_Y = pos[1]
            rotation_angle = pos[2]
            
            #Get color from Bus
            detect_color = chosenColor
            
            start_pick_up = start 
            print(chosenColor,start)
            if detect_color != 'None' and start_pick_up:  #If it detects that the block has not moved for a while, start gripping 
                #If no runtime parameter is given, it is automatically calculated and returned by the result
                self.set_rgb(detect_color)
                self.setBuzzer(0.1)
                result = self.AK.setPitchRangeMoving((world_X, world_Y, 7), -90, -90, 0)  
                if result == False:
                    self.unreachable = True
                else:
                    self.unreachable = False
                    time.sleep(result[2]/1000) #If the specified location can be reached, get the running time

                    self.pickUp()
                    
                    self.dropOff()
                    
                    self.initMove()
                      
                    time.sleep(1.5)

                    detect_color = 'None'
                    get_roi = False
                    roia = get_roi
                    start_pick_up = False
                    start = start_pick_up
                    chosenColor = detect_color
                    self.set_rgb(detect_color)
            
            
    def initMove(self):
        Board.setBusServoPulse(1, self.servo1 - 50, 300)
        Board.setBusServoPulse(2, 500, 500)
        self.AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)
    
    
    def cleanup(self):
        Board.setBusServoPulse(1, self.servo1 - 70, 300)
        time.sleep(0.5)
        Board.setBusServoPulse(2, 500, 500)
        self.AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)
        time.sleep(1.5)
    #time.sleep(0.01)
    
    def setBuzzer(self, timer):
        Board.setBuzzer(0)
        Board.setBuzzer(1)
        time.sleep(timer)
        Board.setBuzzer(0)
    
    def set_rgb(self, color):
        print("started fuction? ")
        if color == "red":
            Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
            Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
            Board.RGB.show()
        elif color == "green":
            Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
            Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
            Board.RGB.show()
        elif color == "blue":
            Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
            Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
            Board.RGB.show()
        else:
            Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
            Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
            Board.RGB.show()
            




sensor = ColorSensing()
arm = ArmMove()

th = threading.Thread(target=arm.colorSort)
th.setDaemon(True)
th.start()    

sensor.start()

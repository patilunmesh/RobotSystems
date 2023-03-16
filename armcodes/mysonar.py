import RPi.GPIO as GPIO
import time
def Ultra():
    while(True):
        GPIO.setmode(GPIO.BCM)
        pinTrigger = 22
        pinEcho = 24

        print("starting")
 
        GPIO.setup(pinTrigger, GPIO.OUT)
        GPIO.setup(pinEcho, GPIO.IN)
        GPIO.output(pinTrigger, False)
        print("settup")
        time.sleep(2)
 
        GPIO.output(pinTrigger, True)
        time.sleep(0.00001)
        GPIO.output(pinTrigger, False)
 

        while GPIO.input(pinEcho)==0:
          pulseStartTime = time.time()
        while GPIO.input(pinEcho)==1:
            pulseEndTime = time.time()
 
        pulseDuration = pulseEndTime - pulseStartTime
        distance = round(pulseDuration * 17150, 2)
     
        print("Distance: %.2f cm" % (distance))
        GPIO.cleanup()
        

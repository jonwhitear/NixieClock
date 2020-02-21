#!/usr/bin/python

# Nixie Clock
#  
#
#

import RPi.GPIO as GPIO
import time
import datetime
import sys
import subprocess
import random
import threading
# Accomodate both python 2 and 3 queue modules.
try:
   import queue
except ImportError:
   import Queue as queue

from flask import Flask, jsonify

lock = threading.Lock()
CommandQueue = queue.Queue(10)

# LED pin mapping.
red = 27
green = 17
blue = 22

red_dutycycle = 50
blue_dutycycle = 50
green_dutycycle = 50

start = datetime.datetime.now()
t_now = datetime.datetime.now()

hours = 0
tenshours = 0
minutes = 0
tensminutes = 0
seconds = 0
tensseconds = 0
microseconds = 0
on_delay = 0.01
off_delay = 0

exitflag = 0
mode = 'normal'

class Driver:
   #Common base class for driver chips

   def __init__(self, PinA, PinB, PinC, PinD):
      self.PinA = PinA
      self.PinB = PinB
      self.PinC = PinC
      self.PinD = PinD

      GPIO.setup(self.PinA, GPIO.OUT)
      GPIO.setup(self.PinB, GPIO.OUT)
      GPIO.setup(self.PinC, GPIO.OUT)
      GPIO.setup(self.PinD, GPIO.OUT)

      GPIO.output(self.PinA, 0) #Turn off the pin
      GPIO.output(self.PinB, 0)
      GPIO.output(self.PinC, 0)
      GPIO.output(self.PinD, 0)

   def displayDriver(self):
      return 'Pins A : ', self.PinA,  ', B: ', self.PinB, 'C : ', self.PinC,  ', D: ', self.PinD

   def setDigit(self, digit):
      self.digit = digit

      if self.digit == 0:
           A, B, C, D = 0, 0, 0, 0
      elif self.digit == 1:
           A, B, C, D = 0, 0, 0, 1
      elif self.digit == 2:
           A, B, C, D = 0, 0, 1, 0
      elif self.digit == 3:
           A, B, C, D = 0, 0, 1, 1
      elif self.digit == 4:
           A, B, C, D = 0, 1, 0, 0
      elif self.digit == 5:
           A, B, C, D = 0, 1, 0, 1
      elif self.digit == 6:
           A, B, C, D = 0, 1, 1, 0
      elif self.digit == 7:
           A, B, C, D = 0, 1, 1, 1
      elif self.digit == 8:
           A, B, C, D = 1, 0, 0, 0
      elif self.digit == 9:
           A, B, C, D = 1, 0, 0, 1
      else:
           #set ABCD to turn off nixie
           A, B, C, D = 1, 1, 1, 1

      #Set the GPIO pins to the BCD output
      GPIO.output(self.PinA, A)
      GPIO.output(self.PinB, B)
      GPIO.output(self.PinC, C)
      GPIO.output(self.PinD, D)

def displayDigits(d1, d2, d3, d4, d5, d6, on_delay, off_delay):
    #Display the six digits passed
    MyDriver[0].setDigit(d6)            #Set Seconds
    MyDriver[1].setDigit(d4)            #Set Minutes
    MyDriver[2].setDigit(d2)            #Set Hours
    GPIO.output(MyAnodePin[0], 1)       # switch tube on
    time.sleep(on_delay)
    GPIO.output(MyAnodePin[0], 0)       # switch tube off
    time.sleep(off_delay)
    
    MyDriver[0].setDigit(d5)            #Set Tens Seconds
    MyDriver[1].setDigit(d3)            #Set Tens Minutes
    MyDriver[2].setDigit(d1)            #Set Tens Hours
    GPIO.output(MyAnodePin[1], 1)       # switch tube on
    time.sleep(on_delay)
    GPIO.output(MyAnodePin[1], 0)       # switch tube off
    time.sleep(off_delay)

def randomiser(duration,on_delay,off_delay):
    #display random digits for "duration" seconds, each digit displayed for 0.2 seconds

    outerloops = int(duration / 0.1)
    innerloops = int((0.1 / (on_delay + off_delay))/2)

    for x in range (0, outerloops):
        d1 = random.randint(0,9)
        d2 = random.randint(0,9)
        d3 = random.randint(0,9)
        d4 = random.randint(0,9)
        d5 = random.randint(0,9)
        d6 = random.randint(0,9)
        for y in range (0, innerloops):
            displayDigits(d1,d2,d3,d4,d5,d6,on_delay,off_delay)

class varThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        print("VAR thread: run")
        global t_now
        global hours
        global tenshours
        global minutes
        global tensminutes
        global seconds
        global tensseconds
        global microseconds
        
        global red_dutycycle
        global blue_dutycycle
        global green_dutycycle
        
        global on_delay
        global off_delay
        global mode
        # Repeatedly get the current time of day and set vars.
        # (the time retrieved will be in UTC; you'll want to adjust for your
        # time zone)
        while not exitflag:
            t_now = datetime.datetime.now()
            #set vars
            hours = t_now.hour % 10
            tenshours = (t_now.hour - hours) / 10
            minutes = t_now.minute % 10
            tensminutes = (t_now.minute - minutes ) /10
            seconds = t_now.second % 10
            tensseconds = (t_now.second - seconds ) /10
            microseconds = t_now.microsecond

            lock.acquire()
            if not CommandQueue.empty():
                print ("Getting type, key, value from command queue")
                type, key, value = CommandQueue.get()

                if type == 'mode':
                    print ("Setting mode to ", key)
                    if key == 'lowpower':
                        mode = value
                        red_dutycycle = 0
                        blue_dutycycle = 0
                        green_dutycycle = 0
                        off_delay = 0.005
                        on_delay = 0.005
                    elif key == 'normal':
                        mode = value
                        off_delay = 0
                        on_delay = 0.01

                elif (type == 'dutycycle') and (mode == 'lowpower'):
                    print ("Ignoring dutycycle setting, as mode is lowpower")
                                    
                elif (type == 'dutycycle') and (mode == 'normal'):
                    print ("Setting", key, "duty cycle/s to ", value)
                    if key == 'red':
                        red_dutycycle = value
                    elif key == 'blue':
                        blue_dutycycle = value
                    elif key == 'green':
                        green_dutycycle = value
                    else: #all
                        red_dutycycle = value
                        blue_dutycycle = value
                        green_dutycycle = value

                elif type == 'delay':
                    print ("Setting", key, "delay to ", value)
                    if key == 'on':
                        on_delay = value
                    else: #off
                        off_delay = value
 
            lock.release()
            time.sleep(0.1)

class backlightThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        print("BACKLIGHT thread: run")

        global red_dutycycle
        global blue_dutycycle
        global green_dutycycle
        
        # Set up LED outputs using PWM so we can control individual brightness.
        RED = GPIO.PWM(red, 50)
        GREEN = GPIO.PWM(green, 50)
        BLUE = GPIO.PWM(blue, 50)
        
        RED.start(0)
        GREEN.start(0)
        BLUE.start(0)
        
        while not exitflag:
            RED.ChangeDutyCycle(red_dutycycle)
            BLUE.ChangeDutyCycle(blue_dutycycle)
            GREEN.ChangeDutyCycle(green_dutycycle)
            time.sleep(1)

class displayThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        print("DISPLAY thread: run")
        global t_now
        global on_delay
        global off_delay
        while not exitflag:
            #if we're at 30 seconds past the minute, call a 2 second randomiser
            if t_now.second == 30:
                randomiser(1,on_delay,off_delay)
            # display the time
            displayDigits(tenshours,hours,tensminutes,minutes,tensseconds,seconds,on_delay,off_delay)

def main():
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        print("Raspberry Pi Board Revision: ", GPIO.RPI_INFO['P1_REVISION'])
        print("GPIO Library Version: ", GPIO.VERSION)

        global MyDriver
        MyDriver=[0 for j in range(3)]
        MyDriver[2] = Driver(19,6,13,26)
        MyDriver[1] = Driver(20,12,16,21)
        MyDriver[0] = Driver(8,24,25,7)

        global MyAnodePin
        MyAnodePin=[0 for j in range(2)]
        MyAnodePin[0]=2
        MyAnodePin[1]=3

        GPIO.setup(MyAnodePin[0], GPIO.OUT)
        GPIO.setup(MyAnodePin[1], GPIO.OUT)
        
        GPIO.setup(red, GPIO.OUT)
        GPIO.setup(green, GPIO.OUT)
        GPIO.setup(blue, GPIO.OUT)

        print("Driver pin assignments:")
        print("Driver 0: ", MyDriver[0].displayDriver())
        print("Driver 1; ", MyDriver[1].displayDriver())
        print("Driver 2; ", MyDriver[2].displayDriver())

        #Startup display loop - cycle through digits, displaying each for delay 0.5s
        loops = int((0.5 / (on_delay + off_delay))/2)
        for x in range (0, 10):
            print("Displaying digit: ", x)
            for y in range (0, loops):
                displayDigits(x,x,x,x,x,x,on_delay,off_delay)

        #Done with init
        #spin up threads
        
        # Create new threads
        myVarThread = varThread()
        myBacklightThread = backlightThread()
        myDisplayThread = displayThread()

        # Start new Threads
        myVarThread.start()
        myBacklightThread.start()
        myDisplayThread.start()
        
        #start the web api (in the main thread)
        print("MAIN thread:")
        app = Flask(__name__)

        @app.route('/')
        def hello_world():
            print ("Returning version info")
            return "Python Nixie Clock, version 200221.1"
        
        @app.route('/dutycycle/<string:colour>/<int:dutycycle>', methods=['PUT'])
        def putdutycycle(colour,dutycycle):
            if (colour == 'red') or (colour == 'blue') or (colour == 'green') or (colour == 'all'):
                print ("Acquiring lock")
                lock.acquire()
                if not CommandQueue.full():
                    print ("Adding colour, duty cycle to command queue")
                    CommandQueue.put(('dutycycle',colour,dutycycle))
                    print ("Releasing lock")
                    lock.release()
                    return jsonify({colour: dutycycle})
                else:
                    print ("Releasing lock")
                    lock.release()
                    print ("Command queue full... failing")
                    abort(404)
            else:
                abort(404)

        @app.route('/delay/<string:type>/<float:delay>', methods=['PUT'])
        def putdelay(type, delay):
            if (type == 'on') or (type == 'off'):
                print ("Acquiring lock")
                lock.acquire()
                if not CommandQueue.full():
                    print ("Adding type, delay to command queue")
                    CommandQueue.put(('delay',type,delay))
                    print ("Releasing lock")
                    lock.release()
                    return jsonify({type: delay})
                else:
                    print ("Releasing lock")
                    lock.release()
                    print ("Command queue full... failing")
                    abort(404)
            else:
                abort(404)

        @app.route('/mode/<string:mode>', methods=['PUT'])
        def putmode(mode):
            if (mode == 'lowpower') or (mode == 'normal'):
                print ("Acquiring lock")
                lock.acquire()
                if not CommandQueue.full():
                    print ("Adding mode to command queue")
                    CommandQueue.put(('mode',mode,0))
                    print ("Releasing lock")
                    lock.release()
                    return jsonify({'mode': mode})
                else:
                    print ("Command queue full... failing")
                    abort(404)
                    print ("Releasing lock")
                    lock.release()

        app.run(debug=False, host='0.0.0.0')

    except KeyboardInterrupt:
        print('Interrupted')
        exitflag = 1
        # Wait for all threads to complete
        myVarThread.join()
        myBacklightThread.join()
        myDisplayThread.join()
        print ("Exiting Main Thread")

    finally:
        # Cleanup GPIO on exit. Otherwise, you'll get a warning next time toy
        # configure the pins.
        GPIO.cleanup()

if __name__ == "__main__":
    print("NixieClock is being run directly")
    main()
else:
    print("NixieClock is being imported into another module")


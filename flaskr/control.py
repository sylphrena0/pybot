import io #used to store frames
import picamera #camera module for RPi camera
import logging #self-explainatory
import json #to get data from js
import socketserver #may be unused?
import RPi.GPIO as GPIO
from threading import Condition #used for frame storage setup
from adafruit_motorkit import MotorKit #motor control lib
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, Flask, Response #web framework imports
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db,close_db #access to database

#define the motorkit controls on init
kit = MotorKit()

#this class is to enable streaming - it essentially makes an object where we can store frames without saving them to a file - modified from a template
class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

#sets the blueprint for this code
bp = Blueprint('control', __name__)

def updateSettings():
    db = get_db()
    settings_list = db.execute('SELECT * FROM settings WHERE id = 1') #grab settings data
    #settings['throttle'] settings['nightvision'] settings['buttoncontrol'] settings['keycontrol'] settings['resolution'] 

    #set nightvision mode
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(24, GPIO.OUT)
    if settings['nightvision'] == 1:
        GPIO.output(24, GPIO.LOW)
        print("Nightvision enabled")
    else:
        GPIO.output(24, GPIO.HIGH)
        print("Nightvision disabled")


updateSettings()

#defines a settings function which is called when /getsettings is accessed
@bp.route('/getsettings')
@login_required
def getsettings():
    db = get_db()
    settings = db.execute( 'SELECT throttle, nightvision, keycontrol, buttoncontrol, resolution FROM settings WHERE id = 1' ).fetchone()
    data = []
    data.append(list(settings))
    print(data)
    updateSettings()
    return Response(json.dumps(data))

#defines a settings function which is called when /changesetting is accessed
@bp.route('/changesetting')
@login_required
def changesetting():
    command = request.args.get('command') #stores command arguement from get requests
    value = request.args.get('value')

    db = get_db()
    print("UPDATE settings SET {} = {} WHERE id = 1".format(command,value))
    db.execute("UPDATE settings SET {} = {} WHERE id = 1".format(command,value))
    db.commit()    

    return Response("nothing")

#defines a movement function which is called when /movement is accessed
@bp.route('/move')
@login_required #important, this requires a login so bad actors cannot control the car without logging in
def move():
    speed = 0.8
    command = request.args.get('command') #stores command arguement from get requests

    #parse commands from request and set speed
    if command == 'forward':
        throttleL, throttleR = speed, speed
    elif command == 'backward':
        throttleL, throttleR = -speed, -speed
    elif command == 'stop':
        throttleL, throttleR = 0, 0
    elif command == 'rightTurn':
        direction = request.args.get('direction')
        if speed >= 0.8:
            throttleL = speed
            throttleR = speed - 0.5
        elif speed < 0.8:
            throttleL = speed + 0.2
            throttleR = speed - 0.2

        if direction == 'forward': #checks if the car is already going forward. If so, no change is needed
            pass
        elif direction == 'backward': #checks if going backward and changes direction if so
            throttleL *= -1
            throttleR *= -1
        '''elif direction == 'stationary': #if no direction, the car doesn't move during the turn - doesn't work with current motors and wheels - turnSpeed = 0.4
            throttleL = turnSpeed
            throttleR = -turnSpeeMesh data file. Mesh data files are provided. Create a folder called “data” in your output directory. Download and install the maze data text files in that folder. Your maze program should be compiled and exported as a runnable jar file called maze.jar. An example invocation is as follows:d'''

    elif command == 'leftTurn':
        direction = request.args.get('direction') #no set directions assumes the direction is forward

        if speed >= 0.8:
            throttleL = speed - 0.5
            throttleR = speed
        elif speed < 0.8:
            throttleL = speed - 0.2
            throttleR = speed + 0.2

        if direction == 'forward': #checks if the car is already going forward. If so, no change is needed
            pass
        elif direction == 'backward': #checks if going backward and changes direction if so
            throttleL *= -1
            throttleR *= -1
        '''else: #if no direction, the car doesn't move during the turn
            throttleL = -turnSpeed
            throttleR = turnSpeed'''
    kit.motor1.throttle = throttleL
    kit.motor2.throttle = -throttleL
    kit.motor3.throttle = throttleR
    kit.motor4.throttle = -throttleR
    return ("nothing")

#defines the index page and controls buttons. control buttons should be removed!
@bp.route('/', methods=['GET','POST'])
@login_required
def index():
    if request.method == 'POST':
        if request.form.get('forward') == 'VALUE1':
            print("worked1")
        elif  request.form.get('back') == 'VALUE2':
            print("worked2")
        else:
            pass # unknown
    elif request.method == 'GET':
        return render_template('control/index.html', form=request.form)
    return render_template('control/index.html')

#defines the settings page, currently blank. contains depreciated code from tutorial
@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():
    return render_template('control/settings.html')

#defines the function that generates our frames
@login_required
def genFrames():
    buffer = StreamingOutput()
    while True:
        with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
            #Uncomment the next line to change your Pi's Camera rotation (in degrees)
            #camera.rotation = 90
            
            camera.capture(buffer, format='jpeg', use_video_port=True, thumbnail = None, quality = 25)
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + buffer.frame + b'\r\n')

#defines the route that will access the video feed and call the feed function
@bp.route('/video_feed')
@login_required
def video_feed():
    return Response(genFrames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
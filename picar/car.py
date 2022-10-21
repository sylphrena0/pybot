import io #used to store video frames for streaming
from picamera2 import Picamera2 as picamera #used for camera control
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput 
import json #to get data from js
from threading import Condition #used for frame storage setup
from adafruit_motorkit import MotorKit #used for motor control
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, Flask, Response #web framework imports
from werkzeug.exceptions import abort
from picar.user import login_required
from picar.db import get_db, close_db, log #access to database

#define the motorkit controls on init
kit = MotorKit()

#sets the blueprint for this code
bp = Blueprint('car', __name__)

############################################
############### [Home Route] ###############
############################################
#defines the index page and controls buttons. control buttons should be removed!
@bp.route('/', methods=['GET','POST'])
@login_required
def index():
    # if request.method == 'POST':
    #     if request.form.get('forward') == 'VALUE1':
    #         print("worked1")
    #     elif  request.form.get('back') == 'VALUE2':
    #         print("worked2")
    #     else:
    #         pass # unknown
    # elif request.method == 'GET':
    #     return render_template('car/index.html', form=request.form)
    return render_template('car/index.html')

############################################
############# [Movement Route] #############
############################################ 
#defines a movement function which is called when /movement is accessed
@bp.route('/move')
@login_required #important, this requires a login so bad actors cannot control the car without logging in
def move():
    speed = 1
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
            throttleR = -0.5*speed
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
            throttleR = -turnSpeed'''

    elif command == 'leftTurn':
        direction = request.args.get('direction') #no set directions assumes the direction is forward

        if speed >= 0.8:
            throttleL = -0.5*speed
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
    kit.motor1.throttle = -throttleL #left back
    kit.motor2.throttle = throttleL #left front
    kit.motor3.throttle = throttleR #right front
    kit.motor4.throttle = -throttleR #right back
    return ("nothing")

###########################################
############ [Settings Routes] ############
########################################### 
#defines a settings function which is called when /getsettings is accessed
@bp.route('/getsettings')
@login_required
def getsettings():
    db = get_db()
    settings = db.execute( 'SELECT throttle, nightvision, keycontrol, buttoncontrol, resolution FROM settings WHERE id = 1' ).fetchone()
    data = []
    data.append(list(settings))
    print(data)
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

#defines the settings page
@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():
    return render_template('car/settings.html')

############################################
############# [Logging Routes] #############
############################################ 
#defines the logs page
@bp.route('/logs', methods=('GET', 'POST'))
@login_required
def logs():
    if request.method == 'POST':
        db = get_db()
        db.execute("DELETE FROM logging")
        db.commit()
        log("INFO", "Logs cleared!")
    return render_template('car/logs.html')

@bp.route('/getlogs')
@login_required
def getlogs():
    lvl = request.args.get("lvl")
    logging = []
    for log in get_db().execute('SELECT * FROM logging WHERE lvl >= {} ORDER BY id DESC'.format(lvl)):
        logging.append(log['datetime'] + " - " + ["DEBUG","INFO","WARN","ERROR","CRIT"][log['lvl']] + ": " + log['msg'])
    if len(logging) < 1:
        logging = ["No entries found"]
    return Response(json.dumps(logging))

###########################################
######## [Streaming Routes / Code] ########
########################################### 
#using picamera2 - modified from picamera2 documentation:
#https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
#https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py


class StreamingOutput(io.BufferedIOBase): #makes a memory object where we can store frames without saving them to a file 
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

#defines the function that generates our frames
@login_required
def genFrames():
    global camera, buffer #camera must be global to allow photos while streaming
    try: camera #checks if camera is initialized yet
    except: #if not, initializes camera:
        log("INFO", "Initializing Camera")
        camera = picamera()
        buffer = StreamingOutput()
        camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
        camera.start_recording(JpegEncoder(), FileOutput(buffer))

    while True:
        with buffer.condition:
            buffer.condition.wait()
            frame = buffer.frame
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
            
#defines the route that will access the video feed and call the feed function
@bp.route('/video_feed')
@login_required
def video_feed():
    return Response(genFrames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@bp.route('/take_photo')
def take_photo():
    request = camera.capture_request()
    request.save("main", "test.jpg")
    request.release()
    return Response('Captured!')
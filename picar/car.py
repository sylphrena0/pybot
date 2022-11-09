import io #used to store video frames for streaming
import json #to get data from js
import schedule #for recording loop
import pandas as pd
from os import mkdir
from datetime import datetime
from threading import Thread #for recording loop
from picamera2 import Picamera2 as picamera #used for camera control
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput 
from time import sleep
from threading import Condition #used for frame storage setup
from adafruit_motorkit import MotorKit #used for motor control
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, Flask, Response #web framework imports
from werkzeug.exceptions import abort
from picar.user import login_required
from picar.db import get_db, close_db, log #access to database

#sets the blueprint for this code
bp = Blueprint('car', __name__)

############################################
############### [Home Route] ###############
############################################
#defines the index page and controls buttons. control buttons should be removed!
@bp.route('/', methods=['GET','POST'])
@login_required
def index():
    return render_template('car/index.html')

############################################
############# [Movement Route] #############
############################################ 
#define the motorkit controls on init
kit = MotorKit()
kit.motor1.throttle, kit.motor2.throttle, kit.motor3.throttle, kit.motor4.throttle = 0, 0, 0, 0 #reset motors on init
active_list = [] 
first = None
#defines a movement function which is called when /movement is accessed
@bp.route('/move')
@login_required #important, this requires a login so bad actors cannot control the car without logging in
def move():
    global first, active_list, left_throttle, right_throttle

    #TODO: TRIALS 
    #     - for every call after first recorded keystroke, take a picture and record keystate
    #     - make javascript call this function every x miliseconds if during a trial? if reasonable?

    #grab arguments from client:
    arrow = request.args.get('arrow')
    state = request.args.get('state')
    record = request.args.get('record')
    speed = 1

    # if state == "down" and arrow in active_list: #ingore event if duplicate keydown makes it through (key combinations make it through js code)
    #     return ("Duplicate event!")

    #preprocessing attributes before changing throttles
    if first is None and state == "down": 
        first = arrow #set first flag if first
    if state == "down": 
        active_list.append(arrow)
    elif state == "up" and arrow in active_list: #don't remove arrow if already removed (duplicate keyups can happen with combinations)
        active_list.remove(arrow)

    print(active_list) #useful for debugging
    active = len(active_list) #count active
    if state == "up" and active != 0: #if keyup, we need to redefine the current arrow
        arrow = active_list[0] if arrow == first else first

    #changing throttles
    if active == 0: #if no arrows are active
        left_throttle, right_throttle = 0, 0 #stop
    elif active == 1:
        if arrow == "up":
            left_throttle, right_throttle = speed, speed
        if arrow == "down":
            left_throttle, right_throttle = -speed, -speed
        if arrow == "left":
            left_throttle = -0.5*speed
            right_throttle = speed
        if arrow == "right":
            left_throttle = speed
            right_throttle = -0.5*speed
    elif active == 2:
        if "up" in active_list:
            if "left" in active_list:
                left_throttle = -0.5*speed
                right_throttle = speed
            elif "right" in active_list:
                left_throttle = speed
                right_throttle = -0.5*speed
            elif first == "up": #second key is down
                left_throttle, right_throttle = speed, speed #go forward, ignoring down arrow
            elif first == "down": #second key is down
                left_throttle, right_throttle = -speed, -speed #go backward, ignoring up arrow
        elif "down" in active_list:
            if "left" in active_list:
                left_throttle = 0.5*speed
                right_throttle = -speed
            elif "right" in active_list:
                left_throttle = -speed
                right_throttle = 0.5*speed
    
    #if user presses 3 or more keys, we do nothing (we also do not stop exisiting movement)

    kit.motor1.throttle = -left_throttle #left back
    kit.motor2.throttle = left_throttle #left front
    kit.motor3.throttle = right_throttle #right front
    kit.motor4.throttle = -right_throttle #right back

    if record == "true":
        with open(trialDirectory + '/commands.txt', 'w') as output:
            commands.loc[len(commands.index)] = [str(datetime.now().timestamp() - start.timestamp()), arrow, state] 

    return ("Success!")

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
    except NameError: #if not, initializes camera:
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

##########################################
############ [Recording Code] ############
##########################################

@bp.route('/initialize_trial') #called every second during a trial
def begin_trial():
    global trialDirectory, start, commands
    commands = pd.DataFrame(columns=('time','arrow','state'))
    start = datetime.now()
    trialDirectory = "trials/trial_%Y-%m-%d_%H-%M-%S"
    mkdir(start.strftime(trialDirectory))
    return Response(f'Created trial directory!')

@bp.route('/capture_image') #called every second during a trial
def record():
    request = camera.capture_request()
    request.save("main", trialDirectory + datetime.now().strftime(f'/{str(datetime.now().timestamp() - start.timestamp())}.jpg')) #name should be time in s since start.
    request.release()
    return Response('Captured!')

@bp.route('/save_trial') #called every second during a trial
def save_trial():
    commands.to_csv(trialDirectory + '/commands.csv')
    return Response(f'Saved recording!')
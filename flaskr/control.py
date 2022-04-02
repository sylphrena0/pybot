import io #used to store frames
import picamera #camera module for RPi camera
import logging #self-explainatory
import json #to get data from js
import socketserver #may be unused?
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

#defines a settings function which is called when /getsettings is accessed
@bp.route('/getsettings')
def getsettings():
    #db = get_db()
    settings = db.execute( 'SELECT throttle, nightvision, buttoncontrol, keycontrol, resolution FROM settings WHERE id = 1' )
    #close_db()
    print(settings)
    return Response(settings)

#defines a movement function which is called when /movement is accessed
@bp.route('/move')
def move():
    speed = 0.8
    command = request.args.get('command')

    #parse commands from request and set speed
    if command == 'forward':
        throttleL, throttleR = speed, speed
    elif command == 'backward':
        throttleL, throttleR = -speed, -speed
    elif command == 'stop':
        throttleL, throttleR = 0, 0
    elif command == 'rightTurn':
        direction = request.args.get('direction')
        if speed >= 0.7:
            throttleL = speed
            throttleR = speed - 0.4
        elif speed < 0.7:
            throttleL = speed + 0.3
            throttleR = speed

        if direction == 'backward': #checks if going backward or forward and changes direction 
            throttleL *= -1
            throttleR *= -1

    elif command == 'leftTurn':
        direction = request.args.get('direction')
        if speed >= 0.7:
            throttleL = speed - 0.4
            throttleR = speed
        elif speed < 0.7:
            throttleL = speed
            throttleR = speed + 0.3

        if direction == 'backward': #checks if going backward or forward and changes direction
            throttleL *= -1
            throttleR *= -1

    kit.motor1.throttle = throttleL
    kit.motor2.throttle = throttleL
    kit.motor3.throttle = throttleR
    kit.motor4.throttle = throttleR
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
def video_feed():
    return Response(genFrames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
import io
import picamera
import logging
import socketserver 
from threading import Condition
from adafruit_motorkit import MotorKit
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, Flask, Response
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db

kit = MotorKit()

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

bp = Blueprint('control', __name__)

@bp.route('/forward')
def forward():
    throttle = 0.4
    kit.motor1.throttle = throttle
    kit.motor2.throttle = throttle
    kit.motor3.throttle = throttle
    kit.motor4.throttle = throttle
    return ("nothing")

@bp.route('/back')
def back():
    throttle = -0.4
    kit.motor1.throttle = throttle
    kit.motor2.throttle = throttle
    kit.motor3.throttle = throttle
    kit.motor4.throttle = throttle
    return ("nothing")

@bp.route('/stop')
def stop():
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    kit.motor3.throttle = 0
    kit.motor4.throttle = 0
    return ("nothing")

@bp.route('/left')
def left():
    try:
        if throttle >= 0.6:
            leftThrottle = throttle
            rightThrottle = throttle - 0.2
        elif throttle < 0.6:
            leftThrottle = throttle + 0.2
            rightThrottle = throttle
        print("Moving at throttle",throttle)
        kit.motor1.throttle = leftThrottle
        kit.motor2.throttle = leftThrottle
        kit.motor3.throttle = rightThrottle
        kit.motor4.throttle = rightThrottle
        return ("nothing")
    except:
        print("Undefined Throttle")
        return ("nothing")

@bp.route('/right')
def right():
    try:
        if throttle >= 0.6:
            leftThrottle = throttle - 0.2
            rightThrottle = throttle
        elif throttle < 0.6:
            leftThrottle = throttle
            rightThrottle = throttle + 0.2
        print("Moving at throttle",throttle)
        kit.motor1.throttle = leftThrottle
        kit.motor2.throttle = leftThrottle
        kit.motor3.throttle = rightThrottle
        kit.motor4.throttle = rightThrottle
        return ("nothing")
    except:
        print("Undefined Throttle")
        return ("nothing")

@bp.route('/', methods=['GET','POST'])
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

@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            return redirect(url_for('control.index'))

    return render_template('control/settings.html')

def genFrames():
    buffer = StreamingOutput()
    while True:
        with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
            #Uncomment the next line to change your Pi's Camera rotation (in degrees)
            #camera.rotation = 90
            
            camera.capture(buffer, format='jpeg', use_video_port=True, thumbnail = None, quality = 25)
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + buffer.frame + b'\r\n')

@bp.route('/video_feed')
def video_feed():
    return Response(genFrames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
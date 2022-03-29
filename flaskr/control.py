import io
import picamera
import logging
import socketserver 
from threading import Condition
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, Flask, Response
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db

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

@bp.route('/', methods=['POST'])
def index():
    if request.method == 'POST':
        if request.form.get('action1') == 'VALUE1':
            print("worked1")
        elif  request.form.get('action2') == 'VALUE2':
            print("worked2")
        else:
            pass # unknown
    elif request.method == 'GET':
        return render_template('index.html', form=form)
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
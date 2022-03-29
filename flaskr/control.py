import io
import picamera
import logging
import socketserver 
from threading import Condition
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, Flask, Response
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('control', __name__)

@bp.route('/')
def index():
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
    while True:
        with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
            #Uncomment the next line to change your Pi's Camera rotation (in degrees)
            #camera.rotation = 90

            frame = null
            camera.capture(frame, format='jpeg')
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@bp.route('/video_feed')
def video_feed():
    return Response(genFrames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
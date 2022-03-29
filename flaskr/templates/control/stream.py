import io
import picamera
import logging
import socketserver
import os 
from threading import Condition

def genFrames():
    while True:
        with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
            output = StreamingOutput()
            #Uncomment the next line to change your Pi's Camera rotation (in degrees)
            #camera.rotation = 90

            frame = null
            camera.capture(frame, format='jpeg')
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(genFrames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
#camera.stop_recording()

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
from flaskr.db import get_db #access to database

def getsettings():
    db = get_db()
    settings = db.execute( 'SELECT throttle, nightvision, buttoncontrol, keycontrol, resolution FROM settings WHERE id = 1' )
    db.close()
    print(settings)
    return Response(settings)

print(getsettings())
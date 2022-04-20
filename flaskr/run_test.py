import io #used to store frames
import logging #self-explainatory
import json #to get data from js
import socketserver #may be unused?
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, Flask, Response #web framework imports
from werkzeug.exceptions import abort
import sqlite3

def get_db():
    db = sqlite3.connect(
        '/home/sylphrena/Documents/picar/instance/flaskr.sqlite',
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = sqlite3.Row

    return db

def close_db(e=None):
    db = g.pop('db', None)

    db.close()


#defines a settings function which is called when /getsettings is accessed
db = get_db()
settings = db.execute( 'SELECT throttle, nightvision, buttoncontrol, keycontrol, resolution FROM settings WHERE id = 1' )
#close_db()
#print(settings)
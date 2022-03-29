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

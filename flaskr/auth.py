import functools
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/register', methods=('GET', 'POST'))
@login_required #cannor create new user unless already registered!
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                print(generate_password_hash(password)) #temp
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.route('/user', methods=('GET', 'POST'))
@login_required
def user():
    if request.method == 'POST':
        oldpassword = request.form['oldpassword']
        password = request.form['newpassword']
        user_id = session["user_id"]

        db = get_db()

        error = None

        if not oldpassword or not password: #check that the form is complete
            error = 'All fields are required.'

        user_data = db.execute('SELECT * FROM user WHERE id = {}'.format(user_id,)).fetchone() #grab user data

        if user_data is None: #catch database errors
            error = 'Database error.'
        elif not check_password_hash(user_data['password'], oldpassword): #check that the old password is correct
            error = 'Incorrect password.'

        print("UPDATE user SET password = '{}' WHERE id = '{}'".format(generate_password_hash(password),user_id))
        db.execute("UPDATE user SET password = '{}' WHERE id = '{}'".format(generate_password_hash(password),user_id)) #update password
        db.commit()

    return render_template('auth/user.html')
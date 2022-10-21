import os
from flask import Flask
from . import db, user, car
import traceback

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='TeAFL25daZuasgs8l768Cx9Tm3cKZl7JEvKvu7gne4dNRKNFVATMuAN3Us3z5NKTd',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    try:
        db.init_app(app)
        app.register_blueprint(user.bp)
        app.register_blueprint(car.bp)
        app.add_url_rule('/', endpoint='index')
    except Exception:
        print(traceback.format_exc()) #sadly, logging doesn't work at this point in application loading
    
    #from .templates.control import stream

    return app

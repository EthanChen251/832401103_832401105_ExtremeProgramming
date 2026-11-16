from flask import Flask
from .accounts import api


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(api)
    return app

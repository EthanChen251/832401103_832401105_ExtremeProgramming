from flask import Flask

from .accounts import api as accounts_api
from .routes import api as contacts_api


def create_app(config=None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    if config is not None:
        app.config.update(config)
    app.register_blueprint(accounts_api)
    app.register_blueprint(contacts_api)
    return app

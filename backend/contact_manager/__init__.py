from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask import Flask

from . import db
from .routes import api


def create_app(config: Mapping[str, Any] | None = None) -> Flask:
    """创建 Flask 应用，初始化本地数据库并注册通讯录接口。"""
    app = Flask(__name__, instance_relative_config=True)
    database_path = Path(app.instance_path) / "contacts.sqlite3"
    app.config.from_mapping(DATABASE=database_path)
    if config is not None:
        app.config.update(config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(db.close_db)
    with app.app_context():
        db.init_db()

    app.register_blueprint(api)
    return app

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, request, current_app
from flask_babel import Babel, lazy_gettext as _l
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_required
from flask_migrate import Migrate
from flask_moment import Moment
from flask_pagedown import PageDown
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES, \
    ARCHIVES, DATA

from flaskext.markdown import Markdown

from config import Config, is_heroku

db = SQLAlchemy()
session = db.session
migrate = Migrate()

login = LoginManager()
login.login_view = "auth.login"
login.login_message = _l("Please log into access this page.")

bootstrap = Bootstrap()
moment = Moment()
babel = Babel()

photos = UploadSet("photos", IMAGES)

backups = UploadSet("backups", DATA)
archives = UploadSet("archives", ARCHIVES)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.view_functions["static"] = login_required(app.send_static_file)
    app.config.from_object(config_class)
    app.jinja_env.globals.update(is_heroku=is_heroku)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.administration import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix="/administration")

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.festival import bp as festival_bp
    app.register_blueprint(festival_bp)

    from app.purchase import bp as purchase_bp
    app.register_blueprint(purchase_bp)

    from app.chronicle import bp as chronicle_bp
    app.register_blueprint(chronicle_bp, url_prefix="/chronicle")

    if not app.debug and not app.testing:
        if is_heroku():
            print("Detected target platform Heroku, switch logging to stream handler")
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists("logs"):
                os.mkdir("logs")
            file_handler = RotatingFileHandler("logs/myfestival.log",
                                               maxBytes=10 * 10 * 1024,
                                               backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s: "
                "%(message)s [in %(pathname)s:%(lineno)d]"))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("MyFestival startup")

    configure_uploads(app, {photos, backups, archives})
    # patch_request_class(app, size=3 * 1024 * 1024)

    Markdown(app)
    PageDown(app)

    return app


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config["LANGUAGES"])


# must be imported here, otherwise the app won't launch
# must be imported to register related stuff with Flask
from app import models  # noqa E402
from app.main import routes  # noqa E402

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


def is_heroku() -> bool:
    platform = os.environ.get("PLATFORM")
    heroku_ = platform == "HEROKU"
    return heroku_


def get_db_url() -> str:
    db_url: str = os.environ.get("DATABASE_URL")
    if is_heroku():
        print("Detected target platform Heroku, replace >postgres://< with >postgresql://<")
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url


class Config(object):
    # in production the string must be hard to guess!
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"

    db_url = get_db_url()
    sqlite = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_DATABASE_URI = db_url or sqlite

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PLATFORM = os.environ.get("PLATFORM")

    POSTS_PER_PAGE = 25

    ITEMS_PER_PAGE = 50

    LANGUAGES = ["en", "de"]

    STATIC_DIR = os.path.join(basedir,
                              "app",
                              "static")

    UPLOADED_PHOTOS_DEST = os.path.join(STATIC_DIR, "photos")
    UPLOADED_BACKUPS_DEST = os.path.join(STATIC_DIR, "backups")
    UPLOADED_ARCHIVES_DEST = os.path.join(STATIC_DIR, "archives")

    # chronicle >>
    MAX_CONTENT_LENGTH = 1024 * 1024

    UPLOAD_EXTENSIONS = [".jpg", ".png", ".gif"]

    UPLOAD_PATH = os.path.join(STATIC_DIR, "chronicles")

    # << chronicle

    # export shoppinglist >>

    SHOPPING_LIST_PATH = os.path.join(STATIC_DIR, "shopping_lists")

    # << export shoppinglist

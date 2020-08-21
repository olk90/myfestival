import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    # in production the string must be hard to guess!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    db_url = os.environ.get('DATABASE_URL')
    sqlite = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_DATABASE_URI = db_url or sqlite

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    POSTS_PER_PAGE = 25

    ITEMS_PER_PAGE = 50

    LANGUAGES = ['en', 'de']

    UPLOADED_PHOTOS_DEST = os.path.join(basedir,
                                        'app',
                                        'static',
                                        'profile_photos')

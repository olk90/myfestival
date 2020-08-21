from config import Config
import unittest

from app import create_app, db, cli


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        cli.register(self.app)

        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

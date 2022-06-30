import os

from hashlib import md5
import unittest

from app import db, session
from app.containers import UserAccessLevel
from app.models import User
from test_config import BaseTestCase


class UserModelCase(BaseTestCase):

    def test_initial_user(self):
        runner = self.app.test_cli_runner()
        result = runner.invoke(args=["install", "admin"])

        user = session.query(User).filter_by(username="admin").first()
        self.assertIsNotNone(user)
        self.assertEquals(UserAccessLevel.OWNER, user.access_level)

        password = os.environ.get("INITIAL_ADMIN_PW")
        self.assertTrue(user.check_password(password))

    def test_password_hashing(self):
        user = User(username="susan")
        user.set_password("cat")
        self.assertFalse(user.check_password("dog"))
        self.assertTrue(user.check_password("cat"))

    def test_default_access_level(self):
        db.session.add(User(username="Palpatine",
                            registration_code="93c191CC"))
        db.session.commit()

        user = session.query(User).filter_by(username="Palpatine").first()
        self.assertEquals(UserAccessLevel.USER, user.access_level)

    def test_avatar(self):
        u = User(username="john", registration_code="93c191CC")
        avatar_url = md5("93c191CC".encode("utf-8")).hexdigest()
        self.assertEqual(
            u.avatar(128),
            ("https://www.gravatar.com/avatar/{}?d=identicon&s=128").format(
                avatar_url))


if __name__ == "__main__":
    unittest.main(verbosity=2)

import pyotp

from app.models import User


def generate_key_for_user(user: User) -> str:
    key = pyotp.random_base32()
    user.otp_secret = key
    return key


def delete_key_for_user(user: User):
    user.otp_secret = None


def generate_uri(user: User) -> str:
    key: str = user.otp_secret
    username: str = user.username
    totp = pyotp.totp.TOTP(key)
    uri = totp.provisioning_uri(name=username, issuer_name="MyFestival")
    return uri


def validate_token(user: User, token: str) -> bool:
    key: str = user.otp_secret
    totp = pyotp.totp.TOTP(key)
    return totp.verify(token)

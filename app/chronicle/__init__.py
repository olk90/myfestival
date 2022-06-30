from flask import Blueprint


bp = Blueprint("chronicle", __name__)


from app.chronicle import forms, routes # noqa

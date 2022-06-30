from flask import Blueprint


bp = Blueprint("festival", __name__)


from app.festival import forms, routes # noqa

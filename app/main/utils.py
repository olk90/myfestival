import os
from functools import wraps

from flask import flash, abort, Response
from flask_babel import _

from config import is_heroku


def not_heroku(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if is_heroku():
            flash(_("This feature is not available on this platform"))
            abort(403)

        return func(*args, **kwargs)

    return decorated_view


def send_file(file_path: str, filename: str, c_type: str):
    with open(file_path, "rb") as f:
        data = f.readlines()
    os.remove(file_path)
    return Response(data, headers={
        "Content-Type": c_type,
        "Content-Disposition": "attachment; filename=%s;" % filename
    })

from functools import wraps

from flask import flash, abort
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

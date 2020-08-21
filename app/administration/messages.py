from flask_babel import _


suspension_failed = \
    _('Suspension failed. The owner was informed of this traitorous act.')


suspended = \
    _('Cannot promote suspended user to admin.')


def suspend_first(username):
    return _('%(username)s must be suspended first.', username=username)

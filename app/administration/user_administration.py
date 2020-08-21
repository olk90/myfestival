from flask import current_app as ca

import app.models as m
from app import db
from app.festival.logic import remove_partner


def disable_user(user):
    ca.logger.info('Disable >{}<'.format(user))
    # remove user from all festivals
    festivals = m.Festival.query.join(m.participants) \
        .filter(m.participants.c.participant_id == user.id).all()
    for f in festivals:
        f.leave(user)

    # remove user from all invoices
    invoices = m.Invoice.query.join(m.sharers) \
        .filter(m.sharers.c.sharer_id == user.id).all()
    for p in invoices:
        p.remove_sharer(user)

    remove_partner(user)
    user.username = None
    user.password_hash = None
    db.session.commit()

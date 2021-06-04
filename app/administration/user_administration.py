from flask import current_app as ca

from app.models import Festival, Invoice, sharers, participants
from app import session
from app.festival.logic import remove_partner


def disable_user(user):
    ca.logger.info('Disable >{}<'.format(user))
    # remove user from all festivals
    festivals = session.query(Festival).join(participants) \
        .filter(participants.c.participant_id == user.id).all()
    for f in festivals:
        f.leave(user)

    # remove user from all invoices
    invoices = session.query(Invoice).join(sharers) \
        .filter(sharers.c.sharer_id == user.id).all()
    for p in invoices:
        p.remove_sharer(user)

    remove_partner(user)
    user.username = None
    user.password_hash = None
    session.commit()

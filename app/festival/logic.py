from flask_login import current_user

from app import db, session
from app.containers import FestivalUpdateInfo
from app.models import Transfer, User, participants as prts, sharers as shrs


def get_partner_selection():
    result = [(-1, '')]
    partners = session.query(User).filter(User.id != current_user.id)
    for p in partners:
        result.append((p.id, p.username))
    return result


def remove_partner(user):
    user.partner_id = None
    partner = session.query(User).filter_by(partner_id=current_user.id).first()
    if partner:
        partner.partner_id = None
    db.session.commit()


def get_participants(festival_id):
    """Returns a list of tuples, do not use to get the corresponding users!"""
    result = []
    participants = session.query(User).join(prts) \
        .filter(prts.c.festival_id == festival_id).all()
    for p in participants:
        result.append((p.id, p.username))
    return result


def get_sharers(invoice_id):
    """Returns a list of tuples, do not use to get the corresponding users!"""
    result = []
    sharers = session.query(User).join(shrs) \
        .filter(shrs.c.invoice_id == invoice_id).all()
    for s in sharers:
        result.append((s.id, s.username))
    return result


def load_participants_from_db(festival_id):
    return session.query(User) \
        .join(prts) \
        .filter(prts.c.festival_id == festival_id).all()


def get_next_payer(receiver, payers):
    partner = session.query(User).filter_by(partner_id=receiver.id).first()
    if partner in payers:
        return partner
    else:
        without_partner = list(filter(lambda p: p.partner_id is None, payers))
        with_partner = list(filter(lambda p: p.partner_id is not None, payers))
        if len(without_partner) > 0:
            return without_partner[0]
        else:
            return with_partner[0]


def calculate_shares(festival):
    participants = get_participants(festival.id)
    for p in participants:
        user = session.query(User).get(p[0])
        user.dept = 0.0

    for p in festival.invoices:
        share = round(p.amount / p.sharers.count(), 2)
        for s in p.sharers:
            s.dept = round(s.dept + share, 2)
        p.creditor.dept = round(p.creditor.dept - p.amount, 2)


def calculate_transfers(festival, participants):

    receivers = list(filter(lambda r: (r.dept < 0), participants))

    for r in receivers:
        not_refunded = -r.dept
        while not_refunded > 0:
            # payers = list(filter(lambda r: (r.dept > 0),
            #                      festival.participants))
            payers = list(filter(lambda r: (r.dept > 0), participants))
            next_payer = get_next_payer(r, payers)
            transfer = Transfer(recipient_id=r.id, payer_id=next_payer.id,
                                festival_id=festival.id)
            if next_payer.dept <= not_refunded:
                transfer.amount = next_payer.dept
                not_refunded = round(not_refunded - next_payer.dept, 2)
                next_payer.dept = 0.0
            else:
                transfer.amount = not_refunded
                next_payer.dept = round(next_payer.dept - not_refunded, 2)
                not_refunded = 0.0
            db.session.add(transfer)
    festival.is_closed = True
    db.session.commit()


def close_festival(festival):
    participants = load_participants_from_db(festival.id)
    calculate_shares(festival)
    calculate_transfers(festival, participants)
    festival.update_info = FestivalUpdateInfo.festival_closed


def reopen_festival(festival):
    transfers = session.query(Transfer).filter_by(festival_id=festival.id).all()
    for t in transfers:
        db.session.delete(t)
    festival.is_closed = False
    festival.update_info = FestivalUpdateInfo.festival_reopened

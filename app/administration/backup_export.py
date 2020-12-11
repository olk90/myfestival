
from alembic.migration import MigrationContext
from flask import current_app as ca
from flask import jsonify
from sqlalchemy import create_engine

import app.models as m
from app.festival.logic import get_participants, get_sharers


def get_version_number():
    db_url = ca.config['SQLALCHEMY_DATABASE_URI']
    engine = create_engine(db_url)
    connection = engine.connect()

    context = MigrationContext.configure(connection)
    current_rev = context.get_current_revision()
    return current_rev


def __build_user_dict(users):
    content = []
    for u in users:
        user = {
            'id': u.id,
            'username': u.username,
            'registration_code': u.registration_code,
            'password_hash': u.password_hash,
            'about_me': u.about_me,
            'last_seen': u.last_seen,
            'access_level': u.access_level,
            'is_suspended': u.is_suspended,
            'partner': u.partner_id,
            'beer_demand': u.beer_demand,
            'mixed_demand': u.mixed_demand,
            'water_demand': u.water_demand,
            'reset_code': u.reset_code
        }
        content.append(user)
    return content


def __build_post_dict(posts):
    content = []
    for p in posts:
        post = {
            'id': p.id,
            'body': p.body,
            'timestamp': p.timestamp,
            'author': p.user_id,
            'is_pinned': p.is_pinned,
            'parent': p.parent_id,
            'internal_time': p.internal_time
        }
        content.append(post)
    return content


def __build_festival_dict(festivals):
    content = []
    for f in festivals:
        participants = get_participants(f.id)
        p_ids = [p[0] for p in participants]
        festival = {
            'id': f.id,
            'title': f.title,
            'info': f.info,
            'creator': f.creator_id,
            'is_closed': f.is_closed,
            'update_info': f.update_info,
            'modified': f.modified,
            'enddate': f.end_date,
            'startdate': f.start_date,
            'participants': p_ids
        }
        content.append(festival)
    return content


def __build_invoice_dict(invoices):
    content = []
    for i in invoices:
        sharers = get_sharers(i.id)
        s_ids = [s[0] for s in sharers]
        invoice = {
            'id': i.id,
            'title': i.title,
            'amount': i.amount,
            'creditor': i.creditor_id,
            'festival': i.festival_id,
            'sharers': s_ids
        }
        content.append(invoice)
    return content


def __build_transfer_dict(transfers):
    content = []
    for t in transfers:
        transfer = {
            'id': t.id,
            'festival': t.festival_id,
            'recipient': t.recipient_id,
            'payer': t.payer_id,
            'amount': t.amount
        }
        content.append(transfer)
    return content


def __build_c_item_dict(c_items):
    content = []
    for c in c_items:
        c_item = {
            'id': c.id,
            'name': c.name,
            'state': c.state,
            'amount': c.amount,
            'requestor': c.requestor_id,
            'pku': c.pku_id,
            'info': c.info
        }
        content.append(c_item)
    return content


def __build_pku_dict(pkus):
    content = []
    for p in pkus:
        pku = {
            'id': p.id,
            'name': p.name,
            'abbreviation': p.abbreviation,
            'internal_name': p.internal_name,
            'delete': p.delete
        }
        content.append(pku)
    return content


def __build_u_item_dict(u_items):
    content = []
    for u in u_items:
        u_item = {
            'id': u.id,
            'name': u.name,
            'owner': u.owner_id,
            'description': u.description
        }
        content.append(u_item)
    return content


def prepare_export():
    ca.logger.info('data export triggered')
    users = m.User.query.all()
    user_output = __build_user_dict(users)

    posts = m.Post.query.all()
    post_output = __build_post_dict(posts)

    festivals = m.Festival.query.all()
    festival_output = __build_festival_dict(festivals)

    invoices = m.Invoice.query.all()
    invoice_output = __build_invoice_dict(invoices)

    transfers = m.Transfer.query.all()
    transfer_output = __build_transfer_dict(transfers)

    c_items = m.ConsumptionItem.query.all()
    c_item_output = __build_c_item_dict(c_items)

    pkus = m.PackagingUnitType.query.all()
    pku_output = __build_pku_dict(pkus)

    u_items = m.UtilityItem.query.all()
    u_item_output = __build_u_item_dict(u_items)

    ca.logger.info('writing dump to file')
    return jsonify({'version_number': get_version_number(),
                    'users': user_output,
                    'posts': post_output,
                    'festivals': festival_output,
                    'invoices': invoice_output,
                    'transfers': transfer_output,
                    'consumptionItems': c_item_output,
                    'packagingUnits': pku_output,
                    'utilityItems': u_item_output})

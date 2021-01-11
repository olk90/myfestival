import json

from flask import current_app as ca
from flask import flash, redirect, url_for
from flask_babel import _

import app.models as m
from app import db
from app.containers import UserAccessLevel
from app.administration.backup_export import get_version_number


def __delete_from_database(items):
    for i in items:
        db.session.delete(i)
    db.session.commit()


def __handle_posts():
    replies = m.Post.query.filter(m.Post.parent_id != None).all()  # noqa: E711
    posts = m.Post.query.filter(m.Post.parent_id == None).all()  # noqa: E711
    __delete_from_database(replies)
    __delete_from_database(posts)


def __handle_items():
    c_items = m.ConsumptionItem.query.all()
    u_items = m.UtilityItem.query.all()
    __delete_from_database(c_items)
    __delete_from_database(u_items)


def __handle_notifications():
    notifications = m.Notification.query.all()
    __delete_from_database(notifications)


def __handle_invoices():
    invoices = m.Invoice.query.all()
    __delete_from_database(invoices)


def __handle_registrations():
    registrations = m.Registration.query.all()
    __delete_from_database(registrations)


def __handle_transfers():
    transfers = m.Transfer.query.all()
    __delete_from_database(transfers)


def __handle_pkus():
    pkus = m.PackagingUnitType.query.all()
    __delete_from_database(pkus)


def __handle_festivals():
    festivals = m.Festival.query.all()
    __delete_from_database(festivals)


def __handle_users():
    other_users = m.User.query.filter(
        m.User.access_level < UserAccessLevel.OWNER).all()
    __delete_from_database(other_users)


def load_backup(backup):
    ca.logger.info('data import triggered')
    content = backup.read()
    data = json.loads(content)
    # abort when the version numbers don't match
    if data['version_number'] != get_version_number():
        ca.logger('import aborted due to version error')
        flash(_('Invalid version number'))
        return redirect(url_for('administration.import_backup'))

    # step 1: delete all entries without incoming dependencies
    ca.logger.info('start deletion of database entries before import')
    __handle_posts()
    __handle_items()
    __handle_notifications()
    __handle_invoices()
    __handle_registrations()
    __handle_transfers()

    # step 2: delete everything that is now deleteable without violation
    __handle_pkus()
    __handle_festivals()

    # finally: delete all users accept the owner
    __handle_users()

    # now read the data from the file and write it to database
    __do_import(data)


def __reset_sequence(sequence, value):
    ca.logger.info('Reset sequence >{}< to value >{}<'.format(sequence, value))
    db.session.execute(
        'ALTER SEQUENCE {} RESTART WITH {}'.format(sequence, value))


def __import_users(users):
    owner = m.User.query.filter_by(access_level=UserAccessLevel.OWNER).first()
    max_id = 1
    for u in users:
        next_id = u['id']
        if next_id > max_id:
            max_id = next_id
        if u['access_level'] == owner.access_level:
            # DO NOT OVERRIDE THE PASSWORD!
            owner.username = u['username']
            owner.registration_code = u['registration_code']
            owner.about_me = u['about_me']
            owner.last_seen = u['last_seen']
            owner.access_level = u['access_level']
            owner.is_suspended = u['is_suspended']
            owner.partner_id = u['partner']
            owner.beer_demand = u['beer_demand']
            owner.mixed_demand = u['mixed_demand']
            owner.water_demand = u['water_demand']
        else:
            user = m.User()
            user.id = next_id
            user.username = u['username']
            user.registration_code = u['registration_code']
            user.password_hash = u['password_hash']
            user.about_me = u['about_me']
            user.last_seen = u['last_seen']
            user.access_level = u['access_level']
            user.is_suspended = u['is_suspended']
            user.partner_id = u['partner']
            user.beer_demand = u['beer_demand']
            user.mixed_demand = u['mixed_demand']
            user.water_demand = u['water_demand']
            user.reset_code = u['reset_code']
            db.session.add(user)
    __reset_sequence('user_id_seq', max_id + 1)
    db.session.commit()


def __import_festivals(festivals):
    max_id = 1
    for f in festivals:
        next_id = f['id']
        if next_id > max_id:
            max_id = next_id
        festival = m.Festival()
        festival.id = next_id
        festival.title = f['title']
        festival.info = f['info']
        festival.creator_id = f['creator']
        festival.is_closed = f['is_closed']
        festival.update_info = f['update_info']
        festival.modified = f['modified']
        festival.end_date = f['end_date']
        festival.start_date = f['start_date']
        db.session.add(festival)
        participants = f['participants']
        for p in participants:
            u = m.User.query.get(p)
            festival.join(u)
    __reset_sequence('festival_id_seq', max_id + 1)
    db.session.commit()


def __import_pkus(pkus):
    max_id = 1
    for p in pkus:
        next_id = p['id']
        if next_id > max_id:
            max_id = next_id
        pku = m.PackagingUnitType()
        pku.id = next_id
        pku.name = p['name']
        pku.abbreviation = p['abbreviation']
        pku.internal_name = p['internal_name']
        pku.delete = p['delete']
        db.session.add(pku)
    __reset_sequence('packaging_unit_type_id_seq', max_id + 1)
    db.session.commit()


def __import_posts(posts):
    parents = filter(lambda x: x['parent'] is None, posts)
    children = filter(lambda x: x['parent'] is not None, posts)
    max_id = 1
    for p in parents:
        next_id = p['id']
        if next_id > max_id:
            max_id = next_id
        post = m.Post()
        post.id = next_id
        post.body = p['body']
        post.timestamp = p['timestamp']
        post.user_id = p['author']
        post.is_pinned = p['is_pinned']
        post.parent_id = p['parent']
        post.internal_time = p['internal_time']
        db.session.add(post)
    db.session.commit()
    for p in children:
        next_id = p['id']
        if next_id > max_id:
            max_id = next_id
        post = m.Post()
        post.id = next_id
        post.body = p['body']
        post.timestamp = p['timestamp']
        post.user_id = p['author']
        post.is_pinned = p['is_pinned']
        post.parent_id = p['parent']
        post.internal_time = p['internal_time']
        db.session.add(post)
    __reset_sequence('post_id_seq', max_id + 1)
    db.session.commit()


def __import_items(c_items, u_items):
    max_id = 1
    for c in c_items:
        next_id = c['id']
        if next_id > max_id:
            max_id = next_id
        c_item = m.ConsumptionItem()
        c_item.id = next_id
        c_item.name = c['name']
        c_item.state = c['state']
        c_item.amount = c['amount']
        c_item.requestor_id = c['requestor']
        c_item.pku_id = c['pku']
        c_item.info = c['info']
        db.session.add(c_item)
    __reset_sequence('consumption_item_id_seq', max_id + 1)
    db.session.commit()
    max_id = 1
    for u in u_items:
        next_id = u['id']
        if next_id > max_id:
            max_id = next_id
        u_item = m.UtilityItem()
        u_item.id = next_id
        u_item.name = u['name']
        u_item.owner_id = u['owner']
        u_item.description = u['description']
        db.session.add(u_item)
    __reset_sequence('utility_item_id_seq', max_id + 1)
    db.session.commit()


def __import_invoices(invoices):
    max_id = 1
    for i in invoices:
        next_id = i['id']
        if next_id > max_id:
            max_id = next_id
        invoice = m.Invoice()
        invoice.id = i['id']
        invoice.title = i['title']
        invoice.amount = i['amount']
        invoice.creditor_id = i['creditor']
        invoice.festival_id = i['festival']
        db.session.add(invoice)
        sharers = i['sharers']
        for s in sharers:
            u = m.User.query.get(s)
            invoice.add_sharer(u)
    __reset_sequence('invoice_id_seq', max_id + 1)
    db.session.commit()


def __import_transfers(transfers):
    max_id = 1
    for t in transfers:
        next_id = t['id']
        if next_id > max_id:
            max_id = next_id
        transfer = m.Transfer()
        transfer.id = next_id
        transfer.festival_id = t['festival']
        transfer.recipient_id = t['recipient']
        transfer.payer_id = t['payer']
        transfer.amount = t['amount']
        db.session.add(transfer)
    __reset_sequence('transfer_id_seq', max_id + 1)
    db.session.commit()


def __do_import(data):
    ca.logger.info('start importing data from file')
    __import_users(data['users'])
    __import_festivals(data['festivals'])
    __import_pkus(data['packagingUnits'])
    __import_posts(data['posts'])
    __import_items(data['consumptionItems'], data['utilityItems'])
    __import_invoices(data['invoices'])
    __import_transfers(data['transfers'])
    ca.logger.info('import finished')

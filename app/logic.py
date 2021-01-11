import random
import string
import os

from flask import abort
from flask_login import current_user

from app import db, session
from app.containers import NotificationType, UserAccessLevel
from app.models import User, Festival, PackagingUnitType


def random_string(length=8):
    """Generate a random string of fixed length """
    letters = string.hexdigits
    return ''.join(random.choice(letters) for i in range(length))


def notify_users(current_user_id=None,
                 notificationType=NotificationType.festival_updated):
    if current_user_id is None:
        current_user_id = current_user.id
    users = session.query(User).filter(User.id != current_user_id).all()
    for u in users:
        u.add_notification(notificationType, u.new_activities())
    db.session.commit()


def notify_user(user, notificationType=NotificationType.admin):
    if user is None:
        abort(500)
    user.add_notification(notificationType, 1)
    db.session.commit()


def notify_owner(notificationType=NotificationType.no_registration_codes):
    payload = 1
    owner = session.query(User).filter_by(access_level=UserAccessLevel.OWNER).first()
    if notificationType is NotificationType.no_registration_codes:
        payload = owner.available_codes()
    owner.add_notification(notificationType, payload)
    db.session.commit()


def create_user(username,
                password=os.environ.get('INITIAL_ADMIN_PW'),
                access_level=UserAccessLevel.USER):
    code = random_string()
    beer_demand = random.randrange(3, 30)
    mixed_demand = random.randrange(6, 60)
    water_demand = random.randrange(3, 10)
    user = User(username=username,
                registration_code=code,
                beer_demand=beer_demand,
                mixed_demand=mixed_demand,
                water_demand=water_demand,
                access_level=access_level)
    if password is None:
        raise RuntimeError('no initial password defined')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()


def create_festival(title, start, end):
    users = session.query(User).all()
    festival = Festival(title=title, creator_id=users[0].id,
                        start_date=start, end_date=end)
    db.session.add(festival)
    for u in users:
        festival.join(u)
    db.session.commit()


def create_pku():
    db.session.add(PackagingUnitType(
        name='Pieces',
        internal_name='Pieces',
        abbreviation='pcs'))
    db.session.add(PackagingUnitType(
        name='Liters',
        internal_name='Liters',
        abbreviation='l'))
    db.session.add(PackagingUnitType(
        name='Pallets',
        internal_name='Pallets',
        abbreviation='plt'))
    db.session.add(PackagingUnitType(
        name='Kilogram',
        internal_name='Kilogram',
        abbreviation='kg'))
    db.session.add(PackagingUnitType(
        name='Gram',
        internal_name='Gram',
        abbreviation='g'))
    db.session.add(PackagingUnitType(
        name='Cans',
        internal_name='Cans',
        delete=False,
        abbreviation='cns'))
    db.session.add(PackagingUnitType(
        name='Sixpacks',
        internal_name='Sixpacks',
        delete=False,
        abbreviation='sp'))
    db.session.commit()

import json
from datetime import datetime
from glob import glob
from hashlib import md5
from time import time

from flask import current_app
from flask_babel import _
from flask_login import UserMixin
from sqlalchemy.sql.expression import extract
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login
from app.containers import (ConsumptionItemState, FestivalUpdateInfo,
                            NotificationType, UserAccessLevel)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# auxiliary table, so there is no class needed
participants = db.Table('participants',
                        db.Column('participant_id', db.Integer,
                                  db.ForeignKey('user.id')),
                        db.Column('festival_id', db.Integer,
                                  db.ForeignKey('festival.id'))
                        )


sharers = db.Table('sharers',
                   db.Column('sharer_id', db.Integer,
                             db.ForeignKey('user.id')),
                   db.Column('invoice_id', db.Integer,
                             db.ForeignKey('invoice.id'))
                   )


chroniclers = db.Table('chroniclers',
                       db.Column('chronicler_id', db.Integer,
                                 db.ForeignKey('user.id')),
                       db.Column('festival_id', db.Integer,
                                 db.ForeignKey('festival.id'))
                       )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    registration_code = db.Column(db.String(8), nullable=False, unique=True)
    reset_code = db.Column(db.String(10))

    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    chronicle_entries = db.relationship(
        'ChronicleEntry', backref='chronicler', lazy='dynamic')
    about_me = db.Column(db.String(666))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    access_level = db.Column(db.Integer, nullable=False,
                             default=UserAccessLevel.USER)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)

    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic')
    created_festivals = db.relationship('Festival',
                                        foreign_keys='Festival.creator_id',
                                        backref='creator', lazy='dynamic')

    # needed in module 'purchase'
    water_demand = db.Column(db.Integer, nullable=False, default=0)
    beer_demand = db.Column(db.Integer, nullable=False, default=0)
    mixed_demand = db.Column(db.Integer, nullable=False, default=0)

    # needed in module 'festival'
    partner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dept = 0.0
    invoices = db.relationship('Invoice',
                               backref='creditor', lazy='dynamic')
    incoming_transfers = db.relationship(
        'Transfer', backref='recipient', lazy='dynamic',
        primaryjoin='User.id == Transfer.recipient_id')
    outgoing_transfers = db.relationship(
        'Transfer', backref='payer', lazy='dynamic',
        primaryjoin='User.id == Transfer.payer_id')
    wishlist_items = db.relationship(
        'ConsumptionItem', backref='requestor', lazy='dynamic',
        primaryjoin='User.id == ConsumptionItem.requestor_id')
    utility_items = db.relationship(
        'UtilityItem', backref='owner', lazy='dynamic',
        primaryjoin='User.id == UtilityItem.owner_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def avatar(self, size, digest=None, ignore_photo=False):
        if ignore_photo:
            digest = md5(digest.encode('utf-8')).hexdigest()
            return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}' \
                .format(digest, size)
        photo_path = current_app.config['UPLOADED_PHOTOS_DEST']
        search_pattern = '/*{}*'.format(self.registration_code)
        current_photo = glob(photo_path + search_pattern)
        if len(current_photo) == 1:
            split = current_photo[0].split(sep='/')
            img_src = '/' + split[-3] + '/' + split[-2] + '/' + split[-1]
            return img_src

        if digest is None:
            digest = md5(self.registration_code.encode('utf-8')).hexdigest()
        else:
            digest = md5(digest.encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def new_activities(self):
        last_visit_time = self.last_seen or datetime(1900, 1, 1)
        return Festival.query.filter(
            Festival.modified > last_visit_time).count()

    def access_level_changed(self):
        n = Notification.query.filter(
            Notification.user_id == self.id,
            Notification.name == NotificationType.admin).first()
        if n is None:
            return 0
        else:
            return int(n.payload_json)

    def available_codes(self):
        if self.is_owner:
            return Registration.query.count()
        else:
            return None

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def is_owner(self):
        return int(self.access_level) == int(UserAccessLevel.OWNER)

    def is_admin(self):
        return int(self.access_level) >= int(UserAccessLevel.ADMIN)

    def get_username(self):
        if self.username is None:
            return _('Deleted User')
        else:
            return self.username

    def translate_access_level(self):
        switcher = {
            1: _('User'),
            2: _('Admin'),
            3: _('Owner')
        }
        return switcher.get(self.access_level, 'Invalid access level')

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_pinned = db.Column(db.Boolean, default=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    internal_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    parent_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def get_replies(self):
        return Post.query.filter(Post.parent_id == self.id).order_by(
            Post.timestamp.desc()).all()

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Festival(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), index=True)
    info = db.Column(db.String(666))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_closed = db.Column(db.Boolean, nullable=False, default=False)
    update_info = db.Column(db.String(50), nullable=False,
                            default=FestivalUpdateInfo.festival_created)

    modified = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=False,
                         default=datetime.utcnow)

    startdate = db.Column(db.Date, nullable=False)
    enddate = db.Column(db.Date, nullable=False)

    invoices = db.relationship('Invoice', backref='festival', lazy='dynamic')
    participants = db.relationship(
        'User', secondary=participants,
        primaryjoin=(participants.c.festival_id == id),
        backref=db.backref('participants', lazy='dynamic'), lazy='dynamic')
    chroniclers = db.relationship(
        'User', secondary=chroniclers,
        primaryjoin=(chroniclers.c.festival_id == id),
        backref=db.backref('chroniclers', lazy='dynamic'), lazy='dynamic')

    def join(self, user):
        if not self.contains_user(user):
            self.participants.append(user)
            self.update_info = FestivalUpdateInfo.user_joined

    def leave(self, user):
        if self.contains_user(user):
            self.participants.remove(user)
            self.update_info = FestivalUpdateInfo.user_left

    def contains_user(self, user):
        return self.participants.filter(
            participants.c.participant_id == user.id).count() > 0

    def get_year(self):
        return extract('year', self.startdate)

    def __repr__(self):
        return '<Festival {}>'.format(self.title)


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), index=True)
    amount = db.Column(db.Float)
    creditor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    festival_id = db.Column(db.Integer, db.ForeignKey('festival.id'))

    sharers = db.relationship(
        'User', secondary=sharers,
        primaryjoin=(sharers.c.invoice_id == id),
        backref=db.backref('sharers', lazy='dynamic'), lazy='dynamic')

    def add_sharer(self, user):
        if not self.contains_user(user):
            self.sharers.append(user)

    def remove_sharer(self, user):
        if self.contains_user(user):
            self.sharers.remove(user)

    def set_sharers(self, sharer_ids):
        users = User.query.filter(User.id.in_(sharer_ids)).all()
        for u in users:
            if not self.contains_user(u):
                self.sharers.append(u)
        # delete all registered sharers, who were not selected during edit
        for s in self.sharers:
            if s not in users:
                self.sharers.remove(s)

    def contains_user(self, user):
        return self.sharers.filter(
            sharers.c.sharer_id == user.id).count() > 0

    def __repr__(self):
        return '<Invoice {}>'.format(self.id)


class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    festival_id = db.Column(db.Integer, db.ForeignKey('festival.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)

    def __repr__(self):
        return '<Transfer {}>'.format(self.id)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)


class ConsumptionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), index=True)
    info = db.Column(db.String(140))
    state = db.Column(db.String(10), index=True, nullable=False,
                      default=ConsumptionItemState.wishlist)
    pku_id = db.Column(db.Integer, db.ForeignKey('packaging_unit_type.id'))
    amount = db.Column(db.Integer, nullable=False, default=1)
    requestor_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<ConsumptionItem {}>'.format(self.id)


class PackagingUnitType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    internal_name = db.Column(db.String(30), nullable=False, index=True)
    name = db.Column(db.String(30), nullable=False)
    abbreviation = db.Column(db.String(5), nullable=False)
    delete = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return '<PackagingUnitType {}>'.format(self.id)


class UtilityItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.String(150))

    def __repr__(self):
        return '<UtilityItem {}>'.format(self.id)


class ChronicleEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    chronicler_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    internal_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    year = db.Column(db.Integer, nullable=False)
    festival_id = db.Column(db.Integer, db.ForeignKey('festival.id'))

    def get_title(self):
        title = self.body.splitlines()[0]
        if title.startswith('# '):
            title = title.replace('# ', '')
        else:
            title = None
        return title

    def has_title(self):
        first_line = self.body.splitlines()[0]
        return first_line.startswith('# ')

    def __repr__(self):
        return '<ChronicleEntry {}>'.format(self.title)

from datetime import date

from app import db
from app.logic import random_string
from app.containers import FestivalUpdateInfo
from app.logic import notify_users
from app.festival.logic import calculate_shares, \
    calculate_transfers, reopen_festival, load_participants_from_db
from app.models import User, Festival, Invoice, Transfer, \
    Notification

from test_config import BaseTestCase


def setup_base_costallocation():
    users = [User(username='user1', registration_code=random_string()),
             User(username='user2', registration_code=random_string()),
             User(username='user3', registration_code=random_string())]
    for u in users:
        db.session.add(u)
    db.session.commit()

    # set partner_ids properly
    u1 = User.query.filter_by(username='user1').first()
    u2 = User.query.filter_by(username='user2').first()
    u3 = User.query.filter_by(username='user3').first()
    u1.partner_id = u2.id
    u2.partner_id = u1.id

    start = date(2019, 8, 13)
    end = date(2019, 8, 18)
    festival = Festival(title='Festival1', creator=u1,
                        startdate=start, enddate=end)
    db.session.add(festival)
    invoices = [
        Invoice(title='Fuel', amount=60.0, creditor=u3, festival=festival),
        Invoice(title='Food', amount=200.0, creditor=u2, festival=festival),
        Invoice(title='Beer', amount=150.25, creditor=u1, festival=festival)]
    for p in invoices:
        db.session.add(p)
    db.session.commit()

    notify_users(u1.id)

    beer = Invoice.query.filter_by(title='Beer').first()
    beer.set_sharers([u.id for u in users if u.username != 'user3'])
    common_invoices = Invoice.query.filter(Invoice.title != 'Beer').all()
    for p in common_invoices:
        p.set_sharers([u.id for u in users])

    for u in users:
        festival.join(u)

    db.session.commit()


def setup_complex_costallocation():
    users = [User(username='EW', registration_code=random_string()),
             User(username='LB', registration_code=random_string()),
             User(username='MJ', registration_code=random_string()),
             User(username='MN', registration_code=random_string()),
             User(username='PL', registration_code=random_string()),
             User(username='RV', registration_code=random_string()),
             User(username='CP', registration_code=random_string()),
             User(username='TB', registration_code=random_string()),
             User(username='TN', registration_code=random_string()),
             User(username='OK', registration_code=random_string())]
    for u in users:
        db.session.add(u)
    db.session.commit()

    # set partner_ids properly
    u1 = User.query.filter_by(username='TB').first()
    u2 = User.query.filter_by(username='TN').first()
    u1.partner_id = u2.id
    u2.partner_id = u1.id

    u3 = User.query.filter_by(username='MJ').first()
    u4 = User.query.filter_by(username='MN').first()
    u3.partner_id = u4.id
    u4.partner_id = u3.id

    start = date(2019, 8, 13)
    end = date(2019, 8, 18)
    festival = Festival(title='Festival1', creator=u1,
                        startdate=start, enddate=end)
    db.session.add(festival)
    u5 = User.query.filter_by(username='EW').first()
    u6 = User.query.filter_by(username='PL').first()
    u7 = User.query.filter_by(username='RV').first()
    invoices = [
        Invoice(title='Tanken 1', amount=66.57, creditor=u5,
                festival=festival),
        Invoice(title='Tanken 2', amount=67.03, creditor=u4,
                festival=festival),
        Invoice(title='Bier', amount=153.5, creditor=u4, festival=festival),
        Invoice(title='DM', amount=17.51, creditor=u4, festival=festival),
        Invoice(title='Tanken 3', amount=50.0,
                creditor=u6, festival=festival),
        Invoice(title='Kaufland', amount=215.0, creditor=u6,
                festival=festival),
        Invoice(title='Tanken 4', amount=80.0, creditor=u7, festival=festival)]
    for p in invoices:
        db.session.add(p)
    db.session.commit()

    beer = Invoice.query.filter_by(title='Bier').first()
    beer.set_sharers([u.id for u in users if u.username != 'TN'])
    common_invoices = Invoice.query.filter(Invoice.title != 'Bier').all()
    for p in common_invoices:
        p.set_sharers([u.id for u in users])

    for u in users:
        festival.join(u)

    db.session.commit()


class FestivalModelTestCase(BaseTestCase):

    def test_create_festival_notification(self):
        setup_base_costallocation()
        festival = Festival.query.first()
        self.assertFalse(festival.is_closed)
        self.assertIsNotNone(festival.creator)
        # users join in setup_base_costallocation
        self.assertEqual(FestivalUpdateInfo.user_joined,
                         festival.update_info)

        users = User.query.all()
        notifications = Notification.query.all()
        # -1, since there is no notification for the creator
        self.assertEqual(len(notifications), len(users) - 1)

    def test_base_costallocation(self):
        setup_base_costallocation()

        festival = Festival.query.first()
        all_invoices = Invoice.query.filter_by(festival=festival).all()
        self.assertNotEqual(0, len(all_invoices))

        users = User.query.all()
        self.assertEqual(3, len(users))

        calculate_shares(festival)

        for u in users:
            self.assertNotEqual(0.0, u.dept)
        payers = list(filter(lambda u: u.dept > 0, users))
        receivers = list(filter(lambda u: u.dept < 0, users))
        self.assertEqual(2, len(payers))
        self.assertEqual(1, len(receivers))

        participants = load_participants_from_db(festival.id)
        calculate_transfers(festival, participants)
        transfers = Transfer.query.all()
        self.assertEqual(2, len(transfers))

    def test_complex_costallocation(self):
        setup_complex_costallocation()

        festival = Festival.query.first()
        self.assertFalse(festival is None)

        users = User.query.all()
        self.assertEqual(10, len(users))
        calculate_shares(festival)

        payers = list(filter(lambda u: u.dept > 0, users))
        receivers = list(filter(lambda u: u.dept < 0, users))
        self.assertEqual(7, len(payers))
        self.assertEqual(3, len(receivers))

        participants = load_participants_from_db(festival.id)
        calculate_transfers(festival, participants)
        transfers = Transfer.query.all()
        self.assertEqual(9, len(transfers))
        invoices = list(map(lambda p: p.amount, Invoice.query.all()))

        overall_costs = sum(invoices)
        # overall costs with creditors' shares
        required_repayment_amount = overall_costs - (4 * 66.67)
        repayments = list(map(lambda t: t.amount, transfers))
        overall_transfer = sum(repayments)
        self.assertLessEqual(required_repayment_amount, overall_transfer)

    def test_reopen_festival(self):
        setup_complex_costallocation()

        festival = Festival.query.first()
        self.assertFalse(festival is None)

        users = User.query.all()
        self.assertEqual(10, len(users))
        calculate_shares(festival)

        payers = list(filter(lambda u: u.dept > 0, users))
        receivers = list(filter(lambda u: u.dept < 0, users))
        self.assertEqual(7, len(payers))
        self.assertEqual(3, len(receivers))

        participants = load_participants_from_db(festival.id)
        calculate_transfers(festival, participants)
        transfers = Transfer.query.all()
        self.assertEqual(9, len(transfers))

        reopen_festival(festival)

        self.assertFalse(festival.is_closed)
        transfers = Transfer.query.all()
        self.assertEqual(0, len(transfers))

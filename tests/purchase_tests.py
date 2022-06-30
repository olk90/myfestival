from datetime import date
from sqlalchemy import or_

from app import db, session
from app.logic import create_festival, create_user, create_pku
from app.containers import UserAccessLevel, ConsumptionItemState
from app.purchase.logic import check_shopping_empty, \
    generate_shopping_list
from app.models import ConsumptionItem, PackagingUnitType

from test_config import BaseTestCase


def setup_testdata(stock_amount=5, request_amount=5):
    create_user(username="Batman", access_level=UserAccessLevel.OWNER)
    create_user(username="Wonderwoman",
                access_level=UserAccessLevel.ADMIN)
    create_user(username="Flash")
    create_user(username="Aquaman")
    create_festival("Summerbreeze",
                    start=date(2019, 8, 13),
                    end=date(2019, 8, 18))
    create_pku()
    pcs = session.query(PackagingUnitType).filter_by(internal_name="Pieces").first()
    in_stock = ConsumptionItem(name="Sausage",
                               state=ConsumptionItemState.stock,
                               pku_id=pcs.id,
                               amount=stock_amount,
                               requestor_id=1)
    request = ConsumptionItem(name="Sausage",
                              pku_id=pcs.id,
                              amount=request_amount,
                              requestor_id=2)
    db.session.add(in_stock)
    db.session.add(request)
    db.session.commit()


class ConsumptionItemModelTest(BaseTestCase):

    def test_shopping_list_drink_demand(self):
        setup_testdata()

        self.assertTrue(check_shopping_empty())
        generate_shopping_list(festival_id=1, is_testing=True)
        self.assertFalse(check_shopping_empty())

        shopping_list = session.query(ConsumptionItem).filter(
            or_(ConsumptionItem.state == ConsumptionItemState.purchase,
                ConsumptionItem.state == ConsumptionItemState.cart)).all()

        self.assertEquals(3, len(shopping_list))
        for s in shopping_list:
            self.assertFalse(s.amount <= 0)

    def test_adjusted_amount(self):
        setup_testdata(stock_amount=5, request_amount=6)

        self.assertTrue(check_shopping_empty())
        generate_shopping_list(festival_id=1, is_testing=True)
        self.assertFalse(check_shopping_empty())

        shopping_list = session.query(ConsumptionItem).filter(
            or_(ConsumptionItem.state == ConsumptionItemState.purchase,
                ConsumptionItem.state == ConsumptionItemState.cart)).all()

        self.assertEquals(4, len(shopping_list))
        sausage = list(filter(lambda x: x.name == "Sausage", shopping_list))
        self.assertTrue(sausage is not None)
        self.assertEquals(1, sausage[0].amount)

    def test_complete_amount(self):
        setup_testdata()
        pcs = session.query(PackagingUnitType).filter_by(internal_name="Pieces").first()
        request = ConsumptionItem(name="Toast",
                                  pku_id=pcs.id,
                                  amount=4,
                                  requestor_id=2)
        db.session.add(request)
        db.session.commit()

        self.assertTrue(check_shopping_empty())
        generate_shopping_list(festival_id=1, is_testing=True)
        self.assertFalse(check_shopping_empty())

        shopping_list = session.query(ConsumptionItem).filter(
            or_(ConsumptionItem.state == ConsumptionItemState.purchase,
                ConsumptionItem.state == ConsumptionItemState.cart)).all()

        self.assertEquals(4, len(shopping_list))
        toast = list(filter(lambda x: x.name == "Toast", shopping_list))
        self.assertTrue(toast is not None)
        self.assertEquals(4, toast[0].amount)

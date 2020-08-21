from math import ceil

from flask import redirect, url_for, flash
from flask_login import current_user
from flask_babel import _
from sqlalchemy import or_, not_

from app import db
from app.containers import ConsumptionItemState
from app.models import PackagingUnitType, ConsumptionItem, Festival, User
from app.festival.logic import load_participants_from_db


def get_pku_selection():
    result = [(-1, '')]
    types = PackagingUnitType.query.all()
    for t in types:
        result.append((t.id, t.abbreviation))
    return result


def get_festivals():
    result = [(-1, '')]
    festivals = Festival.query.filter(not_(Festival.is_closed)).all()
    for f in festivals:
        result.append((f.id, f.title))
    return result


def calculate_redirect(item):
    if item.state == ConsumptionItemState.stock:
        return redirect(url_for('purchase.stock_overview'))
    if item.state == ConsumptionItemState.wishlist:
        return redirect(url_for('purchase.wishlist'))
    return redirect(url_for('main.index'))


def check_shopping_empty():
    shopping_list_len = ConsumptionItem.query.filter(or_(
        ConsumptionItem.state == ConsumptionItemState.purchase,
        ConsumptionItem.state == ConsumptionItemState.cart
    )).count()
    return shopping_list_len == 0


def get_pallets(amount, size, days):
    return ceil((amount * days) / size)


def calculate_drinks(festival_id, is_testing):
    festival = Festival.query.get(festival_id)
    duration = festival.enddate - festival.startdate
    days = duration.days
    beer_amount = mixed_amount = water_amount = 0
    for p in load_participants_from_db(festival_id):
        beer_amount += p.beer_demand
        mixed_amount += p.mixed_demand
        water_amount += p.water_demand
    beer_large_pallets = get_pallets(beer_amount, 24, days)
    mixed_large_pallets = get_pallets(mixed_amount, 24, days)
    beer_small_pallets = get_pallets(beer_amount, 18, days)
    mixed_small_pallets = get_pallets(mixed_amount, 18, days)
    water_pallets = get_pallets(water_amount, (6 * 1.5), days)

    six = PackagingUnitType.query.filter_by(internal_name='Sixpacks').first()
    cns = PackagingUnitType.query.filter_by(internal_name='Cans').first()

    beer_info = '{}x24 or {}x18'.format(beer_large_pallets, beer_small_pallets)
    mixed_info = '{}x24 or {}x18'.format(mixed_large_pallets,
                                         mixed_small_pallets)
    water_info = '6x1.5l'

    user = current_user
    if is_testing:
        user = User.query.get(1)

    beer = ConsumptionItem(name='Beer', pku_id=cns.id,
                           amount=(beer_amount * days),
                           info=beer_info,
                           requestor=user)
    mixed = ConsumptionItem(name='Mixed', pku_id=cns.id,
                            amount=(mixed_amount * days),
                            info=mixed_info,
                            requestor=user)
    water = ConsumptionItem(name='Water', pku_id=six.id,
                            amount=water_pallets,
                            info=water_info,
                            requestor=user)
    db.session.add_all([beer, mixed, water])
    db.session.commit()


def generate_shopping_list(festival_id, is_testing=False):
    calculate_drinks(festival_id, is_testing)
    requested_items = ConsumptionItem.query.filter_by(
        state=ConsumptionItemState.wishlist).all()
    available_items = ConsumptionItem.query.filter_by(
        state=ConsumptionItemState.stock).all()
    for r in requested_items:
        available = list(filter(
            lambda a: (a.name == r.name), available_items))
        if len(available) == 0:
            r.state = ConsumptionItemState.purchase
        else:
            p_amount = r.amount - available[0].amount
            if p_amount <= 0:
                # demand can be satisfied from stock
                db.session.delete(r)
            else:
                r.amount = p_amount
                r.state = ConsumptionItemState.purchase
    db.session.commit()
    if not is_testing:
        flash(_('List generated.'))
        return redirect(url_for('purchase.shopping_list'))

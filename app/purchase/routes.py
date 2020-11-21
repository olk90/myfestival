from flask import render_template, flash, redirect, url_for, \
    request, abort, current_app as ca
from flask_babel import _
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db
from app.containers import ConsumptionItemState
from app.models import ConsumptionItem, PackagingUnitType, UtilityItem
from app.purchase import bp
from app.purchase.logic import get_pku_selection, get_festivals, \
    calculate_redirect, check_shopping_empty, generate_shopping_list
from app.purchase.forms import StockForm, SelectFestivalForm, PKUForm, \
    UtilityForm
from app.purchase.messages import shopping_list_not_empty


@bp.route('/stock_overview', methods=['GET', 'POST'])
@login_required
def stock_overview():
    form = SelectFestivalForm()
    form.festival.choices = get_festivals()
    ca.logger.info(
        '>{}< has loaded stock overview'.format(current_user.username))
    if form.validate_on_submit():
        f_id = form.festival.data
        ca.logger.info(
            '>{}< has triggered shopping list creation for festival >{}<'
            .format(current_user.username, f_id))
        return generate_shopping_list(f_id)

    shopping_list_empty = check_shopping_empty()
    stock = db.session.query(ConsumptionItem, PackagingUnitType) \
        .join(PackagingUnitType).filter(
        ConsumptionItem.state == ConsumptionItemState.stock).all()
    return render_template('purchase/stock_overview.html',
                           form=form,
                           shopping_list_empty=shopping_list_empty,
                           items=stock)


@bp.route('/wishlist', methods=['GET', 'POST'])
@login_required
def wishlist():
    form = SelectFestivalForm()
    form.festival.choices = get_festivals()
    ca.logger.info(
        '>{}< has loaded wishlist'.format(current_user.username))
    if form.validate_on_submit():
        f_id = form.festival.data
        ca.logger.info(
            '>{}< has triggered shopping list creation for festival >{}<'
            .format(current_user.username, f_id))
        return generate_shopping_list(f_id)

    page = request.args.get('page', 1, type=int)
    shopping_list_empty = check_shopping_empty()
    result = db.session.query(ConsumptionItem, PackagingUnitType) \
        .join(PackagingUnitType).filter(
        ConsumptionItem.state == ConsumptionItemState.wishlist) \
        .paginate(page, ca.config['ITEMS_PER_PAGE'], False)
    next_url = url_for('purchase.wishlist',
                       page=result.next_num) if result.has_next else None
    prev_url = url_for('purchase.wishlist',
                       page=result.prev_num) if result.has_prev else None
    return render_template('purchase/wishlist.html',
                           form=form,
                           shopping_list_empty=shopping_list_empty,
                           items=result.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/shopping_list')
@login_required
def shopping_list():
    result = db.session.query(ConsumptionItem, PackagingUnitType) \
        .join(PackagingUnitType).filter(
        ConsumptionItem.state == ConsumptionItemState.purchase).all()
    ca.logger.info(
        '>{}< has loaded shopping list'.format(current_user.username))
    return render_template('purchase/shopping_list.html', items=result)


@bp.route('/finish_purchase')
@login_required
def finish_purchase():
    list_items = ConsumptionItem.query.filter_by(
        state=ConsumptionItemState.purchase).all()
    if not list_items:
        new_items = ConsumptionItem.query.filter_by(
            state=ConsumptionItemState.cart).all()
        available_items = ConsumptionItem.query.filter_by(
            state=ConsumptionItemState.stock).all()
        for i in new_items:
            other = list(filter(lambda a: (a.name == i.name), available_items))
            if len(other) == 0:
                i.state = ConsumptionItemState.stock
            else:
                other.amount += i.amount
                db.session.delete(i)
        db.session.commit()
        ca.logger.info(
            '>{}< has finished purchase'.format(current_user.username))
        return redirect(url_for('purchase.stock_overview'))
    else:
        flash(shopping_list_not_empty)
        ca.logger.error(
            '>{}< was unable to finish purchase: shopping list not empty'
            .format(current_user.username))
        return redirect(url_for('purchase.shopping_list'))


@bp.route('/check_off/<item_id>', methods=['GET', 'POST'])
@login_required
def check_off(item_id):
    item = ConsumptionItem.query.get(item_id)
    item.state = ConsumptionItemState.cart
    db.session.commit()
    ca.logger.info(
        '>{}< has added >{}< to cart'
        .format(current_user.username, item.name))
    flash(_('%(title)s added to cart', title=item.name))
    return redirect(url_for('purchase.shopping_list'))


@bp.route('/add_stock', methods=['GET', 'POST'])
@login_required
def add_stock():
    form = StockForm(state=ConsumptionItemState.stock)
    form.unit.choices = get_pku_selection()
    if form.validate_on_submit():
        item = ConsumptionItem(name=form.name.data,
                               amount=form.amount.data,
                               pku_id=form.unit.data,
                               state=ConsumptionItemState.stock,
                               requestor=current_user)
        db.session.add(item)
        db.session.commit()
        ca.logger.info(
            '>{}< has added >{}< to stock'
            .format(current_user.username, item.name))
        flash(_('Item has been added.'))
        return redirect(url_for('purchase.add_stock'))
    return render_template('purchase/add_item_form.html',
                           overview_id='stock_overview',
                           form=form, heading=_('Add Item'))


@bp.route('/add_request', methods=['GET', 'POST'])
@login_required
def add_request():
    form = StockForm(state=ConsumptionItemState.wishlist)
    form.unit.choices = get_pku_selection()
    if form.validate_on_submit():
        item = ConsumptionItem(name=form.name.data,
                               amount=form.amount.data,
                               pku_id=form.unit.data,
                               requestor=current_user)
        db.session.add(item)
        db.session.commit()
        flash(_('Item has been added.'))
        ca.logger.info(
            '>{}< has added >{}< to wishlist'
            .format(current_user.username, item.name))
        return redirect(url_for('purchase.add_request'))
    return render_template('purchase/add_item_form.html',
                           overview_id='wishlist',
                           form=form, heading=_('Add Item'))


@bp.route('/edit_item/<item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = ConsumptionItem.query.get(item_id)
    pending_items = ConsumptionItem.query.filter(or_(
        ConsumptionItem.state == ConsumptionItemState.purchase,
        ConsumptionItem.state == ConsumptionItemState.cart)).count()
    if pending_items == 0:
        form = StockForm(state=item.state, item_id=item.id, is_edit=True)
        form.unit.choices = get_pku_selection()
        if form.validate_on_submit():
            item.name = form.name.data
            item.amount = form.amount.data
            item.pku_id = form.unit.data
            db.session.commit()
            ca.logger.info(
                '>{}< has edited item >{}<'
                .format(current_user.username, item.id))
            flash(_('Your changes have been saved.'))
            return calculate_redirect(item)
        elif request.method == 'GET':
            form.name.data = item.name
            form.amount.data = item.amount
            form.unit.data = item.pku_id

        return render_template('purchase/add_item_form.html',
                               overview_id=None,
                               form=form, heading=_('Edit Item'))
    else:
        ca.logger.error(
            '>{}< failed to edit item >{}<: purchase not closed'
            .format(current_user.username, item.id))
        flash(_('Cannot edit items while purchase is not closed.'))
        return calculate_redirect(item)


@bp.route('/delete_item/<item_id>', methods=['GET', 'POST'])
@login_required
def delete_item(item_id):
    item = ConsumptionItem.query.get(item_id)
    db.session.delete(item)
    db.session.commit()
    ca.logger.info(
        '>{}< has deleted item >{}<'
        .format(current_user.username, item.name))
    flash(_('%(title)s deleted', title=item.name))
    return redirect(url_for('purchase.stock_overview'))


@bp.route('/pku_overview', methods=['GET', 'POST'])
@login_required
def pku_overview():
    if current_user.is_admin():
        ca.logger.info('>{}< has loaded PKU overview'
                       .format(current_user.username))

        # display all non-erasable PKUs in a separate list
        nonersable_pkus = PackagingUnitType.query \
            .filter(PackagingUnitType.delete == False) \
                .order_by(PackagingUnitType.name).all()  # noqa  E225

        pkus = PackagingUnitType.query.filter(PackagingUnitType.delete) \
            .order_by(PackagingUnitType.name).all()
        return render_template('purchase/pku_overview.html',
                               nonerasables=nonersable_pkus,
                               units=pkus)
    else:
        ca.logger.warn('Blocked PKU overview access for >{}<'
                       .format(current_user.username))
        abort(403)


@bp.route('/delete_pku/<pku_id>', methods=['GET', 'POST'])
@login_required
def delete_pku(pku_id):
    if current_user.is_admin():
        pku = PackagingUnitType.query.get(pku_id)
        if pku.delete:
            db.session.delete(pku)
            db.session.commit()
            ca.logger.info(
                '>{}< has deleted pku >{}<'
                .format(current_user.username, pku.name))
            flash(_('%(title)s deleted', title=pku.name))
        else:
            flash(_('%(title)s cannot be deleted!', title=pku.name))
        return redirect(url_for('purchase.pku_overview'))
    else:
        ca.logger.warn('Blocked PKU deletion for >{}<'
                       .format(current_user.username))
        abort(403)


@bp.route('/edit_pku/<pku_id>', methods=['GET', 'POST'])
@login_required
def edit_pku(pku_id):
    if current_user.is_admin():
        pku = PackagingUnitType.query.get(pku_id)
        form = PKUForm(pku.id, is_edit=True)
        if form.validate_on_submit():
            pku.name = form.name.data
            pku.abbreviation = form.abbreviation.data
            db.session.commit()
            ca.logger.info(
                '>{}< has edited PKU >{}<'
                .format(current_user.username, pku.id))
            flash(_('Your changes have been saved.'))
            return redirect(url_for('purchase.pku_overview'))
        elif request.method == 'GET':
            form.name.data = pku.name
            form.abbreviation.data = pku.abbreviation

        return render_template('add_form.html',
                               form=form, heading=_('Edit packaging unit'))
    else:
        ca.logger.warn('Blocked PKU editing for >{}<'
                       .format(current_user.username))
        abort(403)


@bp.route('/add_pku', methods=['GET', 'POST'])
@login_required
def add_pku():
    if current_user.is_admin():
        form = PKUForm()
        if form.validate_on_submit():
            name = form.name.data
            abbreviation = form.abbreviation.data
            pku = PackagingUnitType(name=name,
                                    abbreviation=abbreviation,
                                    internal_name='')
            db.session.add(pku)
            db.session.commit()
            ca.logger.info(
                '>{}< has added PKU >{}<'
                .format(current_user.username, pku.id))
            flash(_('Packaging unit has been added.'))
            return redirect(url_for('purchase.pku_overview'))

        return render_template('add_form.html',
                               form=form, heading=_('Edit packaging unit'))
    else:
        ca.logger.warn('Blocked adding PKU for >{}<'
                       .format(current_user.username))
        abort(403)


@bp.route('/utility_overview', methods=['GET', 'POST'])
@login_required
def utility_overview():
    utils = db.session.query(UtilityItem).order_by(UtilityItem.name).all()
    ca.logger.info(
        '>{}< has loaded utility overview'
        .format(current_user.username))
    return render_template('purchase/utility_overview.html',
                           items=utils)


@bp.route('/add_util', methods=['GET', 'POST'])
@login_required
def add_util():
    form = UtilityForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        item = UtilityItem(name=name, description=description,
                           owner=current_user)
        db.session.add(item)
        db.session.commit()
        ca.logger.info(
            '>{}< has added utility >{}<'
            .format(current_user.username, item.name))
        flash(_('Your changes have been saved.'))
        return redirect(url_for('purchase.utility_overview'))

    return render_template('add_form.html',
                           form=form, heading=_('Add utility item'))


@bp.route('/edit_util/<item_id>', methods=['GET', 'POST'])
@login_required
def edit_util(item_id):
    util = UtilityItem.query.get(item_id)
    if current_user.is_admin() or current_user == util.owner:
        form = UtilityForm(util_id=util.id, is_edit=True)
        if form.validate_on_submit():
            util.name = form.name.data
            util.description = form.description.data
            db.session.commit()
            ca.logger.info(
                '>{}< has edited utility >{}<'
                .format(current_user.username, util.id))
            flash(_('Your changes have been saved.'))
            return redirect(url_for('purchase.utility_overview'))
        elif request.method == 'GET':
            form.name.data = util.name
            form.description.data = util.description

        return render_template('add_form.html',
                               form=form, heading=_('Edit packaging unit'))
    else:
        ca.logger.warn('Blocked editing utility >{}< for >{}<'
                       .format(util.name, current_user.username))
        abort(403)


@bp.route('/delete_utility/<item_id>', methods=['GET', 'POST'])
@login_required
def delete_utility(item_id):
    item = UtilityItem.query.get(item_id)
    db.session.delete(item)
    db.session.commit()
    ca.logger.info(
        '>{}< has deleted utility >{}<'
        .format(current_user.username, item.name))
    flash(_('%(title)s deleted', title=item.name))
    return redirect(url_for('purchase.utility_overview'))

from flask import render_template, flash, redirect, url_for, \
    request, abort, current_app as ca
from flask_babel import _
from flask_login import current_user, login_required

from app import session
from app.logic import notify_users
from app.festival import bp
from app.festival.forms import FestivalForm, InvoiceForm, EditInvoiceForm
from app.festival.logic import get_participants, \
    close_festival as close, reopen_festival as reopen
from app.containers import NotificationType, FestivalUpdateInfo
from app.models import User, Festival, Invoice, Transfer, \
    participants as prts


@bp.route("/join/<title>")
@login_required
def join_festival(title):
    festival = session.query(Festival).filter_by(title=title).first()
    if festival is None:
        flash(_("%(title)s not found.", title=title))
        return redirect(url_for("main.index"))
    festival.join(current_user)
    invoices = festival.invoices.all()
    for p in invoices:
        p.add_sharer(current_user)
    notify_users()
    ca.logger.info(">{}< has joined >{}<"
                   .format(current_user.username, festival.title))
    flash(_("Welcome at %(title)s!", title=title))
    return redirect(url_for("festival.festival_page", title=title))


@bp.route("/leave/<title>")
@login_required
def leave_festival(title):
    festival = session.query(Festival).filter_by(title=title).first()
    if festival is None:
        flash(_("%(title)s not found.", title=title))
        return redirect(url_for("main.index"))
    festival.leave(current_user)
    invoices = festival.invoices.all()
    for p in invoices:
        p.remove_sharer(current_user)
    notify_users()
    ca.logger.info(">{}< has left >{}<"
                   .format(current_user.username, festival.title))
    flash(_("You have left %(title)s.", title=title))
    return redirect(url_for("festival.festival_page", title=title))


@bp.route("/festival_overview")
@login_required
def festival_overview():
    page = request.args.get("page", 1, type=int)
    festivals = session.query(Festival).order_by(Festival.modified.desc()).paginate(
        page, ca.config["POSTS_PER_PAGE"], False)
    current_user.add_notification(NotificationType.festival_updated, 0)
    session.commit()
    ca.logger.info(">{}< has loaded festival overview"
                   .format(current_user.username))
    next_url = url_for("festival.festival_overview", page=festivals.next_num) \
        if festivals.has_next else None
    prev_url = url_for("festival.festival_overview", page=festivals.prev_num) \
        if festivals.has_prev else None
    return render_template("festival/festival_overview.html",
                           festivals=festivals.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route("/festival/<title>")
@login_required
def festival_page(title):
    festival = session.query(Festival).filter_by(title=title).first_or_404()
    page = request.args.get("page", 1, type=int)
    invoices = festival.invoices.order_by(Invoice.title.desc()).paginate(
        page, ca.config["POSTS_PER_PAGE"], False)
    participants = session.query(User) \
        .join(prts) \
        .filter(prts.c.festival_id == festival.id).all()
    next_url = url_for("festival.festival_page", title=festival.title,
                       page=invoices.next_num) if invoices.has_next else None
    prev_url = url_for("festival.festival_page", title=festival.title,
                       page=invoices.prev_num) if invoices.has_prev else None
    ca.logger.info(">{}< has entered festival page of >{}<"
                   .format(current_user.username, festival.title))
    return render_template("festival/festival.html", festival=festival,
                           invoices=invoices.items,
                           participants=participants,
                           next_url=next_url, prev_url=prev_url)


@bp.route("/create_festival", methods=["GET", "POST"])
@login_required
def create_festival():
    if current_user.is_admin():
        form = FestivalForm()
        if form.validate_on_submit():
            festival = Festival(title=form.title.data,
                                info=form.info.data,
                                creator_id=current_user.id,
                                start_date=form.start_date.data,
                                end_date=form.end_date.data,
                                is_closed=False)
            session.add(festival)
            notify_users()
            flash(_("Festival has been created."))
            ca.logger.info(">{}< has entered festival page of >{}<"
                           .format(current_user.username, festival.title))
            return redirect(url_for("festival.festival_page", title=festival.title))
        return render_template("festival/setup_festival.html",
                               form=form,
                               title=_("Create Festival"))
    else:
        ca.logger.warn("Blocked festival creation access for >{}<"
                       .format(current_user.username))
        abort(403)


@bp.route("/edit_festival/<festival_id>", methods=["GET", "POST"])
@login_required
def edit_festival(festival_id):
    if current_user.is_admin():
        form = FestivalForm(festival_id=festival_id, is_edit=True)
        festival = session.query(Festival).get(festival_id)
        if form.validate_on_submit():
            festival.title = form.title.data
            festival.info = form.info.data
            festival.start_date = form.start_date.data
            festival.end_date = form.end_date.data
            festival.update_info = FestivalUpdateInfo.festival_md_updated
            notify_users()
            flash(_("Your changes have been saved."))
            ca.logger.info(">{}< has entered festival page of >{}<"
                           .format(current_user.username, festival.title))
            return redirect(url_for("festival.festival_page", title=festival.title))
        elif request.method == "GET":
            form.title.data = festival.title
            form.info.data = festival.info
            form.start_date.data = festival.start_date
            form.end_date.data = festival.end_date

        return render_template("festival/setup_festival.html",
                               form=form,
                               title=_("Edit Festival"))
    else:
        ca.logger.warn("Blocked festival editing access for >{}<"
                       .format(current_user.username))
        abort(403)


@bp.route("/close/<title>", methods=["GET", "POST"])
@login_required
def close_festival(title):
    festival = session.query(Festival).filter_by(title=title).first_or_404()
    close(festival)
    notify_users()
    flash(_("Festival has been closed."))
    ca.logger.info(">{}< has closed >{}<"
                   .format(current_user.username, festival.title))
    return redirect(url_for("festival.transfers_page", title=festival.title))


@bp.route("/reopen/<title>", methods=["GET", "POST"])
@login_required
def reopen_festival(title):
    festival = session.query(Festival).filter_by(title=title).first_or_404()
    reopen(festival)
    notify_users()
    flash(_("Festival has been reopened."))
    ca.logger.info(">{}< has reopened >{}<"
                   .format(current_user.username, festival.title))
    return redirect(url_for("festival.festival_page", title=festival.title))


@bp.route("/transfers/<title>", methods=["GET", "POST"])
@login_required
def transfers_page(title):
    page = request.args.get("page", 1, type=int)
    festival = session.query(Festival).filter_by(title=title).first_or_404()
    transfers = session.query(Transfer).filter_by(festival_id=festival.id)\
        .paginate(page, ca.config["POSTS_PER_PAGE"], False)
    next_url = url_for("festival.transfers_page", page=transfers.next_num) \
        if transfers.has_next else None
    prev_url = url_for("festival.transfers_page", page=transfers.prev_num) \
        if transfers.has_prev else None
    ca.logger.info(">{}< has loaded transfer page of >{}<"
                   .format(current_user.username, festival.title))
    return render_template("festival/transfer_overview.html",
                           festival=festival,
                           transfers=transfers.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route("/add_invoice/<title>", methods=["GET", "POST"])
@login_required
def add_invoice(title):
    form = InvoiceForm()
    if form.validate_on_submit():
        festival = session.query(Festival).filter_by(title=title).first()
        invoice = Invoice(creditor_id=current_user.id,
                          festival_id=festival.id, title=form.title.data,
                          amount=form.invoice.data)
        session.add(invoice)
        festival.update_info = FestivalUpdateInfo.new_invoice

        sharers = festival.participants
        for user in sharers:
            invoice.add_sharer(user)

        notify_users()
        flash(_("Your invoice has been registered."))
        ca.logger.info(">{}< has added invoice to >{}<"
                       .format(current_user.username, festival.title))
        return redirect(url_for("festival.festival_page", title=title))
    return render_template("add_form.html", title=_("Add Invoice"),
                           form=form, heading=_("Add Invoice"))


@bp.route("/edit_invoice/<f_title>/<p_title>", methods=["GET", "POST"])
@login_required
def edit_invoice(f_title, p_title):
    festival = session.query(Festival).filter_by(title=f_title).first()
    invoice = session.query(Invoice).filter_by(title=p_title).first()
    form = EditInvoiceForm(p_title, invoice.amount)
    form.sharers.choices = get_participants(festival.id)
    if form.validate_on_submit():
        invoice.title = form.title.data
        invoice.invoice = form.invoice.data
        sharer_ids = form.sharers.data
        invoice.set_sharers(sharer_ids)
        festival.update_info = FestivalUpdateInfo.invoice_updated
        notify_users()
        ca.logger.info(">{}< has edited invoice >{}<"
                       .format(current_user.username, invoice.title))
        flash(_("Invoice has been updated."))
        return redirect(url_for("festival.festival_page", title=f_title))
    elif request.method == "GET":
        form.title.data = invoice.title
        form.invoice.data = invoice.amount
        form.id = festival.id

        participant_ids = [(u.id, u.username) for u in festival.participants]
        sharer_ids = [u.id for u in invoice.sharers]
        participant_ids.sort()
        sharer_ids.sort()

        form.sharers.choices = participant_ids
        form.sharers.data = sharer_ids

    return render_template("add_form.html", title=_("Edit Invoice"),
                           form=form, heading=_("Edit Invoice"))


@bp.route("/delete_invoice/<f_title>/<invoice_id>", methods=["GET", "POST"])
@login_required
def delete_invoice(f_title, invoice_id):
    festival = session.query(Festival).filter_by(title=f_title).first()
    invoice = session.query(Invoice).get(invoice_id)
    session.delete(invoice)
    festival.update_info = FestivalUpdateInfo.invoice_deleted
    notify_users()
    ca.logger.info(
        ">{}< has deleted invoice >{}< (amount: {})"
        .format(current_user.username, invoice.title, invoice.amount))
    flash(_("%(title)s deleted", title=invoice.title))
    return redirect(url_for("festival.festival_page", title=f_title))

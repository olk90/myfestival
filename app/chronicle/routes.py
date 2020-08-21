from flask import abort
from flask import current_app as ca
from flask import flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app import db
from app.chronicle import bp
from app.chronicle.forms import ChronicleEntryForm
from app.chronicle.logic import get_festival_selection
from app.models import ChronicleEntry, Festival


@bp.route('/chronicle_overview')
@login_required
def chronicle_overview():
    page = request.args.get('page', 1, type=int)
    entries = ChronicleEntry.query.order_by(ChronicleEntry.timestamp.desc()) \
        .paginate(page, ca.config['POSTS_PER_PAGE'], False)
    ca.logger.info('>{}< has loaded chronicle overview'
                   .format(current_user.username))
    next_url = \
        url_for('chronicle.chronicle_overview', page=entries.next_num) \
        if entries.has_next else None
    prev_url = \
        url_for('chronicle.chronicle_overview', page=entries.prev_num) \
        if entries.has_prev else None
    return render_template('chronicle/chronicle_overview.html',
                           entries=entries.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/add_entry', methods=['GET', 'POST'])
@login_required
def add_entry():
    form = ChronicleEntryForm()
    form.festival.choices = get_festival_selection()
    if form.validate_on_submit():
        f_id = form.festival.data
        festival = Festival.query.get(f_id)
        y = festival.get_year()
        entry = ChronicleEntry(body=form.body.data,
                               festival_id=f_id,
                               chronicler_id=current_user.id,
                               year=y)
        db.session.add(entry)
        db.session.commit()
        flash(_('Chronicle entry has been added.'))
        ca.logger.info('>{}< has added chronicle entry >{}<'
                       .format(current_user.username, entry.id))
        return redirect(url_for('chronicle.chronicle_entry',
                                entry_id=entry.id))
    return render_template('chronicle/setup_entry.html',
                           form=form)


@bp.route('/edit_entry/<entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = ChronicleEntry.query.get(entry_id)
    if current_user == entry.chronicler:
        form = ChronicleEntryForm(entry_id=entry_id, is_edit=True)
        form.festival.choices = get_festival_selection()
        if form.validate_on_submit():
            f_id = form.festival.data
            entry.festival_id = f_id
            entry.body = form.body.data
            festival = Festival.query.get(f_id)
            entry.year = festival.get_year()
            db.session.commit()
            flash(_('Your changes have been saved.'))
            ca.logger.info('>{}< has edited chronicle entry >{}<'
                           .format(current_user.username, entry.id))
            return redirect(url_for('chronicle.chronicle_entry',
                                    entry_id=entry.id))
        elif request.method == 'GET':
            festival_id = entry.festival_id
            if festival_id:
                form.festival.data = festival_id
            form.body.data = entry.body

        festival = Festival.query.get(entry.festival_id)
        return render_template('chronicle/setup_entry.html',
                               f_title=festival.title,
                               form=form)

    else:
        ca.logger.warn('Blocked editing chronicle entry>{}< for >{}<'
                       .format(entry.id, current_user.username))
        abort(403)


@bp.route('/chronicle_entry/<entry_id>')
@login_required
def chronicle_entry(entry_id):
    entry = ChronicleEntry.query.filter_by(id=entry_id).first_or_404()
    ca.logger.info('>{}< has entered chronicle page >{}<'
                   .format(current_user.username, entry.id))
    return render_template('chronicle/chronicle_entry.html', entry=entry)


@bp.route('/delete_entry/<entry_id>', methods=['GET', 'POST'])
@login_required
def delete_entry(entry_id):
    entry = ChronicleEntry.query.get(entry_id)
    if current_user.is_admin() or current_user == entry.chronicler:
        name = entry.chronicler.username

        db.session.delete(entry)
        db.session.commit()
        ca.logger.info('>{}< deleted chronicle entry >{}< by >{}<'.format(
            current_user.username, entry_id, name))
        flash(_('Chronicle entry has been deleted.'))
        return redirect(url_for('chronicle.chronicle_overview'))
    else:
        ca.logger.warn('Blocked chronicle entry deletion for >{}<'
                       .format(current_user.username))
        abort(403)

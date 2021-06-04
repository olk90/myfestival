from flask import abort
from flask import current_app as ca
from flask import flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

import app.models as m
from app import db, session
from app.administration import bp
from app.administration.forms import CreateRegistrationCodeForm, \
    ImportBackupForm
from app.administration.user_administration import disable_user
from app.administration.backup_export import prepare_export, zip_and_download_images
from app.administration.backup_import import load_backup, load_images
from app.administration.messages import (suspend_first, suspended,
                                         suspension_failed)
from app.containers import UserAccessLevel
from app.logic import notify_owner, notify_user, random_string


@bp.route('/admin_page')
@login_required
def admin_page():
    if current_user.is_admin():
        page = request.args.get('page', 1, type=int)
        regs = session.query(m.Registration).paginate(
            page, ca.config['POSTS_PER_PAGE'], False)
        next_url = url_for('administration.admin_page',
                           page=regs.next_num) if regs.has_next else None
        prev_url = url_for('administration.admin_page',
                           page=regs.prev_num) if regs.has_prev else None
        return render_template('administration/admin_page.html',
                               registrations=regs.items,
                               next_url=next_url, prev_url=prev_url)
    else:
        ca.logger.warn('Blocked admin page access for >{}<'
                       .format(current_user.username))
        abort(403)


@bp.route('/generate_registration_codes', methods=['GET', 'POST'])
@login_required
def generate_registration_codes():
    if current_user.is_owner():
        form = CreateRegistrationCodeForm()
        if form.validate_on_submit():
            number_of_codes = form.number.data
            ca.logger.info('prepare generation of >{}< registration codes'
                           .format(number_of_codes))
            while number_of_codes > 0:
                code = random_string()
                user = session.query(m.User).filter_by(registration_code=code).first()
                if user is None:
                    registration = m.Registration(code=code)
                    db.session.add(registration)
                    number_of_codes -= 1
            notify_owner()
            flash(_('Your changes have been saved.'))
            return redirect(url_for('administration.admin_page'))
        return render_template('add_form.html',
                               title=_('Generate Registration Codes'),
                               form=form)
    else:
        ca.logger.warn('Blocked registration code access for >{}<'
                       .format(current_user.username))
        abort(403)


@bp.route('/delete_registration_code/<rc_id>', methods=['GET', 'POST'])
@login_required
def delete_registration_code(rc_id):
    if current_user.is_owner():
        rc = session.query(m.Registration).get(rc_id)
        db.session.delete(rc)
        notify_owner()
        ca.logger.info(
            '>{}< has deleted registration code >{}<'
            .format(current_user.username, rc.code))
        flash(_('Code deleted'))
        return redirect(url_for('administration.admin_page'))
    else:
        ca.logger.warn('Blocked registration code access for >{}<'
                       .format(current_user.username))
        abort(403)


@bp.route('/add_admin/<username>')
@login_required
def add_admin(username):
    if current_user.is_owner():
        user = session.query(m.User).filter_by(username=username).first()
        if user is None:
            flash(_('%(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user.is_suspended:
            flash(_(suspended))
            return redirect(url_for('main.user', username=username))
        user.access_level = UserAccessLevel.ADMIN
        ca.logger.info('assigned admin rights to user >{}<'
                       .format(user.username))
        notify_user(user)
        flash(_('%(username)s has now admin rights!', username=username))
        return redirect(request.referrer)
    else:
        ca.logger.warn('>{}< was prevented from promoting >{}< to admin'
                       .format(current_user.username, username))
        abort(403)


@bp.route('/remove_admin/<username>')
@login_required
def remove_admin(username):
    if current_user.is_owner():
        user = session.query(m.User).filter_by(username=username).first()
        if user is None:
            flash(_('%(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        user.access_level = UserAccessLevel.USER
        notify_user(user)
        ca.logger.info('removed admin rights from user >{}<'
                       .format(user.username))
        flash(_('%(username)s is no longer admin!', username=username))
        return redirect(request.referrer)
    else:
        ca.logger.warn('>{}< was prevented from stripping >{}< of rank'
                       .format(current_user.username, username))
        abort(403)


@bp.route('/suspend/<username>')
@login_required
def suspend(username):
    if current_user.is_admin():
        user = session.query(m.User).filter_by(username=username).first()
        if user is None:
            flash(_('%(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user.is_owner():
            flash(_(suspension_failed))
            return redirect(url_for('main.index'))
        user.is_suspended = True
        db.session.commit()
        ca.logger.info('suspended user >{}<'
                       .format(user.username))
        flash(_('%(username)s has been suspended!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        ca.logger.warn('>{}< was prevented from suspending >{}<'
                       .format(current_user.username, username))
        abort(403)


@bp.route('/reactivate/<username>')
@login_required
def reactivate(username):
    if current_user.is_admin():
        user = session.query(m.User).filter_by(username=username).first()
        if user is None:
            flash(_('%(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        user.is_suspended = False
        db.session.commit()
        ca.logger.info('reactivated user >{}<'
                       .format(user.username))
        flash(_('%(username)s has been reactivated!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        ca.logger.warn('>{}< was prevented from reactivating >{}<'
                       .format(current_user.username, username))
        abort(403)


@bp.route('/reset_pw/<username>')
@login_required
def reset_pw(username):
    if current_user.is_admin():
        user = session.query(m.User).filter_by(username=username).first()
        if user is None:
            flash(_('%(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        user.password_hash = None
        user.reset_code = random_string(length=10)
        db.session.commit()
        ca.logger.info('reset password user >{}<'
                       .format(user.username))
        flash(_('Password has been reset!', username=username))
        ca.logger.warn('Password reset for >{}<'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        ca.logger.warn('>{}< was prevented from resetting password of >{}<'
                       .format(current_user.username, username))
        abort(403)


@bp.route('/delete_user/<username>')
@login_required
def delete_user(username):
    if current_user.is_owner():
        user = session.query(m.User).filter_by(username=username).first()
        if user is None:
            flash(_('%(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if not user.is_suspended:
            flash(suspend_first(username))
            return redirect(url_for('main.user', username=username))

        ca.logger.info('remove dependencies for user >{}<'
                       .format(user.username))
        disable_user(user)
        flash(_('%(username)s has been deleted!', username=username))
        ca.logger.info('deleted user >{}<'
                       .format(user.username))
        return redirect(url_for('main.members'))
    else:
        ca.logger.warn('>{}< was prevented from deleting >{}<'
                       .format(current_user.username, username))
        abort(403)


@bp.route('/create_backup')
@login_required
def create_backup():
    if current_user.is_owner():
        return prepare_export()
    else:
        ca.logger.warn('>{}< was prevented entering backup page'
                       .format(current_user.username))
        abort(403)


@bp.route('/backup_images')
@login_required
def backup_images():
    if current_user.is_owner():
        return zip_and_download_images()
    else:
        ca.logger.warn('>{}< was prevented entering backup page'
                       .format(current_user.username))
        abort(403)


@bp.route('/import_backup', methods=['GET', 'POST'])
@login_required
def import_backup():
    if current_user.is_owner():
        form = ImportBackupForm()
        if form.validate_on_submit():
            if not current_user.check_password(form.password.data):
                flash(_('Invalid password'))
                return redirect(url_for('administration.import_backup'))
            load_backup(request.files['backup'])
            load_images(request.files['images'])
            flash(_('Import finished'))
        return render_template('add_form.html',
                               title=_('Import backup'),
                               form=form)
    else:
        ca.logger.warn('>{}< was prevented from importing backup'
                       .format(current_user.username))
        abort(403)

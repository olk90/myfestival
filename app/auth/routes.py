from flask import render_template, redirect, url_for, flash, request, \
    current_app as ca
from flask_babel import _
from flask_login import login_user, logout_user, current_user
from werkzeug.urls import url_parse

from app import db
from app.logic import notify_owner
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm
from app.models import User, Registration


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        ca.logger.info('>{}< logged in'.format(current_user.username))
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title=_('Sign In'), form=form)


@bp.route('/logout')
def logout():
    ca.logger.info('>{}< logged out'.format(current_user.username))
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        code = form.registration_code.data
        password = form.password.data
        # special case password reset
        if len(code) == 10:
            user = User.query.filter(
                User.username == username,
                User.reset_code == code
            ).first()
            if user is not None:
                user.reset_code = None
                user.set_password(password)
                flash(_('Password successfully reset.'))
                ca.logger.info('>{}< has reset password'.format(user.username))
                db.session.commit()
                return redirect(url_for('auth.login'))
            else:
                flash(_('Invalid registration code or name.'))
        else:
            user = User(username=username, registration_code=code)
            user.set_password(password)
            db.session.add(user)
            registration = Registration.query.filter_by(code=code).first()
            db.session.delete(registration)
            flash(_('Congratulations, you are now a registered user!'))
            ca.logger.info('>{}< signed up for duty'.format(user.username))
            notify_owner()
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title=_('Register'),
                           form=form)


@bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        user.set_password(form.new_password.data)
        db.session.commit()
        flash(_('Password changed.'))
        ca.logger.debug('>{}< changed password'.format(user.username))
        return redirect(url_for('main.user', username=current_user.username))
    return render_template('auth/register.html', title=_('Change password'),
                           form=form)

from flask_babel import _, lazy_gettext as _l
from flask_login import current_user
from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import EqualTo, DataRequired, ValidationError

from app import session
from app.models import User, Registration


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    registration_code = StringField(_l('Registration Code'), validators=[
        DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[
        DataRequired(), EqualTo('password',
                                message=_l('Passwords are not equal'))])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):  # noqa
        user = session.query(User).filter(User.username == username.data,
                                          User.reset_code == None).first()  # noqa E711
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_registration_code(self, registration_code):  # noqa
        registration_code = registration_code.data
        # special case for password reset
        if len(registration_code) == 10:
            user = session.query(User).filter_by(
                reset_code=registration_code).first()
            if user is None:
                raise ValidationError(_('Invalid registration code.'))
        else:
            user = session.query(User).filter_by(
                registration_code=registration_code).first()
            registration = session.query(Registration).filter_by(
                code=registration_code).first()
            if user is not None:
                raise ValidationError(_('Invalid registration code.'))
            if registration is None:
                raise ValidationError(_('Invalid registration code.'))


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(_l('Old Password'), validators=[
        DataRequired()])
    new_password = PasswordField(_l('New Password'), validators=[
        DataRequired()])
    new_password2 = PasswordField(_l('Repeat new Password'), validators=[
        DataRequired(), EqualTo('new_password',
                                message=_l('New passwords are not equal'))])
    submit = SubmitField(_l('Submit'))

    def validate_old_password(self, old_password):  # noqa
        user = session.query(User).filter_by(username=current_user.username).first()
        is_valid = user.check_password(old_password.data)
        if not is_valid:
            raise ValidationError(_('Old password is not correct.'))

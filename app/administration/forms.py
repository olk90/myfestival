from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import IntegerField, SubmitField, PasswordField
from wtforms.validators import NumberRange, DataRequired


class CreateRegistrationCodeForm(FlaskForm):
    number = IntegerField(_l('Number of codes'), validators=[
        DataRequired(),
        NumberRange(min=1, message=_l('Generate at least one new code!'))])
    submit = SubmitField(_l('Generate'))


class ImportBackupForm(FlaskForm):
    backup = FileField(_l('Backup file'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    submit = SubmitField('Import')

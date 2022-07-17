from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import IntegerField, SubmitField, PasswordField
from wtforms.validators import NumberRange, DataRequired

from app import archives, backups
from config import is_heroku


class CreateRegistrationCodeForm(FlaskForm):
    number = IntegerField(_l("Number of codes"), validators=[
        DataRequired(),
        NumberRange(min=1, message=_l("Generate at least one new code!"))])
    submit = SubmitField(_l("Generate"))


class ImportBackupForm(FlaskForm):
    backup = FileField(_l("Backup file"), validators=[
        DataRequired(),
        FileAllowed(backups, _l("Backup must be a JSON file!"))
    ])
    password = PasswordField(_l("Password"), validators=[
        DataRequired()
    ])
    submit = SubmitField("Import")

    def __init__(self, *args, **kwargs):
        super(ImportBackupForm, self).__init__(*args, **kwargs)
        if not is_heroku():
            self.images = FileField(_l("Image archive"), validators=[
                FileAllowed(archives, _l("File must be an archive!"))
            ])

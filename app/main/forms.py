from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed

from wtforms import StringField, SubmitField, TextAreaField, DecimalField, \
    SelectField, BooleanField
from wtforms.validators import DataRequired, ValidationError, Length, \
    NumberRange

from app import photos
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=666)])
    partner = SelectField(_l('Partner'), choices=[(-1, '')], default='',
                          coerce=int)
    water = DecimalField(_l('Water per day [l]'), places=0,
                         validators=[NumberRange(min=0,
                                                 message=_l('Invalid amount!'))
                                     ]
                         )
    beer = DecimalField(_l('Beer per day [Cans]'), places=0,
                        validators=[NumberRange(min=0,
                                                message=_l('Invalid amount!'))]
                        )
    mixed = DecimalField(_l('Mixed beer per day [Cans]'), places=0,
                         validators=[
                             NumberRange(min=0, message=_l('Invalid amount!'))]
                         )
    photo = FileField(_l('Profile photo'), validators=[
        FileAllowed(photos, _l('File must be an image!'))])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, partner_id, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.partner_id = partner_id

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))

    def validate_partner(self, partner):
        if partner.data != self.partner_id:
            p = User.query.filter_by(partner_id=self.partner.data).first()
            if p is not None:
                raise ValidationError(_('Partner already taken :\'('))


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something:'),
                         validators=[DataRequired(), Length(min=1)])
    submit = SubmitField(_l('Submit'))


class AdminPostForm(FlaskForm):
    post = TextAreaField(_l('Say something:'),
                         validators=[DataRequired(), Length(min=1)])
    is_pinned = BooleanField(_l('Pin post'))
    submit = SubmitField(_l('Submit'))


class ReplyForm(FlaskForm):
    post = TextAreaField(_l('Reply:'),
                         validators=[DataRequired(), Length(min=1)])
    submit = SubmitField(_l('Submit'))

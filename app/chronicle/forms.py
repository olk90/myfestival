from flask_babel import _
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
# from flask_wtf.file import FileField, FileAllowed
from flask_pagedown.fields import PageDownField
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

# from app import photos
from app.models import ChronicleEntry


class ChronicleEntryForm(FlaskForm):
    festival = SelectField(_l('Festival'), choices=[(-1, '')], default='',
                           coerce=int)
    body = PageDownField(_l('Tell the story:'),
                         validators=[DataRequired(), Length(min=1)])
    # TODO: implement upload set
    # pics = FileField(_l('Upload photos'), validators=[
    #     FileAllowed(photos, _l('File must be an image!'))])
    # additional fields (later): file selection (pics), year is to be
    # extracted from the selected festival
    submit = SubmitField(_l('Submit'))

    def validate_title(self, title):
        entry = None
        if not self.is_edit:
            entry = ChronicleEntry.query.filter_by(title=title.data).first()
        else:
            entry = ChronicleEntry.query.filter(
                ChronicleEntry.title == title.data,
                ChronicleEntry.id != self.festival_id
            ).first()

        if entry is not None:
            raise ValidationError(_('Please use a different title.'))

    def validate_festival(self, festival):
        if festival.data == -1:
            raise ValidationError(_('Festival must be selected.'))

    def __init__(self, entry_id=None, is_edit=False, *args, **kwargs):
        super(ChronicleEntryForm, self).__init__(*args, **kwargs)
        self.entry_id = entry_id
        self.is_edit = is_edit

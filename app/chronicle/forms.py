from flask_babel import _
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError


class ChronicleEntryForm(FlaskForm):
    festival = SelectField(_l("Festival"), choices=[(-1, "")], default="",
                           coerce=int)
    body = PageDownField(_l("Tell the story:"),
                         validators=[DataRequired(), Length(min=1)])
    submit = SubmitField(_l("Submit"))

    def validate_festival(self, festival):  # noqa
        if festival.data == -1:
            raise ValidationError(_("Festival must be selected."))

    def __init__(self, entry_id=None, f_id=None, is_edit=False,
                 *args, **kwargs):
        super(ChronicleEntryForm, self).__init__(*args, **kwargs)
        self.entry_id = entry_id
        self.f_id = f_id
        self.is_edit = is_edit

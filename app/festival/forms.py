from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField, TextAreaField, DecimalField, \
    SelectMultipleField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, ValidationError, Length,\
    NumberRange

from app import session
from app.models import Festival
from app.festival.messages import start_before_end


class FestivalForm(FlaskForm):
    title = StringField(_l("Title"), validators=[DataRequired()])
    info = TextAreaField(_l("Info"),
                         validators=[Length(min=0, max=666)])
    start_date = DateField(_l("From"), validators=[DataRequired()])
    end_date = DateField(_l("To"), validators=[DataRequired()])
    submit = SubmitField(_l("Submit"))

    def validate_title(self, title):
        if not self.is_edit:
            festival = session.query(Festival).filter_by(title=title.data).first()
        else:
            festival = session.query(Festival).filter(
                Festival.title == title.data,
                Festival.id != self.festival_id
            ).first()

        if festival is not None:
            raise ValidationError(_("Please use a different title."))

    def validate_end_date(self, end_date):
        if end_date.data < self.start_date.data:
            raise ValidationError(start_before_end)

    def __init__(self, festival_id=None, is_edit=False, *args, **kwargs):
        super(FestivalForm, self).__init__(*args, **kwargs)
        self.festival_id = festival_id
        self.is_edit = is_edit


class InvoiceForm(FlaskForm):
    title = StringField(_l("Title"), validators=[DataRequired()])
    invoice = DecimalField(_l("Invoice"), places=2, validators=[
        DataRequired(),
        NumberRange(min=0, message=_l("Invalid invoice amount!"))])

    submit = SubmitField(_l("Submit"))


class EditInvoiceForm(FlaskForm):
    title = StringField(_l("Title"), validators=[DataRequired()])
    invoice = DecimalField(_l("Invoice"), places=2, validators=[
        DataRequired(),
        NumberRange(min=0, message=_l("Invalid invoice amount!"))])
    sharers = SelectMultipleField("Sharers", coerce=int)
    submit = SubmitField(_l("Submit"))

    def __init__(self, original_title, original_invoice, *args, **kwargs):
        super(EditInvoiceForm, self).__init__(*args, **kwargs)
        self.original_title = original_title
        self.original_invoice = original_invoice

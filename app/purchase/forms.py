from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField, DecimalField, SelectField, \
    TextAreaField
from wtforms.validators import DataRequired, ValidationError, NumberRange, \
    Length

from app import session
from app.models import ConsumptionItem, PackagingUnitType, UtilityItem
from app.containers import ConsumptionItemState
from app.purchase.messages import no_participants
from app.festival.logic import load_participants_from_db


class StockForm(FlaskForm):
    name = StringField(_l("Name"), validators=[
        DataRequired(),
        Length(min=1, max=30)
    ])
    info = TextAreaField(_l("Info"), validators=[
        Length(max=140)
    ])
    amount = DecimalField(_l("Amount"), places=0, validators=[
        DataRequired(),
        NumberRange(min=1, message=_l("Invalid amount!"))])
    unit = SelectField(_l("Unit"), choices=[(-1, "")],
                       validators=[DataRequired()], coerce=int)
    submit = SubmitField(_l("Submit"))

    def __init__(self, state, item_id=None, is_edit=False, *args, **kwargs):
        super(StockForm, self).__init__(*args, **kwargs)
        self.item_id = item_id
        self.is_edit = is_edit
        self.state = state

    def validate_name(self, name):
        if not self.is_edit:
            item = session.query(ConsumptionItem).filter(
                ConsumptionItem.name == name.data,
                ConsumptionItem.state == self.state
            ).first()
        else:
            item = session.query(ConsumptionItem).filter(
                ConsumptionItem.name == name.data,
                ConsumptionItem.state == self.state,
                ConsumptionItem.id == self.item_id
            ).first()

        if not self.is_edit and item is not None:
            raise ValidationError(_("Item already on list."))

    def validate_unit(self, unit):  # noqa
        if unit.data == -1:
            raise ValidationError(_("Unit must be selected."))

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        # keep one unit for each kind of item!
        stock = session.query(ConsumptionItem).filter(
            ConsumptionItem.name == self.name.data,
            ConsumptionItem.state == ConsumptionItemState.stock,
            ConsumptionItem.pku_id != self.unit.data).first()
        invalid_state = self.state != ConsumptionItemState.stock
        if stock is not None and invalid_state:
            pku = session.query(PackagingUnitType).get(stock.pku_id)
            self.unit.errors.append(_("Expected unit: %(u)s", u=pku.name))
            return False
        return True


class SelectFestivalForm(FlaskForm):
    festival = SelectField(_l("Festival"), validators=[DataRequired()],
                           coerce=int)
    create = SubmitField(_l("Create shopping list"))

    def validate_festival(self, festival):  # noqa
        if festival.data == -1:
            raise ValidationError(_("Festival must be selected."))
        participants = load_participants_from_db(festival.data)
        if len(participants) == 0:
            raise ValidationError(no_participants)


class PKUForm(FlaskForm):
    name = StringField(_l("Name"),
                       validators=[DataRequired(), Length(min=1, max=30)])
    abbreviation = StringField(_l("Abbreviation"),
                               validators=[DataRequired(),
                                           Length(min=1, max=5)])
    submit = SubmitField(_l("Submit"))

    def validate_name(self, name):
        if not self.is_edit:
            pku = session.query(PackagingUnitType).filter_by(name=name.data).first()
        else:
            pku = session.query(PackagingUnitType).filter(
                PackagingUnitType.name == name.data,
                PackagingUnitType.id != self.pku_id
            ).first()

        if pku is not None:
            raise ValidationError(_("Please use a different name."))

    def validate_abbreviation(self, abbreviation):
        if not self.is_edit:
            pku = session.query(PackagingUnitType).filter_by(
                abbreviation=abbreviation.data).first()
        else:
            pku = session.query(PackagingUnitType).filter(
                PackagingUnitType.abbreviation == abbreviation.data,
                PackagingUnitType.id != self.pku_id
            ).first()

        if pku is not None:
            raise ValidationError(_("Please use a different abbreviation."))

    def __init__(self, pku_id=None, is_edit=False, *args, **kwargs):
        super(PKUForm, self).__init__(*args, **kwargs)
        self.pku_id = pku_id
        self.is_edit = is_edit


class UtilityForm(FlaskForm):
    name = StringField(_l("Name"),
                       validators=[DataRequired(), Length(min=1, max=30)])
    description = TextAreaField(_l("Description"),
                                validators=[Length(max=150)])
    submit = SubmitField(_l("Submit"))

    def validate_name(self, name):
        if not self.is_edit:
            util = session.query(UtilityItem).filter_by(name=name.data).first()
        else:
            util = session.query(UtilityItem).filter(
                UtilityItem.name == name.data,
                UtilityItem.id != self.util_id
            ).first()

        if util is not None:
            raise ValidationError(_("Please use a different name."))

    def __init__(self, util_id=None, is_edit=False, *args, **kwargs):
        super(UtilityForm, self).__init__(*args, **kwargs)
        self.util_id = util_id
        self.is_edit = is_edit

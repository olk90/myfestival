from enum import IntEnum
from flask_babel import _


class NotificationType:
    festival_updated = "festival_updated"
    no_registration_codes = "no_registration_codes"
    admin = "admin"


class FestivalUpdateInfo:
    festival_created = _("Festival created")
    festival_md_updated = _("Festival masterdata updated")
    new_invoice = _("New invoice added")
    invoice_updated = _("Invoice updated")
    invoice_deleted = _("Invoice deleted")
    user_joined = _("New user has joined")
    user_left = _("User has left")
    festival_closed = _("Festival closed")
    festival_reopened = _("Festival reopened")


class ConsumptionItemState:
    stock = "STOCK"
    wishlist = "WISHLIST"
    purchase = "PURCHASE"
    cart = "CART"


class UserAccessLevel(IntEnum):
    ANONYMOUS = 0
    USER = 1
    ADMIN = 2
    OWNER = 3

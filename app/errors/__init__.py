from flask import Blueprint


bp = Blueprint('errors', __name__)


# keep import in the button to avoid circular dependencies
from app.errors import handlers

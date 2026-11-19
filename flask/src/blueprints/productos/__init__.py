from flask import Blueprint

productos_bp = Blueprint(
    'productos',
    __name__,
    url_prefix='/api'
)

from . import routes
from . import recetas
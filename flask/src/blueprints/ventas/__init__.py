from flask import Blueprint

ventas_bp = Blueprint(
    'ventas',
    __name__,
    url_prefix='/api'
)

from . import pagos
from . import routes

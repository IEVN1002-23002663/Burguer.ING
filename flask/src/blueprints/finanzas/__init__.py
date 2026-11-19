from flask import Blueprint

finanzas_bp = Blueprint(
    'finanzas',
    __name__,
    url_prefix='/api'
)

from . import gastos
from . import reportes
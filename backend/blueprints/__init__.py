from sanic import Blueprint

reps_blueprint = Blueprint('reps', url_prefix="/reps")
health_blueprint = Blueprint('health', url_prefix="/health")
indices_blueprint = Blueprint('indices', url_prefix="/indices")
monitoring_blueprint = Blueprint('monitoring', url_prefix="/monitoring")

from . import reps
from . import health
from . import indices
from . import monitoring

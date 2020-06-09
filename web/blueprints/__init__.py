from sanic import Blueprint

products_blueprint = Blueprint('products', url_prefix="/products")
catalogs_blueprint = Blueprint('catalogs', url_prefix="/catalogs")
users_blueprint = Blueprint('features', url_prefix="/users")
terms_blueprint = Blueprint('terms', url_prefix="/terms")
areas_blueprint = Blueprint('areas', url_prefix="/areas")
welcome_blueprint = Blueprint('welcome', url_prefix="/welcome")
login_blueprint = Blueprint('login', url_prefix="/login")

from . import products
from . import catalogs
from . import users
from . import terms
from . import areas
from . import welcome
from . import login

from sanic import Blueprint

products_blueprint = Blueprint('products', url_prefix="/products")
catalogs_blueprint = Blueprint('catalogs', url_prefix="/catalogs")
users_blueprint = Blueprint('features', url_prefix="/users")
terms_blueprint = Blueprint('terms', url_prefix="/terms")

from . import products
from . import catalogs
from . import users
from . import terms

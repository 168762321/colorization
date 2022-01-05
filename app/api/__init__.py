from flask_restx import Api
from flask import Blueprint

from .colorizer.controller import api as colorize_ns


# Import controller APIs as namespaces.
api_bp = Blueprint("api", __name__)

api = Api(api_bp, title="API", description="Main routes.")

# API namespaces
api.add_namespace(colorize_ns)

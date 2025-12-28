"""
API 模块
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

from flask_app.api import routes

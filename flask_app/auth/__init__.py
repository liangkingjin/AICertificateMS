"""
认证模块
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from flask_app.auth import routes

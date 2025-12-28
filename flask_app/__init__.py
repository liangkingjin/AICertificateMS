"""
Flask 证书管理系统应用工厂
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_babel import Babel
import os

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
babel = Babel()


def create_app(config_class=None):
    """应用工厂函数"""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # 加载配置
    if config_class is None:
        from flask_app.config import Config
        config_class = Config
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app)
    
    # 配置登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录后再访问此页面'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from flask_app.models import User
        return User.query.get(user_id)
    
    # 注册蓝图
    from flask_app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 注册API蓝图
    from flask_app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 初始化 Flask-Admin
    from flask_app.admin import init_admin
    init_admin(app)
    
    # 配置日志
    from flask_app.utils.logging_config import setup_logging
    setup_logging(app)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 注册首页路由
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('admin.index'))
        return redirect(url_for('auth.login'))
    
    return app

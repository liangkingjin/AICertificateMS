"""
Flask 应用配置
"""
import os
from datetime import timedelta

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """基础配置"""
    # Flask 密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'certificate-system-secret-key-2025'
    
    # 数据库配置 - 使用现有的 SQLite 数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(BASE_DIR, "certificate_system.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 设为 True 可查看 SQL 语句
    
    # Flask-Admin 配置
    FLASK_ADMIN_SWATCH = 'cerulean'  # Bootstrap 主题
    
    # Flask-Babel 配置
    BABEL_DEFAULT_LOCALE = 'zh_CN'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Shanghai'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'flask_app', 'static', 'uploads')
    IMAGES_FOLDER = os.path.join(BASE_DIR, 'images')
    FILES_FOLDER = os.path.join(BASE_DIR, 'file')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 最大10MB
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'bmp'}
    
    # Session 配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 分页配置
    ITEMS_PER_PAGE = 20
    
    # CSRF 配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1小时
    
    # 日志配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT = 10


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境应使用更安全的密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

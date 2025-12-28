"""
日志配置模块
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import current_app


def setup_logging(app):
    """设置应用日志"""
    if not app.debug and not app.testing:
        # 生产环境：记录到文件
        log_dir = app.config.get('LOG_DIR')
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, 'app.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=app.config.get('LOG_FILE_MAX_BYTES', 10 * 1024 * 1024),
            backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 10)
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    
    # 控制台输出
    if app.config.get('LOG_TO_STDOUT'):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
        stream_handler.setLevel(log_level)
        app.logger.addHandler(stream_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('应用启动')


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask应用入口文件
证书管理系统 Flask版
"""

from flask_app import create_app
import os

if __name__ == '__main__':
    # 根据环境变量决定配置类
    # 默认使用开发环境配置
    env = os.environ.get('FLASK_ENV', 'development')

    if env == 'production':
        from flask_app.config import ProductionConfig
        config_class = ProductionConfig
        debug_mode = False
    elif env == 'testing':
        from flask_app.config import TestingConfig
        config_class = TestingConfig
        debug_mode = True
    else:  # development 或其他情况
        from flask_app.config import DevelopmentConfig
        config_class = DevelopmentConfig
        debug_mode = True

    app = create_app(config_class)

    print(f"正在运行模式: {env}")
    print(f"DEBUG 模式: {'开启' if debug_mode else '关闭'}")
    print(f"SQLALCHEMY_ECHO: {'开启' if app.config['SQLALCHEMY_ECHO'] else '关闭'}")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode,
        use_reloader=debug_mode  # DEBUG模式下启用热部署
    )

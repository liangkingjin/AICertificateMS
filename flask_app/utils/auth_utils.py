"""
认证相关工具函数
"""
from functools import wraps
from flask import redirect, url_for, request, flash
from flask_login import current_user


def login_required_with_redirect(f):
    """
    登录验证装饰器，未登录时重定向到登录页面
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def require_roles(*roles):
    """
    角色权限装饰器
    用法: @require_roles('admin', 'teacher')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            if current_user.role not in roles:
                flash('您没有权限访问此页面', 'warning')
                return redirect(url_for('admin.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_auth_redirect():
    """
    检查认证状态，未登录返回重定向响应，否则返回None
    """
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.url))
    return None


def check_role_access(allowed_roles, message='您没有权限访问此页面'):
    """
    检查角色权限，无权限返回重定向响应，否则返回None
    
    Args:
        allowed_roles: 允许的角色列表 ['admin', 'teacher']
        message: 无权限时的提示信息
    """
    if current_user.role not in allowed_roles:
        flash(message, 'warning')
        return redirect(url_for('admin.index'))
    return None

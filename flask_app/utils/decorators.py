"""
通用装饰器
"""
from functools import wraps
from flask import redirect, url_for, request, flash
from flask_login import current_user


def admin_required(f):
    """
    管理员权限装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.role != 'admin':
            flash('只有管理员可以访问此页面', 'warning')
            return redirect(url_for('admin.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    """
    教师权限装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.role != 'teacher':
            flash('只有教师可以访问此页面', 'warning')
            return redirect(url_for('admin.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def teacher_or_admin_required(f):
    """
    教师或管理员权限装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.role not in ['teacher', 'admin']:
            flash('只有教师和管理员可以访问此页面', 'warning')
            return redirect(url_for('admin.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def handle_exceptions(error_message='操作失败'):
    """
    异常处理装饰器
    
    Args:
        error_message: 发生异常时的默认提示信息
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                flash(f'{error_message}: {str(e)}', 'danger')
                return redirect(request.referrer or url_for('admin.index'))
        return decorated_function
    return decorator


def check_deadline(f):
    """
    截止时间检查装饰器
    
    用于检查当前时间是否在证书提交截止时间之前。
    管理员和教学秘书不受此限制。
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.role in ['admin', 'secretary']:
            return f(*args, **kwargs)
        
        from flask_app.models import SystemConfig
        from datetime import datetime
        
        deadline = SystemConfig.get_deadline()
        if deadline and datetime.now() > deadline:
            flash(f'❌ 已超过证书提交截止时间（{SystemConfig.get_deadline_display()}），无法继续操作', 'danger')
            return redirect(request.referrer or url_for('my_certs.index'))
        
        return f(*args, **kwargs)
    return decorated_function

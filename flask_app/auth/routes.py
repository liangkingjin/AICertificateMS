"""
认证路由
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_app.auth import auth_bp
from flask_app.auth.forms import LoginForm, RegisterForm
from flask_app.models import User, Dictionary
from flask_app.schemas import LoginSchema, RegisterSchema, validate_data
from flask_app import db
from datetime import datetime


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # 使用 Pydantic 验证
        is_valid, error_msg, validated_data = validate_data(LoginSchema, {
            'account_id': form.account_id.data,
            'password': form.password.data,
            'remember': form.remember.data
        })
        
        if not is_valid:
            flash(error_msg, 'danger')
            return render_template('auth/login.html', form=form)
        
        # 查询用户
        user = User.query.filter_by(account_id=validated_data['account_id']).first()
        
        if user is None:
            flash('学（工）号不存在', 'danger')
            return render_template('auth/login.html', form=form)
        
        if not user.check_password(validated_data['password']):
            flash('密码错误', 'danger')
            return render_template('auth/login.html', form=form)
        
        if not user.is_active:
            flash('账号已被禁用，请联系管理员', 'danger')
            return render_template('auth/login.html', form=form)
        
        # 登录成功
        login_user(user, remember=validated_data['remember'])
        flash(f'欢迎回来，{user.name}！', 'success')
        
        # 重定向到原请求页面或首页
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('admin.index'))
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    
    form = RegisterForm()
    
    # 加载学院选项
    colleges = Dictionary.get_options('学院', include_empty=True)
    form.department.choices = colleges
    
    if form.validate_on_submit():
        # 使用 Pydantic 验证
        is_valid, error_msg, validated_data = validate_data(RegisterSchema, {
            'account_id': form.account_id.data,
            'name': form.name.data,
            'role': form.role.data,
            'department': form.department.data,
            'email': form.email.data,
            'password': form.password.data,
            'confirm_password': form.confirm_password.data,
            'advisor_id': form.advisor_id.data
        })
        
        if not is_valid:
            flash(error_msg, 'danger')
            return render_template('auth/register.html', form=form)
        
        # 检查学（工）号是否已存在
        if User.query.filter_by(account_id=validated_data['account_id']).first():
            flash('该学（工）号已被注册', 'danger')
            return render_template('auth/register.html', form=form)
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=validated_data['email']).first():
            flash('该邮箱已被注册', 'danger')
            return render_template('auth/register.html', form=form)
        
        # 创建用户
        user = User(
            account_id=validated_data['account_id'],
            name=validated_data['name'],
            role=validated_data['role'],
            department=validated_data['department'],
            email=validated_data['email'],
            advisor_id=validated_data['advisor_id'],
            is_active=True,
            created_at=datetime.now(),
            created_by='self_register'
        )
        user.set_password(validated_data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('您已成功退出登录', 'info')
    return redirect(url_for('auth.login'))

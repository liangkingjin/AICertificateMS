"""
认证表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    """登录表单"""
    account_id = StringField('学（工）号', validators=[
        DataRequired(message='请输入学（工）号')
    ], render_kw={'placeholder': '请输入学（工）号', 'class': 'form-control'})
    
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码')
    ], render_kw={'placeholder': '请输入密码', 'class': 'form-control'})
    
    remember = BooleanField('记住我')
    
    submit = SubmitField('登录')


class RegisterForm(FlaskForm):
    """注册表单"""
    account_id = StringField('学（工）号', validators=[
        DataRequired(message='请输入学（工）号'),
        Length(min=1, max=20, message='学（工）号长度1-20位')
    ], render_kw={'placeholder': '请输入学（工）号', 'class': 'form-control'})
    
    name = StringField('姓名', validators=[
        DataRequired(message='请输入姓名'),
        Length(min=1, max=50, message='姓名长度1-50位')
    ], render_kw={'placeholder': '请输入姓名', 'class': 'form-control'})
    
    role = SelectField('角色', choices=[
        ('', '-- 请选择角色 --'),
        ('student', '学生'),
        ('teacher', '教师')
    ], validators=[
        DataRequired(message='请选择角色')
    ], render_kw={'class': 'form-control'})
    
    department = SelectField('单位', validators=[
        DataRequired(message='请选择单位')
    ], render_kw={'class': 'form-control select2'})
    
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='邮箱格式不正确')
    ], render_kw={'placeholder': '请输入邮箱', 'class': 'form-control'})
    
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=8, message='密码至少8位')
    ], render_kw={'placeholder': '请输入密码（至少8位）', 'class': 'form-control'})
    
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(message='请确认密码'),
        EqualTo('password', message='两次密码输入不一致')
    ], render_kw={'placeholder': '请再次输入密码', 'class': 'form-control'})
    
    advisor_id = StringField('指导老师工号', validators=[
        Optional(),
        Length(min=8, max=8, message='指导老师工号必须是8位数字')
    ], render_kw={'placeholder': '学生可选填8位工号', 'class': 'form-control'})
    
    submit = SubmitField('注册')

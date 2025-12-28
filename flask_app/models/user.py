"""
用户模型 - 兼容现有数据库结构
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_app import db, login_manager
from datetime import datetime
import hashlib
import bcrypt
import uuid


class User(db.Model, UserMixin):
    """用户模型"""
    __tablename__ = 'user'
    
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student/teacher/secretary/admin
    department = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    advisor_id = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    created_by = db.Column(db.String(50), nullable=False)
    
    # 关系
    certificates = db.relationship('Certificate', backref='submitter', 
                                   foreign_keys='Certificate.submitter_id',
                                   lazy='dynamic')
    files = db.relationship('File', backref='owner', lazy='dynamic')
    
    def get_id(self):
        """Flask-Login 需要的方法"""
        return str(self.user_id)
    
    def check_password(self, password):
        """
        验证密码 - 兼容多种密码格式
        1. bcrypt 格式 ($2b$...)
        2. SHA256 格式 (64位十六进制)
        3. werkzeug 格式 (pbkdf2:sha256:...)
        """
        if not self.password_hash:
            return False
        
        # bcrypt 格式
        if self.password_hash.startswith('$2b$') or self.password_hash.startswith('$2a$'):
            try:
                return bcrypt.checkpw(password.encode('utf-8'),
                                     self.password_hash.encode('utf-8'))
            except (ValueError, AttributeError, bcrypt.exceptions.Error):
                return False
        
        # werkzeug 格式
        if self.password_hash.startswith('pbkdf2:') or self.password_hash.startswith('scrypt:'):
            return check_password_hash(self.password_hash, password)
        
        # SHA256 格式（旧格式）
        if len(self.password_hash) == 64:
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            return self.password_hash == sha256_hash
        
        return False
    
    def set_password(self, password):
        """设置密码（使用 bcrypt）"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @property
    def role_display(self):
        """角色中文显示"""
        role_map = {
            'student': '学生',
            'teacher': '教师',
            'secretary': '教学秘书',
            'admin': '管理员'
        }
        return role_map.get(self.role, self.role)
    
    @property
    def status_display(self):
        """状态显示"""
        return '启用' if self.is_active else '禁用'
    
    def __repr__(self):
        return f'<User {self.name}({self.account_id})>'


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login 用户加载回调"""
    return User.query.get(user_id)

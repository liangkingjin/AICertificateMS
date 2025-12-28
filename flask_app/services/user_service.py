"""
用户业务逻辑服务
"""
from flask_app import db
from flask_app.models import User
from flask_app.schemas import UserCreateSchema, UserUpdateSchema, validate_data
from datetime import datetime


class UserService:
    """用户服务类"""
    
    @staticmethod
    def create_user(user_data: dict):
        """创建新用户"""
        # 验证数据
        is_valid, error_msg, validated_data = validate_data(UserCreateSchema, user_data)
        if not is_valid:
            return None, error_msg
        
        # 检查用户是否已存在
        existing_user = User.query.filter_by(account_id=validated_data['account_id']).first()
        if existing_user:
            return None, f'用户 {validated_data["account_id"]} 已存在'
        
        # 创建用户
        user = User(
            account_id=validated_data['account_id'],
            name=validated_data['name'],
            role=validated_data['role'],
            department=validated_data.get('department', '未分配'),
            email=validated_data.get('email', ''),
            advisor_id=validated_data.get('advisor_id'),
            is_active=True,
            created_at=datetime.now(),
            created_by='system'
        )
        
        # 设置密码
        password = validated_data.get('password', validated_data['account_id'][-6:])
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return user, None
    
    @staticmethod
    def update_user(user_id: int, user_data: dict):
        """更新用户信息"""
        user = User.query.get_or_404(user_id)
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_data(UserUpdateSchema, user_data)
        if not is_valid:
            return None, error_msg
        
        # 更新字段
        for key, value in validated_data.items():
            if value is not None:
                setattr(user, key, value)
        
        user.updated_at = datetime.now()
        db.session.commit()
        
        return user, None
    
    @staticmethod
    def reset_password(user_id: str, new_password: str):
        """重置用户密码"""
        user = User.query.get_or_404(user_id)
        user.set_password(new_password)
        db.session.commit()
        return user
    
    @staticmethod
    def authenticate(account_id: str, password: str):
        """验证用户登录"""
        user = User.query.filter_by(account_id=account_id, is_active=True).first()
        if user and user.check_password(password):
            return user
        return None
    
    @staticmethod
    def get_user_by_id(user_id: str):
        """根据ID获取用户"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_account_id(account_id: str):
        """根据账号ID获取用户"""
        return User.query.filter_by(account_id=account_id).first()


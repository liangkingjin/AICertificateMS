"""
系统配置模型 - 兼容现有数据库结构
"""
from flask_app import db
from datetime import datetime
import uuid


class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'systemconfig'
    
    config_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    updated_by = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=True)
    
    # 常用配置键
    KEY_DEADLINE = 'deadline'  # 提交截止时间
    KEY_AI_PROMPT = 'ai_prompt'  # AI 提示词
    
    @staticmethod
    def get_value(key, default=None):
        """获取配置值"""
        config = SystemConfig.query.filter_by(config_key=key).first()
        return config.config_value if config else default
    
    @staticmethod
    def set_value(key, value, description=None, updated_by=None):
        """设置配置值"""
        config = SystemConfig.query.filter_by(config_key=key).first()
        if config:
            config.config_value = value
            config.updated_at = datetime.now()
            if updated_by:
                config.updated_by = updated_by
        else:
            config = SystemConfig(
                config_key=key,
                config_value=value,
                description=description,
                updated_by=updated_by
            )
            db.session.add(config)
        db.session.commit()
        return config
    
    @staticmethod
    def get_deadline():
        """
        获取提交截止时间
        
        Returns:
            datetime: 截止时间，如果未设置返回None
        """
        deadline_str = SystemConfig.get_value(SystemConfig.KEY_DEADLINE)
        if not deadline_str:
            return None
        try:
            return datetime.strptime(deadline_str, '%Y-%m-%d %H:%M')
        except ValueError:
            return None
    
    @staticmethod
    def is_before_deadline(check_time=None):
        """
        检查当前时间是否在截止时间之前
        
        Args:
            check_time: 要检查的时间，默认为当前时间
        
        Returns:
            bool: 如果未设置截止时间或当前时间在截止时间之前返回True
        """
        deadline = SystemConfig.get_deadline()
        if deadline is None:
            return True  # 未设置截止时间，允许提交
        if check_time is None:
            check_time = datetime.now()
        return check_time <= deadline
    
    @staticmethod
    def get_deadline_display():
        """
        获取截止时间的友好显示
        
        Returns:
            str: 格式化的截止时间字符串，如果未设置返回"未设置"
        """
        deadline = SystemConfig.get_deadline()
        if deadline is None:
            return "未设置"
        return deadline.strftime('%Y-%m-%d %H:%M')
    
    def __repr__(self):
        return f'<SystemConfig {self.config_key}>'


class APIKey(db.Model):
    """API密钥模型"""
    __tablename__ = 'apikey'
    
    key_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(200), unique=True, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)
    max_usage = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_used_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(50), nullable=False)
    
    @property
    def is_available(self):
        """是否可用"""
        if not self.is_active:
            return False
        if self.max_usage and self.usage_count >= self.max_usage:
            return False
        return True
    
    @property
    def masked_key(self):
        """脱敏显示的API密钥"""
        if len(self.api_key) > 12:
            return self.api_key[:8] + '****' + self.api_key[-4:]
        return '****'
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.last_used_at = datetime.now()
        
        # 检查是否达到上限
        if self.max_usage and self.usage_count >= self.max_usage:
            self.is_active = False
        
        db.session.commit()
    
    @staticmethod
    def get_available_key():
        """获取可用的API密钥"""
        return APIKey.query.filter_by(is_active=True).first()
    
    def __repr__(self):
        return f'<APIKey {self.model_name}: {self.masked_key}>'

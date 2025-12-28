"""
字典模型 - 使用父节点层级结构
"""
from flask_app import db
from datetime import datetime
import uuid


class Dictionary(db.Model):
    """通用字典表 - 基于 parent_id 的层级结构"""
    __tablename__ = 'dictionary'
    
    dict_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dict_name = db.Column(db.String(100), nullable=False, index=True)
    parent_id = db.Column(db.String(36), db.ForeignKey('dictionary.dict_id'), nullable=True)
    description = db.Column(db.String(200), nullable=True)
    status = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    updated_by = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=True)
    
    # 自引用关系
    children = db.relationship('Dictionary', backref=db.backref('parent', remote_side=[dict_id]))
    
    @staticmethod
    def get_options(parent_name, include_empty=True):
        """
        获取指定父节点名称下的字典选项列表
        Args:
            parent_name: 父节点名称，如 '学院', '获奖类别', '获奖等级', '竞赛类型'
            include_empty: 是否包含空选项
        返回: [(value, label), ...]
        """
        # 先找到父节点
        parent = Dictionary.query.filter_by(
            dict_name=parent_name,
            parent_id=None,
            status=True
        ).first()
        
        if not parent:
            # 如果没找到父节点，返回空列表
            options = []
        else:
            # 获取该父节点下的所有子节点
            items = Dictionary.query.filter_by(
                parent_id=parent.dict_id,
                status=True
            ).order_by(Dictionary.created_at.desc()).all()
            
            options = [(item.dict_name, item.dict_name) for item in items]
        
        if include_empty:
            options.insert(0, ('', '-- 请选择 --'))
        
        return options
    
    @staticmethod
    def get_options_by_parent_id(parent_id, include_empty=True):
        """
        根据父节点ID获取子节点选项
        """
        items = Dictionary.query.filter_by(
            parent_id=parent_id,
            status=True
        ).order_by(Dictionary.created_at.desc()).all()
        
        options = [(item.dict_name, item.dict_name) for item in items]
        
        if include_empty:
            options.insert(0, ('', '-- 请选择 --'))
        
        return options
    
    @staticmethod
    def get_values(parent_name):
        """获取指定父节点名称下的字典值列表"""
        parent = Dictionary.query.filter_by(
            dict_name=parent_name,
            parent_id=None,
            status=True
        ).first()
        
        if not parent:
            return []
        
        items = Dictionary.query.filter_by(
            parent_id=parent.dict_id,
            status=True
        ).order_by(Dictionary.created_at.desc()).all()
        return [item.dict_name for item in items]
    
    @staticmethod
    def get_top_level_options(include_empty=True):
        """获取所有顶级节点作为父节点选项"""
        items = Dictionary.query.filter_by(
            parent_id=None,
            status=True
        ).order_by(Dictionary.created_at.desc()).all()
        
        options = [(item.dict_id, item.dict_name) for item in items]
        
        if include_empty:
            options.insert(0, (None, '-- 无（顶级数据） --'))
        
        return options
    
    @property
    def parent_name(self):
        """获取父节点名称"""
        if self.parent:
            return self.parent.dict_name
        return None
    
    @property
    def is_top_level(self):
        """是否为顶级节点"""
        return self.parent_id is None
    
    @property
    def status_display(self):
        """状态显示"""
        return '启用' if self.status else '禁用'
    
    def __repr__(self):
        return f'<Dictionary {self.dict_id}: {self.dict_name}>'

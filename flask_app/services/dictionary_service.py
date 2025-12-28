"""
字典业务逻辑服务
"""
from flask_app import db
from flask_app.models import Dictionary
from datetime import datetime


class DictionaryService:
    """字典服务类"""
    
    @staticmethod
    def get_options_by_parent(parent_name: str):
        """根据父节点名称获取选项列表"""
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
        ).order_by(Dictionary.dict_name).all()
        
        return [{'id': item.dict_id, 'name': item.dict_name} for item in items]
    
    @staticmethod
    def create_dictionary_item(name: str, parent_id: int = None, description: str = None):
        """创建字典项"""
        item = Dictionary(
            dict_name=name,
            parent_id=parent_id,
            description=description,
            status=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(item)
        db.session.commit()
        
        return item
    
    @staticmethod
    def update_dictionary_item(item_id: int, name: str = None, description: str = None, status: bool = None):
        """更新字典项"""
        item = Dictionary.query.get_or_404(item_id)
        
        if name is not None:
            item.dict_name = name
        if description is not None:
            item.description = description
        if status is not None:
            item.status = status
        
        item.updated_at = datetime.now()
        db.session.commit()
        
        return item
    
    @staticmethod
    def delete_dictionary_item(item_id: int):
        """删除字典项（软删除）"""
        item = Dictionary.query.get_or_404(item_id)
        item.status = False
        item.updated_at = datetime.now()
        db.session.commit()
        return item


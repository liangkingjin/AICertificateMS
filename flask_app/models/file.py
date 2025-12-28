"""
文件模型 - 兼容现有数据库结构
"""
from flask_app import db
from datetime import datetime
import uuid


class File(db.Model):
    """文件模型"""
    __tablename__ = 'file'
    
    file_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # pdf/image
    file_size = db.Column(db.Integer, nullable=False)
    file_md5 = db.Column(db.String(32), nullable=False, index=True)
    upload_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    @property
    def file_size_display(self):
        """文件大小友好显示"""
        size = self.file_size
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        else:
            return f'{size / (1024 * 1024):.1f} MB'
    
    @property
    def is_image(self):
        """是否为图片"""
        return self.file_type == 'image'
    
    @property
    def is_pdf(self):
        """是否为PDF"""
        return self.file_type == 'pdf'
    
    def __repr__(self):
        return f'<File {self.file_id}: {self.file_name}>'

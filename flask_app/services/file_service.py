"""
文件业务逻辑服务
"""
from flask_app import db
from flask_app.models import File
from flask_app.utils.file_utils import (
    save_uploaded_file, calculate_file_md5, create_file_record,
    get_user_upload_folder, generate_unique_filename
)
from datetime import datetime
import os


class FileService:
    """文件服务类"""
    
    @staticmethod
    def save_file(file, user_id: str, upload_folder: str):
        """保存上传的文件"""
        # 计算MD5
        file_md5 = calculate_file_md5(file)
        
        # 检查是否已存在相同MD5的文件
        existing_file = File.query.filter_by(md5_hash=file_md5).first()
        if existing_file and os.path.exists(existing_file.file_path):
            # 文件已存在，返回现有记录
            return existing_file, None
        
        # 保存文件
        user_folder = get_user_upload_folder(upload_folder, user_id)
        os.makedirs(user_folder, exist_ok=True)
        
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(user_folder, filename)
        
        file.save(file_path)
        
        # 创建文件记录
        file_record = create_file_record(
            file_path=file_path,
            user_id=user_id,
            md5_hash=file_md5,
            file_size=os.path.getsize(file_path)
        )
        
        return file_record, None
    
    @staticmethod
    def get_file_by_id(file_id: int):
        """根据ID获取文件记录"""
        return File.query.get(file_id)
    
    @staticmethod
    def get_file_by_md5(md5_hash: str):
        """根据MD5获取文件记录"""
        return File.query.filter_by(md5_hash=md5_hash).first()
    
    @staticmethod
    def delete_file(file_id: str):
        """删除文件记录和文件"""
        file_record = File.query.get_or_404(file_id)
        
        # 删除物理文件
        if os.path.exists(file_record.file_path):
            try:
                os.remove(file_record.file_path)
            except OSError:
                pass  # 文件可能已被删除
        
        # 删除记录
        db.session.delete(file_record)
        db.session.commit()
        
        return True


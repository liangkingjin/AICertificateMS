"""
文件处理工具函数
"""
import os
import hashlib
from datetime import datetime
from flask import current_app
from flask_login import current_user


def calculate_file_md5(file_content):
    """
    计算文件内容的MD5值
    
    Args:
        file_content: 文件内容（bytes）
    
    Returns:
        str: MD5哈希值
    """
    return hashlib.md5(file_content).hexdigest()


def get_file_extension(filename):
    """
    获取文件扩展名（带点）
    
    Args:
        filename: 文件名
    
    Returns:
        str: 扩展名（如 .png, .pdf）
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext if ext else '.jpg'


def get_file_type(file_path):
    """
    根据文件路径判断文件类型
    
    Args:
        file_path: 文件路径
    
    Returns:
        str: 'pdf' 或 'image'
    """
    if file_path.lower().endswith('.pdf'):
        return 'pdf'
    return 'image'


def get_upload_folder():
    """
    获取上传目录路径
    
    Returns:
        str: 上传目录的绝对路径
    """
    return current_app.config.get(
        'UPLOAD_FOLDER',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
    )


def get_user_upload_folder(user=None):
    """
    获取用户专属的上传目录
    
    Args:
        user: User对象，默认为当前用户
    
    Returns:
        str: 用户上传目录的绝对路径
    """
    if user is None:
        user = current_user
    
    user_folder = f"{user.account_id}_{user.name}"
    base_dir = get_upload_folder()
    user_dir = os.path.join(base_dir, user_folder)
    
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def generate_unique_filename(original_filename):
    """
    生成唯一的文件名
    
    Args:
        original_filename: 原始文件名
    
    Returns:
        str: 唯一文件名
    """
    ext = get_file_extension(original_filename)
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{date_str}_cert{ext}"


def save_uploaded_file(file_content, original_filename, user=None):
    """
    保存上传的文件
    
    Args:
        file_content: 文件内容（bytes）
        original_filename: 原始文件名
        user: User对象，默认为当前用户
    
    Returns:
        tuple: (file_path, file_md5, file_type)
    """
    if user is None:
        user = current_user
    
    # 计算MD5
    file_md5 = calculate_file_md5(file_content)
    
    # 获取保存路径
    save_dir = get_user_upload_folder(user)
    unique_filename = generate_unique_filename(original_filename)
    file_path = os.path.join(save_dir, unique_filename)
    
    # 保存文件
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    # 判断文件类型
    file_type = get_file_type(file_path)
    
    return file_path, file_md5, file_type


def create_file_record(user_id, filename, file_path, file_type, file_size, file_md5):
    """
    创建文件记录
    
    Args:
        user_id: 用户ID
        filename: 文件名
        file_path: 文件路径
        file_type: 文件类型
        file_size: 文件大小
        file_md5: 文件MD5
    
    Returns:
        File: 文件记录对象
    """
    from flask_app.models import File
    from flask_app import db
    
    file_record = File(
        user_id=user_id,
        file_name=filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        file_md5=file_md5,
        upload_time=datetime.now()
    )
    db.session.add(file_record)
    db.session.commit()
    
    return file_record


def is_image_file(file_path):
    """
    判断是否为图片文件
    """
    return file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))


def is_pdf_file(file_path):
    """
    判断是否为PDF文件
    """
    return file_path.lower().endswith('.pdf')

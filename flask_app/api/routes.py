"""
API 路由
"""
from flask import jsonify, request, send_file, abort, current_app
from flask_login import login_required, current_user
from flask_app.api import api_bp
from flask_app.models import Dictionary
import os
import hashlib
import time


@api_bp.route('/dictionaries/<parent_name>')
@login_required
def get_dictionaries(parent_name):
    """获取字典数据（根据父节点名称）"""
    # 先找父节点
    parent = Dictionary.query.filter_by(
        dict_name=parent_name,
        parent_id=None,
        status=True
    ).first()
    
    if not parent:
        return jsonify({
            'success': True,
            'data': []
        })
    
    # 获取子节点
    items = Dictionary.query.filter_by(parent_id=parent.dict_id, status=True).order_by(Dictionary.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [{'id': item.dict_id, 'name': item.dict_name} for item in items]
    })


@api_bp.route('/user/info')
@login_required
def get_user_info():
    """获取当前用户信息"""
    return jsonify({
        'success': True,
        'data': {
            'user_id': current_user.user_id,
            'account_id': current_user.account_id,
            'name': current_user.name,
            'role': current_user.role,
            'department': current_user.department,
            'email': current_user.email
        }
    })


@api_bp.route('/certificate/file/<string:cert_id>')
@login_required
def get_certificate_file(cert_id):
    """获取证书文件（安全访问，防止直接URL访问）"""
    from flask_app.models import Certificate
    from flask import Response
    
    cert = Certificate.query.get_or_404(cert_id)
    
    # 检查权限：学生只能查看自己的证书，教师可以查看自己指导的学生证书，管理员和教学秘书可以查看所有（教学秘书只能查看本院）
    if current_user.role == 'student':
        if cert.submitter_id != current_user.user_id:
            abort(403)
    elif current_user.role == 'teacher':
        if cert.submitter_id != current_user.user_id and cert.advisor_id != current_user.account_id:
            abort(403)
    elif current_user.role == 'secretary':
        # 教学秘书只能查看本院证书
        if cert.department != current_user.department:
            abort(403)
    # 管理员可以查看所有证书
    
    if not cert.file_path or not os.path.exists(cert.file_path):
        abort(404)
    
    # 检查是否是图片文件
    is_image = cert.file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))
    
    # 检查Referer，防止直接URL访问图片
    referer = request.headers.get('Referer', '')
    host = request.headers.get('Host', '')
    
    if is_image:
        # 对于图片请求，检查Referer
        # 如果Referer存在，必须来自我们的域名
        if referer:
            if not (referer.startswith(f'http://{host}') or referer.startswith(f'https://{host}')):
                abort(403)
        else:
            # 如果没有Referer，检查是否是浏览器直接访问
            # 通过检查Accept头来判断：直接访问时Accept通常不包含image/*
            accept_header = request.headers.get('Accept', '')
            # 如果Accept头不包含image，可能是直接访问（复制链接打开）
            if 'image' not in accept_header.lower():
                abort(403)
    
    # 设置安全响应头，防止图片被嵌入到其他网站
    response = send_file(cert.file_path)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    # 防止右键复制链接直接访问
    if is_image:
        response.headers['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response


@api_bp.route('/file/<path:file_path>')
@login_required
def get_uploaded_file(file_path):
    """安全访问上传的文件（需要登录）"""
    return _get_uploaded_file_internal(file_path, require_auth=True)


@api_bp.route('/file-public/<token>/<path:file_path>')
def get_uploaded_file_public(token, file_path):
    """
    公开访问上传的文件（用于AI识别，带token验证）
    token: 临时访问令牌（基于文件路径和时间的简单hash）
    """
    # 简单的token验证（基于文件路径）
    # 生成预期的token（基于文件路径和当前小时）
    current_hour = int(time.time() // 3600)  # 每小时更新一次
    expected_token = hashlib.md5(f"{file_path}{current_hour}{current_app.config.get('SECRET_KEY', '')}".encode()).hexdigest()[:16]
    
    if token != expected_token:
        # 尝试上一小时的token（允许1小时的时间窗口）
        prev_hour = current_hour - 1
        expected_token_prev = hashlib.md5(f"{file_path}{prev_hour}{current_app.config.get('SECRET_KEY', '')}".encode()).hexdigest()[:16]
        if token != expected_token_prev:
            abort(403)
    
    return _get_uploaded_file_internal(file_path, require_auth=False)


def _get_uploaded_file_internal(file_path: str, require_auth: bool = True):
    """
    安全访问上传的文件
    通过相对路径访问，防止路径遍历攻击
    """
    from flask_app.models import Certificate, File
    from flask_login import current_user
    
    # 获取上传文件夹配置
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        abort(404)
    
    # 规范化文件路径，防止路径遍历
    # 移除开头的斜杠和点
    file_path = file_path.lstrip('/').lstrip('.')
    
    # 使用 secure_join 防止路径遍历攻击
    try:
        # 构建完整路径
        full_path = os.path.join(upload_folder, file_path)
        # 规范化路径，解析 .. 等
        full_path = os.path.normpath(full_path)
        upload_folder = os.path.normpath(upload_folder)
        
        # 确保文件在 uploads 目录内（防止路径遍历）
        if not full_path.startswith(upload_folder):
            abort(403)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            abort(404)
        
        # 如果需要认证，检查权限
        if require_auth:
            # 检查权限：通过文件路径查找关联的证书或文件记录
            # 方法1：通过证书查找
            cert = Certificate.query.filter_by(file_path=full_path).first()
            if cert:
                # 检查权限
                if current_user.role == 'student':
                    if cert.submitter_id != current_user.user_id:
                        abort(403)
                elif current_user.role == 'teacher':
                    if cert.submitter_id != current_user.user_id and cert.advisor_id != current_user.account_id:
                        abort(403)
                elif current_user.role == 'secretary':
                    if cert.department != current_user.department:
                        abort(403)
                # 管理员可以访问所有文件
            else:
                # 方法2：通过文件记录查找
                file_record = File.query.filter_by(file_path=full_path).first()
                if file_record:
                    # 检查权限：只能访问自己的文件，或者管理员/教学秘书可以访问
                    if current_user.role == 'student':
                        if file_record.user_id != current_user.user_id:
                            abort(403)
                    elif current_user.role == 'secretary':
                        # 教学秘书可以访问本院用户的文件
                        from flask_app.models import User
                        file_owner = User.query.get(file_record.user_id)
                        if file_owner and file_owner.department != current_user.department:
                            abort(403)
                    # 管理员和教师可以访问所有文件
                else:
                    # 如果找不到关联记录，只有管理员可以访问
                    if current_user.role != 'admin':
                        abort(403)
        
        # 检查是否是图片文件
        is_image = full_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))
        
        # 对于需要认证的请求，检查Referer防止直接URL访问图片
        if require_auth and is_image:
            referer = request.headers.get('Referer', '')
            host = request.headers.get('Host', '')
            
            # 对于图片请求，检查Referer
            # 如果Referer存在，必须来自我们的域名
            if referer:
                if not (referer.startswith(f'http://{host}') or referer.startswith(f'https://{host}')):
                    abort(403)
            else:
                # 如果没有Referer，检查是否是浏览器直接访问
                accept_header = request.headers.get('Accept', '')
                # 如果Accept头不包含image，可能是直接访问（复制链接打开）
                if 'image' not in accept_header.lower():
                    abort(403)
        
        # 设置安全响应头
        response = send_file(full_path)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        if require_auth:
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            # 防止右键复制链接直接访问
            if is_image:
                response.headers['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
        
        return response
        
    except (ValueError, OSError):
        abort(404)

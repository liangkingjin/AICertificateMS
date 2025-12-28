"""
证书相关工具函数
"""
from flask import request
from flask_login import current_user


def get_certificate_options():
    """
    获取证书表单所需的所有字典选项
    
    Returns:
        dict: 包含所有选项的字典
        {
            'colleges': [...],
            'categories': [...],
            'levels': [...],
            'comp_types': [...],
            'standard_scores': [...],
            'contributions': [...]
        }
    """
    from flask_app.models import Dictionary
    
    return {
        'colleges': Dictionary.get_options('学院'),
        'categories': Dictionary.get_options('获奖类别'),
        'levels': Dictionary.get_options('获奖等级'),
        'comp_types': Dictionary.get_options('竞赛类型'),
        'standard_scores': Dictionary.get_options('标准分'),
        'contributions': Dictionary.get_options('贡献值')
    }


def get_basic_certificate_options():
    """
    获取基础证书选项（不包含评分相关）
    """
    from flask_app.models import Dictionary
    
    return {
        'colleges': Dictionary.get_options('学院'),
        'categories': Dictionary.get_options('获奖类别'),
        'levels': Dictionary.get_options('获奖等级'),
        'comp_types': Dictionary.get_options('竞赛类型')
    }


def get_form_certificate_data():
    """
    从请求表单中提取证书数据
    
    Returns:
        dict: 证书数据字典
    """
    return {
        'student_id': request.form.get('student_id', '').strip(),
        'student_name': request.form.get('student_name', '').strip(),
        'department': request.form.get('department', '').strip(),
        'competition_name': request.form.get('competition_name', '').strip(),
        'award_category': request.form.get('award_category', '').strip(),
        'award_level': request.form.get('award_level', '').strip(),
        'competition_type': request.form.get('competition_type', '').strip(),
        'organizer': request.form.get('organizer', '').strip(),
        'award_date': request.form.get('award_date', '').strip(),
        'advisor': request.form.get('advisor', '').strip(),
        'advisor_id': request.form.get('advisor_id', '').strip()
    }


def check_certificate_edit_permission(cert, user=None):
    """
    检查用户是否有权限编辑证书
    
    规则:
    - 管理员: 可以编辑任何状态
    - 教师: 可以编辑草稿和待教师审核状态
    - 学生: 只能编辑草稿状态
    
    Args:
        cert: Certificate对象
        user: User对象，默认为当前用户
    
    Returns:
        bool: 是否可编辑
    """
    if user is None:
        user = current_user
    
    if not user.is_authenticated:
        return False
    
    if user.role == 'admin':
        return True
    elif user.role == 'teacher':
        return cert.status in ['draft', 'pending_teacher']
    else:  # student
        return cert.status == 'draft'


def get_submit_status_by_role(user=None):
    """
    根据用户角色获取提交后的状态
    
    规则:
    - 学生提交: pending_teacher (待教师审核)
    - 教师提交: pending_admin (待管理员审核)
    - 管理员提交: approved (审核通过)
    
    Args:
        user: User对象，默认为当前用户
    
    Returns:
        str: 提交后的状态
    """
    if user is None:
        user = current_user
    
    if user.role == 'student':
        return 'pending_teacher'
    elif user.role == 'teacher':
        return 'pending_admin'
    else:  # admin
        return 'approved'


def build_certificate_from_form(validated_data, file_path='', file_md5='', status='draft'):
    """
    根据验证后的数据构建证书对象
    
    Args:
        validated_data: 验证后的数据字典
        file_path: 文件路径
        file_md5: 文件MD5
        status: 状态
    
    Returns:
        Certificate: 证书对象
    """
    from flask_app.models import Certificate
    from datetime import datetime
    
    cert = Certificate(
        submitter_id=current_user.user_id,
        submitter_role=current_user.role,
        student_id=validated_data['student_id'],
        student_name=validated_data['student_name'],
        department=validated_data['department'],
        competition_name=validated_data['competition_name'],
        award_category=validated_data['award_category'],
        award_level=validated_data['award_level'],
        competition_type=validated_data['competition_type'],
        organizer=validated_data.get('organizer', ''),
        award_date=validated_data.get('award_date', ''),
        advisor=validated_data['advisor'],
        advisor_id=validated_data.get('advisor_id'),
        file_path=file_path,
        file_md5=file_md5,
        extraction_method='glm4v',
        status=status,
        created_at=datetime.now()
    )
    
    if status != 'draft':
        cert.submitted_at = datetime.now()
    
    return cert


def update_certificate_from_form(cert, validated_data):
    """
    使用表单数据更新证书对象
    
    Args:
        cert: 证书对象
        validated_data: 验证后的数据字典
    """
    cert.student_id = validated_data['student_id']
    cert.student_name = validated_data['student_name']
    cert.department = validated_data['department']
    cert.competition_name = validated_data['competition_name']
    cert.award_category = validated_data['award_category']
    cert.award_level = validated_data['award_level']
    cert.competition_type = validated_data['competition_type']
    cert.organizer = validated_data.get('organizer', '')
    cert.award_date = validated_data.get('award_date', '')
    cert.advisor = validated_data['advisor']
    cert.advisor_id = validated_data.get('advisor_id')


def convert_existing_cert_to_dict(cert):
    """
    将已存在的证书对象转换为字典（用于秒传时填充表单）
    
    Args:
        cert: Certificate对象
    
    Returns:
        dict: 证书信息字典
    """
    return {
        'student_id': cert.student_id,
        'student_name': cert.student_name,
        'student_department': cert.department,
        'department': cert.department,
        'competition_name': cert.competition_name,
        'award_category': cert.award_category,
        'award_level': cert.award_level,
        'competition_type': cert.competition_type,
        'organizer': cert.organizer,
        'award_date': cert.award_date,
        'advisor': cert.advisor,
        'advisor_id': cert.advisor_id or ''
    }

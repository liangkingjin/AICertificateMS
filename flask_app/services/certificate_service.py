"""
证书业务逻辑服务
"""
from flask_app import db
from flask_app.models import Certificate, File, Dictionary, User
from flask_app.schemas import CertificateSubmitSchema, CertificateUpdateSchema, validate_data
from flask_app.utils.file_utils import (
    save_uploaded_file, calculate_file_md5, create_file_record
)
from flask_app.utils.certificate_utils import (
    get_certificate_options, build_certificate_from_form
)
from flask_app.utils.date_utils import parse_award_date
import os


class CertificateService:
    """证书服务类"""

    @staticmethod
    def get_certificate_options():
        """获取证书表单所需的所有字典选项"""
        return get_certificate_options()
    
    @staticmethod
    def validate_certificate_data(data: dict):
        """验证证书数据"""
        return validate_data(CertificateSubmitSchema, data)
    
    @staticmethod
    def create_certificate(form_data: dict, file_path: str, submitter_id: str):
        """创建证书记录"""
        # 验证数据
        is_valid, error_msg, validated_data = CertificateService.validate_certificate_data(form_data)
        if not is_valid:
            return None, error_msg
        
        # 解析获奖日期
        award_date = CertificateService.parse_award_date(validated_data.get('award_date'))
        
        # 创建证书对象
        cert = Certificate(
            student_id=validated_data['student_id'],
            student_name=validated_data['student_name'],
            department=validated_data['department'],
            competition_name=validated_data.get('competition_name', ''),
            award_category=validated_data.get('award_category', ''),
            award_level=validated_data.get('award_level', ''),
            competition_type=validated_data.get('competition_type', ''),
            organizer=validated_data.get('organizer', ''),
            award_date=award_date,
            advisor=validated_data.get('advisor', ''),
            advisor_id=validated_data.get('advisor_id', ''),
            file_path=file_path,
            submitter_id=submitter_id,
            status='draft',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(cert)
        db.session.commit()
        
        return cert, None
    
    @staticmethod
    def update_certificate(cert_id: str, form_data: dict, user_role: str):
        """更新证书记录"""
        cert = Certificate.query.get_or_404(cert_id)
        
        # 验证权限
        # TODO: 添加权限检查逻辑
        
        # 验证数据
        is_valid, error_msg, validated_data = validate_data(CertificateUpdateSchema, form_data)
        if not is_valid:
            return None, error_msg
        
        # 更新字段
        for key, value in validated_data.items():
            if value is not None:
                setattr(cert, key, value)
        
        cert.updated_at = datetime.now()
        db.session.commit()
        
        return cert, None
    
    @staticmethod
    def submit_certificate(cert_id: str):
        """提交证书（从草稿变为已提交）"""
        cert = Certificate.query.get_or_404(cert_id)
        
        if cert.status != 'draft':
            return None, '只能提交草稿状态的证书'
        
        cert.status = 'submitted'
        cert.updated_at = datetime.now()
        db.session.commit()
        
        return cert, None
    
    @staticmethod
    def get_user_certificates(user_id: str, role: str, status: str = None):
        """获取用户的证书列表"""
        query = Certificate.query
        
        if role == 'student':
            query = query.filter_by(submitter_id=user_id)
        elif role == 'teacher':
            # 教师可以查看自己指导的学生证书
            query = query.filter(Certificate.advisor_id == User.account_id).join(User)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Certificate.created_at.desc()).all()


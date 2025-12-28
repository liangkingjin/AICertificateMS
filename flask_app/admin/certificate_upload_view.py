"""
证书上传视图
"""
from flask import redirect, url_for, request, flash, current_app
from flask_admin import BaseView, expose
from flask_login import current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import hashlib

from flask_app.models import Certificate, File, SystemConfig
from flask_app.schemas import CertificateSubmitSchema, validate_data
from flask_app import db
from flask_app.utils.date_utils import parse_award_date


class CertificateUploadView(BaseView):
    """证书上传视图"""
    
    @expose('/', methods=['GET', 'POST'])
    def index(self, cls=None, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        from flask_app.models import Dictionary
        
        # 获取字典选项
        colleges = Dictionary.get_options('学院')
        categories = Dictionary.get_options('获奖类别')
        levels = Dictionary.get_options('获奖等级')
        comp_types = Dictionary.get_options('竞赛类型')
        
        extracted_info = None
        file_path = None
        file_md5 = None
        is_quick_upload = False
        existing_cert = None
        can_edit = True
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            # 检查截止时间（非管理员用户）
            if current_user.role not in ['admin', 'secretary']:
                deadline = SystemConfig.get_deadline()
                if deadline and datetime.now() > deadline:
                    flash(f'❌ 已超过证书提交截止时间（{SystemConfig.get_deadline_display()}），无法继续操作', 'danger')
                    return redirect(request.url)
            
            if action == 'upload':
                # 处理文件上传
                file = request.files.get('certificate_file')
                if file and file.filename:
                    # 验证文件类型，只允许图片格式
                    allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
                    original_filename = file.filename
                    ext = os.path.splitext(original_filename)[1].lower()
                    
                    if ext not in allowed_extensions:
                        flash('❌ 不支持该文件格式！请将PDF或其他格式转换为图片（支持 JPG、PNG、BMP、GIF、WEBP）后再上传。', 'danger')
                        return redirect(request.url)
                    
                    # 计算MD5
                    file_content = file.read()
                    file_md5 = hashlib.md5(file_content).hexdigest()
                    file.seek(0)
                    
                    # 检查秒传
                    existing_cert = Certificate.query.filter_by(
                        file_md5=file_md5,
                        submitter_id=current_user.user_id
                    ).first()
                    
                    if existing_cert:
                        # 秒传成功
                        is_quick_upload = True
                        flash('⚡ 秒传成功！检测到相同证书，已加载原有数据', 'info')
                        
                        # 根据角色和证书状态判断是否可编辑
                        if current_user.role in ['admin', 'secretary']:
                            can_edit = True  # 管理员和教学秘书可以编辑任何状态
                        elif current_user.role == 'teacher':
                            can_edit = existing_cert.status in ['draft', 'pending_teacher']
                        else:  # student
                            can_edit = existing_cert.status == 'draft'
                        
                        # 确保 award_date 是字符串格式
                        award_date_str = ''
                        if existing_cert.award_date:
                            if isinstance(existing_cert.award_date, datetime):
                                award_date_str = existing_cert.award_date.strftime('%Y-%m-%d')
                            else:
                                award_date_str = str(existing_cert.award_date)
                        
                        extracted_info = {
                            'student_id': existing_cert.student_id,
                            'student_name': existing_cert.student_name,
                            'student_department': existing_cert.department,
                            'competition_name': existing_cert.competition_name,
                            'award_category': existing_cert.award_category,
                            'award_level': existing_cert.award_level,
                            'competition_type': existing_cert.competition_type,
                            'organizer': existing_cert.organizer,
                            'award_date': award_date_str,
                            'advisor': existing_cert.advisor,
                            'advisor_id': existing_cert.advisor_id or ''
                        }
                        file_path = existing_cert.file_path
                    else:
                        # 保存文件到 static/uploads 目录
                        original_filename = secure_filename(file.filename)
                        ext = os.path.splitext(original_filename)[1].lower()
                        if not ext:
                            ext = '.jpg'  # 默认扩展名
                        
                        user_folder = f"{current_user.account_id}_{current_user.name}"
                        
                        # 统一保存到 static/uploads 目录
                        base_dir = current_app.config.get('UPLOAD_FOLDER', 
                            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads'))
                        
                        file_type = 'image'  # 只支持图片
                        
                        save_dir = os.path.join(base_dir, user_folder)
                        os.makedirs(save_dir, exist_ok=True)
                        
                        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                        unique_filename = f"{date_str}_cert{ext}"
                        file_path = os.path.join(save_dir, unique_filename)
                        
                        with open(file_path, 'wb') as f:
                            f.write(file_content)
                        
                        # 保存文件记录
                        file_record = File(
                            user_id=current_user.user_id,
                            file_name=unique_filename,
                            file_path=file_path,
                            file_type=file_type,
                            file_size=len(file_content),
                            file_md5=file_md5,
                            upload_time=datetime.now()
                        )
                        db.session.add(file_record)
                        db.session.commit()
                        
                        flash('✅ 文件上传成功，请点击"AI识别"按钮提取证书信息', 'success')
                else:
                    flash('请选择要上传的文件', 'warning')
            
            elif action == 'extract':
                # AI识别
                file_path = request.form.get('file_path')
                file_md5 = request.form.get('file_md5')
                
                if file_path and os.path.exists(file_path):
                    try:
                        from flask_app.api.certificate_extractor import CertificateExtractor
                        import logging

                        logging.basicConfig(level=logging.DEBUG)
                        logger = logging.getLogger(__name__)

                        logger.info(f"开始AI识别文件: {file_path}")
                        extractor = CertificateExtractor()
                        logger.info(f"文件类型: image")

                        # 只支持图片识别
                        extracted_info = extractor.extract_certificate_info(file_path, 'image')
                        logger.info(f"AI识别结果: {extracted_info}")

                        if not extracted_info or all(v == '' for v in extracted_info.values()):
                            flash('⚠️ AI识别未返回有效数据，请检查API配置或稍后重试', 'warning')
                        else:
                            # 将列表类型的字段转换为字符串（逗号分隔）
                            for key, value in extracted_info.items():
                                if isinstance(value, list):
                                    extracted_info[key] = ', '.join(str(item) for item in value)

                            flash('✅ AI识别完成，请核对信息后保存', 'success')

                        # 预填充用户信息
                        if current_user.role == 'student':
                            extracted_info['student_id'] = current_user.account_id
                            if not extracted_info.get('student_name'):
                                extracted_info['student_name'] = current_user.name
                        elif current_user.role == 'teacher':
                            extracted_info['advisor'] = current_user.name
                            extracted_info['advisor_id'] = current_user.account_id

                    except ValueError as ve:
                        flash(f'⚠️ AI配置错误：{str(ve)}，请检查API密钥配置', 'warning')
                        logger.error(f"API配置错误: {ve}")
                        extracted_info = {}
                    except Exception as e:
                        import traceback
                        flash(f'❌ AI识别失败：{str(e)}', 'danger')
                        logger.error(f"AI识别异常: {e}\n{traceback.format_exc()}")
                        extracted_info = {}
                else:
                    flash('文件不存在，请重新上传', 'danger')
            
            elif action == 'save':
                # 保存证书
                file_path = request.form.get('file_path')
                file_md5 = request.form.get('file_md5')
                status = request.form.get('status', 'draft')
                
                # 验证数据
                cert_data = {
                    'student_id': request.form.get('student_id', ''),
                    'student_name': request.form.get('student_name', ''),
                    'department': request.form.get('department', ''),
                    'competition_name': request.form.get('competition_name', ''),
                    'award_category': request.form.get('award_category', ''),
                    'award_level': request.form.get('award_level', ''),
                    'competition_type': request.form.get('competition_type', ''),
                    'organizer': request.form.get('organizer', ''),
                    'award_date': request.form.get('award_date', ''),
                    'advisor': request.form.get('advisor', ''),
                    'advisor_id': request.form.get('advisor_id', '')
                }
                
                is_valid, error_msg, validated_data = validate_data(CertificateSubmitSchema, cert_data)
                
                if not is_valid:
                    flash(f'❌ 数据验证失败：{error_msg}', 'danger')
                    extracted_info = cert_data
                else:
                    # 检查是否为更新已有证书
                    existing_cert_id = request.form.get('existing_cert_id')
                    if existing_cert_id:
                        cert = Certificate.query.get(existing_cert_id)
                        if cert:
                            # 检查编辑权限
                            can_edit = False
                            if current_user.role in ['admin', 'secretary']:
                                can_edit = True
                            elif current_user.role == 'teacher' and cert.status in ['draft', 'pending_teacher']:
                                can_edit = True
                            elif current_user.role == 'student' and cert.status == 'draft':
                                can_edit = True
                            
                            if can_edit:
                                # 更新草稿
                                for key, value in validated_data.items():
                                    if key == 'student_department':
                                        setattr(cert, 'department', value)
                                    elif hasattr(cert, key):
                                        setattr(cert, key, value)
                                cert.department = validated_data.get('department', cert.department)
                                if status == 'submitted':
                                    # 根据角色确定提交后的状态
                                    if current_user.role == 'student':
                                        cert.status = 'pending_teacher'
                                    elif current_user.role == 'teacher':
                                        cert.status = 'pending_admin'
                                    else:
                                        cert.status = 'approved'
                                    cert.submitted_at = datetime.now()
                                db.session.commit()
                                flash('✅ 证书更新成功！', 'success')
                                return redirect(url_for('my_certs.index'))
                            else:
                                flash('此状态下的证书不可编辑', 'warning')
                                return redirect(url_for('my_certs.index'))
                    
                    # 创建新证书
                    # 根据角色确定提交后的状态
                    if status == 'submitted':
                        if current_user.role == 'student':
                            final_status = 'pending_teacher'
                        elif current_user.role == 'teacher':
                            final_status = 'pending_admin'
                        else:
                            final_status = 'approved'
                    else:
                        final_status = 'draft'
                    
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
                        award_date=parse_award_date(validated_data.get('award_date', '')),
                        advisor=validated_data['advisor'],
                        advisor_id=validated_data.get('advisor_id'),
                        file_path=file_path or '',
                        file_md5=file_md5 or '',
                        extraction_method='glm4v',
                        status=final_status,
                        created_at=datetime.now()
                    )
                    
                    if final_status != 'draft':
                        cert.submitted_at = datetime.now()
                    
                    db.session.add(cert)
                    db.session.commit()
                    
                    flash('✅ 证书保存成功！', 'success')
                    return redirect(url_for('my_certs.index'))
        
        # 确保 extracted_info 中的 award_date 是字符串格式
        if extracted_info and extracted_info.get('award_date'):
            award_date = extracted_info['award_date']
            if isinstance(award_date, datetime):
                extracted_info['award_date'] = award_date.strftime('%Y-%m-%d')
            elif award_date and not isinstance(award_date, str):
                extracted_info['award_date'] = str(award_date)
            # 如果已经是字符串，确保格式正确（取前10个字符，即 YYYY-MM-DD）
            elif isinstance(award_date, str) and len(award_date) > 10:
                extracted_info['award_date'] = award_date[:10]
        
        return self.render('admin/custom/certificate_upload.html',
                          extracted_info=extracted_info,
                          file_path=file_path,
                          file_md5=file_md5,
                          is_quick_upload=is_quick_upload,
                          existing_cert=existing_cert,
                          can_edit=can_edit,
                          colleges=colleges,
                          categories=categories,
                          levels=levels,
                          comp_types=comp_types,
                          deadline=SystemConfig.get_deadline_display() if current_user.role not in ['admin', 'secretary'] else None,
                          is_overdue=not SystemConfig.is_before_deadline() if current_user.role not in ['admin', 'secretary'] else False)
    
    def is_accessible(self):
        return current_user.is_authenticated

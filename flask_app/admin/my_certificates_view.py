"""
我的证书视图
"""
from flask import redirect, url_for, request, flash
from flask_admin import BaseView, expose
from flask_login import current_user
from datetime import datetime
import logging

from flask_app.models import Certificate, Dictionary, SystemConfig
from flask_app.schemas import CertificateSubmitSchema, validate_data
from flask_app import db
from flask_app.utils.date_utils import parse_award_date

logger = logging.getLogger(__name__)


class MyCertificatesView(BaseView):
    """我的证书视图"""
    
    @expose('/')
    def index(self, cls=None, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        # 获取当前用户的证书
        certificates = Certificate.query.filter_by(
            submitter_id=current_user.user_id
        ).order_by(Certificate.created_at.desc()).all()
        
        return self.render('admin/custom/my_certificates.html',
                          certificates=certificates)
    
    @expose('/edit/<string:cert_id>', methods=['GET', 'POST'])
    def edit(self, cert_id):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        cert = Certificate.query.get_or_404(cert_id)
        
        # 检查权限
        if cert.submitter_id != current_user.user_id:
            flash('您没有权限编辑此证书', 'danger')
            return redirect(url_for('my_certs.index'))
        
        # 根据角色检查编辑权限
        # 学生：只能在草稿状态编辑
        if current_user.role == 'student' and cert.status != 'draft':
            flash('已提交的证书不可编辑', 'warning')
            return redirect(url_for('my_certs.index'))
        
        # 教师：可以在草稿和待教师审核状态编辑
        if current_user.role == 'teacher' and cert.status not in ['draft', 'pending_teacher']:
            flash('此状态下的证书不可编辑', 'warning')
            return redirect(url_for('my_certs.index'))
        
        # 管理员和教学秘书：可以在任何状态编辑（教学秘书只能编辑本院证书）
        if current_user.role == 'secretary' and cert.department != current_user.department:
            flash('您没有权限编辑此证书', 'danger')
            return redirect(url_for('my_certs.index'))
        
        colleges = Dictionary.get_options('学院')
        categories = Dictionary.get_options('获奖类别')
        levels = Dictionary.get_options('获奖等级')
        comp_types = Dictionary.get_options('竞赛类型')
        
        # 非学生角色需要评分信息选项
        standard_scores = []
        contributions = []
        if current_user.role not in ['student']:
            standard_scores = Dictionary.get_options('标准分')
            contributions = Dictionary.get_options('贡献值')
        
        if request.method == 'POST':
            # 记录所有接收到的表单数据
            logger.info(f"=== 编辑证书POST请求开始 ===")
            logger.info(f"证书ID: {cert_id}")
            logger.info(f"接收到的所有表单参数: {dict(request.form)}")

            # 检查截止时间（非管理员用户）
            if current_user.role not in ['admin', 'secretary']:
                deadline = SystemConfig.get_deadline()
                if deadline and datetime.now() > deadline:
                    flash(f'❌ 已超过证书提交截止时间（{SystemConfig.get_deadline_display()}），无法继续操作', 'danger')
                    return redirect(url_for('my_certs.index'))

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

            # 先获取status，用于判断是否为提交操作
            # 检查所有可能的status参数来源
            raw_status = request.form.get('status')
            raw_action = request.form.get('action')
            raw_action_status = request.form.get('action_status')
            status = raw_action_status or raw_status or raw_action or 'draft'

            logger.info(f"原始status参数: {raw_status}")
            logger.info(f"原始action参数: {raw_action}")
            logger.info(f"原始action_status参数: {raw_action_status}")
            logger.info(f"最终status值: {status}")
            logger.info(f"当前用户角色: {current_user.role}")

            is_valid, error_msg, validated_data = validate_data(CertificateSubmitSchema, cert_data)

            if not is_valid:
                flash(f'❌ 数据验证失败：{error_msg}', 'danger')
                # 验证失败时，重新渲染编辑页面
                return self.render('admin/custom/certificate_edit.html',
                                  cert=cert,
                                  colleges=colleges,
                                  categories=categories,
                                  levels=levels,
                                  comp_types=comp_types,
                                  standard_scores=standard_scores,
                                  contributions=contributions)

            # 验证成功，更新证书信息
            cert.student_id = validated_data['student_id']
            cert.student_name = validated_data['student_name']
            cert.department = validated_data['department']
            cert.competition_name = validated_data['competition_name']
            cert.award_category = validated_data['award_category']
            cert.award_level = validated_data['award_level']
            cert.competition_type = validated_data['competition_type']
            cert.organizer = validated_data.get('organizer', '')
            cert.award_date = parse_award_date(validated_data.get('award_date', ''))
            cert.advisor = validated_data['advisor']
            cert.advisor_id = validated_data.get('advisor_id')
            
            # 处理评分信息（非学生角色）
            if current_user.role not in ['student']:
                standard_score = request.form.get('standard_score', '').strip()
                contribution = request.form.get('contribution', '').strip()
                cert.standard_score = standard_score if standard_score else None
                cert.contribution = contribution if contribution else None
            
            # 处理提交操作
            # 明确检查status是否为'submitted'
            if status and str(status).strip() == 'submitted':
                logger.info(f"进入提交审核分支，当前证书原状态: {cert.status}")
                # 根据角色确定提交后的状态
                if current_user.role == 'student':
                    cert.status = 'pending_teacher'
                    cert.submitted_at = datetime.now()
                    logger.info(f"学生提交，状态设置为: pending_teacher")
                    flash('✅ 证书已提交，等待教师审核！', 'success')
                elif current_user.role == 'teacher':
                    cert.status = 'pending_admin'
                    cert.submitted_at = datetime.now()
                    logger.info(f"教师提交，状态设置为: pending_admin")
                    flash('✅ 证书已提交，等待管理员审核！', 'success')
                else:
                    cert.status = 'approved'
                    cert.submitted_at = datetime.now()
                    logger.info(f"其他角色提交，状态设置为: approved")
                    flash('✅ 证书已审核通过！', 'success')
            else:
                # 保存草稿
                logger.info(f"进入保存草稿分支，status参数值: {status}")
                cert.status = 'draft'
                logger.info(f"证书状态设置为: draft")
                flash('✅ 证书保存成功！', 'success')

            db.session.commit()
            return redirect(url_for('my_certs.index'))
        
        return self.render('admin/custom/certificate_edit.html',
                          cert=cert,
                          colleges=colleges,
                          categories=categories,
                          levels=levels,
                          comp_types=comp_types,
                          standard_scores=standard_scores,
                          contributions=contributions)
    
    @expose('/delete/<string:cert_id>', methods=['POST'])
    def delete(self, cert_id):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        cert = Certificate.query.get_or_404(cert_id)
        
        if cert.submitter_id != current_user.user_id:
            flash('您没有权限删除此证书', 'danger')
            return redirect(url_for('my_certs.index'))
        
        # 根据角色检查删除权限
        # 学生：只能删除草稿
        if current_user.role == 'student' and cert.status != 'draft':
            flash('已提交的证书不可删除', 'warning')
            return redirect(url_for('my_certs.index'))
        
        # 教师：可以删除草稿和待教师审核状态的证书
        if current_user.role == 'teacher' and cert.status not in ['draft', 'pending_teacher']:
            flash('此状态下的证书不可删除', 'warning')
            return redirect(url_for('my_certs.index'))
        
        # 管理员：可以删除任何状态的证书
        
        db.session.delete(cert)
        db.session.commit()
        flash('✅ 证书已删除', 'success')
        return redirect(url_for('my_certs.index'))
    
    @expose('/view/<string:cert_id>')
    def view(self, cert_id):
        """查看证书详情（只读）"""
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        cert = Certificate.query.get_or_404(cert_id)
        
        # 检查权限：只能查看自己的证书
        if cert.submitter_id != current_user.user_id:
            flash('您没有权限查看此证书', 'danger')
            return redirect(url_for('my_certs.index'))
        
        colleges = Dictionary.get_options('学院')
        categories = Dictionary.get_options('获奖类别')
        levels = Dictionary.get_options('获奖等级')
        comp_types = Dictionary.get_options('竞赛类型')
        
        return self.render('admin/custom/certificate_view.html',
                          cert=cert,
                          colleges=colleges,
                          categories=categories,
                          levels=levels,
                          comp_types=comp_types)
    
    def is_accessible(self):
        return current_user.is_authenticated

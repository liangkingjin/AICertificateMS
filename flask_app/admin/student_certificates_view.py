"""
学生证书视图（教师用）
"""
from flask import redirect, url_for, request, flash, Response
from flask_admin import BaseView, expose
from flask_login import current_user
from datetime import datetime
import io
from urllib.parse import quote

from flask_app.models import Certificate, Dictionary
from flask_app import db
from flask_app.utils.date_utils import parse_award_date


class StudentCertificatesView(BaseView):
    """学生证书视图（教师用）"""
    
    @expose('/')
    def index(self, cls=None, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))

        if current_user.role not in ['teacher', 'admin', 'secretary']:
            flash('只有教师、教学秘书和管理员可以访问此页面', 'warning')
            return redirect(url_for('admin.index'))

        # 构建基础查询（根据角色）
        if current_user.role == 'teacher':
            query = Certificate.query.filter_by(advisor_id=current_user.account_id)
        elif current_user.role == 'secretary':
            query = Certificate.query.filter_by(department=current_user.department)
        else:
            query = Certificate.query

        # 执行查询
        certificates = query.order_by(Certificate.created_at.desc()).all()

        return self.render('admin/custom/student_certificates.html',
                          certificates=certificates)
    
    @expose('/export')
    def export(self):
        """导出证书数据为Excel"""
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        if current_user.role not in ['teacher', 'admin', 'secretary']:
            flash('没有权限', 'warning')
            return redirect(url_for('admin.index'))

        from openpyxl import Workbook

        # 构建基础查询（根据角色）
        if current_user.role == 'teacher':
            query = Certificate.query.filter_by(advisor_id=current_user.account_id)
        elif current_user.role == 'secretary':
            query = Certificate.query.filter_by(department=current_user.department)
        else:
            query = Certificate.query

        # 执行查询
        certificates = query.order_by(Certificate.created_at.desc()).all()
        
        # 创建Excel
        wb = Workbook()
        ws = wb.active
        ws.title = '证书数据'
        
        # 表头
        headers = ['序号', '学号', '姓名', '学院', '竞赛项目', '获奖类别', '获奖等级', 
                   '竞赛类型', '获奖时间', '指导教师', '指导老师工号', '标准分', '贡献值', '状态', '创建时间']
        ws.append(headers)
        
        # 数据行
        for idx, cert in enumerate(certificates, 1):
            ws.append([
                idx,
                cert.student_id,
                cert.student_name,
                cert.department,
                cert.competition_name,
                cert.award_category,
                cert.award_level,
                cert.competition_type,
                cert.award_date.strftime('%Y-%m-%d') if cert.award_date else '',
                cert.advisor,
                cert.advisor_id or '',
                cert.standard_score or '',
                cert.contribution or '',
                cert.status_display,
                cert.created_at.strftime('%Y-%m-%d %H:%M') if cert.created_at else ''
            ])
        
        # 输出
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'证书数据_{timestamp}.xlsx'
        filename_encoded = quote(filename.encode('utf-8'))

        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{filename_encoded}",
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
    
    @expose('/edit/<string:cert_id>', methods=['GET', 'POST'])
    def edit(self, cert_id):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if current_user.role not in ['teacher', 'admin', 'secretary']:
            flash('没有权限', 'warning')
            return redirect(url_for('admin.index'))
        
        cert = Certificate.query.get_or_404(cert_id)
        
        # 检查权限
        if current_user.role == 'teacher' and cert.advisor_id != current_user.account_id:
            flash('您没有权限编辑此证书', 'danger')
            return redirect(url_for('student_certs.index'))
        
        # 教学秘书只能编辑本院证书
        if current_user.role == 'secretary' and cert.department != current_user.department:
            flash('您没有权限编辑此证书', 'danger')
            return redirect(url_for('student_certs.index'))
        
        colleges = Dictionary.get_options('学院')
        categories = Dictionary.get_options('获奖类别')
        levels = Dictionary.get_options('获奖等级')
        comp_types = Dictionary.get_options('竞赛类型')
        standard_scores = Dictionary.get_options('标准分')
        contributions = Dictionary.get_options('贡献值')
        
        # 判断是否可以编辑
        # 管理员和教学秘书可以编辑任何状态，老师只能编辑草稿和待教师审核状态
        if current_user.role in ['admin', 'secretary']:
            can_edit = True
        elif current_user.role == 'teacher':
            can_edit = cert.status in ['draft', 'pending_teacher']
        else:
            can_edit = False
        
        if request.method == 'POST':
            if not can_edit:
                flash('您没有权限编辑此证书', 'danger')
                return redirect(url_for('student_certs.index'))

            # 获取操作类型（优先从隐藏字段获取）
            action = request.form.get('action_status') or request.form.get('action', 'save')
            
            cert.competition_name = request.form.get('competition_name', cert.competition_name)
            cert.student_name = request.form.get('student_name', cert.student_name)
            cert.student_id = request.form.get('student_id', cert.student_id)
            cert.department = request.form.get('department', cert.department)
            cert.award_category = request.form.get('award_category', cert.award_category)
            cert.award_level = request.form.get('award_level', cert.award_level)
            cert.competition_type = request.form.get('competition_type', cert.competition_type)
            cert.advisor = request.form.get('advisor', cert.advisor)
            cert.advisor_id = request.form.get('advisor_id', cert.advisor_id)
            
            # 标准分和贡献值（字符串类型）
            standard_score = request.form.get('standard_score')
            contribution = request.form.get('contribution')
            
            if standard_score:
                cert.standard_score = standard_score
            
            if contribution:
                cert.contribution = contribution
            
            # 获奖时间
            award_date_str = request.form.get('award_date')
            if award_date_str:
                cert.award_date = parse_award_date(award_date_str)
            
            # 处理提交操作
            if action == 'submit' and cert.status in ['draft', 'pending_teacher']:
                # 教师提交后进入待管理员审核
                cert.status = 'pending_admin'
                cert.submitted_at = datetime.now()
                db.session.commit()
                flash('✅ 证书已提交，等待管理员审核！', 'success')
            else:
                db.session.commit()
                flash('✅ 证书更新成功！', 'success')
            
            return redirect(url_for('student_certs.index'))
        
        return self.render('admin/custom/student_certificate_edit.html',
                          cert=cert,
                          can_edit=can_edit,
                          colleges=colleges,
                          categories=categories,
                          levels=levels,
                          comp_types=comp_types,
                          standard_scores=standard_scores,
                          contributions=contributions)
    
    @expose('/approve/<string:cert_id>')
    def approve(self, cert_id):
        """审核通过证书"""
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.role not in ['teacher', 'admin', 'secretary']:
            flash('没有权限', 'warning')
            return redirect(url_for('admin.index'))
        
        cert = Certificate.query.get_or_404(cert_id)
        
        # 检查权限
        if current_user.role == 'teacher':
            # 老师只能通过自己指导的证书
            if cert.advisor_id != current_user.account_id:
                flash('您没有权限审核此证书', 'danger')
                return redirect(url_for('student_certs.index'))
            # 老师只能通过待教师审核状态的证书
            if cert.status != 'pending_teacher':
                flash('只能审核"待教师审核"状态的证书', 'warning')
                return redirect(url_for('student_certs.index'))
            # 老师通过后变成待管理员审核
            cert.status = 'pending_admin'
            flash('✅ 证书已通过教师审核，等待管理员审核！', 'success')
        elif current_user.role == 'secretary':
            # 教学秘书只能审核本院证书，权限同管理员
            if cert.department != current_user.department:
                flash('您没有权限审核此证书', 'danger')
                return redirect(url_for('student_certs.index'))
            cert.status = 'approved'
            flash('✅ 证书审核通过！', 'success')
        else:
            # 管理员可以通过任何状态的证书，直接变成审核通过
            cert.status = 'approved'
            flash('✅ 证书审核通过！', 'success')
        
        db.session.commit()
        return redirect(url_for('student_certs.index'))
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in ['teacher', 'admin', 'secretary']
    
    def is_visible(self):
        return current_user.is_authenticated and current_user.role in ['teacher', 'admin', 'secretary']

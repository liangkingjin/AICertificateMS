"""
Flask-Admin 模块初始化
"""
from flask import redirect, url_for, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.menu import MenuLink
from flask_login import current_user
from flask_app import db


class SecureAdminIndexView(AdminIndexView):
    """安全的管理首页视图 - AdminLTE3 风格仪表盘"""
    
    @expose('/')
    def index(self, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        from flask_app.models import User, Certificate, Dictionary
        from sqlalchemy import func
        
        # 判断是否需要按学院筛选（教师和教学秘书只能看本院数据）
        is_limited = current_user.role in ['teacher', 'secretary']
        user_department = current_user.department if is_limited else None
        
        # 统计数据
        if is_limited:
            # 教师和教学秘书只能看本院数据
            stats = {
                'total_users': User.query.filter_by(department=user_department).count(),
                'total_students': User.query.filter_by(role='student', department=user_department).count(),
                'total_teachers': User.query.filter_by(role='teacher', department=user_department).count(),
                'total_secretaries': User.query.filter_by(role='secretary', department=user_department).count(),
                'total_admins': User.query.filter_by(role='admin').count(),  # 管理员数量不限制
                'total_certificates': Certificate.query.filter_by(department=user_department).count(),
                'pending_certificates': Certificate.query.filter(
                    Certificate.department == user_department,
                    Certificate.status.not_in(['draft', 'approved'])
                ).count(),
                'draft_certificates': Certificate.query.filter_by(department=user_department, status='draft').count(),
            }
        else:
            # 管理员和学生看全部数据
            stats = {
                'total_users': User.query.count(),
                'total_students': User.query.filter_by(role='student').count(),
                'total_teachers': User.query.filter_by(role='teacher').count(),
                'total_secretaries': User.query.filter_by(role='secretary').count(),
                'total_admins': User.query.filter_by(role='admin').count(),
                'total_certificates': Certificate.query.count(),
                'pending_certificates': Certificate.query.filter(
                    Certificate.status.not_in(['draft', 'approved'])
                ).count(),
                'draft_certificates': Certificate.query.filter_by(status='draft').count(),
            }
        
        # 按学院统计证书 - 转换为可JSON序列化的列表
        dept_query = db.session.query(
            Certificate.department, 
            func.count(Certificate.cert_id)
        )
        if is_limited:
            dept_query = dept_query.filter(Certificate.department == user_department)
        dept_query = dept_query.group_by(Certificate.department).order_by(
            func.count(Certificate.cert_id).desc()
        ).all()
        dept_stats = [{'name': d[0] or '未知', 'count': d[1]} for d in dept_query]

        # 按获奖类别统计
        category_query = db.session.query(
            Certificate.award_category,
            func.count(Certificate.cert_id)
        )
        if is_limited:
            category_query = category_query.filter(Certificate.department == user_department)
        category_query = category_query.group_by(Certificate.award_category).order_by(
            func.count(Certificate.cert_id).desc()
        ).all()
        category_stats = [{'name': c[0] or '未知', 'count': c[1]} for c in category_query]

        # 按获奖等级统计
        level_query = db.session.query(
            Certificate.award_level,
            func.count(Certificate.cert_id)
        )
        if is_limited:
            level_query = level_query.filter(Certificate.department == user_department)
        level_query = level_query.group_by(Certificate.award_level).order_by(
            func.count(Certificate.cert_id).desc()
        ).all()
        level_stats = [{'name': l[0] or '未知', 'count': l[1]} for l in level_query]

        # 按竞赛类型统计
        type_query = db.session.query(
            Certificate.competition_type,
            func.count(Certificate.cert_id)
        )
        if is_limited:
            type_query = type_query.filter(Certificate.department == user_department)
        type_query = type_query.group_by(Certificate.competition_type).all()
        type_stats = [{'name': t[0] or '未知', 'count': t[1]} for t in type_query]
        
        # 根据角色显示不同内容
        if current_user.role == 'student':
            # 学生只看自己的证书
            my_certs = Certificate.query.filter_by(submitter_id=current_user.user_id).count()
            my_submitted = Certificate.query.filter_by(
                submitter_id=current_user.user_id, 
                status='submitted'
            ).count()
            my_draft = Certificate.query.filter_by(
                submitter_id=current_user.user_id, 
                status='draft'
            ).count()
            stats.update({
                'my_certs': my_certs,
                'my_submitted': my_submitted,
                'my_draft': my_draft
            })
        elif current_user.role == 'teacher':
            # 教师看自己指导的学生证书
            guided_certs = Certificate.query.filter_by(advisor_id=current_user.account_id).count()
            stats.update({
                'guided_certs': guided_certs,
                'my_department': current_user.department
            })
        elif current_user.role == 'secretary':
            # 教学秘书看本院的证书
            dept_certs = Certificate.query.filter_by(department=current_user.department).count()
            dept_pending = Certificate.query.filter(
                Certificate.department == current_user.department,
                Certificate.status.in_(['pending_teacher', 'pending_admin'])
            ).count()
            stats.update({
                'dept_certs': dept_certs,
                'dept_pending': dept_pending,
                'my_department': current_user.department
            })
        
        return self.render('admin/index.html', 
                          stats=stats,
                          dept_stats=dept_stats,
                          category_stats=category_stats,
                          level_stats=level_stats,
                          type_stats=type_stats)


def init_admin(app):
    """初始化 Flask-Admin"""
    from flask_app.admin.views import (
        UserAdminView, CertificateAdminView, DictionaryAdminView,
        SystemConfigAdminView, APIKeyAdminView, FileAdminView
    )
    from flask_app.admin.custom_views import (
        CertificateUploadView, UserImportView, MyCertificatesView,
        StudentCertificatesView, StatisticsView
    )
    from flask_app.models import User, Certificate, Dictionary, SystemConfig, APIKey, File
    
    admin = Admin(
        app,
        name='证书管理系统',
        index_view=SecureAdminIndexView(
            name='仪表盘',
            template='admin/index.html',
            url='/admin'
        )
    )
    
    # ===== 证书管理 =====
    admin.add_view(CertificateUploadView(
        name='上传证书',
        endpoint='cert_upload',
        category='证书管理'
    ))
    
    admin.add_view(MyCertificatesView(
        name='我的证书',
        endpoint='my_certs',
        category='证书管理'
    ))
    
    admin.add_view(StudentCertificatesView(
        name='证书数据',
        endpoint='student_certs',
        category='证书管理'
    ))
    
    # ===== 用户管理（仅管理员） =====
    admin.add_view(UserAdminView(
        User, db.session,
        name='用户列表',
        endpoint='user_admin',
        category='用户管理'
    ))
    
    admin.add_view(UserImportView(
        name='批量导入',
        endpoint='user_import',
        category='用户管理'
    ))
    
    # ===== 系统设置（仅管理员） =====
    admin.add_view(DictionaryAdminView(
        Dictionary, db.session,
        name='字典管理',
        endpoint='dict_admin',
        category='系统设置'
    ))
    
    admin.add_view(SystemConfigAdminView(
        SystemConfig, db.session,
        name='系统配置',
        endpoint='config_admin',
        category='系统设置'
    ))
    
    admin.add_view(APIKeyAdminView(
        APIKey, db.session,
        name='API密钥',
        endpoint='apikey_admin',
        category='系统设置'
    ))
    
    admin.add_view(FileAdminView(
        File, db.session,
        name='文件管理',
        endpoint='file_admin',
        category='系统设置'
    ))
    
    # ===== 统计报表 =====
    admin.add_view(StatisticsView(
        name='统计报表',
        endpoint='statistics',
        category='数据分析'
    ))
    
    # ===== 退出链接 =====
    admin.add_link(MenuLink(name='退出登录', url='/auth/logout'))
    
    return admin

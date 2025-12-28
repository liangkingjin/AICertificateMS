"""
统计报表视图
"""
from flask import redirect, url_for, flash
from flask_admin import BaseView, expose
from flask_login import current_user
from datetime import datetime, timedelta

from flask_app.models import Certificate, User
from flask_app import db
from sqlalchemy import func, extract


class StatisticsView(BaseView):
    """统计报表视图"""
    
    @expose('/')
    def index(self, cls=None, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.role not in ['teacher', 'admin', 'secretary']:
            flash('只有教师、教学秘书和管理员可以访问统计报表', 'warning')
            return redirect(url_for('admin.index'))
        
        # 教师和教学秘书只能看本院数据
        is_limited = current_user.role in ['teacher', 'secretary']
        user_department = current_user.department if is_limited else None
        
        # 基础统计
        if is_limited:
            total_certificates = Certificate.query.filter_by(department=user_department).count()
            submitted_certificates = Certificate.query.filter_by(department=user_department, status='submitted').count()
            total_students = User.query.filter_by(role='student', department=user_department).count()
            total_teachers = User.query.filter_by(role='teacher', department=user_department).count()
        else:
            total_certificates = Certificate.query.count()
            submitted_certificates = Certificate.query.filter_by(status='submitted').count()
            total_students = User.query.filter_by(role='student').count()
            total_teachers = User.query.filter_by(role='teacher').count()
        
        # 按学院统计
        dept_query = db.session.query(
            Certificate.department,
            func.count(Certificate.cert_id)
        )
        if is_limited:
            dept_query = dept_query.filter(Certificate.department == user_department)
        dept_stats = dept_query.group_by(Certificate.department).order_by(
            func.count(Certificate.cert_id).desc()
        ).all()
        
        dept_data = {
            'labels': [d[0] or '未知' for d in dept_stats],
            'data': [d[1] for d in dept_stats]
        }
        
        # 按获奖类别统计
        category_query = db.session.query(
            Certificate.award_category,
            func.count(Certificate.cert_id)
        )
        if is_limited:
            category_query = category_query.filter(Certificate.department == user_department)
        category_stats = category_query.group_by(Certificate.award_category).order_by(
            func.count(Certificate.cert_id).desc()
        ).all()

        category_data = {
            'labels': [c[0] or '未知' for c in category_stats],
            'data': [c[1] for c in category_stats]
        }

        # 按获奖等级统计
        level_query = db.session.query(
            Certificate.award_level,
            func.count(Certificate.cert_id)
        )
        if is_limited:
            level_query = level_query.filter(Certificate.department == user_department)
        level_stats = level_query.group_by(Certificate.award_level).order_by(
            func.count(Certificate.cert_id).desc()
        ).all()

        level_data = {
            'labels': [l[0] or '未知' for l in level_stats],
            'data': [l[1] for l in level_stats]
        }

        # 按竞赛类型统计
        type_query = db.session.query(
            Certificate.competition_type,
            func.count(Certificate.cert_id)
        )
        if is_limited:
            type_query = type_query.filter(Certificate.department == user_department)
        type_stats = type_query.group_by(Certificate.competition_type).order_by(
            func.count(Certificate.cert_id).desc()
        ).all()
        
        type_data = {
            'labels': [t[0] or '未知' for t in type_stats],
            'data': [t[1] for t in type_stats]
        }
        
        # 月度趋势（最近12个月）
        trend_data = {'labels': [], 'data': []}
        for i in range(11, -1, -1):
            date = datetime.now() - timedelta(days=i*30)
            month_label = date.strftime('%Y-%m')
            query = Certificate.query.filter(
                func.strftime('%Y-%m', Certificate.created_at) == month_label
            )
            if is_limited:
                query = query.filter(Certificate.department == user_department)
            count = query.count()
            trend_data['labels'].append(month_label)
            trend_data['data'].append(count)
        
        # 学院详细统计
        by_department = []
        for dept_name, dept_count in dept_stats:
            student_count = User.query.filter_by(role='student', department=dept_name).count()
            national_count = Certificate.query.filter(
                Certificate.department == dept_name,
                Certificate.award_category.like('%国家%')
            ).count()
            provincial_count = Certificate.query.filter(
                Certificate.department == dept_name,
                Certificate.award_category.like('%省%')
            ).count()
            
            by_department.append({
                'name': dept_name or '未知',
                'total': dept_count,
                'students': student_count or 1,
                'national': national_count,
                'provincial': provincial_count,
                'other': dept_count - national_count - provincial_count
            })
        
        stats = {
            'total_certificates': total_certificates,
            'submitted_certificates': submitted_certificates,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'dept_data': dept_data,
            'category_data': category_data,
            'level_data': level_data,
            'type_data': type_data,
            'trend_data': trend_data,
            'by_department': by_department
        }
        
        return self.render('admin/custom/statistics.html', stats=stats)
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in ['teacher', 'admin', 'secretary']
    
    def is_visible(self):
        return current_user.is_authenticated and current_user.role in ['teacher', 'admin', 'secretary']

"""
证书模型 - 兼容现有数据库结构
"""
from flask_app import db
from datetime import datetime
import uuid


class Certificate(db.Model):
    """证书模型"""
    __tablename__ = 'certificate'
    
    cert_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submitter_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    submitter_role = db.Column(db.String(20), nullable=False)
    student_id = db.Column(db.String(20), nullable=False)
    student_name = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    competition_name = db.Column(db.String(200), nullable=False)
    award_category = db.Column(db.String(50), nullable=False)  # 国家级、省级等
    award_level = db.Column(db.String(50), nullable=False)  # 一等奖、二等奖等
    competition_type = db.Column(db.String(20), nullable=False)  # A类、B类
    organizer = db.Column(db.String(200), nullable=False)
    award_date = db.Column(db.Date, nullable=True)  # 获奖日期，精确到日
    advisor = db.Column(db.String(50), nullable=False)  # 指导教师姓名
    advisor_id = db.Column(db.String(20), nullable=True)  # 指导教师工号
    file_path = db.Column(db.String(500), nullable=False)
    file_md5 = db.Column(db.String(32), nullable=False, index=True)
    extraction_method = db.Column(db.String(50), nullable=False)  # glm4v/baidu等
    extraction_confidence = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=False)  # draft/submitted
    standard_score = db.Column(db.String(50), nullable=True)  # 标准分（字典选项）
    contribution = db.Column(db.String(50), nullable=True)  # 贡献值（字典选项）
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True)
    
    @property
    def status_display(self):
        """状态中文显示"""
        status_map = {
            'draft': '草稿',
            'submitted': '已提交',
            'pending_teacher': '待教师审核',
            'pending_admin': '待管理员审核',
            'approved': '已通过'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def is_submitted(self):
        """是否已提交（非草稿状态）"""
        return self.status != 'draft'
    
    @property
    def is_approved(self):
        """是否已审核通过"""
        return self.status == 'approved'
    
    @property
    def can_edit_by_student(self):
        """学生是否可编辑"""
        return self.status == 'draft'
    
    @property
    def can_edit_by_teacher(self):
        """教师是否可编辑"""
        return self.status in ['draft', 'pending_teacher']
    
    @property
    def is_draft(self):
        """是否为草稿"""
        return self.status == 'draft'
    
    def submit(self, role='student'):
        """提交证书，根据角色设置不同状态"""
        if role == 'student':
            self.status = 'pending_teacher'
        elif role == 'teacher':
            self.status = 'pending_admin'
        else:  # admin
            self.status = 'approved'
        self.submitted_at = datetime.now()
    
    def __repr__(self):
        return f'<Certificate {self.cert_id}: {self.student_name} - {self.competition_name}>'

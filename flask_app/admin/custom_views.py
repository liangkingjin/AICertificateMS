"""
Flask-Admin 自定义视图

此模块已重构，实际视图已拆分到独立的视图文件中。
保留此文件是为了向后兼容，所有视图类现在从对应模块导入。
"""
from flask_app.admin.certificate_upload_view import CertificateUploadView
from flask_app.admin.my_certificates_view import MyCertificatesView
from flask_app.admin.student_certificates_view import StudentCertificatesView
from flask_app.admin.user_import_view import UserImportView
from flask_app.admin.statistics_view import StatisticsView

__all__ = [
    'CertificateUploadView',
    'MyCertificatesView',
    'StudentCertificatesView',
    'UserImportView',
    'StatisticsView'
]

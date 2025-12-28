"""
Flask-Admin ModelView 视图
"""
from flask import redirect, url_for, request, flash
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Widget
from flask_login import current_user
from wtforms import SelectField, PasswordField
from wtforms.validators import Optional
from datetime import datetime
from flask_app.models import Dictionary


class SecureModelView(ModelView):
    """基础安全模型视图"""
    
    # 模板配置 - 使用中文汉化模板
    list_template = 'admin/model/list_override.html'
    create_template = 'admin/model/create_zh.html'
    edit_template = 'admin/model/edit_zh.html'
    
    # 分页
    page_size = 20
    can_set_page_size = True
    
    def is_accessible(self):
        """检查是否可访问"""
        return current_user.is_authenticated and current_user.role == 'admin'
    
    def inaccessible_callback(self, name, **kwargs):
        """无权限时的回调"""
        flash('您没有权限访问此页面', 'warning')
        return redirect(url_for('auth.login', next=request.url))


class UserAdminView(SecureModelView):
    """用户管理视图"""
    
    # 列表显示字段
    column_list = ['account_id', 'name', 'role', 'department', 'email', 
                   'advisor_id', 'is_active', 'created_at', 'created_by']
    
    # 可搜索字段
    column_searchable_list = ['account_id', 'name', 'email', 'department']
    
    # 可筛选字段
    column_filters = ['role', 'department', 'is_active', 'created_by']
    
    # 可编辑字段（行内编辑）
    column_editable_list = ['is_active']
    
    # 可排序字段
    column_sortable_list = ['account_id', 'name', 'role', 'created_at']
    
    # 默认排序
    column_default_sort = ('created_at', True)
    
    # 字段标签
    column_labels = {
        'user_id': 'ID',
        'account_id': '学（工）号',
        'name': '姓名',
        'role': '角色',
        'department': '单位',
        'email': '邮箱',
        'advisor_id': '指导老师工号',
        'is_active': '状态',
        'created_at': '创建时间',
        'created_by': '创建来源'
    }
    
    # 字段格式化
    column_formatters = {
        'role': lambda v, c, m, p: {
            'student': '🎓 学生', 
            'teacher': '👨‍🏫 教师',
            'secretary': '📝 教学秘书',
            'admin': '👔 管理员'
        }.get(m.role, m.role),
        'is_active': lambda v, c, m, p: '✅ 启用' if m.is_active else '❌ 禁用',
        'created_by': lambda v, c, m, p: {
            'self_register': '自行注册',
            'admin_import': '管理员导入',
            'system': '系统创建'
        }.get(m.created_by, m.created_by)
    }
    
    # 表单排除字段
    form_excluded_columns = ['password_hash', 'certificates', 'files', 'created_at', 'updated_at', 'created_by']
    
    # 表单字段参数
    form_args = {
        'account_id': {'label': '学（工）号'},
        'name': {'label': '姓名'},
        'role': {'label': '角色'},
        'department': {'label': '单位'},
        'email': {'label': '邮箱'},
        'advisor_id': {'label': '指导老师工号'},
        'is_active': {'label': '启用状态'},
        'created_by': {'label': '创建来源'}
    }
    
    # 导出配置
    can_export = True
    export_types = ['csv', 'xlsx']
    export_max_rows = 0
    
    # 创建/编辑时的字段覆盖
    form_overrides = {
        'role': SelectField,
        'department': SelectField
    }
    
    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.department.choices = Dictionary.get_options('学院')
        form.role.choices = Dictionary.get_options('角色')
        return form
    
    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.department.choices = Dictionary.get_options('学院')
        form.role.choices = Dictionary.get_options('角色')
        return form
    
    def on_model_change(self, form, model, is_created):
        """创建用户时设置默认密码"""
        if is_created:
            # 新建用户时，设置默认密码为账号
            model.set_password(model.account_id)
            model.created_by = 'system'
        return super().on_model_change(form, model, is_created)


class CertificateAdminView(SecureModelView):
    """证书管理视图（管理员）"""
    
    # 列表显示字段
    column_list = [
        'cert_id', 'student_id', 'student_name', 'department',
        'competition_name', 'award_category', 'award_level',
        'competition_type', 'advisor', 'status', 'submitted_at'
    ]
    
    # 可搜索字段
    column_searchable_list = ['student_id', 'student_name', 'competition_name', 'advisor']
    
    # 可筛选字段
    column_filters = ['department', 'award_category', 'award_level', 
                      'competition_type', 'status', 'submitter_role']
    
    # 可排序字段
    column_sortable_list = ['cert_id', 'student_id', 'student_name', 'submitted_at', 'created_at']
    
    # 默认排序
    column_default_sort = ('created_at', True)
    
    # 字段标签
    column_labels = {
        'cert_id': 'ID',
        'submitter_id': '提交者ID',
        'submitter_role': '提交者角色',
        'student_id': '学号',
        'student_name': '学生姓名',
        'department': '学院',
        'competition_name': '竞赛项目',
        'award_category': '获奖类别',
        'award_level': '获奖等级',
        'competition_type': '竞赛类型',
        'organizer': '主办单位',
        'award_date': '获奖时间',
        'advisor': '指导教师',
        'advisor_id': '指导老师工号',
        'file_path': '文件路径',
        'file_md5': '文件MD5',
        'extraction_method': '识别方法',
        'extraction_confidence': '识别置信度',
        'status': '状态',
        'standard_score': '标准分',
        'contribution': '贡献值',
        'created_at': '创建时间',
        'submitted_at': '提交时间'
    }
    
    # 字段格式化
    column_formatters = {
        'status': lambda v, c, m, p: '📝 草稿' if m.status == 'draft' else '✅ 已提交',
        'submitter_role': lambda v, c, m, p: {
            'student': '学生', 
            'teacher': '教师'
        }.get(m.submitter_role, m.submitter_role)
    }
    
    # 表单排除字段
    form_excluded_columns = ['submitter', 'file_md5', 'extraction_method', 
                             'extraction_confidence', 'created_at']
    
    # 表单字段覆盖
    form_overrides = {
        'department': SelectField,
        'award_category': SelectField,
        'award_level': SelectField,
        'competition_type': SelectField,
        'status': SelectField
    }
    
    form_choices = {
        'status': [
            ('draft', '草稿'),
            ('submitted', '已提交')
        ]
    }
    
    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.department.choices = Dictionary.get_options('学院')
        form.award_category.choices = Dictionary.get_options('获奖类别')
        form.award_level.choices = Dictionary.get_options('获奖等级')
        form.competition_type.choices = Dictionary.get_options('竞赛类型')
        return form
    
    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.department.choices = Dictionary.get_options('学院')
        form.award_category.choices = Dictionary.get_options('获奖类别')
        form.award_level.choices = Dictionary.get_options('获奖等级')
        form.competition_type.choices = Dictionary.get_options('竞赛类型')
        return form
    
    # 导出配置
    can_export = True
    export_types = ['csv', 'xlsx']
    export_max_rows = 0
    
    # 列导出映射
    column_export_list = [
        'cert_id', 'student_id', 'student_name', 'department',
        'competition_name', 'award_category', 'award_level',
        'competition_type', 'organizer', 'award_date',
        'advisor', 'advisor_id', 'status', 'standard_score',
        'contribution', 'submitted_at'
    ]


class DictionaryAdminView(SecureModelView):
    """字典管理视图"""
    
    column_list = ['dict_name', 'parent', 'description', 'status', 'updated_at']
    column_searchable_list = ['dict_name', 'description']
    column_filters = ['status', 'parent_id']
    column_sortable_list = ['dict_id', 'dict_name', 'created_at', 'updated_at']
    column_default_sort = ('created_at', True)
    
    column_labels = {
        'dict_id': 'ID',
        'dict_name': '名称',
        'parent_id': '父节点',
        'parent': '父节点',
        'description': '描述',
        'status': '状态',
        'created_at': '创建时间',
        'updated_at': '更新时间',
        'updated_by': '更新人'
    }
    
    column_formatters = {
        'parent': lambda v, c, m, p: m.parent.dict_name if m.parent else '📌 顶级数据',
        'status': lambda v, c, m, p: '✅ 启用' if m.status else '❌ 禁用'
    }
    
    form_excluded_columns = ['children', 'created_at', 'updated_at', 'parent', 'parent_id']  # 排除 parent 关系和时间字段
    
    # 父节点选择 - 使用 form_extra_fields
    form_extra_fields = {
        'parent_select': SelectField('父节点')
    }
    
    def _get_parent_choices(self):
        """获取父节点选项（显示所有字典数据）"""
        choices = [('', '-- 无（顶级数据） --')]
        all_items = Dictionary.query.filter_by(status=True).order_by(Dictionary.created_at.desc()).all()
        for item in all_items:
            if item.is_top_level:
                label = f"📌 {item.dict_name}"
            else:
                label = f"  └── {item.dict_name}"
            choices.append((str(item.dict_id), label))
        return choices
    
    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.parent_select.choices = self._get_parent_choices()
        return form
    
    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.parent_select.choices = self._get_parent_choices()
        # 设置当前值
        if obj and obj.parent_id:
            form.parent_select.data = str(obj.parent_id)
        return form
    
    def on_model_change(self, form, model, is_created):
        """表单提交时处理父节点字段"""
        if hasattr(form, 'parent_select'):
            parent_val = form.parent_select.data
            if parent_val in ('', None, 'None'):
                model.parent_id = None
            else:
                model.parent_id = parent_val
        return super().on_model_change(form, model, is_created)
    
    can_export = True
    export_types = ['csv', 'xlsx']


class SystemConfigAdminView(SecureModelView):
    """系统配置视图"""
    
    column_list = ['config_key', 'config_value', 'description', 'updated_at']
    column_searchable_list = ['config_key', 'description']
    column_sortable_list = ['config_id', 'config_key', 'updated_at']
    column_default_sort = ('updated_at', True)
    
    column_labels = {
        'config_id': 'ID',
        'config_key': '配置键',
        'config_value': '配置值',
        'description': '描述',
        'updated_at': '更新时间',
        'updated_by': '更新人'
    }
    
    form_excluded_columns = ['updated_at']
    
    form_widget_args = {
        'config_value': {
            'rows': 5
        }
    }
    
    can_delete = False  # 禁止删除系统配置
    
    def create_form(self, obj=None):
        form = super().create_form(obj)
        self._apply_config_widgets(form)
        return form
    
    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        self._apply_config_widgets(form)
        return form
    
    def _apply_config_widgets(self, form):
        """根据配置键应用不同的表单控件"""
        if hasattr(form, 'config_key') and hasattr(form, 'config_value'):
            config_key = form.config_key.data if form.config_key.data else ''
            
            if config_key == 'deadline':
                form.config_value.description = '格式: YYYY-MM-DD HH:MM'
                form.config_value.render_kw = {
                    'placeholder': '例如: 2025-12-31 23:59',
                    'class': 'form-control',
                    'type': 'datetime-local',
                    'step': '60'
                }
            elif config_key == 'ai_prompt':
                form.config_value.render_kw = {
                    'rows': 10,
                    'placeholder': '输入AI识别提示词...'
                }
    
    def on_model_change(self, form, model, is_created):
        """保存前验证截止时间格式"""
        if model.config_key == 'deadline':
            deadline_str = model.config_value.strip()
            if deadline_str:
                try:
                    datetime.strptime(deadline_str, '%Y-%m-%d %H:%M')
                except ValueError:
                    from wtforms import ValidationError
                    raise ValidationError('截止时间格式无效，请使用格式: YYYY-MM-DD HH:MM')
        return super().on_model_change(form, model, is_created)


class APIKeyAdminView(SecureModelView):
    """API密钥管理视图"""
    
    column_list = ['model_name', 'api_key', 'is_active',
                   'usage_count', 'max_usage', 'last_used_at', 'created_at']
    column_searchable_list = ['model_name']
    column_filters = ['is_active', 'model_name']
    column_sortable_list = ['key_id', 'model_name', 'usage_count', 'last_used_at', 'created_at']
    column_default_sort = ('created_at', True)
    
    column_labels = {
        'key_id': 'ID',
        'model_name': '模型名称',
        'api_key': 'API密钥',
        'prompt': '提示词',
        'is_active': '是否可用',
        'usage_count': '调用次数',
        'max_usage': '最大调用次数',
        'created_at': '创建时间',
        'last_used_at': '最后使用时间',
        'created_by': '创建者'
    }
    
    # 隐藏敏感信息
    column_formatters = {
        'api_key': lambda v, c, m, p: m.masked_key,
        'is_active': lambda v, c, m, p: '✅ 可用' if m.is_active else '❌ 不可用'
    }

    form_excluded_columns = ['created_at', 'updated_at', 'created_by', 'last_used_at']

    form_widget_args = {
        'prompt': {
            'rows': 8
        }
    }


class FileAdminView(SecureModelView):
    """文件管理视图"""
    
    column_list = ['file_name', 'file_type', 'file_size', 
                   'file_md5', 'upload_time']
    column_searchable_list = ['file_name', 'file_md5']
    column_filters = ['file_type']
    column_sortable_list = ['file_id', 'file_name', 'file_size', 'upload_time']
    column_default_sort = ('upload_time', True)
    
    column_labels = {
        'file_id': 'ID',
        'user_id': '用户ID',
        'file_name': '文件名',
        'file_path': '文件路径',
        'file_type': '文件类型',
        'file_size': '文件大小',
        'file_md5': 'MD5',
        'upload_time': '上传时间'
    }
    
    column_formatters = {
        'file_size': lambda v, c, m, p: m.file_size_display,
        'file_type': lambda v, c, m, p: '📄 PDF' if m.file_type == 'pdf' else '🖼️ 图片'
    }
    
    can_create = False  # 禁止手动创建
    can_edit = False  # 禁止编辑

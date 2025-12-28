"""
Pydantic 数据验证模型
用于 Flask 表单数据验证
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import re


class LoginSchema(BaseModel):
    """登录数据验证"""
    account_id: str = Field(..., min_length=1, max_length=20, description="学（工）号")
    password: str = Field(..., min_length=1, description="密码")
    remember: bool = Field(default=False, description="记住我")
    
    @field_validator('account_id')
    @classmethod
    def validate_account_id(cls, v):
        if not v or not v.strip():
            raise ValueError('学（工）号不能为空')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v:
            raise ValueError('密码不能为空')
        return v


class RegisterSchema(BaseModel):
    """注册数据验证"""
    account_id: str = Field(..., min_length=1, max_length=20, description="学（工）号")
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    role: str = Field(..., description="角色")
    department: str = Field(..., min_length=1, description="单位")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, max_length=50, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    advisor_id: Optional[str] = Field(None, description="指导老师工号")
    
    @field_validator('account_id')
    @classmethod
    def validate_account_id(cls, v):
        if not v or not v.strip():
            raise ValueError('学（工）号不能为空')
        return v.strip()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('姓名不能为空')
        return v.strip()
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = ['student', 'teacher', 'admin']
        if v not in valid_roles:
            raise ValueError('请选择有效的角色')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('邮箱不能为空')
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.strip()):
            raise ValueError('邮箱格式不正确')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少8位')
        return v
    
    @field_validator('advisor_id')
    @classmethod
    def validate_advisor_id(cls, v):
        if v and v.strip() and not re.match(r'^\d{8}$', v.strip()):
            raise ValueError('指导老师工号必须是8位数字')
        return v.strip() if v else None
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('两次密码输入不一致')
        return self


class UserCreateSchema(BaseModel):
    """用户创建数据验证（管理员导入）"""
    account_id: str = Field(..., min_length=1, max_length=20, description="学（工）号")
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    role: str = Field(..., description="角色：student/teacher/admin")
    department: str = Field(..., min_length=1, description="单位")
    email: str = Field(..., description="邮箱")
    password: str = Field(default="12345678", min_length=8, max_length=50, description="密码")
    advisor_id: Optional[str] = Field(None, description="指导老师工号")
    
    @field_validator('account_id')
    @classmethod
    def validate_account_id(cls, v):
        if not v or not v.strip():
            raise ValueError('学（工）号不能为空')
        return v.strip()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('姓名不能为空')
        return v.strip()
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = ['student', 'teacher', 'admin']
        if v not in valid_roles:
            raise ValueError(f'角色必须是以下之一：{", ".join(valid_roles)}')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('邮箱不能为空')
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.strip()):
            raise ValueError('邮箱格式不正确')
        return v.strip()
    
    @field_validator('advisor_id')
    @classmethod
    def validate_advisor_id(cls, v):
        if v and v.strip() and not re.match(r'^\d{8}$', str(v).strip()):
            raise ValueError('指导老师工号必须是8位数字')
        return v.strip() if v else None


class UserUpdateSchema(BaseModel):
    """用户更新数据验证"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    department: Optional[str] = Field(None, min_length=1)
    email: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)
    advisor_id: Optional[str] = Field(None)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v.strip()):
                raise ValueError('邮箱格式不正确')
            return v.strip()
        return v


class PasswordResetSchema(BaseModel):
    """密码重置验证"""
    user_id: str = Field(..., description="用户ID")
    new_password: str = Field(..., min_length=8, max_length=50, description="新密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError('两次密码输入不一致')
        return self


class CertificateSubmitSchema(BaseModel):
    """证书提交数据验证"""
    student_id: str = Field(..., min_length=1, max_length=20, description="学号")
    student_name: str = Field(..., min_length=1, max_length=50, description="学生姓名")
    department: str = Field(..., min_length=1, description="学生所在学院")
    competition_name: str = Field(..., min_length=1, max_length=200, description="竞赛项目")
    award_category: str = Field(..., min_length=1, description="获奖类别")
    award_level: str = Field(..., min_length=1, description="获奖等级")
    competition_type: str = Field(..., min_length=1, description="竞赛类型")
    organizer: str = Field(default="", max_length=200, description="主办单位")
    award_date: str = Field(default="", description="获奖时间")
    advisor: str = Field(..., min_length=1, max_length=50, description="指导教师")
    advisor_id: str = Field(..., min_length=8, max_length=8, description="指导老师工号")
    
    @field_validator('student_id')
    @classmethod
    def validate_student_id(cls, v):
        if not v or not v.strip():
            raise ValueError('学号不能为空')
        return v.strip()
    
    @field_validator('student_name')
    @classmethod
    def validate_student_name(cls, v):
        if not v or not v.strip():
            raise ValueError('学生姓名不能为空')
        return v.strip()
    
    @field_validator('advisor_id')
    @classmethod
    def validate_advisor_id(cls, v):
        if not v or not v.strip():
            raise ValueError('指导老师工号不能为空')
        if not re.match(r'^\d{8}$', v.strip()):
            raise ValueError('指导老师工号必须是8位数字')
        return v.strip()


class CertificateUpdateSchema(BaseModel):
    """证书更新数据验证（教师编辑）"""
    competition_name: Optional[str] = Field(None, max_length=200)
    student_name: Optional[str] = Field(None, max_length=50)
    student_id: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None)
    award_category: Optional[str] = Field(None)
    award_level: Optional[str] = Field(None)
    competition_type: Optional[str] = Field(None)
    advisor: Optional[str] = Field(None, max_length=50)
    advisor_id: Optional[str] = Field(None)
    standard_score: Optional[float] = Field(None, ge=0, le=100)
    contribution: Optional[float] = Field(None, ge=0, le=100)
    
    @field_validator('advisor_id')
    @classmethod
    def validate_advisor_id(cls, v):
        if v and v.strip() and not re.match(r'^\d{8}$', v.strip()):
            raise ValueError('指导老师工号必须是8位数字')
        return v.strip() if v else None


class DictionarySchema(BaseModel):
    """字典数据验证"""
    dict_name: str = Field(..., min_length=1, max_length=100, description="名称")
    parent_id: Optional[int] = Field(None, description="父节点ID")
    description: Optional[str] = Field(None, max_length=200)
    status: bool = Field(default=True)


class SystemConfigSchema(BaseModel):
    """系统配置验证"""
    config_key: str = Field(..., min_length=1, max_length=100)
    config_value: str = Field(..., min_length=0)
    description: Optional[str] = Field(None, max_length=200)


class APIKeySchema(BaseModel):
    """API密钥验证"""
    model_name: str = Field(..., min_length=1, max_length=50, description="模型名称")
    api_key: str = Field(..., min_length=10, description="API密钥")
    prompt: str = Field(default="", description="提示词")
    is_active: bool = Field(default=True)
    max_usage: Optional[int] = Field(None, ge=0)


def validate_data(schema_class, data: dict) -> tuple:
    """
    使用指定的Pydantic模型验证数据
    
    Args:
        schema_class: Pydantic模型类
        data: 待验证的字典数据
    
    Returns:
        (is_valid, error_message, validated_data)
    """
    try:
        validated = schema_class(**data)
        return True, "", validated.model_dump()
    except Exception as e:
        error_msg = str(e)
        # 提取更友好的错误信息
        if hasattr(e, 'errors'):
            errors = e.errors()
            if errors:
                first_error = errors[0]
                field = first_error.get('loc', [''])[0]
                msg = first_error.get('msg', str(e))
                error_msg = f"{field}: {msg}"
        return False, error_msg, None

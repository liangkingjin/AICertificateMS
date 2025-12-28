"""
工具模块 - 公共方法抽取
"""
from .auth_utils import (
    login_required_with_redirect, 
    require_roles,
    check_auth_redirect,
    check_role_access
)
from .certificate_utils import (
    get_certificate_options,
    get_basic_certificate_options,
    get_form_certificate_data,
    check_certificate_edit_permission,
    get_submit_status_by_role,
    build_certificate_from_form,
    update_certificate_from_form,
    convert_existing_cert_to_dict
)
from .decorators import (
    admin_required, 
    teacher_required, 
    teacher_or_admin_required,
    handle_exceptions
)
from .file_utils import (
    calculate_file_md5,
    get_file_extension,
    get_file_type,
    get_upload_folder,
    get_user_upload_folder,
    generate_unique_filename,
    save_uploaded_file,
    create_file_record,
    is_image_file,
    is_pdf_file
)

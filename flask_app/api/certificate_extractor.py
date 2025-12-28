"""
证书信息提取器 - 使用新的zai-sdk
"""
# 尝试导入新的zai-sdk
try:
    from zai import ZhipuAiClient
    ZAI_AVAILABLE = True
except ImportError:
    ZAI_AVAILABLE = False
    ZhipuAiClient = None

# 尝试导入旧的zhipuai库（作为备用）
try:
    from zhipuai import ZhipuAI
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False
    ZhipuAI = None

import base64
import json
import re
import os
from typing import Dict, Any
from datetime import datetime


class CertificateExtractor:
    """证书信息提取器，支持图片和PDF文件"""

    # 默认空结果
    EMPTY_RESULT = {
        "student_department": "",
        "competition_name": "",
        "student_id": "",
        "student_name": "",
        "award_category": "",
        "award_level": "",
        "competition_type": "",
        "organizer": "",
        "award_date": "",
        "advisor": ""
    }
    
    def __init__(self):
        self._current_key_index = 0
    
    def _get_available_api_key(self):
        """获取可用的API密钥，如果没有可用密钥则抛出异常"""
        from flask_app.models import APIKey

        available_keys = APIKey.query.filter_by(is_active=True).order_by(APIKey.created_at.desc()).all()

        if not available_keys:
            raise Exception("没有可用的API密钥，请联系管理员配置AI识别服务的API密钥")

        key = available_keys[self._current_key_index % len(available_keys)]
        self._current_key_index += 1

        if key.max_usage and key.usage_count >= key.max_usage:
            key.is_active = False
            from flask_app import db
            db.session.commit()
            return self._get_available_api_key()

        return key
    
    def _increment_usage_count(self, key_id):
        """增加API密钥的使用次数"""
        from flask_app.models import APIKey
        from flask_app import db

        key = APIKey.query.get(key_id)
        if key:
            key.usage_count += 1
            key.last_used_at = datetime.now()
            db.session.commit()
    
    def _get_prompt(self):
        """从系统配置获取提示词"""
        from flask_app.models import SystemConfig
        
        prompt = SystemConfig.get_value('ai_prompt')
        if prompt:
            return prompt
        
        # 默认提示词
        return """请从以下证书中提取所有关键信息，严格按照JSON格式返回，字段包括：
student_department（学生所在学院）、
competition_name（竞赛项目）、
student_id（学号）、
student_name（学生姓名）、
award_category（获奖类别，国家级、省级、校级奖或院级奖）、
award_level（获奖等级，一等奖、二等奖、三等奖、金奖、银奖、铜奖、优秀奖）、
competition_type（竞赛类型，A类或B类）、
organizer（主办单位）、
award_date（获奖日期，格式为YYYY-MM-DD，如果只有年月则取当月一号，如2024年12月则返回2024-12-01）、
advisor（指导教师）。
如果某个字段无法提取，请返回空字符串。只返回JSON，不要返回其他内容。"""
    
    def encode_file_base64(self, file_path: str) -> str:
        """将文件编码为base64"""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def extract_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        从图片提取证书信息（使用新的zai-sdk）
        
        Args:
            image_path: 图片文件路径
        """
        api_key_obj = self._get_available_api_key()
        prompt = api_key_obj.prompt if api_key_obj.prompt else self._get_prompt()
        
        # 使用新的zai-sdk
        if ZAI_AVAILABLE:
            try:
                client = ZhipuAiClient(api_key=api_key_obj.api_key)
                
                # 使用base64编码
                img_base = self.encode_file_base64(image_path)
                image_content = img_base
                
                response = client.chat.completions.create(
                    model="glm-4.6v",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_content
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    thinking={
                        "type": "enabled"
                    }
                )
                
                self._increment_usage_count(api_key_obj.key_id)
                
                return self._parse_response(response)
            except Exception as e:
                print(f"使用zai-sdk提取图片失败: {e}，尝试使用旧接口")
                # 如果新接口失败，回退到旧接口
                return self._extract_from_image_legacy(image_path)
        else:
            # 如果没有安装zai-sdk，使用旧接口
            print("zai-sdk未安装，使用旧接口提取图片")
            return self._extract_from_image_legacy(image_path)
    
    def _extract_from_image_legacy(self, image_path: str) -> Dict[str, Any]:
        """从图片提取证书信息（旧接口，作为备用）"""
        if not ZHIPUAI_AVAILABLE:
            raise ImportError("未安装zhipuai库，无法提取图片信息")
        
        img_base = self.encode_file_base64(image_path)
        
        api_key_obj = self._get_available_api_key()
        client = ZhipuAI(api_key=api_key_obj.api_key)
        
        prompt = api_key_obj.prompt if api_key_obj.prompt else self._get_prompt()
        model = api_key_obj.model_name or 'glm-4v'
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        self._increment_usage_count(api_key_obj.key_id)
        
        return self._parse_response(response)
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        从PDF文件提取证书信息（使用新的zai库接口）
        
        Args:
            pdf_path: PDF文件路径
        """
        api_key_obj = self._get_available_api_key()
        prompt = api_key_obj.prompt if api_key_obj.prompt else self._get_prompt()
        
        # 使用新的zai库接口
        if ZAI_AVAILABLE:
            try:
                client = ZhipuAiClient(api_key=api_key_obj.api_key)
                
                # 使用base64编码
                pdf_base = self.encode_file_base64(pdf_path)
                pdf_content = f"data:application/pdf;base64,{pdf_base}"
                
                response = client.chat.completions.create(
                    model="glm-4.6v",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "file_url",
                                    "file_url": {
                                        "url": pdf_content
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    thinking={
                        "type": "enabled"
                    }
                )
                
                self._increment_usage_count(api_key_obj.key_id)
                
                return self._parse_response(response)
            except Exception as e:
                print(f"使用zai库提取PDF失败: {e}，尝试使用旧接口")
                # 如果新接口失败，回退到旧接口
                return self._extract_from_pdf_legacy(pdf_path)
        else:
            # 如果没有安装zai库，使用旧接口
            print("zai库未安装，使用旧接口提取PDF")
            return self._extract_from_pdf_legacy(pdf_path)
    
    def _extract_from_pdf_legacy(self, pdf_path: str) -> Dict[str, Any]:
        """从PDF文件提取证书信息（旧接口，作为备用）"""
        if not ZHIPUAI_AVAILABLE:
            raise ImportError("未安装zhipuai库，无法提取PDF信息")
        
        pdf_base = self.encode_file_base64(pdf_path)
        
        api_key_obj = self._get_available_api_key()
        client = ZhipuAI(api_key=api_key_obj.api_key)
        
        prompt = api_key_obj.prompt if api_key_obj.prompt else self._get_prompt()
        model = api_key_obj.model_name or 'glm-4v'
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "file",
                            "file": {
                                "file_data": f"data:application/pdf;base64,{pdf_base}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        self._increment_usage_count(api_key_obj.key_id)
        
        return self._parse_response(response)
    
    def extract_certificate_info(self, file_path: str, file_type: str = "image") -> Dict[str, Any]:
        """
        提取证书信息（统一入口）
        
        Args:
            file_path: 文件路径
            file_type: 文件类型，"image" 或 "pdf"
        
        Returns:
            提取的证书信息字典
        """
        try:
            if file_type == "pdf":
                return self.extract_from_pdf(file_path)
            else:
                return self.extract_from_image(file_path)
        except Exception as e:
            print(f"提取证书信息失败: {e}")
            return self.EMPTY_RESULT.copy()
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """解析API响应（兼容新旧接口格式）"""
        try:
            # 处理新接口（zai库）的响应格式
            if hasattr(response, 'choices') and len(response.choices) > 0:
                message_obj = response.choices[0].message
                # 新接口可能直接返回message对象或content属性
                if hasattr(message_obj, 'content'):
                    message = message_obj.content
                elif isinstance(message_obj, str):
                    message = message_obj
                else:
                    # 尝试获取文本内容
                    message = str(message_obj)
            else:
                # 旧接口格式
                message = response.choices[0].message.content
            
            # 尝试提取JSON内容
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', message)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = message
            
            extracted_info = json.loads(json_str)
            return extracted_info
        except (json.JSONDecodeError, AttributeError, IndexError, TypeError) as e:
            print(f"解析响应失败: {e}")
            print(f"响应内容: {response}")
            return self.EMPTY_RESULT.copy()

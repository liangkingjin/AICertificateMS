# -*- coding: utf-8 -*-
"""
日期工具类
"""
from datetime import datetime, date
import re


def parse_award_date(date_str):
    """
    解析获奖日期字符串为Date对象

    支持多种日期格式：
    - 2024-12-01
    - 2024/12/01
    - 2024年12月01日
    - 2024年12月
    - 2024-12

    Args:
        date_str: 日期字符串或date对象

    Returns:
        date: 解析后的date对象，解析失败返回None
    """
    if not date_str:
        return None

    # 已经是date对象
    if isinstance(date_str, date):
        return date_str

    date_str = str(date_str).strip()

    # 尝试多种格式
    patterns = [
        (r'^(\d{4})-(\d{1,2})-(\d{1,2})$', '%Y-%m-%d'),  # 2024-12-01
        (r'^(\d{4})/(\d{1,2})/(\d{1,2})$', '%Y/%m/%d'),  # 2024/12/01
        (r'^(\d{4})年(\d{1,2})月(\d{1,2})日$', None),  # 2024年12月01日
        (r'^(\d{4})年(\d{1,2})月$', None),  # 2024年12月 -> 取一号
        (r'^(\d{4})-(\d{1,2})$', None),  # 2024-12 -> 取一号
    ]

    for pattern, fmt in patterns:
        match = re.match(pattern, date_str)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                return date(int(groups[0]), int(groups[1]), int(groups[2]))
            elif len(groups) == 2:
                return date(int(groups[0]), int(groups[1]), 1)  # 取当月一号

    # 尝试直接解析
    try:
        return datetime.strptime(date_str[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass

    return None

import os
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def safe_media_url(image_field):
    """
    安全地获取图片URL，处理空值情况和文件不存在的情况
    """
    if not image_field:
        return '/static/placeholder.png'
    
    # 如果是字符串路径，直接使用
    if isinstance(image_field, str):
        if image_field.strip():
            # 检查文件是否真实存在
            file_path = os.path.join(settings.MEDIA_ROOT, image_field)
            if os.path.exists(file_path):
                return f"{settings.MEDIA_URL}{image_field}"
            else:
                print(f"图片文件不存在: {file_path}")
                return '/static/placeholder.png'
        else:
            return '/static/placeholder.png'
    
    # 如果是ImageField对象
    if hasattr(image_field, 'name') and image_field.name:
        # 检查文件是否真实存在
        file_path = os.path.join(settings.MEDIA_ROOT, image_field.name)
        if os.path.exists(file_path):
            return image_field.url
        else:
            print(f"图片文件不存在: {file_path}")
            return '/static/placeholder.png'
    
    return '/static/placeholder.png'
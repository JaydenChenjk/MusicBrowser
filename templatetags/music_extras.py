import os
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def media_url_or_placeholder(image_field):
    """
    安全地获取图片URL，如果图片不存在则返回占位符
    """
    if not image_field:
        return '/static/placeholder.png'
    
    # 检查文件是否真实存在
    file_path = os.path.join(settings.MEDIA_ROOT, image_field.name)
    if os.path.exists(file_path):
        return image_field.url
    else:
        return '/static/placeholder.png'

@register.filter
def safe_media_url(image_field):
    """
    安全地获取图片URL，处理空值情况
    """
    if image_field and hasattr(image_field, 'url'):
        return image_field.url
    return '/static/placeholder.png'
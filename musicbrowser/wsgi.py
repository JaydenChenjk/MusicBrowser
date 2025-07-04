import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbrowser.settings')    #  设置环境变量指向项目配置文件settings.py

application = get_wsgi_application()    # 构造符合 WSGI 规范的 application 对象
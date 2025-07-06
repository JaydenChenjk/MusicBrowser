from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "output"
SECRET_KEY = "hello_Django"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [      # Django 内置应用
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "music",           
]

MIDDLEWARE = [      # Django 中间件
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "musicbrowser.urls"  # URL 路由配置
TEMPLATES = [{  # 模板配置
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "musicbrowser.wsgi.application"

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

# 静态文件配置
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# 媒体文件配置 - 关键修改
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "output"

# 文件上传设置
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB

# 时区设置
TIME_ZONE = 'Asia/Shanghai'
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "hello_Django"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [  # Django启用的apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "music",           
]

MIDDLEWARE = [  # Django请求的中间件
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "musicbrowser.urls"
TEMPLATES = [{  # Django模板配置
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],   # 全局模板目录
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "musicbrowser.wsgi.application"    # WSGI应用入口

DATABASES = {   # 数据库配置
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

STATIC_URL = "/static/"     # 配置静态文件
STATICFILES_DIRS = [BASE_DIR / "static"]


MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"         # 用于存歌手/歌曲图片

TIME_ZONE = 'Asia/Shanghai'    # 时区设置
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"    # 默认的主键字段类型
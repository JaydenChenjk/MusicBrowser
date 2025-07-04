from django.conf import settings    #引入settings.py 
from django.conf.urls.static import static   
from django.contrib import admin    
from django.urls import path, include   

urlpatterns = [
    path("admin/", admin.site.urls),    # Django管理后台
    path("", include("music.urls")),     # 全部交给app处理
]

if settings.DEBUG:   # 如果是调试模式，添加静态文件和媒体文件的处理
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    
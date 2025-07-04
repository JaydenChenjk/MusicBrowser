from django.urls import path
from . import views     # 导入当前目录下的views.py

app_name = "music"  # 设置当前app的命名空间，避免与其他app的url冲突

urlpatterns = [
    path("", views.song_list, name="song_list"),    #歌曲列表页
    path("songs/<int:pk>/", views.song_detail, name="song_detail"),   #歌曲详情页
    path("artists/", views.artist_list, name="artist_list"),    #歌手列表页
    path("artists/<int:pk>/", views.artist_detail, name="artist_detail"),    #歌手详情页

    path("songs/<int:song_id>/comment/", views.add_comment, name="add_comment"),    # 添加评论
    path("comments/<int:pk>/delete/", views.delete_comment, name="delete_comment"),   # 删除评论

    path("search/", views.search, name="search"),      # 搜索结果页
]
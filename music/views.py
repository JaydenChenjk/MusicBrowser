import time
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Song, Artist, Comment
from .forms import CommentForm, SearchForm


def _paginate(request, queryset, per_page=20):      # 分页功能
    page_number = request.GET.get("page", "1")      # 获取当前页码，默认为1
    paginator = Paginator(queryset, per_page)      # 创建分页器对象，指定每页条数
    page_obj  = paginator.get_page(page_number)     # 获取指定页码的页面对象，自动处理非法页码
    return page_obj


def song_list(request):     # 歌曲列表页
    search_form = SearchForm(request.GET)       # 创建一个SearchForm对象，用于接收页面上提交的搜索字段
    page_obj = _paginate(request, Song.objects.select_related("artist").all())      # 获取所有歌曲，并进行分页处理
    return render(request, "songs/list.html", {     # 把数据传给渲染页面
        "page_obj": page_obj,
        "search_form": search_form,
    })


def song_detail(request, pk):   # 歌曲详情页
    song = get_object_or_404(Song.objects.select_related("artist"), pk=pk)      #从数据库中获取主键为pk的Song对象

    # 处理新评论
    if request.method == "POST":     #判断是否为提交评论的表单请求
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            Comment.objects.create(song=song, text=comment_form.cleaned_data["text"])
            return redirect(reverse("music:song_detail", args=[pk]))    # 重定向到当前歌曲详情页
    else:
        comment_form = CommentForm()    # 初始化一个空白的评论表单

    comments = song.comments.order_by("-created_at")    	# 获取该歌曲的所有评论，按创建时间倒序排列
    search_form = SearchForm(request.GET)   # 创建一个SearchForm对象，用于接收页面上提交的搜索字段
    return render(request, "songs/detail.html", {   # 渲染歌曲详情页
        "song": song,
        "comment_form": comment_form,
        "comments": comments,
        "search_form": search_form,
    })


def add_comment(request, song_id):      # 兜底跳转
    return redirect(reverse("music:song_detail", args=[song_id]))


def delete_comment(request, pk):        # 删除评论
    if request.method == "POST":
        comment = get_object_or_404(Comment, pk=pk)     # 获取主键为pk的Comment对象
        song_id = comment.song_id       # 提前记录下song_id
        comment.delete()
        return redirect(reverse("music:song_detail", args=[song_id]))
    return redirect("/")    # 如果不是POST请求，则跳转首页


def artist_list(request):       # 歌手列表页
    search_form = SearchForm(request.GET)
    page_obj = _paginate(request, Artist.objects.all())
    return render(request, "artists/list.html", {
        "page_obj": page_obj,
        "search_form": search_form,
    })


def artist_detail(request, pk):        # 歌手详情页
    artist = get_object_or_404(Artist, pk=pk)
    songs  = artist.songs.all()
    search_form = SearchForm(request.GET)
    return render(request, "artists/detail.html", {
        "artist": artist,
        "songs": songs,
        "search_form": search_form,
    })



def search(request):     # 搜索结果页
    form = SearchForm(request.GET)
    if form.is_valid():
        q = form.cleaned_data["q"].strip()
        mode = form.cleaned_data["mode"]
    else:
        q = ""
        mode = "song"
    t0 = time.perf_counter()     # 搜索计时

    if mode == "artist":
        qs = Artist.objects
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(biography__icontains=q))    # 匹配歌手名字或简介中的关键字，忽略大小写
        page_obj = _paginate(request, qs)   # 调用分页函数
    else:
        qs = Song.objects.select_related("artist")  # 歌曲和对应歌手信息一起查询
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(lyrics__icontains=q) |
                Q(artist__name__icontains=q)
            )
        page_obj = _paginate(request, qs)

    elapsed = (time.perf_counter() - t0) * 1000     # 统计搜索耗时
    return render(request, "search/result.html", {      # 渲染搜索结果页
        "page_obj": page_obj,
        "q": q,
        "mode": mode,
        "elapsed": elapsed,
        "search_form": form,
    })
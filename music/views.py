import time
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
from .models import Song, Artist, Comment
from .forms import CommentForm, SearchForm


def _paginate(request, queryset, per_page=20):
    page_number = request.GET.get("page", "1")
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)
    return page_obj


def song_list(request):
    search_form = SearchForm(request.GET)
    songs = Song.objects.select_related("artist").all()
    
    # 调试信息：检查图片路径
    if settings.DEBUG:
        for song in songs[:3]:  # 只检查前3个
            if song.cover_img:
                file_path = os.path.join(settings.MEDIA_ROOT, song.cover_img.name)
                print(f"歌曲 {song.name}: 图片路径 {song.cover_img.name}, 文件存在: {os.path.exists(file_path)}")
    
    page_obj = _paginate(request, songs)
    return render(request, "songs/list.html", {
        "page_obj": page_obj,
        "search_form": search_form,
    })


def song_detail(request, pk):
    song = get_object_or_404(Song.objects.select_related("artist"), pk=pk)
    
    # 调试信息
    if settings.DEBUG and song.cover_img:
        file_path = os.path.join(settings.MEDIA_ROOT, song.cover_img.name)
        print(f"歌曲详情 {song.name}: 图片路径 {song.cover_img.name}, 文件存在: {os.path.exists(file_path)}")

    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            Comment.objects.create(song=song, text=comment_form.cleaned_data["text"])
            return redirect(reverse("music:song_detail", args=[pk]))
    else:
        comment_form = CommentForm()

    comments = song.comments.order_by("-created_at")
    search_form = SearchForm(request.GET)
    return render(request, "songs/detail.html", {
        "song": song,
        "comment_form": comment_form,
        "comments": comments,
        "search_form": search_form,
    })


def add_comment(request, song_id):
    return redirect(reverse("music:song_detail", args=[song_id]))


def delete_comment(request, pk):
    if request.method == "POST":
        comment = get_object_or_404(Comment, pk=pk)
        song_id = comment.song_id
        comment.delete()
        return redirect(reverse("music:song_detail", args=[song_id]))
    return redirect("/")


def artist_list(request):
    search_form = SearchForm(request.GET)
    artists = Artist.objects.all()
    
    # 调试信息：检查歌手图片路径
    if settings.DEBUG:
        for artist in artists[:3]:  # 只检查前3个
            if artist.profile_img:
                file_path = os.path.join(settings.MEDIA_ROOT, artist.profile_img.name)
                print(f"歌手 {artist.name}: 图片路径 {artist.profile_img.name}, 文件存在: {os.path.exists(file_path)}")
    
    page_obj = _paginate(request, artists)
    return render(request, "artists/list.html", {
        "page_obj": page_obj,
        "search_form": search_form,
    })


def artist_detail(request, pk):
    artist = get_object_or_404(Artist, pk=pk)
    songs = artist.songs.all()
    search_form = SearchForm(request.GET)
    
    # 调试信息
    if settings.DEBUG and artist.profile_img:
        file_path = os.path.join(settings.MEDIA_ROOT, artist.profile_img.name)
        print(f"歌手详情 {artist.name}: 图片路径 {artist.profile_img.name}, 文件存在: {os.path.exists(file_path)}")
    
    return render(request, "artists/detail.html", {
        "artist": artist,
        "songs": songs,
        "search_form": search_form,
    })


def search(request):
    form = SearchForm(request.GET)
    if form.is_valid():
        q = form.cleaned_data["q"].strip()
        mode = form.cleaned_data["mode"]
    else:
        q = ""
        mode = "song"
    t0 = time.perf_counter()

    if mode == "artist":
        qs = Artist.objects
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(biography__icontains=q))
        page_obj = _paginate(request, qs)
    else:
        qs = Song.objects.select_related("artist")
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(lyrics__icontains=q) |
                Q(artist__name__icontains=q)
            )
        page_obj = _paginate(request, qs)

    elapsed = (time.perf_counter() - t0) * 1000
    return render(request, "search/result.html", {
        "page_obj": page_obj,
        "q": q,
        "mode": mode,
        "elapsed": elapsed,
        "search_form": form,
    })
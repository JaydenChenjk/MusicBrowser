import time
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Song, Artist, Comment
from .forms import CommentForm, SearchForm


def _paginate(request, queryset, per_page=20):      # 分页功能
    page_number = request.GET.get("page", "1")
    paginator = Paginator(queryset, per_page)
    page_obj  = paginator.get_page(page_number)
    return page_obj


def song_list(request):
    search_form = SearchForm(request.GET)
    page_obj = _paginate(request, Song.objects.select_related("artist").all())
    return render(request, "songs/list.html", {
        "page_obj": page_obj,
        "search_form": search_form,
    })

def song_detail(request, pk):
    song = get_object_or_404(Song.objects.select_related("artist"), pk=pk)

    # 处理新评论
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


# --- 评论 ---

def add_comment(request, song_id):
    # 由于在 song_detail 已处理 POST，可用于外部 JS/Ajax；此处兜底
    return redirect(reverse("music:song_detail", args=[song_id]))


def delete_comment(request, pk):
    if request.method == "POST":
        comment = get_object_or_404(Comment, pk=pk)
        song_id = comment.song_id
        comment.delete()
        return redirect(reverse("music:song_detail", args=[song_id]))
    return redirect("/")


# --- 歌手 ---

def artist_list(request):
    search_form = SearchForm(request.GET)
    page_obj = _paginate(request, Artist.objects.all())
    return render(request, "artists/list.html", {
        "page_obj": page_obj,
        "search_form": search_form,
    })


def artist_detail(request, pk):
    artist = get_object_or_404(Artist, pk=pk)
    songs  = artist.songs.all()
    search_form = SearchForm(request.GET)
    return render(request, "artists/detail.html", {
        "artist": artist,
        "songs": songs,
        "search_form": search_form,
    })


# --- 搜索 ---

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

    elapsed = (time.perf_counter() - t0) * 1000   # 毫秒
    return render(request, "search/result.html", {
        "page_obj": page_obj,
        "q": q,
        "mode": mode,
        "elapsed": elapsed,
        "search_form": form,
    })
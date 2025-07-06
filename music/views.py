import time
import os
import json
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages
from .models import Song, Artist, Comment
from .forms import CommentForm, SearchForm
from django.utils.text import slugify

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
            Comment.objects.create(
                song=song, 
                text=comment_form.cleaned_data["text"]
            )
            messages.success(request, "评论添加成功！")
            return redirect(reverse("music:song_detail", args=[pk]))
        else:
            messages.error(request, "评论添加失败，请检查输入内容。")
    else:
        comment_form = CommentForm()

    comments = song.comments.order_by("-created_at")
    search_form = SearchForm(request.GET)
    return render(request, "songs/detail.html", {
        "song": song,
        "form": comment_form,
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
        messages.success(request, "评论删除成功！")
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

def add_songs_from_json(request):
    """
    从项目根目录的 songs.json 文件读取数据并添加到数据库
    修复版本：解决图片路径和歌手匹配问题
    """
    # 构建 songs.json 文件的绝对路径
    json_file_path = os.path.join(settings.BASE_DIR, 'songs.json')

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return HttpResponse("错误: songs.json 文件未找到！请确保它位于项目根目录下。", status=404)
    except json.JSONDecodeError as e:
        return HttpResponse(f"错误: songs.json 文件格式不正确！{str(e)}", status=400)
    except Exception as e:
        return HttpResponse(f"读取文件时发生错误：{str(e)}", status=500)

    songs_added_count = 0
    songs_updated_count = 0
    songs_exist_count = 0
    songs_error_count = 0
    error_details = []

    # 遍历JSON中的每一首歌曲
    for i, song_data in enumerate(data):
        try:
            # 验证必要字段是否存在
            required_fields = ['name', 'artist_name', 'source_url', 'lyrics']
            missing_fields = [field for field in required_fields if field not in song_data or not song_data[field]]
            
            if missing_fields:
                error_msg = f"第{i+1}首歌曲缺少必要字段: {', '.join(missing_fields)}"
                error_details.append(error_msg)
                songs_error_count += 1
                continue
            
            # === 生成标准化的图片路径 ===
            safe_artist_name = slugify(song_data['artist_name'], allow_unicode=True)
            if not safe_artist_name:  # 处理全中文名无法slugify的情况
                safe_artist_name = f"artist_{hash(song_data['artist_name']) % 10000}"
            
            safe_song_name = slugify(song_data['name'], allow_unicode=True)
            if not safe_song_name:  # 处理全中文名无法slugify的情况
                safe_song_name = f"song_{hash(song_data['name']) % 10000}"
            
            profile_img_path = f"artist_images/{safe_artist_name}.jpg"
            cover_img_path = f"song_images/{safe_song_name}.jpg"
            
            # 检查图片文件是否真实存在
            profile_img_exists = os.path.exists(os.path.join(settings.MEDIA_ROOT, profile_img_path))
            cover_img_exists = os.path.exists(os.path.join(settings.MEDIA_ROOT, cover_img_path))
            
            # 处理歌手URL，去除查询参数以避免重复
            artist_source_url = song_data['source_url'].split('?')[0]
            
            # === 严格按照 songs.json 中的 artist_name 查找或创建歌手 ===
            artist = Artist.objects.filter(name=song_data['artist_name']).first()
            if not artist:
                # 创建新歌手
                artist = Artist.objects.create(
                    name=song_data['artist_name'],
                    biography=song_data.get('biography', ''),
                    profile_img=profile_img_path if profile_img_exists else '',
                    source_url=artist_source_url
                )
                print(f"创建新歌手: {artist.name}")
            else:
                # 更新现有歌手信息
                updated = False
                if not artist.profile_img and profile_img_exists:
                    artist.profile_img = profile_img_path
                    updated = True
                if not artist.source_url:
                    artist.source_url = artist_source_url
                    updated = True
                if not artist.biography and song_data.get('biography'):
                    artist.biography = song_data.get('biography', '')
                    updated = True
                if updated:
                    artist.save()
                    print(f"更新歌手信息: {artist.name}")

            # === 处理歌词 ===
            if isinstance(song_data['lyrics'], list):
                lyrics = '\n'.join(song_data['lyrics'])
            else:
                lyrics = str(song_data['lyrics'])

            # === 查找或创建歌曲 ===
            song = Song.objects.filter(source_url=song_data['source_url']).first()
            if not song:
                # 创建新歌曲
                song = Song.objects.create(
                    name=song_data['name'],
                    artist=artist,
                    lyrics=lyrics,
                    cover_img=cover_img_path if cover_img_exists else '',
                    source_url=song_data['source_url']
                )
                songs_added_count += 1
                print(f"创建新歌曲: {song.name} - {artist.name}")
            else:
                # 更新现有歌曲
                updated = False
                
                # 确保歌曲关联到正确的歌手
                if song.artist.name != song_data['artist_name']:
                    song.artist = artist
                    updated = True
                    print(f"修正歌曲歌手: {song.name} 从 {song.artist.name} 到 {artist.name}")
                
                # 更新歌曲名称（如果不同）
                if song.name != song_data['name']:
                    song.name = song_data['name']
                    updated = True
                
                # 更新歌词
                if song.lyrics != lyrics:
                    song.lyrics = lyrics
                    updated = True
                
                # 更新封面图片
                if not song.cover_img and cover_img_exists:
                    song.cover_img = cover_img_path
                    updated = True
                
                if updated:
                    song.save()
                    songs_updated_count += 1
                    print(f"更新歌曲: {song.name} - {artist.name}")
                else:
                    songs_exist_count += 1
                
        except Exception as e:
            error_msg = f"第{i+1}首歌曲处理失败 ({song_data.get('name', '未知')}): {str(e)}"
            error_details.append(error_msg)
            songs_error_count += 1
            print(f"错误: {error_msg}")

    # 生成详细的结果报告
    result_html = f"""
    <h2>数据导入完成</h2>
    <ul>
        <li>成功添加新歌曲: {songs_added_count} 首</li>
        <li>更新歌曲信息: {songs_updated_count} 首</li>
        <li>已存在歌曲: {songs_exist_count} 首</li>
        <li>处理失败: {songs_error_count} 首</li>
    </ul>
    """
    
    if error_details:
        result_html += "<h3>错误详情：</h3><ul>"
        for error in error_details[:20]:  # 显示前20个错误
            result_html += f"<li>{error}</li>"
        if len(error_details) > 20:
            result_html += f"<li>... 还有 {len(error_details) - 20} 个错误</li>"
        result_html += "</ul>"
    
    # 检查图片文件情况
    result_html += "<h3>图片文件检查：</h3><ul>"
    artist_img_dir = os.path.join(settings.MEDIA_ROOT, "artist_images")
    song_img_dir = os.path.join(settings.MEDIA_ROOT, "song_images")
    
    if os.path.exists(artist_img_dir):
        artist_img_count = len([f for f in os.listdir(artist_img_dir) if f.endswith('.jpg')])
        result_html += f"<li>歌手图片文件: {artist_img_count} 个</li>"
    else:
        result_html += "<li>歌手图片目录不存在</li>"
    
    if os.path.exists(song_img_dir):
        song_img_count = len([f for f in os.listdir(song_img_dir) if f.endswith('.jpg')])
        result_html += f"<li>歌曲图片文件: {song_img_count} 个</li>"
    else:
        result_html += "<li>歌曲图片目录不存在</li>"
    
    result_html += "</ul>"
    result_html += f'<p><a href="/">返回首页</a></p>'
    
    return HttpResponse(result_html)
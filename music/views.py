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
import re
import string

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
    从 output/songs.json 文件读取数据并添加到数据库
    只用主歌手名，图片路径只写本地存在的。
    """
    # 构建 songs.json 文件的绝对路径
    json_file_path = os.path.join(settings.BASE_DIR, 'output', 'songs.json')

    # === 新增：读取 artists.json，构建别名到主名的映射 ===
    artist_alias_to_main = {}
    artist_json_path = os.path.join(settings.BASE_DIR, 'output', 'artists.json')
    if os.path.exists(artist_json_path):
        with open(artist_json_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                artist_obj = json.loads(line)
                # 主名为第一个
                main_name = re.split(r'[\/，,、\s]+', artist_obj['name'])[0].strip()
                # 分割所有别名
                for alias in re.split(r'[\/，,、\s]+', artist_obj['name']):
                    alias = alias.strip()
                    if alias:
                        artist_alias_to_main[alias] = main_name

    def normalize_name(name):
        # 小写，去除空格、下划线、连字符、标点
        name = name.lower()
        name = name.replace(' ', '').replace('_', '').replace('-', '')
        name = ''.join(c for c in name if c not in string.punctuation)
        return name

    def fuzzy_find_file(directory, artist_name):
        if not os.path.exists(directory):
            return None
        norm_artist = normalize_name(artist_name)
        for file in os.listdir(directory):
            if not file.lower().endswith('.jpg'):
                continue
            norm_file = normalize_name(os.path.splitext(file)[0])
            # 只要 artist 名在文件名里，或文件名在 artist 名里
            if norm_artist in norm_file or norm_file in norm_artist:
                return file
        return None

    try:
        # 逐行读取JSON文件（每行一个JSON对象）
        data = []
        with open(json_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        song_data = json.loads(line)
                        data.append(song_data)
                    except json.JSONDecodeError as e:
                        print(f"警告: 第{line_num}行JSON格式错误: {e}")
                        continue
    except FileNotFoundError:
        return HttpResponse("错误: songs.json 文件未找到！请确保它位于 output 目录下。", status=404)
    except Exception as e:
        return HttpResponse(f"读取文件时发生错误：{str(e)}", status=500)

    def get_main_artist(artist_name):
        # 分割所有候选名
        for candidate in re.split(r'[\/，,、\s]+', artist_name):
            candidate = candidate.strip()
            if candidate in artist_alias_to_main:
                return artist_alias_to_main[candidate]
        # 如果都找不到，fallback：取第一个
        return re.split(r'[\/，,、\s]+', artist_name)[0].strip()

    songs_added_count = 0
    songs_updated_count = 0
    songs_exist_count = 0
    songs_error_count = 0
    artists_created_count = 0
    artists_updated_count = 0
    error_details = []

    for i, song_data in enumerate(data):
        try:
            required_fields = ['name', 'artist_name', 'source_url']
            missing_fields = [field for field in required_fields if field not in song_data or not song_data[field]]
            if missing_fields:
                error_msg = f"第{i+1}首歌曲缺少必要字段: {', '.join(missing_fields)}"
                error_details.append(error_msg)
                songs_error_count += 1
                continue

            # 只用主歌手名
            main_artist_name = get_main_artist(song_data['artist_name'])

            def safe_filename(name):
                safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                return safe_name.strip()
            safe_artist_name = safe_filename(main_artist_name)
            safe_song_name = safe_filename(song_data['name'])

            expected_artist_img = f"{safe_artist_name}.jpg"
            expected_song_img = f"{safe_song_name}.jpg"

            artist_img_dir = os.path.join(settings.MEDIA_ROOT, "artist_images")
            song_img_dir = os.path.join(settings.MEDIA_ROOT, "song_images")

            # === 用 fuzzy 匹配 artist 图片 ===
            found_artist_img = fuzzy_find_file(artist_img_dir, main_artist_name)
            # 歌曲图片可继续用原来的严格匹配
            def find_file_case_insensitive(directory, filename):
                if not os.path.exists(directory):
                    return None
                filename_lower = filename.lower()
                for file in os.listdir(directory):
                    if file.lower() == filename_lower:
                        return file
                return None
            found_song_img = find_file_case_insensitive(song_img_dir, expected_song_img)

            profile_img_path = f"artist_images/{found_artist_img}" if found_artist_img else ""
            cover_img_path = f"song_images/{found_song_img}" if found_song_img else ""

            if settings.DEBUG:
                print(f"处理歌曲: {song_data['name']} - {song_data['artist_name']}")
                print(f"  主歌手: {main_artist_name}")
                print(f"  期望歌手图片: {expected_artist_img}")
                print(f"  找到歌手图片: {found_artist_img or '未找到'}")
                print(f"  期望歌曲图片: {expected_song_img}")
                print(f"  找到歌曲图片: {found_song_img or '未找到'}")

            # 严格按照主歌手名查找或创建歌手
            artist = Artist.objects.filter(name__exact=main_artist_name).first()
            if not artist:
                artist = Artist.objects.create(
                    name=main_artist_name,
                    biography=song_data.get('biography', ''),
                    profile_img=profile_img_path,
                    source_url=song_data.get('artist_source_url', song_data['source_url'])
                )
                artists_created_count += 1
                print(f"创建新歌手: {artist.name}")
            else:
                updated = False
                if not artist.profile_img and found_artist_img:
                    artist.profile_img = profile_img_path
                    updated = True
                if not artist.biography and song_data.get('biography'):
                    artist.biography = song_data.get('biography', '')
                    updated = True
                if not artist.source_url and song_data.get('artist_source_url'):
                    artist.source_url = song_data.get('artist_source_url', song_data['source_url'])
                    updated = True
                if updated:
                    artist.save()
                    artists_updated_count += 1
                    print(f"更新歌手信息: {artist.name}")

            lyrics = song_data.get('lyrics', '')
            if isinstance(lyrics, list):
                lyrics = '\n'.join(lyrics)
            else:
                lyrics = str(lyrics) if lyrics else ''

            song = Song.objects.filter(source_url=song_data['source_url']).first()
            if not song:
                song = Song.objects.create(
                    name=song_data['name'],
                    artist=artist,
                    lyrics=lyrics,
                    cover_img=cover_img_path,
                    source_url=song_data['source_url']
                )
                songs_added_count += 1
                print(f"创建新歌曲: {song.name} - {artist.name}")
            else:
                updated = False
                if song.artist.name != main_artist_name:
                    old_artist = song.artist.name
                    song.artist = artist
                    updated = True
                    print(f"修正歌曲歌手: {song.name} 从 '{old_artist}' 更正为 '{artist.name}'")
                if song.name != song_data['name']:
                    song.name = song_data['name']
                    updated = True
                if song.lyrics != lyrics:
                    song.lyrics = lyrics
                    updated = True
                if not song.cover_img and found_song_img:
                    song.cover_img = cover_img_path
                    updated = True
                if updated:
                    song.save()
                    songs_updated_count += 1
                    print(f"更新歌曲: {song.name} - {artist.name}")
                else:
                    songs_exist_count += 1
        except Exception as e:
            error_msg = f"第{i+1}首歌曲处理失败 ({song_data.get('name', '未知')} - {song_data.get('artist_name', '未知')}): {str(e)}"
            error_details.append(error_msg)
            songs_error_count += 1
            print(f"错误: {error_msg}")

    # 生成详细的结果报告
    result_html = f"""
    <html><body>
    <h2>数据导入完成</h2>
    <h3>歌曲处理结果：</h3>
    <ul>
        <li>成功添加新歌曲: {songs_added_count} 首</li>
        <li>更新歌曲信息: {songs_updated_count} 首</li>
        <li>已存在歌曲: {songs_exist_count} 首</li>
        <li>处理失败: {songs_error_count} 首</li>
    </ul>
    
    <h3>歌手处理结果：</h3>
    <ul>
        <li>创建新歌手: {artists_created_count} 位</li>
        <li>更新歌手信息: {artists_updated_count} 位</li>
    </ul>
    """
    
    if error_details:
        result_html += "<h3>错误详情：</h3><ul>"
        for error in error_details[:10]:  # 显示前10个错误
            result_html += f"<li>{error}</li>"
        if len(error_details) > 10:
            result_html += f"<li>... 还有 {len(error_details) - 10} 个错误</li>"
        result_html += "</ul>"
    
    # 检查图片文件情况
    result_html += "<h3>图片文件检查：</h3><ul>"
    artist_img_dir = os.path.join(settings.MEDIA_ROOT, "artist_images")
    song_img_dir = os.path.join(settings.MEDIA_ROOT, "song_images")
    
    if os.path.exists(artist_img_dir):
        artist_files = [f for f in os.listdir(artist_img_dir) if f.endswith('.jpg')]
        result_html += f"<li>歌手图片目录: {artist_img_dir}</li>"
        result_html += f"<li>歌手图片文件: {len(artist_files)} 个</li>"
    else:
        result_html += f"<li>歌手图片目录不存在: {artist_img_dir}</li>"
    
    if os.path.exists(song_img_dir):
        song_files = [f for f in os.listdir(song_img_dir) if f.endswith('.jpg')]
        result_html += f"<li>歌曲图片目录: {song_img_dir}</li>"
        result_html += f"<li>歌曲图片文件: {len(song_files)} 个</li>"
    else:
        result_html += f"<li>歌曲图片目录不存在: {song_img_dir}</li>"
    
    result_html += "</ul>"
    
    # 添加数据库统计信息
    total_artists = Artist.objects.count()
    total_songs = Song.objects.count()
    result_html += f"""
    <h3>数据库统计：</h3>
    <ul>
        <li>总歌手数: {total_artists}</li>
        <li>总歌曲数: {total_songs}</li>
    </ul>
    """
    
    result_html += f'<p><a href="/">返回首页</a> | <a href="/artists/">查看歌手列表</a></p>'
    result_html += "</body></html>"
    
    return HttpResponse(result_html)
    
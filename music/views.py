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
    修复版本：严格按照JSON数据匹配歌手，修复图片路径问题，支持大小写不敏感的图片查找
    """
    # 构建 songs.json 文件的绝对路径
    json_file_path = os.path.join(settings.BASE_DIR, 'songs.json')

    try:
        # 逐行读取JSON文件（每行一个JSON对象）
        data = []
        with open(json_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:  # 跳过空行
                    try:
                        song_data = json.loads(line)
                        data.append(song_data)
                    except json.JSONDecodeError as e:
                        print(f"警告: 第{line_num}行JSON格式错误: {e}")
                        continue
    except FileNotFoundError:
        return HttpResponse("错误: songs.json 文件未找到！请确保它位于项目根目录下。", status=404)
    except Exception as e:
        return HttpResponse(f"读取文件时发生错误：{str(e)}", status=500)

    def find_file_case_insensitive(directory, filename):
        """
        在指定目录中查找文件名（大小写不敏感）
        返回找到的实际文件名，如果没找到返回None
        """
        if not os.path.exists(directory):
            return None
        
        filename_lower = filename.lower()
        for file in os.listdir(directory):
            if file.lower() == filename_lower:
                return file
        return None

    songs_added_count = 0
    songs_updated_count = 0
    songs_exist_count = 0
    songs_error_count = 0
    artists_created_count = 0
    artists_updated_count = 0
    error_details = []

    # 遍历JSON中的每一首歌曲
    for i, song_data in enumerate(data):
        try:
            # 验证必要字段是否存在
            required_fields = ['name', 'artist_name', 'source_url']
            missing_fields = [field for field in required_fields if field not in song_data or not song_data[field]]
            
            if missing_fields:
                error_msg = f"第{i+1}首歌曲缺少必要字段: {', '.join(missing_fields)}"
                error_details.append(error_msg)
                songs_error_count += 1
                continue
            
            # === 生成标准化的图片路径 ===
            # 使用原始名称生成文件名，但要处理特殊字符
            def safe_filename(name):
                # 移除或替换不安全的字符
                safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                return safe_name.strip()
            
            safe_artist_name = safe_filename(song_data['artist_name'])
            safe_song_name = safe_filename(song_data['name'])
            
            # 生成期望的图片文件名
            expected_artist_img = f"{safe_artist_name}.jpg"
            expected_song_img = f"{safe_song_name}.jpg"
            
            # 大小写不敏感地查找图片文件
            artist_img_dir = os.path.join(settings.MEDIA_ROOT, "artist_images")
            song_img_dir = os.path.join(settings.MEDIA_ROOT, "song_images")
            
            found_artist_img = find_file_case_insensitive(artist_img_dir, expected_artist_img)
            found_song_img = find_file_case_insensitive(song_img_dir, expected_song_img)
            
            # 生成实际的图片路径
            profile_img_path = f"artist_images/{found_artist_img}" if found_artist_img else ""
            cover_img_path = f"song_images/{found_song_img}" if found_song_img else ""
            
            # 调试信息
            if settings.DEBUG:
                print(f"处理歌曲: {song_data['name']} - {song_data['artist_name']}")
                print(f"  期望歌手图片: {expected_artist_img}")
                print(f"  找到歌手图片: {found_artist_img or '未找到'}")
                print(f"  期望歌曲图片: {expected_song_img}")
                print(f"  找到歌曲图片: {found_song_img or '未找到'}")
            
            # === 严格按照 songs.json 中的 artist_name 查找或创建歌手 ===
            # 使用 artist_name 精确匹配
            artist = Artist.objects.filter(name__exact=song_data['artist_name']).first()
            
            if not artist:
                # 创建新歌手
                artist = Artist.objects.create(
                    name=song_data['artist_name'],
                    biography=song_data.get('biography', ''),
                    profile_img=profile_img_path,
                    source_url=song_data.get('artist_source_url', song_data['source_url'])
                )
                artists_created_count += 1
                print(f"创建新歌手: {artist.name}")
            else:
                # 更新现有歌手信息
                updated = False
                
                # 只有当当前没有图片且找到了图片文件时才更新
                if not artist.profile_img and found_artist_img:
                    artist.profile_img = profile_img_path
                    updated = True
                
                # 更新简介（如果当前为空且JSON中有数据）
                if not artist.biography and song_data.get('biography'):
                    artist.biography = song_data.get('biography', '')
                    updated = True
                
                # 更新source_url（如果当前为空）
                if not artist.source_url and song_data.get('artist_source_url'):
                    artist.source_url = song_data.get('artist_source_url', song_data['source_url'])
                    updated = True
                
                if updated:
                    artist.save()
                    artists_updated_count += 1
                    print(f"更新歌手信息: {artist.name}")

            # === 处理歌词 ===
            lyrics = song_data.get('lyrics', '')
            if isinstance(lyrics, list):
                lyrics = '\n'.join(lyrics)
            else:
                lyrics = str(lyrics) if lyrics else ''

            # === 查找或创建歌曲 ===
            # 使用 source_url 作为唯一标识
            song = Song.objects.filter(source_url=song_data['source_url']).first()
            
            if not song:
                # 创建新歌曲
                song = Song.objects.create(
                    name=song_data['name'],
                    artist=artist,  # 使用上面找到或创建的歌手
                    lyrics=lyrics,
                    cover_img=cover_img_path,
                    source_url=song_data['source_url']
                )
                songs_added_count += 1
                print(f"创建新歌曲: {song.name} - {artist.name}")
            else:
                # 更新现有歌曲
                updated = False
                
                # 严格检查：如果歌曲的歌手与JSON中的不一致，则更新
                if song.artist.name != song_data['artist_name']:
                    old_artist = song.artist.name
                    song.artist = artist
                    updated = True
                    print(f"修正歌曲歌手: {song.name} 从 '{old_artist}' 更正为 '{artist.name}'")
                
                # 更新歌曲名称（如果不同）
                if song.name != song_data['name']:
                    song.name = song_data['name']
                    updated = True
                
                # 更新歌词
                if song.lyrics != lyrics:
                    song.lyrics = lyrics
                    updated = True
                
                # 更新封面图片（只有当前没有图片且找到了图片文件时）
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
    
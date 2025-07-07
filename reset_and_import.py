#!/usr/bin/env python3
"""
一键重置并重新导入所有歌手和歌曲的脚本
"""
import os
import json
import re
import django
from pathlib import Path
import string

# 设置Django环境
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbrowser.settings')
django.setup()

from music.models import Song, Artist
from django.conf import settings

def find_file_case_insensitive(directory, filename):
    if not os.path.exists(directory):
        return None
    filename_lower = filename.lower()
    for file in os.listdir(directory):
        if file.lower() == filename_lower:
            return file
    return None

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

def get_main_artist(artist_name):
    # 分割所有候选名
    for candidate in re.split(r'[\/，,、\s]+', artist_name):
        candidate = candidate.strip()
        if candidate in artist_alias_to_main:
            return artist_alias_to_main[candidate]
    # 如果都找不到，fallback：取第一个
    return re.split(r'[\/，,、\s]+', artist_name)[0].strip()

def safe_filename(name):
    safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    return safe_name.strip()

def reset_and_import():
    print("彻底清空数据库...")
    Song.objects.all().delete()
    Artist.objects.all().delete()
    print("数据库已清空！\n开始导入数据...")

    # === 新增：读取 artists.json，构建别名到主名的映射 ===
    global artist_alias_to_main
    artist_alias_to_main = {}
    artist_source_urls = {}  # 新增：存储歌手名到source_url的映射
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
                # 存储主名到source_url的映射
                artist_source_urls[main_name] = artist_obj.get('source_url', '')

    json_file_path = os.path.join(settings.BASE_DIR, 'output', 'songs.json')
    try:
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
    except Exception as e:
        print(f"读取songs.json失败: {e}")
        return

    songs_added_count = 0
    songs_error_count = 0
    artists_created_count = 0
    error_details = []
    artist_cache = {}

    for i, song_data in enumerate(data):
        try:
            required_fields = ['name', 'artist_name', 'source_url']
            missing_fields = [field for field in required_fields if field not in song_data or not song_data[field]]
            if missing_fields:
                error_msg = f"第{i+1}首歌曲缺少必要字段: {', '.join(missing_fields)}"
                error_details.append(error_msg)
                songs_error_count += 1
                continue

            main_artist_name = get_main_artist(song_data['artist_name'])
            safe_artist_name = safe_filename(main_artist_name)
            safe_song_name = safe_filename(song_data['name'])
            expected_artist_img = f"{safe_artist_name}.jpg"
            expected_song_img = f"{safe_song_name}.jpg"
            artist_img_dir = os.path.join(settings.MEDIA_ROOT, "artist_images")
            song_img_dir = os.path.join(settings.MEDIA_ROOT, "song_images")
            # === 用 fuzzy 匹配 artist 图片 ===
            found_artist_img = fuzzy_find_file(artist_img_dir, main_artist_name)
            found_song_img = find_file_case_insensitive(song_img_dir, expected_song_img)
            profile_img_path = f"artist_images/{found_artist_img}" if found_artist_img else ""
            cover_img_path = f"song_images/{found_song_img}" if found_song_img else ""

            # 歌手缓存优化
            if main_artist_name in artist_cache:
                artist = artist_cache[main_artist_name]
            else:
                artist = Artist.objects.filter(name__exact=main_artist_name).first()
                if not artist:
                    artist = Artist.objects.create(
                        name=main_artist_name,
                        biography=song_data.get('biography', ''),
                        profile_img=profile_img_path,
                        source_url=artist_source_urls.get(main_artist_name, song_data['source_url'])
                    )
                    artists_created_count += 1
                artist_cache[main_artist_name] = artist

            lyrics = song_data.get('lyrics', '')
            if isinstance(lyrics, list):
                lyrics = '\n'.join(lyrics)
            else:
                lyrics = str(lyrics) if lyrics else ''

            Song.objects.create(
                name=song_data['name'],
                artist=artist,
                lyrics=lyrics,
                cover_img=cover_img_path,
                source_url=song_data['source_url']
            )
            songs_added_count += 1
        except Exception as e:
            error_msg = f"第{i+1}首歌曲处理失败 ({song_data.get('name', '未知')} - {song_data.get('artist_name', '未知')}): {str(e)}"
            error_details.append(error_msg)
            songs_error_count += 1

    print(f"\n导入完成！成功添加歌曲: {songs_added_count} 首，创建歌手: {artists_created_count} 位，失败: {songs_error_count} 首")
    if error_details:
        print("前10个错误:")
        for err in error_details[:10]:
            print(err)
    print("\n数据库总歌手数:", Artist.objects.count())
    print("数据库总歌曲数:", Song.objects.count())

if __name__ == "__main__":
    reset_and_import() 
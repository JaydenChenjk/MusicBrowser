#!/usr/bin/env python3
"""
一键重置并重新导入所有歌手和歌曲的脚本
"""
import os
import json
import re
import django
from pathlib import Path

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

def get_main_artist(artist_name):
    # 只取第一个歌手名，分隔符包括 / ， ,
    return re.split(r'[\/，,]', artist_name)[0].strip()

def safe_filename(name):
    safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    return safe_name.strip()

def reset_and_import():
    print("彻底清空数据库...")
    Song.objects.all().delete()
    Artist.objects.all().delete()
    print("数据库已清空！\n开始导入数据...")

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
            found_artist_img = find_file_case_insensitive(artist_img_dir, expected_artist_img)
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
                        source_url=song_data.get('artist_source_url', song_data['source_url'])
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
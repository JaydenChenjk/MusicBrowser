#!/usr/bin/env python3
"""
数据一致性检查脚本
用于检查数据库中的歌曲和歌手数据与JSON文件的一致性
"""

import os
import json
import django
from pathlib import Path

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbrowser.settings')
django.setup()

from django.conf import settings
from music.models import Song, Artist

def check_data_consistency():
    """检查数据库与JSON文件的一致性"""
    
    # 读取JSON文件
    json_file_path = os.path.join(settings.OUT_DIR, 'songs.json')
    
    if not os.path.exists(json_file_path):
        print(f"错误: JSON文件不存在: {json_file_path}")
        return
    
    # 逐行读取JSON文件（每行一个JSON对象）
    json_data = []
    with open(json_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:  # 跳过空行
                try:
                    song_data = json.loads(line)
                    json_data.append(song_data)
                except json.JSONDecodeError as e:
                    print(f"警告: 第{line_num}行JSON格式错误: {e}")
                    continue
    
    print(f"JSON文件包含 {len(json_data)} 首歌曲")
    
    # 统计信息
    db_songs = Song.objects.count()
    db_artists = Artist.objects.count()
    print(f"数据库中有 {db_songs} 首歌曲，{db_artists} 位歌手")
    
    # 检查歌手名称不匹配的情况
    print("\n=== 检查歌手名称不匹配的情况 ===")
    mismatched_artists = []
    
    for song_data in json_data:
        song = Song.objects.filter(source_url=song_data['source_url']).first()
        if song and song.artist.name != song_data['artist_name']:
            mismatched_artists.append({
                'song': song_data['name'],
                'json_artist': song_data['artist_name'],
                'db_artist': song.artist.name,
                'source_url': song_data['source_url']
            })
    
    if mismatched_artists:
        print(f"发现 {len(mismatched_artists)} 首歌曲的歌手名称不匹配:")
        for item in mismatched_artists[:10]:  # 显示前10个
            print(f"  歌曲: {item['song']}")
            print(f"    JSON中: {item['json_artist']}")
            print(f"    数据库: {item['db_artist']}")
            print(f"    URL: {item['source_url']}")
            print()
    else:
        print("✓ 所有歌曲的歌手名称都匹配")
    
    # 检查图片文件
    print("\n=== 检查图片文件 ===")
    artist_img_dir = os.path.join(settings.MEDIA_ROOT, "artist_images")
    song_img_dir = os.path.join(settings.MEDIA_ROOT, "song_images")
    
    if os.path.exists(artist_img_dir):
        artist_files = [f for f in os.listdir(artist_img_dir) if f.endswith('.jpg')]
        print(f"歌手图片目录: {len(artist_files)} 个文件")
    else:
        print(f"歌手图片目录不存在: {artist_img_dir}")
    
    if os.path.exists(song_img_dir):
        song_files = [f for f in os.listdir(song_img_dir) if f.endswith('.jpg')]
        print(f"歌曲图片目录: {len(song_files)} 个文件")
    else:
        print(f"歌曲图片目录不存在: {song_img_dir}")
    
    # 检查数据库中图片字段为空的记录
    print("\n=== 检查图片字段为空的记录 ===")
    artists_no_img = Artist.objects.filter(profile_img='').count()
    songs_no_img = Song.objects.filter(cover_img='').count()
    
    print(f"没有头像的歌手: {artists_no_img} 位")
    print(f"没有封面的歌曲: {songs_no_img} 首")
    
    # 大小写不敏感的文件查找函数
    def find_file_case_insensitive(directory, filename):
        """在指定目录中查找文件名（大小写不敏感）"""
        if not os.path.exists(directory):
            return None
        
        filename_lower = filename.lower()
        for file in os.listdir(directory):
            if file.lower() == filename_lower:
                return file
        return None
    
    # 检查图片文件是否真实存在（大小写不敏感）
    print("\n=== 检查图片文件真实存在性（大小写不敏感） ===")
    artists_with_img = Artist.objects.exclude(profile_img='')
    missing_artist_imgs = []
    
    for artist in artists_with_img:
        if artist.profile_img:
            # 从路径中提取文件名
            img_filename = os.path.basename(artist.profile_img)
            img_dir = os.path.join(settings.MEDIA_ROOT, "artist_images")
            found_file = find_file_case_insensitive(img_dir, img_filename)
            
            if not found_file:
                missing_artist_imgs.append(artist.name)
    
    if missing_artist_imgs:
        print(f"图片文件不存在的歌手: {len(missing_artist_imgs)} 位")
        for name in missing_artist_imgs[:5]:
            print(f"  - {name}")
    else:
        print("✓ 所有歌手的图片文件都存在")
    
    songs_with_img = Song.objects.exclude(cover_img='')
    missing_song_imgs = []
    
    for song in songs_with_img:
        if song.cover_img:
            # 从路径中提取文件名
            img_filename = os.path.basename(song.cover_img)
            img_dir = os.path.join(settings.MEDIA_ROOT, "song_images")
            found_file = find_file_case_insensitive(img_dir, img_filename)
            
            if not found_file:
                missing_song_imgs.append(f"{song.name} - {song.artist.name}")
    
    if missing_song_imgs:
        print(f"图片文件不存在的歌曲: {len(missing_song_imgs)} 首")
        for name in missing_song_imgs[:5]:
            print(f"  - {name}")
    else:
        print("✓ 所有歌曲的图片文件都存在")

if __name__ == "__main__":
    check_data_consistency()
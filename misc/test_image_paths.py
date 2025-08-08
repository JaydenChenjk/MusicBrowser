#!/usr/bin/env python3
"""
测试图片路径和歌手匹配问题的脚本
"""
import os
import json
import django
from pathlib import Path

# 设置Django环境
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbrowser.settings')
django.setup()

from music.models import Song, Artist
from django.conf import settings

def test_image_paths():
    """测试图片路径问题"""
    print("=== 测试图片路径问题 ===")
    
    # 检查歌手图片
    print("\n1. 检查歌手图片:")
    artists = Artist.objects.all()[:10]  # 只检查前10个
    for artist in artists:
        if artist.profile_img:
            # 处理ImageField对象
            if hasattr(artist.profile_img, 'name'):
                img_path = artist.profile_img.name
            else:
                img_path = str(artist.profile_img)
            
            file_path = os.path.join(settings.MEDIA_ROOT, img_path)
            exists = os.path.exists(file_path)
            print(f"  歌手: {artist.name}")
            print(f"    数据库路径: {img_path}")
            print(f"    完整路径: {file_path}")
            print(f"    文件存在: {exists}")
            if not exists:
                # 尝试在artist_images目录中查找
                artist_dir = os.path.join(settings.MEDIA_ROOT, "artist_images")
                if os.path.exists(artist_dir):
                    found_files = [f for f in os.listdir(artist_dir) if f.lower().startswith(artist.name.lower())]
                    print(f"    可能的匹配文件: {found_files}")
            print()
    
    # 检查歌曲图片
    print("\n2. 检查歌曲图片:")
    songs = Song.objects.all()[:10]  # 只检查前10个
    for song in songs:
        if song.cover_img:
            # 处理ImageField对象
            if hasattr(song.cover_img, 'name'):
                img_path = song.cover_img.name
            else:
                img_path = str(song.cover_img)
            
            file_path = os.path.join(settings.MEDIA_ROOT, img_path)
            exists = os.path.exists(file_path)
            print(f"  歌曲: {song.name} - {song.artist.name}")
            print(f"    数据库路径: {img_path}")
            print(f"    完整路径: {file_path}")
            print(f"    文件存在: {exists}")
            if not exists:
                # 尝试在song_images目录中查找
                song_dir = os.path.join(settings.MEDIA_ROOT, "song_images")
                if os.path.exists(song_dir):
                    found_files = [f for f in os.listdir(song_dir) if f.lower().startswith(song.name.lower())]
                    print(f"    可能的匹配文件: {found_files}")
            print()

def test_artist_matching():
    """测试歌手匹配问题"""
    print("\n=== 测试歌手匹配问题 ===")
    
    # 读取songs.json中的一些数据
    json_file_path = os.path.join(settings.BASE_DIR, 'output', 'songs.json')
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            sample_data = []
            for i, line in enumerate(f):
                if i >= 20:  # 只读取前20行
                    break
                line = line.strip()
                if line:
                    try:
                        song_data = json.loads(line)
                        sample_data.append(song_data)
                    except json.JSONDecodeError:
                        continue
        
        print(f"\n从songs.json读取了 {len(sample_data)} 条记录")
        
        # 检查数据库中的歌手匹配
        for song_data in sample_data[:10]:  # 只检查前10个
            artist_name = song_data.get('artist_name', '')
            song_name = song_data.get('name', '')
            
            # 在数据库中查找歌手
            artist = Artist.objects.filter(name__exact=artist_name).first()
            
            print(f"\n歌曲: {song_name}")
            print(f"  JSON中的歌手: {artist_name}")
            print(f"  数据库中找到的歌手: {artist.name if artist else '未找到'}")
            
            if artist:
                # 检查这个歌手的歌曲
                songs = artist.songs.all()
                print(f"  该歌手的歌曲数量: {songs.count()}")
                if songs.exists():
                    print(f"  示例歌曲: {[s.name for s in songs[:3]]}")
            else:
                print(f"  警告: 歌手 '{artist_name}' 在数据库中未找到!")
                
    except Exception as e:
        print(f"读取songs.json时出错: {e}")

def check_image_directories():
    """检查图片目录"""
    print("\n=== 检查图片目录 ===")
    
    artist_dir = os.path.join(settings.MEDIA_ROOT, "artist_images")
    song_dir = os.path.join(settings.MEDIA_ROOT, "song_images")
    
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"歌手图片目录: {artist_dir}")
    print(f"歌曲图片目录: {song_dir}")
    
    if os.path.exists(artist_dir):
        artist_files = [f for f in os.listdir(artist_dir) if f.endswith('.jpg')]
        print(f"歌手图片文件数量: {len(artist_files)}")
        print(f"前5个歌手图片: {artist_files[:5]}")
    else:
        print("歌手图片目录不存在!")
    
    if os.path.exists(song_dir):
        song_files = [f for f in os.listdir(song_dir) if f.endswith('.jpg')]
        print(f"歌曲图片文件数量: {len(song_files)}")
        print(f"前5个歌曲图片: {song_files[:5]}")
    else:
        print("歌曲图片目录不存在!")

if __name__ == "__main__":
    check_image_directories()
    test_image_paths()
    test_artist_matching() 
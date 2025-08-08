#!/usr/bin/env python3
"""
清理数据库中无效图片路径和组合歌手的脚本
"""
import os
import django
from pathlib import Path

# 设置Django环境
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbrowser.settings')
django.setup()

from music.models import Song, Artist
from django.db.models import Q

def clean_invalid_image_paths():
    print("清理无效图片路径...")
    # 歌手图片
    artists = Artist.objects.filter(Q(profile_img__startswith='http'))
    for artist in artists:
        print(f"清空歌手图片: {artist.name} 原路径: {artist.profile_img}")
        artist.profile_img = ''
        artist.save()
    # 歌曲图片
    songs = Song.objects.filter(Q(cover_img__startswith='http'))
    for song in songs:
        print(f"清空歌曲图片: {song.name} - {song.artist.name} 原路径: {song.cover_img}")
        song.cover_img = ''
        song.save()

def delete_combined_artists():
    print("删除组合歌手记录...")
    # 名字里有 / ， , 的歌手
    combined = Artist.objects.filter(Q(name__contains='/') | Q(name__contains='，') | Q(name__contains=','))
    for artist in combined:
        print(f"删除组合歌手: {artist.name}")
        artist.delete()

def main():
    clean_invalid_image_paths()
    delete_combined_artists()
    print("数据库清理完成！")

if __name__ == "__main__":
    main() 
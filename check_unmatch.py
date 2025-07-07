#!/usr/bin/env python3
"""
修复歌手不匹配的脚本
严格按照songs.json中的artist_name来更正数据库中的歌手分配
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

def fix_artist_mismatch():
    """修复歌手不匹配的问题"""
    
    # 读取JSON文件
    json_file_path = os.path.join(settings.BASE_DIR, 'songs.json')
    
    if not os.path.exists(json_file_path):
        print(f"错误: JSON文件不存在: {json_file_path}")
        return
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    print(f"开始修复歌手不匹配问题...")
    print(f"JSON文件包含 {len(json_data)} 首歌曲")
    
    fixed_count = 0
    error_count = 0
    
    for i, song_data in enumerate(json_data):
        try:
            # 根据source_url找到歌曲
            song = Song.objects.filter(source_url=song_data['source_url']).first()
            
            if not song:
                print(f"警告: 找不到歌曲 {song_data['name']} (URL: {song_data['source_url']})")
                continue
            
            # 检查歌手是否匹配
            if song.artist.name != song_data['artist_name']:
                print(f"修复歌曲: {song_data['name']}")
                print(f"  当前歌手: {song.artist.name}")
                print(f"  正确歌手: {song_data['artist_name']}")
                
                # 查找或创建正确的歌手
                correct_artist = Artist.objects.filter(name__exact=song_data['artist_name']).first()
                
                if not correct_artist:
                    # 创建新歌手
                    def safe_filename(name):
                        return name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_').strip()
                    
                    safe_artist_name = safe_filename(song_data['artist_name'])
                    profile_img_path = f"artist_images/{safe_artist_name}.jpg"
                    profile_img_full_path = os.path.join(settings.MEDIA_ROOT, profile_img_path)
                    profile_img_exists = os.path.exists(profile_img_full_path)
                    
                    correct_artist = Artist.objects.create(
                        name=song_data['artist_name'],
                        biography=song_data.get('biography', ''),
                        profile_img=profile_img_path if profile_img_exists else '',
                        source_url=song_data.get('artist_source_url', song_data['source_url'])
                    )
                    print(f"  创建新歌手: {correct_artist.name}")
                
                # 更新歌曲的歌手
                song.artist = correct_artist
                song.save()
                
                fixed_count += 1
                print(f"  ✓ 修复完成")
                
        except Exception as e:
            error_count += 1
            print(f"错误: 处理歌曲 {song_data.get('name', '未知')} 时发生错误: {str(e)}")
    
    print(f"\n修复完成!")
    print(f"修复的歌曲数: {fixed_count}")
    print(f"错误数: {error_count}")
    
    # 清理没有歌曲的歌手
    print("\n清理没有歌曲的歌手...")
    orphaned_artists = Artist.objects.filter(songs__isnull=True)
    orphaned_count = orphaned_artists.count()
    
    if orphaned_count > 0:
        print(f"发现 {orphaned_count} 位没有歌曲的歌手:")
        for artist in orphaned_artists[:10]:
            print(f"  - {artist.name}")
        
        # 询问是否删除
        response = input("\n是否删除这些没有歌曲的歌手? (y/n): ")
        if response.lower() == 'y':
            orphaned_artists.delete()
            print(f"已删除 {orphaned_count} 位没有歌曲的歌手")
    else:
        print("✓ 没有发现没有歌曲的歌手")

if __name__ == "__main__":
    fix_artist_mismatch()
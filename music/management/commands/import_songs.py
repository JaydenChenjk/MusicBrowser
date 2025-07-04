#!/usr/bin/env python3
"""
Django歌曲数据导入脚本
用于从output/songs.json文件中导入歌曲数据到数据库
"""

import os
import sys
import json
import django
from pathlib import Path

# 设置Django环境
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbrowser.settings')

# 初始化Django
django.setup()

from music.models import Artist, Song


def load_songs_from_json(json_file_path):
    """从JSON文件加载歌曲数据"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"错误：找不到文件 {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"错误：JSON格式错误 - {e}")
        return None
    except Exception as e:
        print(f"错误：读取文件时发生错误 - {e}")
        return None


def import_songs_to_database(songs_data):
    """将歌曲数据导入数据库"""
    if not songs_data:
        print("没有数据需要导入")
        return
    
    # 统计信息
    created_artists = 0
    created_songs = 0
    updated_artists = 0
    updated_songs = 0
    errors = 0
    
    print(f"开始导入 {len(songs_data)} 首歌曲的数据...")
    
    for i, song_data in enumerate(songs_data, 1):
        try:
            # 打印进度
            if i % 100 == 0:
                print(f"处理进度: {i}/{len(songs_data)}")
            
            # 获取歌曲信息
            song_name = song_data.get('name', '').strip()
            artist_name = song_data.get('artist', '').strip()
            lyrics = song_data.get('lyrics', '').strip()
            song_url = song_data.get('url', '').strip()
            artist_bio = song_data.get('artist_bio', '').strip()
            
            # 检查必要字段
            if not song_name or not artist_name or not song_url:
                print(f"警告：第{i}首歌曲缺少必要信息，跳过")
                continue
            
            # 创建或获取歌手
            artist_defaults = {
                'biography': artist_bio,
                'source_url': song_url  # 如果没有专门的歌手URL，使用歌曲URL
            }
            
            artist, artist_created = Artist.objects.get_or_create(
                name=artist_name,
                defaults=artist_defaults
            )
            
            if artist_created:
                created_artists += 1
            else:
                # 更新歌手信息（如果有新的传记信息）
                if artist_bio and not artist.biography:
                    artist.biography = artist_bio
                    artist.save()
                    updated_artists += 1
            
            # 创建或更新歌曲
            song_defaults = {
                'artist': artist,
                'lyrics': lyrics,
                'source_url': song_url
            }
            
            song, song_created = Song.objects.get_or_create(
                name=song_name,
                artist=artist,
                defaults=song_defaults
            )
            
            if song_created:
                created_songs += 1
            else:
                # 更新歌曲信息
                updated = False
                if lyrics and not song.lyrics:
                    song.lyrics = lyrics
                    updated = True
                if song_url and song.source_url != song_url:
                    song.source_url = song_url
                    updated = True
                
                if updated:
                    song.save()
                    updated_songs += 1
                    
        except Exception as e:
            print(f"错误：处理第{i}首歌曲时发生错误 - {e}")
            errors += 1
            continue
    
    # 打印统计信息
    print(f"\n导入完成！")
    print(f"创建歌手: {created_artists}")
    print(f"更新歌手: {updated_artists}")
    print(f"创建歌曲: {created_songs}")
    print(f"更新歌曲: {updated_songs}")
    print(f"错误数量: {errors}")
    
    # 验证数据库中的总数
    total_artists = Artist.objects.count()
    total_songs = Song.objects.count()
    print(f"\n数据库中现有:")
    print(f"歌手总数: {total_artists}")
    print(f"歌曲总数: {total_songs}")


def main():
    """主函数"""
    # JSON文件路径
    json_file_path = BASE_DIR / 'output' / 'songs.json'
    
    print("Django歌曲数据导入工具")
    print("=" * 50)
    
    # 检查文件是否存在
    if not json_file_path.exists():
        print(f"错误：找不到文件 {json_file_path}")
        print("请确保songs.json文件存在于output目录中")
        return
    
    # 加载JSON数据
    print(f"正在加载数据文件: {json_file_path}")
    songs_data = load_songs_from_json(json_file_path)
    
    if songs_data is None:
        return
    
    print(f"成功加载 {len(songs_data)} 首歌曲的数据")
    
    # 确认导入
    response = input("\n是否继续导入数据到数据库？(y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("取消导入")
        return
    
    # 导入数据
    import_songs_to_database(songs_data)


if __name__ == "__main__":
    main()
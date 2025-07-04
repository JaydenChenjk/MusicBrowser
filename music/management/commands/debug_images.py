# 在 music/management/commands/debug_images.py 中创建此文件
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from music.models import Artist, Song

class Command(BaseCommand):
    help = '调试图片路径问题，检查数据库记录与实际文件的对应关系'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        self.stdout.write(f"媒体文件根目录: {media_root}")
        self.stdout.write(f"媒体文件URL: {settings.MEDIA_URL}")
        self.stdout.write("=" * 50)
        
        # 检查歌手头像
        self.stdout.write("检查歌手头像:")
        artist_issues = []
        for artist in Artist.objects.all():
            status = "✓" if artist.profile_img else "✗(无图片字段)"
            db_path = artist.profile_img.name if artist.profile_img else "无"
            
            if artist.profile_img:
                full_path = os.path.join(media_root, artist.profile_img.name)
                file_exists = os.path.exists(full_path)
                if not file_exists:
                    status = "✗(文件不存在)"
                    artist_issues.append({
                        'name': artist.name,
                        'db_path': db_path,
                        'full_path': full_path,
                        'issue': '文件不存在'
                    })
            
            self.stdout.write(f"  {status} {artist.name}: {db_path}")
        
        self.stdout.write("-" * 30)
        
        # 检查歌曲封面
        self.stdout.write("检查歌曲封面:")
        song_issues = []
        for song in Song.objects.select_related('artist').all():
            status = "✓" if song.cover_img else "✗(无图片字段)"
            db_path = song.cover_img.name if song.cover_img else "无"
            
            if song.cover_img:
                full_path = os.path.join(media_root, song.cover_img.name)
                file_exists = os.path.exists(full_path)
                if not file_exists:
                    status = "✗(文件不存在)"
                    song_issues.append({
                        'name': song.name,
                        'artist': song.artist.name,
                        'db_path': db_path,
                        'full_path': full_path,
                        'issue': '文件不存在'
                    })
            
            self.stdout.write(f"  {status} {song.name} - {song.artist.name}: {db_path}")
        
        # 检查实际文件夹结构
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("检查实际文件夹结构:")
        
        # 检查歌手图片文件夹
        artist_img_dir = os.path.join(media_root, "artist_images")
        if os.path.exists(artist_img_dir):
            self.stdout.write(f"歌手图片文件夹: {artist_img_dir}")
            for file in os.listdir(artist_img_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    self.stdout.write(f"  实际文件: {file}")
        else:
            self.stdout.write(f"歌手图片文件夹不存在: {artist_img_dir}")
        
        # 检查歌曲图片文件夹
        song_img_dir = os.path.join(media_root, "song_images")
        if os.path.exists(song_img_dir):
            self.stdout.write(f"歌曲图片文件夹: {song_img_dir}")
            for artist_folder in os.listdir(song_img_dir):
                artist_folder_path = os.path.join(song_img_dir, artist_folder)
                if os.path.isdir(artist_folder_path):
                    self.stdout.write(f"  歌手文件夹: {artist_folder}")
                    for file in os.listdir(artist_folder_path):
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            self.stdout.write(f"    实际文件: {file}")
        else:
            self.stdout.write(f"歌曲图片文件夹不存在: {song_img_dir}")
        
        # 输出问题总结
        if artist_issues or song_issues:
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("发现的问题:")
            
            if artist_issues:
                self.stdout.write(f"歌手头像问题 ({len(artist_issues)}个):")
                for issue in artist_issues:
                    self.stdout.write(f"  - {issue['name']}: {issue['issue']}")
                    self.stdout.write(f"    数据库路径: {issue['db_path']}")
                    self.stdout.write(f"    完整路径: {issue['full_path']}")
            
            if song_issues:
                self.stdout.write(f"歌曲封面问题 ({len(song_issues)}个):")
                for issue in song_issues:
                    self.stdout.write(f"  - {issue['name']} ({issue['artist']}): {issue['issue']}")
                    self.stdout.write(f"    数据库路径: {issue['db_path']}")
                    self.stdout.write(f"    完整路径: {issue['full_path']}")
        
        # 建议修复方案
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("建议的修复方案:")
        self.stdout.write("1. 运行 python manage.py fix_image_paths 来修复路径")
        self.stdout.write("2. 检查文件权限，确保Django能读取图片文件")
        self.stdout.write("3. 如果文件名包含特殊字符，考虑重命名文件")
        self.stdout.write("4. 确保 MEDIA_ROOT 和 MEDIA_URL 配置正确")
        
        self.stdout.write(self.style.SUCCESS("调试完成！"))
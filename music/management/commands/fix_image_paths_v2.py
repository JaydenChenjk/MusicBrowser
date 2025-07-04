# 在 music/management/commands/fix_image_paths_v2.py 中创建此文件
import os
import shutil
import glob
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from music.models import Artist, Song

class Command(BaseCommand):
    help = '智能修复图片路径，处理各种文件名情况'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要执行的操作，不实际修改文件',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        media_root = settings.MEDIA_ROOT
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN 模式 - 不会实际修改文件"))
        
        self.stdout.write(f"媒体文件根目录: {media_root}")
        
        # 修复歌手头像
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("修复歌手头像:")
        
        artist_img_dir = os.path.join(media_root, "artist_images")
        if os.path.exists(artist_img_dir):
            # 获取所有实际存在的图片文件
            actual_files = {}
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif']:
                for file_path in glob.glob(os.path.join(artist_img_dir, ext)):
                    filename = os.path.basename(file_path)
                    name_without_ext = os.path.splitext(filename)[0]
                    actual_files[name_without_ext.lower()] = filename
            
            for artist in Artist.objects.all():
                # 生成应该使用的文件名
                safe_name = slugify(artist.name, allow_unicode=True)
                if not safe_name:
                    safe_name = f"artist_{artist.id}"
                
                expected_path = f"artist_images/{safe_name}.jpg"
                
                # 检查数据库中的路径是否正确
                if artist.profile_img and artist.profile_img.name == expected_path:
                    full_path = os.path.join(media_root, expected_path)
                    if os.path.exists(full_path):
                        self.stdout.write(f"  ✓ {artist.name}: 已正确")
                        continue
                
                # 尝试找到匹配的实际文件
                possible_matches = [
                    artist.name.lower(),
                    safe_name.lower(),
                    slugify(artist.name).lower(),
                ]
                
                found_file = None
                for match in possible_matches:
                    if match in actual_files:
                        found_file = actual_files[match]
                        break
                
                if found_file:
                    old_path = os.path.join(artist_img_dir, found_file)
                    new_path = os.path.join(artist_img_dir, f"{safe_name}.jpg")
                    
                    if old_path != new_path:
                        self.stdout.write(f"  → {artist.name}: {found_file} -> {safe_name}.jpg")
                        if not dry_run:
                            if os.path.exists(old_path):
                                shutil.move(old_path, new_path)
                    
                    if not dry_run:
                        artist.profile_img.name = expected_path
                        artist.save()
                else:
                    self.stdout.write(f"  ✗ {artist.name}: 未找到匹配的图片文件")
        
        # 修复歌曲封面
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("修复歌曲封面:")
        
        song_img_dir = os.path.join(media_root, "song_images")
        if os.path.exists(song_img_dir):
            for song in Song.objects.select_related('artist').all():
                # 生成应该使用的路径
                safe_artist_name = slugify(song.artist.name, allow_unicode=True)
                safe_song_name = slugify(song.name, allow_unicode=True)
                
                if not safe_artist_name:
                    safe_artist_name = f"artist_{song.artist.id}"
                if not safe_song_name:
                    safe_song_name = f"song_{song.id}"
                
                expected_path = f"song_images/{safe_artist_name}/{safe_song_name}.jpg"
                
                # 检查数据库中的路径是否正确
                if song.cover_img and song.cover_img.name == expected_path:
                    full_path = os.path.join(media_root, expected_path)
                    if os.path.exists(full_path):
                        self.stdout.write(f"  ✓ {song.name} - {song.artist.name}: 已正确")
                        continue
                
                # 尝试找到匹配的实际文件
                possible_artist_dirs = [
                    song.artist.name,
                    safe_artist_name,
                    slugify(song.artist.name),
                ]
                
                found_file = None
                for artist_dir in possible_artist_dirs:
                    artist_dir_path = os.path.join(song_img_dir, artist_dir)
                    if os.path.exists(artist_dir_path):
                        possible_song_files = [
                            f"{song.name}.jpg",
                            f"{safe_song_name}.jpg",
                            f"{slugify(song.name)}.jpg",
                        ]
                        
                        for song_file in possible_song_files:
                            file_path = os.path.join(artist_dir_path, song_file)
                            if os.path.exists(file_path):
                                found_file = (artist_dir, song_file)
                                break
                        
                        if found_file:
                            break
                
                if found_file:
                    old_artist_dir, old_song_file = found_file
                    old_path = os.path.join(song_img_dir, old_artist_dir, old_song_file)
                    new_dir = os.path.join(song_img_dir, safe_artist_name)
                    new_path = os.path.join(new_dir, f"{safe_song_name}.jpg")
                    
                    self.stdout.write(f"  → {song.name} - {song.artist.name}: {old_artist_dir}/{old_song_file} -> {safe_artist_name}/{safe_song_name}.jpg")
                    
                    if not dry_run:
                        os.makedirs(new_dir, exist_ok=True)
                        if old_path != new_path and os.path.exists(old_path):
                            shutil.move(old_path, new_path)
                        
                        song.cover_img.name = expected_path
                        song.save()
                else:
                    self.stdout.write(f"  ✗ {song.name} - {song.artist.name}: 未找到匹配的图片文件")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN 完成 - 没有实际修改任何文件"))
            self.stdout.write("如果以上操作看起来正确，请运行: python manage.py fix_image_paths_v2")
        else:
            self.stdout.write(self.style.SUCCESS("\n图片路径修复完成！"))
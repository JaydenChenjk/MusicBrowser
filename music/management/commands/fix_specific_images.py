import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from music.models import Artist, Song

class Command(BaseCommand):
    help = '修复特定的图片路径问题'

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
        
        self.stdout.write("开始修复特定的图片路径问题...")
        
        # 修复歌曲图片问题
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("修复歌曲图片:")
        
        # 1. 修复"怼个好年(Prod. By A-Fi Beats)"的图片
        song_name = "怼个好年(Prod. By A-Fi Beats)"
        song = Song.objects.filter(name=song_name).first()
        if song:
            old_path = "song_images/怼个好年prod-by-a-fi-beats.jpg"
            new_path = "song_images/怼个好年prod-by-a-fi-beats.jpg"
            
            old_full_path = os.path.join(media_root, old_path)
            new_full_path = os.path.join(media_root, new_path)
            
            if os.path.exists(old_full_path):
                self.stdout.write(f"  → {song_name}: 修复图片路径")
                if not dry_run:
                    song.cover_img.name = new_path
                    song.save()
            else:
                self.stdout.write(f"  ✗ {song_name}: 图片文件不存在 - {old_full_path}")
        else:
            self.stdout.write(f"  ✗ 未找到歌曲: {song_name}")
        
        # 修复歌手图片问题
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("修复歌手图片:")
        
        # 2. 修复"ずっと真夜中でいいのに。"的图片
        artist_name = "ずっと真夜中でいいのに。"
        artist = Artist.objects.filter(name=artist_name).first()
        if artist:
            new_path = "artist_images/ずっと真夜中でいいのにzutomayoztmyずとまよ.jpg"
            
            new_full_path = os.path.join(media_root, new_path)
            
            if os.path.exists(new_full_path):
                self.stdout.write(f"  → {artist_name}: 修复图片路径")
                if not dry_run:
                    artist.profile_img.name = new_path
                    artist.save()
            else:
                self.stdout.write(f"  ✗ {artist_name}: 图片文件不存在 - {new_full_path}")
        else:
            self.stdout.write(f"  ✗ 未找到歌手: {artist_name}")
        
        # 3. 修复"The Walters"歌手的图片路径
        artist_name = "The Walters"
        artist = Artist.objects.filter(name=artist_name).first()
        if artist:
            new_path = "artist_images/the-walters.jpg"
            
            new_full_path = os.path.join(media_root, new_path)
            
            if os.path.exists(new_full_path):
                self.stdout.write(f"  → {artist_name}: 修复图片路径")
                if not dry_run:
                    artist.profile_img.name = new_path
                    artist.save()
            else:
                self.stdout.write(f"  ✗ {artist_name}: 图片文件不存在 - {new_full_path}")
        else:
            self.stdout.write(f"  ✗ 未找到歌手: {artist_name}")
        
        # 4. 修复"ワンダーランズ×ショウタイム"的图片
        artist_name = "ワンダーランズ×ショウタイム"
        artist = Artist.objects.filter(name=artist_name).first()
        if artist:
            # 图片已经在artist_images目录下
            new_path = "artist_images/ワンダーランズ×ショウタイム.jpg"
            
            new_full_path = os.path.join(media_root, new_path)
            
            if os.path.exists(new_full_path):
                self.stdout.write(f"  → {artist_name}: 修复图片路径")
                if not dry_run:
                    artist.profile_img.name = new_path
                    artist.save()
            else:
                self.stdout.write(f"  ✗ {artist_name}: 图片文件不存在 - {new_full_path}")
        else:
            self.stdout.write(f"  ✗ 未找到歌手: {artist_name}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN 完成 - 没有实际修改任何文件"))
            self.stdout.write("如果以上操作看起来正确，请运行: python manage.py fix_specific_images")
        else:
            self.stdout.write(self.style.SUCCESS("\n特定图片路径修复完成！")) 
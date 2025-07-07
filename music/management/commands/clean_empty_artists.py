from django.core.management.base import BaseCommand
from music.models import Artist
from django.db import models

class Command(BaseCommand):
    help = '删除没有歌曲的歌手'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要执行的操作，不实际删除',
        )
        parser.add_argument(
            '--specific',
            nargs='+',
            help='指定要删除的歌手名称列表',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_artists = options['specific']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN 模式 - 不会实际删除"))
        
        if specific_artists:
            # 删除指定的歌手
            self.stdout.write(f"准备删除指定的歌手: {', '.join(specific_artists)}")
            artists_to_delete = Artist.objects.filter(name__in=specific_artists)
        else:
            # 删除所有没有歌曲的歌手
            self.stdout.write("准备删除所有没有歌曲的歌手...")
            artists_to_delete = Artist.objects.annotate(
                song_count=models.Count('songs')
            ).filter(song_count=0)
        
        if not artists_to_delete.exists():
            self.stdout.write("没有找到要删除的歌手")
            return
        
        self.stdout.write(f"找到 {artists_to_delete.count()} 个要删除的歌手:")
        
        for artist in artists_to_delete:
            song_count = artist.songs.count()
            has_image = bool(artist.profile_img)
            self.stdout.write(f"  - {artist.name}: 歌曲数={song_count}, 有图片={has_image}")
        
        if not dry_run:
            # 实际删除
            deleted_count = artists_to_delete.count()
            artists_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f"成功删除 {deleted_count} 个歌手"))
        else:
            self.stdout.write(self.style.WARNING(f"DRY RUN: 将删除 {artists_to_delete.count()} 个歌手"))
            self.stdout.write("如果以上操作看起来正确，请运行: python manage.py clean_empty_artists")
        
        # 显示剩余歌手统计
        total_artists = Artist.objects.count()
        artists_with_songs = Artist.objects.annotate(
            song_count=models.Count('songs')
        ).filter(song_count__gt=0).count()
        
        self.stdout.write(f"\n数据库统计:")
        self.stdout.write(f"总歌手数: {total_artists}")
        self.stdout.write(f"有歌曲的歌手: {artists_with_songs}")
        self.stdout.write(f"空歌手: {total_artists - artists_with_songs}") 
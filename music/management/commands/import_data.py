import json, os, urllib.request, pathlib
from django.core.management.base import BaseCommand
from django.conf import settings
from music.models import Artist, Song

class Command(BaseCommand):
    help = "导入 artists.json 与 songs.json 到数据库，并把图片存到 MEDIA_ROOT"

    def add_arguments(self, parser):
        parser.add_argument("--dir", default="output", help="JSON 所在目录")

    def handle(self, *args, **opts):
        base = pathlib.Path(opts["dir"])
        artist_path = base / "artists.json"
        song_path   = base / "songs.json"
        if not artist_path.exists() or not song_path.exists():
            self.stderr.write("未找到 JSON 文件")
            return

        # 1. 先导入或更新歌手
        with open(artist_path, encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                artist, _ = Artist.objects.update_or_create(
                    source_url=obj["source_url"],
                    defaults={
                        "name": obj["name"],
                        "biography": obj["biography"],
                        "profile_img": f"artist_images/{obj['profile_img'].split('/')[-1].split('?')[0][:60]}",
                    },
                )
        self.stdout.write("√ Artist 导入完成")

        # 2. 导入歌曲
        with open(song_path, encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                artist = Artist.objects.filter(name=obj["artist_name"]).first()
                if not artist:
                    continue
                song, _ = Song.objects.update_or_create(
                    source_url=obj["source_url"],
                    defaults={
                        "name": obj["name"],
                        "lyrics": obj["lyrics"],
                        "artist": artist,
                        "cover_img": f"song_images/{obj['artist_name']}/{obj['cover_img'].split('/')[-1].split('?')[0][:60]}",
                    },
                )
        self.stdout.write("√ Song 导入完成")
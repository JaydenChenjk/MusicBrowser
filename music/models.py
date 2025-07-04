from django.db import models
from django.utils.text import slugify

class Artist(models.Model):     
    name = models.CharField(max_length=200, db_index=True)
    biography = models.TextField(blank=True)
    profile_img = models.ImageField(upload_to="artist_images/", blank=True)
    source_url = models.URLField(unique=True)

    def __str__(self):
        return self.name


def song_cover_path(instance, filename):
    # 始终使用歌曲名的 slug 作为文件名，保持磁盘与数据库一致
    ext = filename.split('.')[-1] or 'jpg'
    filename = f"{slugify(instance.name)}.{ext}"
    return f"song_images/{instance.artist.name}/{filename}"

class Song(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="songs")     # 指向Artist类
    lyrics = models.TextField(blank=True)
    cover_img = models.ImageField(upload_to=song_cover_path, blank=True)
    source_url = models.URLField(unique=True)  

    def __str__(self):
        return f"{self.name} - {self.artist.name}"


class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)   #自动记录评论时间
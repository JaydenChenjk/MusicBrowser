from django.db import models
from django.utils.text import slugify
import os

def artist_profile_path(instance, filename):
    """生成歌手头像的存储路径"""
    # 使用slugify处理中文字符，避免路径问题
    ext = filename.split('.')[-1] or 'jpg'
    safe_name = slugify(instance.name, allow_unicode=True)
    if not safe_name:  # 如果slugify后为空，使用ID
        safe_name = f"artist_{instance.id}"
    filename = f"{safe_name}.{ext}"
    return f"artist_images/{filename}"

def song_cover_path(instance, filename):
    """生成歌曲封面的存储路径"""
    # 使用slugify处理中文字符，避免路径问题
    ext = filename.split('.')[-1] or 'jpg'
    safe_artist_name = slugify(instance.artist.name, allow_unicode=True)
    safe_song_name = slugify(instance.name, allow_unicode=True)
    
    if not safe_artist_name:
        safe_artist_name = f"artist_{instance.artist.id}"
    if not safe_song_name:
        safe_song_name = f"song_{instance.id}"
    
    filename = f"{safe_song_name}.{ext}"
    return f"song_images/{safe_artist_name}/{filename}"

class Artist(models.Model):     
    name = models.CharField(max_length=200, db_index=True)
    biography = models.TextField(blank=True)
    profile_img = models.ImageField(upload_to=artist_profile_path, blank=True)
    source_url = models.URLField(unique=True)

    def __str__(self):
        return self.name

class Song(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="songs")
    lyrics = models.TextField(blank=True)
    cover_img = models.ImageField(upload_to=song_cover_path, blank=True)
    source_url = models.URLField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.artist.name}"

class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
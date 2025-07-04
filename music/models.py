from django.db import models

class Artist(models.Model):     
    name = models.CharField(max_length=200, db_index=True)
    biography = models.TextField(blank=True)
    profile_img = models.ImageField(upload_to="artist/", blank=True)
    source_url = models.URLField(unique=True)

    def __str__(self):
        return self.name


class Song(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="songs")     # 指向Artist类
    lyrics = models.TextField(blank=True)
    cover_img = models.ImageField(upload_to="cover/", blank=True)
    source_url = models.URLField(unique=True)  

    def __str__(self):
        return f"{self.name} - {self.artist.name}"


class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)   #自动记录评论时间
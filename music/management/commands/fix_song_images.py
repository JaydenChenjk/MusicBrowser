import os
import re
import string
from difflib import SequenceMatcher
from django.core.management.base import BaseCommand
from django.conf import settings
from music.models import Song

class Command(BaseCommand):
    help = '使用智能模糊匹配算法修复歌曲图片路径'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要执行的操作，不实际修改数据库',
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.6,
            help='相似度阈值 (0.0-1.0，默认0.6)',
        )

    def normalize_for_matching(self, text):
        """标准化文本用于匹配"""
        if not text:
            return ""
        
        # 转换为小写
        text = text.lower()
        
        # 替换常见的分隔符为空格
        text = re.sub(r'[_\-\.,;:!?()[\]{}"\']+', ' ', text)
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 移除所有标点符号
        text = ''.join(c for c in text if c not in string.punctuation)
        
        return text

    def calculate_similarity(self, str1, str2):
        """计算两个字符串的相似度"""
        if not str1 or not str2:
            return 0.0
        
        # 标准化两个字符串
        norm1 = self.normalize_for_matching(str1)
        norm2 = self.normalize_for_matching(str2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # 使用序列匹配器计算相似度
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # 额外检查：如果一个是另一个的子字符串，提高相似度
        if norm1 in norm2 or norm2 in norm1:
            similarity = max(similarity, 0.8)
        
        return similarity

    def find_best_match(self, song_name, directory):
        """在目录中查找最佳匹配的图片文件"""
        if not os.path.exists(directory):
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for filename in os.listdir(directory):
            if not filename.lower().endswith('.jpg'):
                continue
            
            # 移除文件扩展名
            file_name_without_ext = os.path.splitext(filename)[0]
            
            # 计算相似度
            similarity = self.calculate_similarity(song_name, file_name_without_ext)
            
            if similarity > best_score:
                best_score = similarity
                best_match = filename
        
        return best_match, best_score

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        threshold = options['threshold']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN 模式 - 不会实际修改数据库"))
        
        self.stdout.write(f"开始修复歌曲图片路径 (相似度阈值: {threshold})...")
        
        song_img_dir = os.path.join(settings.MEDIA_ROOT, "song_images")
        if not os.path.exists(song_img_dir):
            self.stdout.write(self.style.ERROR(f"歌曲图片目录不存在: {song_img_dir}"))
            return
        
        # 获取所有歌曲
        songs = Song.objects.all()
        self.stdout.write(f"找到 {songs.count()} 首歌曲")
        
        fixed_count = 0
        no_match_count = 0
        already_correct_count = 0
        
        for song in songs:
            # 检查当前图片路径是否正确
            current_path = song.cover_img.name if song.cover_img else ""
            current_full_path = os.path.join(settings.MEDIA_ROOT, current_path) if current_path else ""
            
            # 如果当前路径存在且正确，跳过
            if current_path and os.path.exists(current_full_path):
                already_correct_count += 1
                continue
            
            # 查找最佳匹配
            best_match, similarity = self.find_best_match(song.name, song_img_dir)
            
            if best_match and similarity >= threshold:
                new_path = f"song_images/{best_match}"
                new_full_path = os.path.join(settings.MEDIA_ROOT, new_path)
                
                if os.path.exists(new_full_path):
                    self.stdout.write(f"  → {song.name}: {current_path or '无图片'} -> {new_path} (相似度: {similarity:.2f})")
                    
                    if not dry_run:
                        song.cover_img.name = new_path
                        song.save()
                    
                    fixed_count += 1
                else:
                    self.stdout.write(f"  ✗ {song.name}: 找到匹配文件但文件不存在 - {new_full_path}")
                    no_match_count += 1
            else:
                if best_match:
                    self.stdout.write(f"  ✗ {song.name}: 最佳匹配 '{best_match}' 相似度过低 ({similarity:.2f} < {threshold})")
                else:
                    self.stdout.write(f"  ✗ {song.name}: 未找到匹配的图片文件")
                no_match_count += 1
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN 完成 - 没有实际修改数据库"))
            self.stdout.write("如果以上操作看起来正确，请运行: python manage.py fix_song_images")
        else:
            self.stdout.write(self.style.SUCCESS(f"\n修复完成！"))
            self.stdout.write(f"修复歌曲: {fixed_count} 首")
            self.stdout.write(f"已有正确图片: {already_correct_count} 首")
            self.stdout.write(f"未找到匹配: {no_match_count} 首")
            
            # 显示统计信息
            total_songs = Song.objects.count()
            songs_with_images = Song.objects.filter(cover_img__isnull=False).exclude(cover_img='').count()
            self.stdout.write(f"\n数据库统计:")
            self.stdout.write(f"总歌曲数: {total_songs}")
            self.stdout.write(f"有图片的歌曲: {songs_with_images}")
            self.stdout.write(f"图片覆盖率: {songs_with_images/total_songs*100:.1f}%" if total_songs > 0 else "图片覆盖率: 0%") 
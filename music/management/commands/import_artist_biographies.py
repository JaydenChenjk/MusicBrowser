import os
import json
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from music.models import Artist

class Command(BaseCommand):
    help = '从 artists.json 文件导入歌手简介数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要执行的操作，不实际修改数据库',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN 模式 - 不会实际修改数据库"))
        
        # 构建 artists.json 文件的绝对路径
        artist_json_path = os.path.join(settings.BASE_DIR, 'output', 'artists.json')
        
        if not os.path.exists(artist_json_path):
            self.stdout.write(self.style.ERROR(f"错误: artists.json 文件未找到！路径: {artist_json_path}"))
            return
        
        self.stdout.write(f"开始从 {artist_json_path} 导入歌手简介...")
        
        # 构建别名到主名的映射
        artist_alias_to_main = {}
        artist_data = {}
        
        try:
            with open(artist_json_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        artist_obj = json.loads(line)
                        # 主名为第一个
                        main_name = re.split(r'[\/，,、\s]+', artist_obj['name'])[0].strip()
                        # 分割所有别名
                        for alias in re.split(r'[\/，,、\s]+', artist_obj['name']):
                            alias = alias.strip()
                            if alias:
                                artist_alias_to_main[alias] = main_name
                        
                        # 保存主名的数据
                        if main_name not in artist_data:
                            artist_data[main_name] = artist_obj
                        else:
                            # 如果已经有数据，合并biography
                            if artist_obj.get('biography') and not artist_data[main_name].get('biography'):
                                artist_data[main_name]['biography'] = artist_obj['biography']
                            if artist_obj.get('profile_img') and not artist_data[main_name].get('profile_img'):
                                artist_data[main_name]['profile_img'] = artist_obj['profile_img']
                            if artist_obj.get('source_url') and not artist_data[main_name].get('source_url'):
                                artist_data[main_name]['source_url'] = artist_obj['source_url']
                                
                    except json.JSONDecodeError as e:
                        self.stdout.write(self.style.WARNING(f"警告: 第{line_num}行JSON格式错误: {e}"))
                        continue
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"读取文件时发生错误：{str(e)}"))
            return
        
        self.stdout.write(f"成功解析 {len(artist_data)} 个歌手的数据")
        
        updated_count = 0
        created_count = 0
        not_found_count = 0
        
        for main_name, artist_obj in artist_data.items():
            # 查找数据库中的歌手
            artist = Artist.objects.filter(name__exact=main_name).first()
            
            if artist:
                # 更新现有歌手
                updated = False
                
                if artist_obj.get('biography') and not artist.biography:
                    if not dry_run:
                        artist.biography = artist_obj['biography']
                    updated = True
                    self.stdout.write(f"  → {main_name}: 添加简介")
                
                if artist_obj.get('profile_img') and not artist.profile_img:
                    if not dry_run:
                        artist.profile_img.name = artist_obj['profile_img']
                    updated = True
                    self.stdout.write(f"  → {main_name}: 添加头像")
                
                if artist_obj.get('source_url') and not artist.source_url:
                    if not dry_run:
                        artist.source_url = artist_obj['source_url']
                    updated = True
                    self.stdout.write(f"  → {main_name}: 添加来源链接")
                
                if updated and not dry_run:
                    artist.save()
                    updated_count += 1
                elif not updated:
                    self.stdout.write(f"  ✓ {main_name}: 已有完整信息")
            else:
                # 创建新歌手前，先用source_url查找是否已存在
                existing_artist = None
                if artist_obj.get('source_url'):
                    existing_artist = Artist.objects.filter(source_url=artist_obj['source_url']).first()
                if existing_artist:
                    # 已有同source_url的歌手，更新信息
                    updated = False
                    if artist_obj.get('biography') and not existing_artist.biography:
                        existing_artist.biography = artist_obj['biography']
                        updated = True
                    if artist_obj.get('profile_img') and not existing_artist.profile_img:
                        existing_artist.profile_img.name = artist_obj['profile_img']
                        updated = True
                    if artist_obj.get('source_url') and not existing_artist.source_url:
                        existing_artist.source_url = artist_obj['source_url']
                        updated = True
                    if updated:
                        existing_artist.save()
                        updated_count += 1
                        self.stdout.write(f"  → {main_name}: 更新已存在source_url的歌手信息")
                    else:
                        self.stdout.write(f"  ✓ {main_name}: 已有完整信息 (source_url)")
                else:
                    if not dry_run:
                        artist, created = Artist.objects.get_or_create(
                            name=main_name,
                            defaults={
                                'biography': artist_obj.get('biography', ''),
                                'profile_img': artist_obj.get('profile_img', ''),
                                'source_url': artist_obj.get('source_url', '')
                            }
                        )
                        if created:
                            created_count += 1
                            self.stdout.write(f"  + {main_name}: 创建新歌手")
                        else:
                            # 如果歌手已存在，更新信息
                            updated = False
                            if artist_obj.get('biography') and not artist.biography:
                                artist.biography = artist_obj['biography']
                                updated = True
                            if artist_obj.get('profile_img') and not artist.profile_img:
                                artist.profile_img.name = artist_obj['profile_img']
                                updated = True
                            if artist_obj.get('source_url') and not artist.source_url:
                                artist.source_url = artist_obj['source_url']
                                updated = True
                            if updated:
                                artist.save()
                                updated_count += 1
                                self.stdout.write(f"  → {main_name}: 更新歌手信息")
                    else:
                        self.stdout.write(f"  + {main_name}: 将创建新歌手")
        
        # 处理别名歌手
        self.stdout.write("\n处理别名歌手...")
        for alias, main_name in artist_alias_to_main.items():
            if alias == main_name:
                continue  # 跳过主名
                
            alias_artist = Artist.objects.filter(name__exact=alias).first()
            main_artist = Artist.objects.filter(name__exact=main_name).first()
            
            if alias_artist and main_artist:
                # 如果别名歌手存在，将其歌曲转移到主歌手名下
                songs_to_move = alias_artist.songs.all()
                if songs_to_move.exists():
                    if not dry_run:
                        songs_to_move.update(artist=main_artist)
                        alias_artist.delete()
                    self.stdout.write(f"  → {alias} -> {main_name}: 合并歌手，移动 {songs_to_move.count()} 首歌曲")
                else:
                    if not dry_run:
                        alias_artist.delete()
                    self.stdout.write(f"  → {alias} -> {main_name}: 删除空歌手")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN 完成 - 没有实际修改数据库"))
            self.stdout.write("如果以上操作看起来正确，请运行: python manage.py import_artist_biographies")
        else:
            self.stdout.write(self.style.SUCCESS(f"\n导入完成！"))
            self.stdout.write(f"更新歌手: {updated_count} 个")
            self.stdout.write(f"创建歌手: {created_count} 个")
            
            # 显示统计信息
            total_artists = Artist.objects.count()
            artists_with_bio = Artist.objects.filter(biography__isnull=False).exclude(biography='').count()
            self.stdout.write(f"\n数据库统计:")
            self.stdout.write(f"总歌手数: {total_artists}")
            self.stdout.write(f"有简介的歌手: {artists_with_bio}")
            self.stdout.write(f"简介覆盖率: {artists_with_bio/total_artists*100:.1f}%" if total_artists > 0 else "简介覆盖率: 0%") 
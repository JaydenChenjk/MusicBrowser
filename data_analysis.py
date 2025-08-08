#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐数据分析脚本
基础分析、词云、歌词中英文每句长度分布统计
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import re
import jieba
from wordcloud import WordCloud
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'PingFang HK']
plt.rcParams['axes.unicode_minus'] = False

# 中英文停用词，含常见英文缩写和口语词
STOPWORDS = set([
    # 中文
    '的', '了', '在', '是', '有', '和', '与', '等', '等。', '等，', '作词', '作曲', '编曲',
    '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们', '啊', '哦', '呀', '吧', '吗', '呢', '啊', '哇', '啦',
    '也', '都', '就', '还', '很', '被', '让', '把', '而', '但', '或', '而且', '如果', '因为', '所以', '而是', '不是', '不是',
    '这', '那', '这儿', '那儿', '这里', '那里', '一个', '没有', '什么', '怎么', '这样', '那样', '自己', '会', '要', '会', '能',
    '着', '着呢', '着吧', '着吗', '着啊', '着呀', '着哇', '着啦', '着吧', '着呢', '着吗', '着啊', '着呀', '着哇', '着啦',
    '和', '与', '及', '并', '并且', '或', '或者', '而', '但是', '不过', '只是', '就是', '因为', '所以', '如果', '虽然', '但是',
    '而且', '并且', '那么', '那么', '然后', '而后', '之后', '以前', '以后', '之前', '之后', '已经', '正在', '正在', '已经',
    '可以', '应该', '不会', '不会', '不能', '不能', '不会', '不会', '不能', '不能', '要', '想', '得', '让', '被', '给', '把',
    '从', '到', '对', '向', '往', '和', '跟', '与', '比', '被', '为', '以', '用', '像', '像是', '像这样', '像那样', '像什么',
    ' ', '\n', '\t', '\r', '', '——', '…', '（', '）', '：', '；', '，', '。', '！', '？', '、', '“', '”', '‘', '’', '《', '》', '【', '】', '·', ' ',
    # 英文
    'the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'on', 'with', 'as', 'by', 'at', 'from', 'it', 'an', 'be', 'this', 'that', 'are', 'was', 'were', 'or', 'but', 'not', 'so', 'if', 'then', 'than', 'when', 'which', 'who', 'whom', 'what', 'where', 'how', 'why', 'all', 'any', 'can', 'could', 'should', 'would', 'has', 'have', 'had', 'do', 'does', 'did', 'will', 'just', 'about', 'into', 'out', 'up', 'down', 'over', 'under', 'again', 'once', 'only', 'such', 'too', 'very', 'no', 'nor', 'more', 'most', 'some', 'other', 'own', 'same', 'than', 'too', 'very', 's', 't', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn',
    # 常见英文缩写和口语词
    "im", "you're", "youre", "dont", "can't", "cant", "wont", "won't", "didnt", "didn't", "doesnt", "doesn't", "isnt", "isn't", "arent", "aren't", "wasnt", "wasn't", "werent", "weren't", "ive", "i've", "ill", "i'll", "youll", "you'll", "youve", "you've", "theyre", "they're", "shes", "she's", "hes", "he's", "lets", "let's", "thats", "that's", "whats", "what's", "theres", "there's",
    # 常见虚词和语气词
    "oh", "la", "yeah", "something", "anything", "everything", "nothing", "someone", "anyone", "everyone", "noone", "somebody", "anybody", "everybody", "nobody", "somewhere", "anywhere", "everywhere", "nowhere", "somehow", "anyhow", "somewhat", "anyway", "anyways", "someway", "someways", "somewhen", "anywhen", "somewhy", "anywhy", "somewhat", "anywhat", "somewho", "anywho", "somewhere", "anywhere", "everywhere", "nowhere", "somehow", "anyhow", "someway", "anyway", "someways", "anyways", "somewhen", "anywhen", "somewhy", "anywhy", "somewhat", "anywhat", "somewho", "anywho"
])

def load_data():
    print("正在加载数据...")
    with open('output/artists.json', 'r', encoding='utf-8') as f:
        artists_data = json.load(f)
    with open('output/songs.json', 'r', encoding='utf-8') as f:
        songs_data = json.load(f)
    print(f"加载完成: {len(artists_data)} 个艺术家, {len(songs_data)} 首歌曲")
    return artists_data, songs_data

def lyrics_wordcloud(songs_data):
    print("\n=== 歌词词云分析 ===")
    all_lyrics = []
    for song in songs_data:
        if 'lyrics' in song and song['lyrics']:
            lyrics_text = ' '.join(song['lyrics'])
            lyrics_text = re.sub(r'作词.*?编曲.*?', '', lyrics_text)
            lyrics_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z\s]', '', lyrics_text)
            all_lyrics.append(lyrics_text)
    all_lyrics_text = ' '.join(all_lyrics)
    words = jieba.cut(all_lyrics_text)
    filtered_words = [w for w in words if len(w) > 1 and w.lower() not in STOPWORDS]
    font_path_try = ['/System/Library/Fonts/STHeiti Medium.ttc', None]
    wordcloud = None
    for font_path in font_path_try:
        try:
            wordcloud = WordCloud(
                font_path=font_path,
                width=3000, height=1500, background_color='white', max_words=100, colormap='viridis'
            ).generate(' '.join(filtered_words))
            print(f"歌词词云生成成功，使用字体: {font_path}")
            break
        except Exception as e:
            print(f"歌词词云生成失败，尝试字体: {font_path}, 错误: {e}")
    if wordcloud is not None:
        plt.figure(figsize=(12, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('歌词高频词云图', fontsize=16)
        plt.savefig('lyrics_wordcloud.png', dpi=300, bbox_inches='tight')
    else:
        print("所有字体均失败，未生成歌词词云。")

def avg_line_length_hist(songs_data):
    print("\n=== 歌曲平均句长分布统计（中文按汉字数，英文按单词数） ===")
    zh_avg_lengths = []
    en_avg_lengths = []
    for song in songs_data:
        if 'lyrics' in song and song['lyrics']:
            lines = [line.strip() for line in song['lyrics'] if line.strip()]
            if not lines:
                continue
            all_text = ''.join(lines)
            zh_chars = len(re.findall(r'[\u4e00-\u9fa5]', all_text))
            en_chars = len(re.findall(r'[A-Za-z]', all_text))
            total_chars = len(all_text)
            zh_ratio = zh_chars / (total_chars + 1e-6)
            en_ratio = en_chars / (total_chars + 1e-6)  # 中文歌：汉字比例>0.3且英文比例<0.3
            if zh_ratio > 0.3 and en_ratio < 0.3:
                avg_len = np.mean([len(re.findall(r'[\u4e00-\u9fa5]', line)) for line in lines])
                zh_avg_lengths.append(avg_len)  # 英文歌：英文比例>0.3且汉字比例<0.1
            elif en_ratio > 0.3 and zh_ratio < 0.1:
                avg_len = np.mean([len(re.findall(r'[A-Za-z]+', line)) for line in lines])
                en_avg_lengths.append(avg_len)  # 其他语言跳过
    if zh_avg_lengths:  # 中文直方图
        plt.figure(figsize=(8,5))
        plt.hist(zh_avg_lengths, bins=np.arange(4, 17, 0.5), color='#4e79a7', edgecolor='black', alpha=0.8)
        plt.xlabel('每句平均汉字数')
        plt.ylabel('歌曲数')
        plt.title('中文歌每首歌平均句长分布')
        plt.tight_layout()
        plt.savefig('zh_avg_line_length_hist.png', dpi=300, bbox_inches='tight')
        print("已保存中文歌每首歌平均句长分布直方图：zh_avg_line_length_hist.png")
    else:
        print("无中文歌曲数据")
    if en_avg_lengths:  # 英文直方图
        plt.figure(figsize=(8,5))
        plt.hist(en_avg_lengths, bins=np.arange(2, 15, 0.5), color='#f28e2b', edgecolor='black', alpha=0.8)
        plt.xlabel('每句平均单词数')
        plt.ylabel('歌曲数')
        plt.title('英文歌每首歌平均句长分布')
        plt.tight_layout()
        plt.savefig('en_avg_line_length_hist.png', dpi=300, bbox_inches='tight')
        print("已保存英文歌每首歌平均句长分布直方图：en_avg_line_length_hist.png")
    else:
        print("无英文歌曲数据")

def top_words_bar(songs_data):
    print("\n=== 歌词高频词柱状图分析 ===")
    from collections import Counter
    all_lyrics = []
    for song in songs_data:
        if 'lyrics' in song and song['lyrics']:
            lyrics_text = ' '.join(song['lyrics'])
            lyrics_text = re.sub(r'作词.*?编曲.*?', '', lyrics_text)
            lyrics_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z\s]', '', lyrics_text)
            all_lyrics.append(lyrics_text)
    all_lyrics_text = ' '.join(all_lyrics)
    words = jieba.cut(all_lyrics_text)
    filtered_words = [w for w in words if len(w) > 1 and w.lower() not in STOPWORDS]
    word_counts = Counter(filtered_words)
    top_words = word_counts.most_common(20)
    if top_words:
        words, counts = zip(*top_words)
        # 词频标准化：除以总歌曲数2070，保留5位小数
        total_songs = 2070
        normalized_counts = [round(count / total_songs, 5) for count in counts]
        plt.figure(figsize=(12, 8))
        bars = plt.bar(range(len(words)), normalized_counts, color='#59a14f', alpha=0.8)
        plt.xlabel('词语')
        plt.ylabel('平均出现次数（每首歌）')
        plt.title('歌词高频词TOP20（标准化）')
        plt.xticks(range(len(words)), words, rotation=45, ha='right')
        # 在柱子上显示数值
        for bar, count in zip(bars, normalized_counts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.0001, 
                    f'{count:.5f}', ha='center', va='bottom', fontsize=8)
        plt.tight_layout()
        plt.savefig('top_words_bar.png', dpi=300, bbox_inches='tight')
        print("已保存歌词高频词柱状图：top_words_bar.png")
    else:
        print("无有效词语数据")

def award_analysis(artists_data):
    print("\n=== 歌手获奖情况分析 ===")
    
    # 定义获奖相关词汇（中英文合并）
    award_keywords = [
        # 中文获奖词汇
        '奖', '获奖', '得奖', '提名', '冠军', '亚军', '季军', '金牌', '银牌', '铜牌', 
        '最佳', '优秀', '杰出', '卓越', '突出', '贡献', '成就', '荣誉', '称号',
        '格莱美', '奥斯卡', '金曲奖', '金马奖', '金像奖', '金钟奖', '金鹰奖', '百花奖',
        '华表奖', '飞天奖', '白玉兰', '金鸡奖', '金棕榈', '金熊奖', '金狮奖', '金球奖',
        # 英文获奖词汇
        'award', 'awards', 'winner', 'winning', 'won', 'nomination', 'nominated', 
        'champion', 'championship', 'gold', 'silver', 'bronze', 'medal', 'medals',
        'best', 'excellent', 'outstanding', 'distinguished', 'achievement', 'achievements',
        'honor', 'honors', 'honour', 'honours', 'recognition',
        'grammy', 'oscar', 'emmy', 'tony', 'pulitzer', 'nobel', 'academy', 'academies'
    ]
    
    # 统计每个歌手的获奖词汇出现次数
    artist_award_counts = []
    
    for artist in artists_data:
        if 'biography' in artist and artist['biography']:
            bio_text = artist['biography'].lower()
            total_count = 0
            
            # 统计所有获奖词汇的出现次数
            for keyword in award_keywords:
                count = bio_text.count(keyword.lower())
                total_count += count
            
            if total_count > 0:
                artist_award_counts.append({
                    'name': artist['name'],
                    'count': total_count
                })
    
    print(f"有获奖信息的艺术家数量: {len(artist_award_counts)}")
    
    if artist_award_counts:
        # 统计获奖次数分布
        count_distribution = {}
        for artist in artist_award_counts:
            count = artist['count']
            count_distribution[count] = count_distribution.get(count, 0) + 1
        
        # 按指定区间重新分组
        def get_group(count):
            if count == 1: return "1"
            elif count == 2: return "2"
            elif count == 3: return "3"
            elif count == 4: return "4"
            elif count == 5: return "5"
            elif 6 <= count <= 10: return "6-10"
            elif 11 <= count <= 30: return "11-30"
            elif 31 <= count <= 50: return "31-50"
            else: return "50+"
        
        # 重新统计分组后的分布
        group_distribution = {}
        for artist in artist_award_counts:
            group = get_group(artist['count'])
            group_distribution[group] = group_distribution.get(group, 0) + 1
        
        # 按指定顺序排列
        group_order = ["1", "2", "3", "4", "5", "6-10", "11-30", "31-50", "50+"]
        groups = []
        numbers = []
        for group in group_order:
            if group in group_distribution:
                groups.append(group)
                numbers.append(group_distribution[group])
        
        # 可视化：获奖次数分布柱状图
        plt.figure(figsize=(12, 8))
        bars = plt.bar(groups, numbers, color='#e15759', alpha=0.8, edgecolor='black')
        plt.xlabel('获奖词汇出现次数')
        plt.ylabel('歌手数量')
        plt.title('歌手简介中获奖词汇出现次数分布')
        plt.grid(True, alpha=0.3)
        
        # 在柱子上显示数值
        for bar, count in zip(bars, numbers):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('award_count_distribution.png', dpi=300, bbox_inches='tight')
        print("已保存获奖次数分布图：award_count_distribution.png")
        
        # 统计信息
        all_counts = [artist['count'] for artist in artist_award_counts]
        print(f"获奖词汇出现次数统计:")
        print(f"平均次数: {np.mean(all_counts):.2f}")
        print(f"中位数: {np.median(all_counts):.2f}")
        print(f"最多次数: {max(all_counts)}")
        print(f"最少次数: {min(all_counts)}")
        
        # 输出获奖最多的歌手TOP5
        sorted_artists = sorted(artist_award_counts, key=lambda x: x['count'], reverse=True)
        print("\n获奖词汇最多的歌手TOP5:")
        for i, artist in enumerate(sorted_artists[:5], 1):
            print(f"{i}. {artist['name']}: {artist['count']} 次")
        
        # 输出分组分布详情
        print("\n获奖次数分布详情:")
        for group in group_order:
            if group in group_distribution:
                print(f"出现{group}次获奖词汇的歌手: {group_distribution[group]}人")
    else:
        print("没有找到包含获奖信息的歌手")

def main():
    print("网易云音乐数据分析开始...")
    try:
        artists_data, songs_data = load_data()
        lyrics_wordcloud(songs_data)
        top_words_bar(songs_data)
        avg_line_length_hist(songs_data)
        award_analysis(artists_data)
        print("\n=== 分析完成 ===")
        print("生成的图表文件:")
        print("- lyrics_wordcloud.png")
        print("- top_words_bar.png")
        print("- zh_avg_line_length_hist.png")
        print("- en_avg_line_length_hist.png")
        print("- award_count_distribution.png")
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
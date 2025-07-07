import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import jieba
from wordcloud import WordCloud
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
with open('output/artists.json', 'r', encoding='utf-8') as f:
    artists_data = json.load(f)

# 分析传记长度
biography_lengths = []
artist_names = []
biography_texts = []

for artist in artists_data:
    if 'biography' in artist and artist['biography']:
        bio_length = len(artist['biography'])
        biography_lengths.append(bio_length)
        artist_names.append(artist['name'])
        biography_texts.append(artist['biography'])

# 创建DataFrame
df_artists = pd.DataFrame({
    'artist_name': artist_names,
    'biography_length': biography_lengths,
    'biography_text': biography_texts
})

# 统计分析
print("传记长度统计:")
print(f"平均长度: {np.mean(biography_lengths):.2f}")
print(f"中位数长度: {np.median(biography_lengths):.2f}")
print(f"最长传记: {max(biography_lengths)}")
print(f"最短传记: {min(biography_lengths)}")

# 可视化
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# 传记长度分布直方图
ax1.hist(biography_lengths, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
ax1.set_xlabel('传记长度（字符数）')
ax1.set_ylabel('艺术家数量')
ax1.set_title('艺术家传记长度分布')
ax1.grid(True, alpha=0.3)

# 传记长度箱线图
ax2.boxplot(biography_lengths, patch_artist=True, boxprops=dict(facecolor='lightgreen'))
ax2.set_ylabel('传记长度（字符数）')
ax2.set_title('传记长度分布箱线图')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('biography_length_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# 文本内容分析 - 提取关键词
all_text = ' '.join(biography_texts)
# 使用jieba分词
words = jieba.cut(all_text)
# 过滤停用词和短词
filtered_words = [word for word in words if len(word) > 1 and word not in ['简介', '的', '了', '在', '是', '有', '和', '与', '等', '等。', '等，']]

# 生成词云
wordcloud = WordCloud(
    font_path='/System/Library/Fonts/PingFang.ttc',  # macOS中文字体
    width=800, 
    height=400,
    background_color='white',
    max_words=100
).generate(' '.join(filtered_words))

plt.figure(figsize=(12, 8))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('艺术家传记关键词云图', fontsize=16)
plt.savefig('artist_biography_wordcloud.png', dpi=300, bbox_inches='tight')
plt.show()
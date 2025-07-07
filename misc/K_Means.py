from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np

# 读取歌曲数据
with open('output/songs.json', 'r', encoding='utf-8') as f:
    songs_data = json.load(f)

# 处理歌词数据
song_lyrics = []
song_names = []
artist_names = []

for song in songs_data:
    if 'lyrics' in song and song['lyrics']:
        # 合并歌词为文本
        lyrics_text = ' '.join(song['lyrics'])
        # 清理歌词文本
        lyrics_text = re.sub(r'作词.*?编曲.*?', '', lyrics_text)
        lyrics_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z\s]', '', lyrics_text)
        
        if len(lyrics_text.strip()) > 10:  # 过滤太短的歌词
            song_lyrics.append(lyrics_text.strip())
            song_names.append(song['name'])
            artist_names.append(song['artist_name'])

print(f"有效歌曲数量: {len(song_lyrics)}")

# TF-IDF特征提取
tfidf = TfidfVectorizer(
    max_features=1000,
    stop_words=['的', '了', '在', '是', '有', '和', '与', '等', '等。', '等，', '作词', '作曲', '编曲'],
    min_df=2,
    max_df=0.8
)

tfidf_matrix = tfidf.fit_transform(song_lyrics)
print(f"TF-IDF矩阵形状: {tfidf_matrix.shape}")

# t-SNE降维
tsne = TSNE(n_components=2, random_state=42, perplexity=30)
lyrics_2d = tsne.fit_transform(tfidf_matrix.toarray())

# K-means聚类
kmeans = KMeans(n_clusters=5, random_state=42)
clusters = kmeans.fit_predict(tfidf_matrix)

# 可视化
plt.figure(figsize=(12, 10))
colors = ['red', 'blue', 'green', 'orange', 'purple']

for i in range(5):
    mask = clusters == i
    plt.scatter(lyrics_2d[mask, 0], lyrics_2d[mask, 1], 
                c=colors[i], label=f'聚类 {i+1}', alpha=0.7, s=30)

plt.title('歌曲歌词t-SNE聚类可视化', fontsize=16)
plt.xlabel('t-SNE维度1')
plt.ylabel('t-SNE维度2')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('lyrics_tsne_clustering.png', dpi=300, bbox_inches='tight')
plt.show()

# 分析每个聚类的特征
for i in range(5):
    mask = clusters == i
    cluster_songs = [song_names[j] for j in range(len(song_names)) if mask[j]]
    cluster_artists = [artist_names[j] for j in range(len(artist_names)) if mask[j]]
    
    print(f"\n聚类 {i+1} 特征:")
    print(f"歌曲数量: {len(cluster_songs)}")
    print(f"代表歌曲: {cluster_songs[:5]}")
    print(f"代表艺术家: {list(set(cluster_artists))[:5]}")

# 歌词长度分析
lyrics_lengths = [len(lyrics) for lyrics in song_lyrics]

plt.figure(figsize=(10, 6))
plt.hist(lyrics_lengths, bins=50, alpha=0.7, color='coral', edgecolor='black')
plt.xlabel('歌词长度（字符数）')
plt.ylabel('歌曲数量')
plt.title('歌曲歌词长度分布')
plt.grid(True, alpha=0.3)
plt.savefig('lyrics_length_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"歌词长度统计:")
print(f"平均长度: {np.mean(lyrics_lengths):.2f}")
print(f"中位数长度: {np.median(lyrics_lengths):.2f}")
print(f"最长歌词: {max(lyrics_lengths)}")
print(f"最短歌词: {min(lyrics_lengths)}")
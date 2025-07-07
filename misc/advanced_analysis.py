import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
import jieba
from wordcloud import WordCloud
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
import networkx as nx
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'PingFang HK']
plt.rcParams['axes.unicode_minus'] = False

# 中英文停用词
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
    'the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'on', 'with', 'as', 'by', 'at', 'from', 'it', 'an', 'be', 'this', 'that', 'are', 'was', 'were', 'or', 'but', 'not', 'so', 'if', 'then', 'than', 'when', 'which', 'who', 'whom', 'what', 'where', 'how', 'why', 'all', 'any', 'can', 'could', 'should', 'would', 'has', 'have', 'had', 'do', 'does', 'did', 'will', 'just', 'about', 'into', 'out', 'up', 'down', 'over', 'under', 'again', 'once', 'only', 'such', 'too', 'very', 'no', 'nor', 'more', 'most', 'some', 'other', 'own', 'same', 'than', 'too', 'very', 's', 't', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn'
])

def conclusion_2_lyrics_clustering(songs_data):
    print("\n=== 结论二：歌词聚类分析（PCA+t-SNE+MiniBatchKMeans+轮廓系数） ===")
    song_lyrics = []
    song_names = []
    artist_names = []
    for song in songs_data:
        if 'lyrics' in song and song['lyrics']:
            lyrics_text = ' '.join(song['lyrics'])
            lyrics_text = re.sub(r'作词.*?编曲.*?', '', lyrics_text)
            lyrics_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z\s]', '', lyrics_text)
            if len(lyrics_text.strip()) > 10:
                song_lyrics.append(lyrics_text.strip())
                song_names.append(song['name'])
                artist_names.append(song['artist_name'])
    print(f"有效歌曲数量: {len(song_lyrics)}")
    # TF-IDF特征
    tfidf = TfidfVectorizer(
        max_features=1000,
        stop_words=list(STOPWORDS),
        min_df=2,
        max_df=0.8
    )
    tfidf_matrix = tfidf.fit_transform(song_lyrics)
    print(f"TF-IDF矩阵形状: {tfidf_matrix.shape}")
    # PCA降到50维
    print("PCA降维...")
    pca = PCA(n_components=min(50, tfidf_matrix.shape[1]))
    pca_result = pca.fit_transform(tfidf_matrix.toarray())
    # t-SNE降到2维
    print("t-SNE降维...")
    tsne = TSNE(n_components=2, random_state=42, perplexity=20, learning_rate=300)
    lyrics_2d = tsne.fit_transform(pca_result)
    # 自动选择最佳聚类数
    best_k = 2
    best_score = -1
    best_labels = None
    for k in range(2, 9):
        kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=256)
        labels = kmeans.fit_predict(pca_result)
        score = silhouette_score(pca_result, labels)
        print(f"聚类数{k}，轮廓系数: {score:.4f}")
        if score > best_score:
            best_score = score
            best_k = k
            best_labels = labels
    print(f"最佳聚类数: {best_k}，轮廓系数: {best_score:.4f}")
    # 可视化
    plt.figure(figsize=(12, 10))
    colors = sns.color_palette('hls', best_k)
    for i in range(best_k):
        mask = best_labels == i
        plt.scatter(lyrics_2d[mask, 0], lyrics_2d[mask, 1], color=colors[i], label=f'聚类 {i+1}', alpha=0.7, s=30)
    plt.title('歌曲歌词t-SNE聚类可视化', fontsize=16)
    plt.xlabel('t-SNE维度1')
    plt.ylabel('t-SNE维度2')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('lyrics_tsne_clustering.png', dpi=300, bbox_inches='tight')
    # 输出每个聚类的代表关键词
    print("每个聚类的代表关键词：")
    for i in range(best_k):
        mask = best_labels == i
        cluster_texts = [song_lyrics[j] for j in range(len(song_lyrics)) if mask[j]]
        if not cluster_texts:
            continue
        tfidf_c = TfidfVectorizer(max_features=10, stop_words=list(STOPWORDS))
        tfidf_c_matrix = tfidf_c.fit_transform(cluster_texts)
        words = tfidf_c.get_feature_names_out()
        scores = np.asarray(tfidf_c_matrix.sum(axis=0)).flatten()
        top_idx = np.argsort(scores)[::-1][:5]
        print(f"聚类{i+1}高频词: {[words[j] for j in top_idx]}")
    # 歌词长度分布
    lyrics_lengths = [len(lyrics) for lyrics in song_lyrics]
    plt.figure(figsize=(10, 6))
    plt.hist(lyrics_lengths, bins=50, alpha=0.7, color='coral', edgecolor='black')
    plt.xlabel('歌词长度（字符数）')
    plt.ylabel('歌曲数量')
    plt.title('歌曲歌词长度分布')
    plt.grid(True, alpha=0.3)
    plt.savefig('lyrics_length_distribution.png', dpi=300, bbox_inches='tight')
    print(f"歌词长度统计:")
    print(f"平均长度: {np.mean(lyrics_lengths):.2f}")
    print(f"中位数长度: {np.median(lyrics_lengths):.2f}")
    print(f"最长歌词: {max(lyrics_lengths)}")
    print(f"最短歌词: {min(lyrics_lengths)}")

def conclusion_3_network_analysis(songs_data):
    print("\n=== 结论三：网络分析 ===")
    artist_song_counts = defaultdict(int)
    artist_songs = defaultdict(list)
    for song in songs_data:
        if 'artist_name' in song and 'name' in song:
            artist_name = song['artist_name']
            song_name = song['name']
            artist_song_counts[artist_name] += 1
            artist_songs[artist_name].append(song_name)
    song_counts = list(artist_song_counts.values())
    artist_names_list = list(artist_song_counts.keys())
    print(f"艺术家总数: {len(artist_names_list)}")
    print(f"平均每个艺术家的歌曲数: {np.mean(song_counts):.2f}")
    # 只保留累积分布图
    plt.figure(figsize=(10, 6))
    sorted_counts = sorted(song_counts, reverse=True)
    cumulative = np.cumsum(sorted_counts) / sum(sorted_counts)
    plt.plot(range(1, len(sorted_counts) + 1), cumulative, 'b-', linewidth=2)
    plt.xlabel('艺术家排名')
    plt.ylabel('累积作品比例')
    plt.title('艺术家作品数量累积分布')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('artist_song_cumulative.png', dpi=300, bbox_inches='tight')
    print(f"已保存艺术家作品数量累积分布图：artist_song_cumulative.png")
    # 网络图和中心性分析等可按需保留 
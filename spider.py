import re
import json
import time
from pathlib import Path
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

BASE_DIR = Path(__file__).parent
OUT_DIR = BASE_DIR / "output"
SONG_DIR = OUT_DIR / "songs"
ARTIST_PATH = OUT_DIR / "artists.json"
ARTIST_IMAGE_DIR = OUT_DIR / "artist_images"
SONG_IMAGE_DIR = OUT_DIR / "song_images"

DOWNLOAD_DELAY = (1, 2)
SAVE_HTML = False
HTML_DIR = BASE_DIR / "html_cache"

session = requests.Session()
ua = UserAgent()

def fetch(url: str, retries=3, encoding="utf-8") -> Optional[str]:  # 获取网页内容，支持重试机制
    headers = {"User-Agent": ua.random, "Referer": "https://music.163.com/"}
    cookies = {
        "MUSIC_U": "001F0C3464BBE6B14FBDA113C73FE3419DAED076DEA22648DF26CF85A75749520A92B7EE808DFA6C6F3E3D3692B748E0D4D8D3787CE9262BE7FC81B3E3657507BDADFE483292D3C1465179124E5AAF130FF69473679A62ADD58D3F773A01BE6F66350E203076EF07DE8600535618FEFAE75DA2487F4DBBE3027E05E2177E741B3B0A994963F1E370A3FE3071C5CC8F83B7FB24F95AF6D817636FB33EB7603042EA314F9A4A3CD94092BC9EBD5AAEC720932257DEECE49610FE35B2A82DC5F9E5D14DE49F1B2EACA6519E71A637F2001978A828035C9245ED9B774C12334113E53C2C30D639EB92098A36E2EAF549EA3109EB773D7B86241A3A03D3148972D1B95BD197F3481A32E817AB0703D030C7B229D5E70457BB9A6E56DDC90226AAFCA9D53FF1C014FE47504CE651E8B96125060DC9648052A54E7FFA5B034F2DCF2EFE22BFDD235173121008D50A170A08A7AA9ECA93F389F499A75CF9156B370E1F0790",
        "__csrf": "fcb2230733cdf5aed1306195a0020e78",
        "NMTID": "00OSufGEJLMwTDST0S3i3wcAdq-bWoAAAGXwSYaPQ"
        }
    for _ in range(retries):
        try:
            resp = session.get(url, headers = headers, cookies = cookies, timeout = 10)
            if resp.status_code == 404:
                return None
            if resp.status_code == 200:
                resp.encoding = encoding
                return resp.text
        except:
            time.sleep(2)
    return None

def fetch_all_artist_ids() -> List[str]:  # 获取所有歌手分类页面的歌手ID列表
    ids = set()
    cat_ids = [1001, 1002, 1003, 2001, 2002, 2003, 6001, 6002, 6003]
    for cat_id in cat_ids:
        url = f"https://music.163.com/discover/artist/cat?id={cat_id}"
        html = fetch(url)
        if not html:
            continue
        found = re.findall(r"/artist\?id=(\d+)", html)
        ids.update(found)
        time.sleep(0.2)
    return list(ids)



def load_existing_source_urls(filename: str) -> set:  # 加载已存在的源URL，避免重复爬取
    source_urls = set()
    path = OUT_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if "source_url" in entry:
                            source_urls.add(entry["source_url"])
                    except Exception:
                        continue
    return source_urls

def parse_artist_desc_page(html: str) -> Optional[dict]:  # 解析歌手详情页面，提取姓名、简介和头像

    soup = BeautifulSoup(html, "html.parser")

    name_tag = soup.find("meta", attrs={"name": "keywords"})
    desc_div = soup.find("div", class_="n-artdesc")
    img_tag = soup.find("img")

    name = name_tag.get("content", "").strip() if name_tag else ""
    bio = desc_div.get_text(strip=True) if desc_div else ""
    profile_img = img_tag.get("src", "").strip() if img_tag and img_tag.get("src", "").startswith("http") else ""

    return {
        "name": name,
        "biography": bio,
        "profile_img": profile_img
    }

def fetch_songs_by_artist_id(html: str) -> List[str]:  # 给定网易云歌手，返回其主页列出的所有歌曲的 song_id 列表
    if not html:
        return []
    song_ids = re.findall(r"/song\?id=(\d+)", html)
    return list(set(song_ids))[:30] # 限制最多返回30首歌的ID

def parse_song_page(html: str, song_id: str) -> dict:  # 解析歌曲页面，提取歌曲信息包括歌词
    soup = BeautifulSoup(html, "html.parser")

    name_tag = soup.find("meta", property="og:title")
    artist_tag = soup.find("meta", property="og:music:artist")
    image_tag = soup.find("meta", property="og:image")

    name = name_tag["content"].strip() if name_tag else ""
    artist_name = artist_tag["content"].strip() if artist_tag else ""
    cover_img = image_tag["content"].strip() if image_tag else ""

    # 抓取歌词
    lyric_url = f"https://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=1"
    headers = {"User-Agent": ua.random, "Referer": "https://music.163.com/"}
    try:
        resp = requests.get(lyric_url, headers=headers, cookies={}, timeout=5)
        data = resp.text.strip()
        lyrics_text = json.loads(data)['lrc']['lyric']
        lyrics = [line for line in re.findall(r'\[.*?\](.*)', lyrics_text) if line.strip()]
    except Exception:
        lyrics = []

    return {
        "name": name,
        "artist_name": artist_name,
        "cover_img": cover_img,
        "lyrics": lyrics
    }

def save_as_json(content: dict, filename: str):  # 将内容保存为JSON格式到文件
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(content, ensure_ascii=False) + "\n")

def crawl():  # 主爬虫函数，爬取歌手和歌曲数据
    ARTIST_CAT_IDS = fetch_all_artist_ids()
    artist_urls = [f"https://music.163.com/artist/desc?id={id}" for id in ARTIST_CAT_IDS]
    existing_source_urls = load_existing_source_urls("artists.json")
    artists = []
    ARTIST_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    SONG_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    artist_cnt = 0
    song_cnt = 0
    temp_song_cnt = 0

    for url in artist_urls:
        if url in existing_source_urls:
            continue
        html = fetch(url)
        if not html:
            continue
        info = parse_artist_desc_page(html)
        if not info:
            continue
        
        if not info["name"] or not info["biography"] or not info["profile_img"]:
            continue
        
        match = re.search(r"id=(\d+)", url)
        if match:
            id = match.group(1)
        html1 = fetch(f"https://music.163.com/artist?id={id}")  # 用于获取song_ids
        if not html1:
            continue

        song_ids = fetch_songs_by_artist_id(html1)
        if not song_ids:
            continue

        artist = {
            "name": info["name"],
            "profile_img": info["profile_img"],
            "biography": info["biography"], 
            "source_url": url,
        }

        try:    # 下载歌手图片
            img_data = requests.get(info["profile_img"], timeout=10).content
            img_path = ARTIST_IMAGE_DIR / f'{info["name"]}.jpg'
            with open(img_path, "wb") as img_file:
                img_file.write(img_data)
        except Exception:
            pass

        artists.append(artist)
        save_as_json(artist, "artists.json")
        artist_cnt += 1

        for sid in song_ids:
            html = fetch(f"https://music.163.com/song?id={sid}")
            # print(f"正在处理歌曲 ID: {sid}")
            if not html:
                continue
            try:
                s = parse_song_page(html, sid)
                if not s:
                    print(f"无法解析歌曲 ID: {sid}")
                song = {
                    "name": s["name"],
                    "artist_name": s["artist_name"],
                    "lyrics": s["lyrics"],
                    "cover_img": s["cover_img"],
                    "source_url": f"https://music.163.com/song?id={sid}"
                }
                if not song["name"] or not song["artist_name"] or not song["lyrics"] or not song["cover_img"]:
                    continue
                print(f"正在处理歌曲: {song['name']} - {song['artist_name']}")
                save_as_json(song, "songs.json")
                song_cnt += 1
                
                img_data1 = requests.get(song["cover_img"], timeout=10).content
                img_path1 = SONG_IMAGE_DIR / f'{song["artist_name"]}' / f'{song["name"]}.jpg'
                img_path1.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
                with open(img_path1, "wb") as img_file1:
                    img_file1.write(img_data1)
            except Exception:
                continue
        
        print(f"已处理第{artist_cnt}位歌手: {info['name']}，歌曲数: {song_cnt - temp_song_cnt}，总计歌曲数: {song_cnt}")
        temp_song_cnt = song_cnt  

        if artist_cnt > 100 and song_cnt > 2000:
            print(f"已处理 {artist_cnt} 位歌手，{song_cnt} 首歌曲，停止爬取")
            break



if __name__ == "__main__":
    crawl()
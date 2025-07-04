#!/usr/bin/env python3
"""
检查songs.json文件格式的脚本
用于验证数据格式是否正确
"""

import json
import os
from pathlib import Path


def check_json_format(json_file_path):
    """检查JSON文件格式"""
    print(f"正在检查文件: {json_file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(json_file_path):
        print(f"❌ 错误：文件不存在 {json_file_path}")
        return False
    
    # 获取文件大小
    file_size = os.path.getsize(json_file_path)
    print(f"📁 文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    try:
        # 加载JSON数据
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON格式正确")
        print(f"📊 数据条目数量: {len(data)}")
        
        # 检查数据结构
        if not isinstance(data, list):
            print("❌ 错误：JSON应该是一个数组")
            return False
        
        if len(data) == 0:
            print("❌ 错误：数组为空")
            return False
        
        # 检查前几个条目的结构
        print("\n🔍 检查数据结构...")
        sample_size = min(5, len(data))
        
        required_fields = ['name', 'artist', 'url']
        optional_fields = ['lyrics', 'artist_bio', 'cover_img', 'profile_img']
        
        field_stats = {}
        for field in required_fields + optional_fields:
            field_stats[field] = 0
        
        for i, item in enumerate(data[:sample_size]):
            print(f"\n📋 样本 {i+1}:")
            if not isinstance(item, dict):
                print(f"❌ 错误：第{i+1}项不是对象")
                continue
            
            # 检查必需字段
            for field in required_fields:
                if field in item and item[field]:
                    field_stats[field] += 1
                    print(f"  ✅ {field}: {item[field][:50]}...")
                else:
                    print(f"  ❌ 缺少必需字段: {field}")
            
            # 检查可选字段
            for field in optional_fields:
                if field in item and item[field]:
                    field_stats[field] += 1
                    print(f"  📝 {field}: {item[field][:50]}...")
        
        # 统计所有数据的字段覆盖率
        print(f"\n📈 字段覆盖率统计（基于前{sample_size}个样本）:")
        for field, count in field_stats.items():
            percentage = (count / sample_size) * 100
            status = "✅" if field in required_fields and percentage == 100 else "📊"
            print(f"  {status} {field}: {count}/{sample_size} ({percentage:.1f}%)")
        
        # 快速检查整个数据集的完整性
        print(f"\n🔍 完整性检查（所有{len(data)}条记录）...")
        missing_name = sum(1 for item in data if not item.get('name', '').strip())
        missing_artist = sum(1 for item in data if not item.get('artist', '').strip())
        missing_url = sum(1 for item in data if not item.get('url', '').strip())
        
        print(f"  缺少歌曲名称: {missing_name}")
        print(f"  缺少歌手名称: {missing_artist}")
        print(f"  缺少URL: {missing_url}")
        
        # 统计不同歌手数量
        artists = set()
        for item in data:
            artist = item.get('artist', '').strip()
            if artist:
                artists.add(artist)
        
        print(f"  不同歌手数量: {len(artists)}")
        
        if missing_name == 0 and missing_artist == 0 and missing_url == 0:
            print("✅ 所有必需字段都完整！")
            return True
        else:
            print("⚠️  有些记录缺少必需字段")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 读取文件时发生错误: {e}")
        return False


def main():
    """主函数"""
    print("歌曲JSON文件格式检查工具")
    print("=" * 50)
    
    # 默认文件路径
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    json_file_path = base_dir / 'output' / 'songs.json'
    
    # 检查文件
    success = check_json_format(json_file_path)
    
    if success:
        print(f"\n🎉 文件格式检查通过！可以进行数据导入。")
        print("\n下一步：")
        print("1. 运行独立脚本：python import_songs.py")
        print("2. 或使用Django管理命令：python manage.py import_songs")
    else:
        print(f"\n❌ 文件格式检查失败，请检查JSON文件格式。")


if __name__ == "__main__":
    main()
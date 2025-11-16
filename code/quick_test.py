#!/usr/bin/env python3
"""
快速测试搜索功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from complete_data_system import MedicalDatabase

def quick_test():
    """快速测试"""
    print("🔍 快速测试搜索功能")
    print("=" * 40)
    
    # 检查数据库
    db_path = "data/msd_medical_knowledge.db"
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    # 初始化数据库
    try:
        db = MedicalDatabase()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    # 测试搜索
    test_queries = ["MSD", "Manual", "heart", "health"]
    
    for query in test_queries:
        print(f"\\n🔍 搜索: '{query}'")
        try:
            results = db.search_articles(query, limit=5)
            print(f"  找到 {len(results)} 个结果")
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  [{i}] {result.get('title', '无标题')[:50]}...")
                    print(f"      质量: {result.get('quality_score', 0)} | 词数: {result.get('word_count', 0)}")
            else:
                print("  未找到结果")
                
        except Exception as e:
            print(f"  ❌ 搜索失败: {e}")
    
    # 显示统计
    print("\\n📊 数据库统计:")
    try:
        stats = db.get_statistics()
        print(f"  总文章数: {stats.get('total_articles', 0)}")
        print(f"  平均质量: {stats.get('average_quality_score', 0):.1f}")
        print(f"  平均词数: {stats.get('average_word_count', 0):.0f}")
    except Exception as e:
        print(f"  ❌ 统计失败: {e}")
    
    print("\\n🎉 测试完成！")

if __name__ == "__main__":
    quick_test()

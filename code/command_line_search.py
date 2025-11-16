#!/usr/bin/env python3
"""
命令行搜索工具
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from complete_data_system import MedicalDatabase

def print_header():
    """打印标题"""
    print("🏥 默沙东诊疗手册医学知识库搜索")
    print("=" * 60)

def print_article(article, show_content=False):
    """打印文章信息"""
    print(f"📄 标题: {article.get('title', '无标题')}")
    print(f"🏷️  分类: {article.get('category', '未分类')}")
    print(f"🌐 语言: {article.get('language', 'en')}")
    print(f"⭐ 质量评分: {article.get('quality_score', 0)}/100")
    print(f"📝 词数: {article.get('word_count', 0)}")
    
    if article.get('excerpt'):
        print(f"📖 摘要: {article['excerpt'][:200]}...")
    
    if show_content and article.get('content'):
        print(f"📄 内容: {article['content'][:500]}...")
    
    print(f"🔗 URL: {article.get('url', '无URL')}")
    print("-" * 40)

def search_articles(db, query, language=None, category=None, limit=10):
    """搜索文章"""
    try:
        results = db.search_articles(
            query=query,
            language=language,
            category=category,
            limit=limit
        )
        return results
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return []

def show_statistics(db):
    """显示统计信息"""
    try:
        stats = db.get_statistics()
        
        print("\\n📊 数据库统计信息")
        print("=" * 40)
        
        print(f"📄 总文章数: {stats.get('total_articles', 0):,}")
        print(f"🔬 医学术语数: {stats.get('total_medical_terms', 0):,}")
        print(f"💊 药物信息数: {stats.get('total_drugs', 0):,}")
        print(f"⭐ 平均质量评分: {stats.get('average_quality_score', 0):.1f}")
        print(f"📝 平均词数: {stats.get('average_word_count', 0):.0f}")
        
        if stats.get('by_language'):
            print("\\n🌐 按语言分布:")
            for lang, count in stats['by_language'].items():
                print(f"  {lang}: {count}")
        
        if stats.get('by_version'):
            print("\\n📚 按版本分布:")
            for version, count in stats['by_version'].items():
                print(f"  {version}: {count}")
        
        if stats.get('top_categories'):
            print("\\n🏷️ 热门分类:")
            for category, count in list(stats['top_categories'].items())[:5]:
                print(f"  {category}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 获取统计失败: {e}")
        return False

def interactive_search(db):
    """交互式搜索"""
    print("\\n🔍 交互式搜索模式")
    print("输入 'help' 查看帮助，输入 'quit' 退出")
    
    while True:
        try:
            query = input("\\n🔎 请输入搜索词: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 再见！")
                break
            elif query.lower() == 'help':
                show_help()
                continue
            elif not query:
                print("⚠️ 请输入有效的搜索词")
                continue
            
            # 可选的过滤条件
            print("\\n⚙️  可选过滤条件 (直接回车跳过):")
            language_input = input("🌐 语言 (zh/en/fr/de...): ").strip()
            category_input = input("🏷️  分类: ").strip()
            
            # 执行搜索
            print(f"\\n🔍 正在搜索: {query}")
            results = search_articles(
                db, 
                query, 
                language=language_input if language_input else None,
                category=category_input if category_input else None,
                limit=20
            )
            
            if results:
                print(f"\\n✅ 找到 {len(results)} 个结果:")
                print("=" * 60)
                
                for i, article in enumerate(results, 1):
                    print(f"[{i}] ", end="")
                    print_article(article)
                
                # 询问是否查看详细内容
                while True:
                    try:
                        choice = input(f"\\n查看详细内容 (1-{len(results)}) 或按回车跳过: ").strip()
                        if not choice:
                            break
                        
                        index = int(choice) - 1
                        if 0 <= index < len(results):
                            print(f"\\n📖 详细内容 (第 {index + 1} 项):")
                            print("=" * 60)
                            print_article(results[index], show_content=True)
                        else:
                            print("⚠️ 无效的选择")
                    except ValueError:
                        print("⚠️ 请输入有效的数字")
                        continue
                    break
            else:
                print("❌ 未找到相关结果")
                print("💡 建议:")
                print("  - 检查拼写")
                print("  - 尝试使用更通用的术语")
                print("  - 尝试使用英文术语")
        
        except KeyboardInterrupt:
            print("\\n\\n👋 用户中断，退出搜索")
            break
        except Exception as e:
            print(f"❌ 搜索过程中出错: {e}")

def show_help():
    """显示帮助信息"""
    print("\\n📖 帮助信息")
    print("=" * 40)
    print("可用命令:")
    print("  help          - 显示此帮助信息")
    print("  stats         - 显示数据库统计")
    print("  quit/exit/q   - 退出程序")
    print()
    print("搜索技巧:")
    print("  - 使用准确的医学术语")
    print("  - 可以使用中文或英文搜索")
    print("  - 支持组合搜索 (如: 高血压 治疗)")
    print("  - 可以按语言和分类过滤")

def main():
    """主函数"""
    print_header()
    
    # 检查数据库
    db_path = "data/msd_medical_knowledge.db"
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        print("请先运行 complete_data_system.py 初始化数据库")
        return
    
    # 初始化数据库连接
    try:
        db = MedicalDatabase()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    # 显示初始统计信息
    show_statistics(db)
    
    # 选择操作模式
    print("\\n请选择操作模式:")
    print("1. 交互式搜索")
    print("2. 单次搜索")
    print("3. 显示帮助")
    print("4. 退出")
    
    while True:
        try:
            choice = input("\\n请选择 (1-4): ").strip()
            
            if choice == '1':
                interactive_search(db)
                break
            elif choice == '2':
                query = input("\\n🔎 请输入搜索词: ").strip()
                if query:
                    results = search_articles(db, query, limit=10)
                    if results:
                        print(f"\\n✅ 找到 {len(results)} 个结果:")
                        for i, article in enumerate(results, 1):
                            print(f"[{i}] ", end="")
                            print_article(article)
                    else:
                        print("❌ 未找到相关结果")
                break
            elif choice == '3':
                show_help()
            elif choice == '4':
                print("👋 再见！")
                break
            else:
                print("⚠️ 请选择 1-4")
                
        except KeyboardInterrupt:
            print("\\n\\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    main()

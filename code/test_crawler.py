#!/usr/bin/env python3
"""
爬虫系统测试脚本
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_imports():
    """测试导入"""
    print("🔍 测试模块导入...")
    
    try:
        from config.crawler_config import CRAWLER_CONFIG, USER_AGENTS
        print("✅ 配置模块导入成功")
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False
    
    try:
        from database.setup_database import DatabaseManager
        print("✅ 数据库模块导入成功")
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        return False
    
    try:
        from parsers.content_parser import MSDContentParser
        print("✅ 解析器模块导入成功")
    except Exception as e:
        print(f"❌ 解析器模块导入失败: {e}")
        return False
    
    try:
        from processors.data_processor import DataProcessor
        print("✅ 处理器模块导入成功")
    except Exception as e:
        print(f"❌ 处理器模块导入失败: {e}")
        return False
    
    try:
        from crawler.main_crawler import MSDManualsCrawler
        print("✅ 爬虫模块导入成功")
    except Exception as e:
        print(f"❌ 爬虫模块导入失败: {e}")
        return False
    
    return True

def test_database():
    """测试数据库"""
    print("\\n🗄️ 测试数据库功能...")
    
    try:
        from database.setup_database import DatabaseManager
        
        # 创建数据库管理器
        db_manager = DatabaseManager(use_sqlite=True)
        print("✅ 数据库管理器创建成功")
        
        # 创建表
        db_manager.create_tables()
        print("✅ 数据库表创建成功")
        
        # 插入测试数据
        session = db_manager.get_session()
        try:
            from database.models import Article
            
            # 创建测试文章
            article = Article(
                url="https://test.example.com/test-article",
                title="测试文章标题",
                content="这是一篇测试文章的内容，用于验证爬虫系统的功能。",
                category="test-category",
                language="zh",
                version="home"
            )
            
            session.add(article)
            session.commit()
            print("✅ 测试数据插入成功")
            
        except Exception as e:
            session.rollback()
            print(f"❌ 测试数据插入失败: {e}")
            return False
        finally:
            session.close()
        
        db_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_parser():
    """测试解析器"""
    print("\\n📄 测试内容解析器...")
    
    try:
        from parsers.content_parser import MSDContentParser
        from bs4 import BeautifulSoup
        
        # 创建测试HTML
        test_html = """
        <html>
        <head><title>高血压</title></head>
        <body>
            <main>
                <h1>高血压概述</h1>
                <p>高血压是一种常见的慢性疾病，指动脉血压持续升高。</p>
                <p>患者常伴有头痛、头晕等症状。</p>
            </main>
        </body>
        </html>
        """
        
        # 模拟响应对象
        class MockResponse:
            def __init__(self, url, content):
                self.url = url
                self.content = content
        
        # 创建解析器
        parser = MSDContentParser()
        
        # 解析测试内容
        mock_response = MockResponse("https://test.example.com/hypertension", test_html.encode('utf-8'))
        parsed_data = parser.parse(mock_response)
        
        print(f"✅ 解析成功")
        print(f"   - 标题: {parsed_data['title']}")
        print(f"   - 内容长度: {len(parsed_data['content'])} 字符")
        print(f"   - 医学术语: {len(parsed_data['medical_terms'])} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ 解析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_processor():
    """测试数据处理器"""
    print("\\n⚙️ 测试数据处理器...")
    
    try:
        from processors.data_processor import DataProcessor
        
        # 测试数据
        test_data = {
            'title': '高血压概述',
            'content': '高血压是一种常见的慢性疾病，指动脉血压持续升高。患者常伴有头痛、头晕等症状。',
            'url': 'https://www.msdmanuals.com/test',
            'metadata': {
                'category': 'cardiovascular-disorders',
                'language': 'zh',
                'author': '测试医生'
            },
            'medical_terms': [
                {'term': '高血压', 'context': '高血压是一种...', 'frequency': 3},
                {'term': '慢性疾病', 'context': '高血压是一种...', 'frequency': 1}
            ]
        }
        
        # 创建处理器
        processor = DataProcessor()
        
        # 处理数据
        processed_data = processor.process(test_data)
        
        print(f"✅ 处理成功")
        print(f"   - 质量评分: {processed_data['quality_score']}")
        print(f"   - 关键词数量: {len(processed_data.get('keywords', []))}")
        print(f"   - 词数统计: {processed_data.get('statistics', {}).get('word_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crawler_initialization():
    """测试爬虫初始化"""
    print("\\n🕷️ 测试爬虫初始化...")
    
    try:
        from crawler.main_crawler import MSDManualsCrawler
        
        # 创建爬虫实例
        crawler = MSDManualsCrawler()
        print("✅ 爬虫实例创建成功")
        
        # 测试配置加载
        assert crawler.config is not None
        print("✅ 配置加载成功")
        
        # 测试数据库连接
        assert crawler.db_manager is not None
        print("✅ 数据库管理器初始化成功")
        
        # 测试解析器
        assert crawler.content_parser is not None
        print("✅ 内容解析器初始化成功")
        
        # 测试数据处理器
        assert crawler.data_processor is not None
        print("✅ 数据处理器初始化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 爬虫初始化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始爬虫系统测试\\n")
    
    tests = [
        ("模块导入", test_imports),
        ("数据库功能", test_database),
        ("内容解析器", test_parser),
        ("数据处理器", test_processor),
        ("爬虫初始化", test_crawler_initialization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\\n{'='*50}")
        print(f"🧪 测试: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\\n{'='*50}")
    print(f"📊 测试结果汇总")
    print('='*50)
    print(f"总测试: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\\n🎉 所有测试通过！爬虫系统准备就绪。")
        return True
    else:
        print("\\n⚠️ 部分测试失败，请检查相关组件。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

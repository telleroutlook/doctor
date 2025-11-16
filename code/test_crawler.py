#!/usr/bin/env python3
"""爬虫系统测试脚本"""

import logging
import sys
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_imports():
    """测试模块导入是否正常"""
    from config.crawler_config import CRAWLER_CONFIG, USER_AGENTS, LANGUAGE_VERSION_URLS
    from database.setup_database import DatabaseManager
    from parsers.content_parser import MSDContentParser
    from processors.data_processor import DataProcessor
    from crawler.main_crawler import MSDManualsCrawler

    assert isinstance(CRAWLER_CONFIG, dict)
    assert isinstance(USER_AGENTS, list) and USER_AGENTS
    assert "home" in LANGUAGE_VERSION_URLS
    assert DatabaseManager is not None
    assert MSDContentParser is not None
    assert DataProcessor is not None
    assert MSDManualsCrawler is not None


def test_database(tmp_path):
    """验证数据库的基本增删改查能力"""
    from database.setup_database import DatabaseManager
    from database.models import Article

    db_path = tmp_path / "msd_manuals_test.db"
    db_manager = DatabaseManager(use_sqlite=True, sqlite_path=db_path)
    db_manager.create_tables()

    session = db_manager.get_session()
    test_url = "https://test.example.com/test-article"

    try:
        session.query(Article).filter_by(url=test_url).delete()
        article = Article(
            url=test_url,
            title="测试文章标题",
            content="这是一篇测试文章的内容，用于验证爬虫系统的功能。",
            category="test-category",
            language="zh",
            version="home"
        )

        session.add(article)
        session.commit()

        stored = session.query(Article).filter_by(url=test_url).one()
        assert stored.title == "测试文章标题"
    finally:
        session.query(Article).filter_by(url=test_url).delete()
        session.commit()
        session.close()
        db_manager.close()


def test_parser():
    """验证解析器能够提取标题和正文"""
    from parsers.content_parser import MSDContentParser

    test_html = """
    <html>
    <head><title>高血压概述与长期管理策略</title></head>
    <body>
        <main>
            <h1>高血压概述与长期管理策略</h1>
            <section>
                <p>高血压是一种常见的慢性疾病，指动脉血压持续升高，长期得不到控制会影响心、脑、肾等重要器官的功能，严重时可导致心力衰竭或脑卒中。</p>
                <p>患者常伴有头痛、头晕、视力模糊等症状，部分患者在早期可能没有明显不适，因此需要通过定期体检进行筛查。</p>
                <p>规范的生活方式管理、合理饮食、坚持运动以及按时服药是降低心血管风险的关键，医生还会根据患者的危险分层调整治疗方案。</p>
            </section>
        </main>
    </body>
    </html>
    """

    class MockResponse:
        def __init__(self, url, content):
            self.url = url
            self.content = content

    parser = MSDContentParser()
    mock_response = MockResponse("https://test.example.com/hypertension", test_html.encode("utf-8"))
    parsed_data = parser.parse(mock_response)

    assert parsed_data["title"].startswith("高血压")
    assert "慢性疾病" in parsed_data["content"]
    assert parsed_data["medical_terms"] is not None


def test_processor():
    """验证数据处理器输出的结构"""
    from processors.data_processor import DataProcessor

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

    processor = DataProcessor()
    processed_data = processor.process(test_data)

    assert processed_data['quality_score'] >= 0
    assert processed_data['statistics']['word_count'] > 0
    assert len(processed_data.get('keywords', [])) >= 1


def test_crawler_initialization():
    """验证爬虫初始化依赖是否齐全"""
    from crawler.main_crawler import MSDManualsCrawler

    crawler = MSDManualsCrawler()
    assert crawler.config
    assert crawler.db_manager is not None
    assert crawler.content_parser is not None
    assert crawler.data_processor is not None


def test_language_version_pairs():
    """确保语言配置组合正确且结构一致"""
    from crawler.main_crawler import MSDManualsCrawler
    from config.crawler_config import LANGUAGE_VERSION_URLS

    crawler = MSDManualsCrawler()
    all_pairs = crawler.get_language_version_pairs()
    assert ("en", "home") in all_pairs

    zh_pairs = crawler.get_language_version_pairs(language='zh')
    assert {version for _, version in zh_pairs} >= {'home', 'professional'}

    for version, languages in LANGUAGE_VERSION_URLS.items():
        for lang, entry in languages.items():
            assert 'start_url' in entry
            assert entry['start_url'].startswith('http')
            assert isinstance(entry.get('extra_urls', []), list)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

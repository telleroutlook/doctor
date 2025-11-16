#!/usr/bin/env python3
"""
默沙东诊疗手册爬虫项目初始化脚本
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def create_project_structure():
    """创建项目目录结构"""
    
    # 定义项目目录结构
    directories = [
        'config',
        'database/migrations',
        'crawler/spiders',
        'parsers',
        'processors',
        'api',
        'web_interface/static/css',
        'web_interface/static/js',
        'web_interface/templates',
        'tests',
        'docs',
        'scripts',
        'logs',
        'data/raw',
        'data/processed',
        'data/backup'
    ]
    
    # 创建目录
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")

def setup_database():
    """设置数据库配置文件"""
    
    db_config = {
        "host": "localhost",
        "port": 3306,
        "username": "root", 
        "password": "password",
        "database": "msd_manuals",
        "charset": "utf8mb4",
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True
    }
    
    with open('config/database_config.py', 'w', encoding='utf-8') as f:
        f.write(f'''# 数据库配置
DATABASE_CONFIG = {json.dumps(db_config, indent=4, ensure_ascii=False)}

# SQLite备用配置（用于测试）
SQLITE_CONFIG = {{
    "database": "msd_manuals.db",
    "timeout": 30,
    "check_same_thread": False
}}

class DatabaseManager:
    def __init__(self, config_type="mysql"):
        self.config_type = config_type
        if config_type == "mysql":
            import mysql.connector
            self.config = DATABASE_CONFIG
        else:
            import sqlite3
            self.config = SQLITE_CONFIG
    
    def get_connection(self):
        if self.config_type == "mysql":
            import mysql.connector
            return mysql.connector.connect(**self.config)
        else:
            import sqlite3
            return sqlite3.connect(self.config["database"])
''')
    
    print("✅ 创建数据库配置文件")

def setup_crawler_config():
    """设置爬虫配置文件"""
    
    crawler_config = '''# 爬虫配置
import random

# 爬虫基础配置
CRAWLER_CONFIG = {
    "max_workers": 3,
    "delay_between_requests": 5.0,
    "max_retries": 3,
    "timeout": 30,
    "respect_robots_txt": True,
    "download_timeout": 60,
    "download_delay": 5,
    "randomize_download_delay": True,
    "download_delay_range": (4, 6),
}

# 用户代理轮换
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
]

# 请求头配置
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5,zh-CN;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

# 域名特定配置
DOMAIN_CONFIGS = {
    "www.msdmanuals.com": {
        "delay": 5.0,
        "max_concurrent": 3,
        "priority": "high"
    },
    "www.msdmanuals.cn": {
        "delay": 6.0,
        "max_concurrent": 2,
        "priority": "high"
    },
    "www.msdvetmanual.com": {
        "delay": 7.0,
        "max_concurrent": 1,
        "priority": "medium"
    }
}

# 重试配置
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay_range": (1, 5),
    "backoff_factor": 2,
    "retry_status_codes": [429, 500, 502, 503, 504],
    "give_up_status_codes": [403, 404, 451]
}

# 状态文件配置
STATE_CONFIG = {
    "state_file": "crawler_state.json",
    "save_interval": 100,
    "checkpoints_dir": "checkpoints",
    "backup_enabled": True,
    "backup_interval": 500
}
'''
    
    with open('config/crawler_config.py', 'w', encoding='utf-8') as f:
        f.write(crawler_config)
    
    print("✅ 创建爬虫配置文件")

def setup_requirements():
    """创建requirements.txt文件"""
    
    requirements = '''# 核心爬虫框架
scrapy>=2.11.0
scrapy-redis>=0.7.0
scrapy-splash>=0.3.0

# 数据库
mysql-connector-python>=8.0.32
sqlalchemy>=2.0.0
alembic>=1.12.0
pymongo>=4.5.0

# 数据处理
beautifulsoup4>=4.12.0
lxml>=4.9.0
nltk>=3.8.0
spacy>=3.6.0
pandas>=2.0.0
numpy>=1.24.0

# 文本处理
regex>=2023.0.0
jieba>=0.42.1
wordcloud>=1.9.2

# HTTP和异步
requests>=2.31.0
aiohttp>=3.8.0
httpx>=0.24.0

# 日志和监控
loguru>=0.7.0
prometheus-client>=0.16.0

# Web框架
flask>=2.3.0
flask-cors>=4.0.0
gunicorn>=21.0.0

# 测试
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0

# 工具库
python-dotenv>=1.0.0
pytz>=2023.3
pydantic>=2.3.0
click>=8.1.0
colorama>=0.4.6
'''
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    print("✅ 创建requirements.txt文件")

def create_main_script():
    """创建主程序入口"""
    
    main_script = '''#!/usr/bin/env python3
"""
默沙东诊疗手册爬虫系统主程序
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from crawler.main_crawler import MSDManualsCrawler
from database.setup_database import setup_database
from api.server import start_api_server
from web_interface.app import create_search_interface

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/crawler.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='默沙东诊疗手册爬虫系统')
    parser.add_argument('command', choices=['crawl', 'setup-db', 'api', 'search', 'test'], 
                       help='要执行的命令')
    parser.add_argument('--config', default='config/crawler_config.py', 
                       help='配置文件路径')
    parser.add_argument('--output', default='data/output', 
                       help='输出目录')
    parser.add_argument('--language', default='en', 
                       help='爬取语言版本 (en, zh, fr, etc.)')
    parser.add_argument('--version', default='home', 
                       help='爬取版本 (home, professional, veterinary)')
    parser.add_argument('--max-pages', type=int, default=1000, 
                       help='最大爬取页面数')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if args.command == 'crawl':
        logger.info("开始爬取数据...")
        crawler = MSDManualsCrawler(config_path=args.config)
        crawler.run(
            language=args.language,
            version=args.version,
            max_pages=args.max_pages,
            output_dir=args.output
        )
        
    elif args.command == 'setup-db':
        logger.info("初始化数据库...")
        setup_database()
        
    elif args.command == 'api':
        logger.info("启动API服务...")
        start_api_server()
        
    elif args.command == 'search':
        logger.info("启动搜索界面...")
        create_search_interface()
        
    elif args.command == 'test':
        logger.info("运行测试...")
        import subprocess
        result = subprocess.run(['pytest', '-v'], cwd=project_root)
        sys.exit(result.returncode)

if __name__ == '__main__':
    main()
'''
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(main_script)
    
    # 设置执行权限
    os.chmod('main.py', 0o755)
    
    print("✅ 创建主程序入口")

def create_database_models():
    """创建数据库模型"""
    
    models_script = '''"""
数据库模型定义
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Article(Base):
    """文章表"""
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    subtitle = Column(String(500))
    category = Column(String(100), index=True)
    subcategory = Column(String(100))
    content = Column(Text)
    content_html = Column(Text)
    excerpt = Column(Text)
    version = Column(String(20), default='home', index=True)
    language = Column(String(10), default='en', index=True)
    author = Column(String(200))
    last_reviewed = Column(DateTime)
    published_date = Column(DateTime)
    word_count = Column(Integer, default=0)
    hash_content = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_category_language', 'category', 'language'),
        Index('idx_version_language', 'version', 'language'),
        Index('idx_content_length', 'word_count'),
    )
    
    # 关系
    medical_terms = relationship("MedicalTerm", secondary="article_terms", back_populates="articles")
    
class Category(Base):
    """分类表"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    level = Column(Integer, default=1)
    description = Column(Text)
    article_count = Column(Integer, default=0)
    version = Column(String(20), default='home', index=True)
    language = Column(String(10), default='en', index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 约束
    __table_args__ = (
        UniqueConstraint('slug', 'version', 'language', name='uk_slug_version_lang'),
        Index('idx_parent', 'parent_id'),
    )
    
    # 关系
    parent = relationship("Category", remote_side=[id], backref="children")

class MedicalTerm(Base):
    """医学术语表"""
    __tablename__ = 'medical_terms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(300), nullable=False, index=True)
    definition = Column(Text)
    synonyms = Column(JSON)  # JSON数组
    category = Column(String(100), index=True)  # 症状, 诊断, 治疗, 药物等
    icd_code = Column(String(20))
    umls_id = Column(String(20))
    frequency_score = Column(Float, default=0.0)
    related_articles = Column(JSON)  # JSON数组
    version = Column(String(20), default='home', index=True)
    language = Column(String(10), default='en', index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 约束
    __table_args__ = (
        UniqueConstraint('term', 'version', 'language', name='uk_term_version_lang'),
        Index('idx_category', 'category'),
    )
    
    # 关系
    articles = relationship("Article", secondary="article_terms", back_populates="medical_terms")

class ArticleTerm(Base):
    """文章术语关联表"""
    __tablename__ = 'article_terms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    term_id = Column(Integer, ForeignKey('medical_terms.id'), nullable=False)
    frequency = Column(Integer, default=1)
    position = Column(JSON)  # JSON数组，记录位置信息
    
    # 索引
    __table_args__ = (
        UniqueConstraint('article_id', 'term_id', name='uk_article_term'),
        Index('idx_article', 'article_id'),
        Index('idx_term', 'term_id'),
    )

class Drug(Base):
    """药物信息表"""
    __tablename__ = 'drugs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    generic_name = Column(String(300), index=True)
    brand_names = Column(JSON)  # JSON数组
    drug_class = Column(String(200), index=True)
    description = Column(Text)
    indications = Column(Text)  # 适应症
    contraindications = Column(Text)  # 禁忌症
    dosage = Column(Text)
    side_effects = Column(Text)
    interactions = Column(Text)
    article_id = Column(Integer, ForeignKey('articles.id'))
    version = Column(String(20), default='home', index=True)
    language = Column(String(10), default='en', index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    article = relationship("Article")

class SearchLog(Base):
    """搜索日志表"""
    __tablename__ = 'search_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(500))
    results_count = Column(Integer, default=0)
    execution_time = Column(Float, default=0.0)
    user_agent = Column(String(200))
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_query', 'query'),
        Index('idx_date', 'created_at'),
    )
'''
    
    with open('database/models.py', 'w', encoding='utf-8') as f:
        f.write(models_script)
    
    print("✅ 创建数据库模型")

def create_readme():
    """创建README文件"""
    
    readme_content = '''# 默沙东诊疗手册爬虫系统

一个高效、合规的医学文献数据抓取与检索系统。

## 🚀 功能特性

- **合规抓取**: 严格遵守robots.txt政策，智能频率控制
- **医学解析**: 专门优化的医学内容解析器
- **多语言支持**: 支持16种语言版本的抓取
- **智能搜索**: 基于自然语言处理的全文检索
- **增量更新**: 支持断点续传和增量更新
- **质量保证**: 完整的数据质量检查机制

## 📦 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 初始化数据库
python main.py setup-db
```

## 🕷️ 快速开始

### 爬取数据
```bash
# 爬取英文消费者版数据
python main.py crawl --language en --version home --max-pages 1000

# 爬取中文专业版数据
python main.py crawl --language zh --version professional --max-pages 500

# 指定输出目录
python main.py crawl --language en --version home --output ./output --max-pages 2000
```

### 启动服务
```bash
# 启动搜索API
python main.py api

# 启动搜索界面
python main.py search
```

### 运行测试
```bash
python main.py test
```

## 📁 项目结构

```
msd_crawler_project/
├── config/                 # 配置文件
├── database/               # 数据库相关
├── crawler/                # 爬虫核心代码
├── parsers/                # 内容解析器
├── processors/             # 数据处理器
├── api/                    # API服务
├── web_interface/          # Web界面
├── tests/                  # 测试代码
├── data/                   # 数据文件
├── docs/                   # 文档
└── scripts/                # 脚本工具
```

## ⚙️ 配置说明

### 数据库配置
- 支持MySQL和SQLite
- 自动创建必要的表结构
- 支持全文搜索索引

### 爬虫配置
- 可配置并发数和延迟
- 智能重试机制
- 断点续传支持

## 📊 数据结构

### 主要表
- `articles`: 文章内容
- `categories`: 医学分类
- `medical_terms`: 医学术语
- `drugs`: 药物信息
- `search_logs`: 搜索日志

### 搜索功能
- 全文搜索
- 按分类筛选
- 关键词高亮
- 相关性排序

## 🛠️ 技术栈

- **爬虫框架**: Scrapy
- **数据库**: MySQL/SQLite
- **文本处理**: NLTK, spaCy
- **Web框架**: Flask
- **前端**: HTML5 + JavaScript

## 📄 许可证

本项目仅用于学术研究目的。请遵守相关法律法规和网站使用条款。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📞 联系方式

如有问题，请通过GitHub Issues联系我们。
'''
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ 创建README.md文件")

def main():
    """主函数"""
    print("🚀 开始初始化默沙东诊疗手册爬虫项目...")
    
    # 创建项目结构
    create_project_structure()
    
    # 设置配置文件
    setup_database()
    setup_crawler_config()
    setup_requirements()
    
    # 创建核心文件
    create_main_script()
    create_database_models()
    create_readme()
    
    print("\\n✅ 项目初始化完成！")
    print("\\n📋 下一步操作:")
    print("1. 安装依赖: pip install -r requirements.txt")
    print("2. 初始化数据库: python main.py setup-db")
    print("3. 开始爬取: python main.py crawl --language en --version home --max-pages 100")
    print("\\n📚 查看README.md获取详细使用说明")

if __name__ == '__main__':
    main()

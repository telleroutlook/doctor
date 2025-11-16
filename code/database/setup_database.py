#!/usr/bin/env python3
"""
数据库设置和初始化
"""

import os
import sqlite3
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 导入数据库模型
from .models import Base, Article, Category, MedicalTerm, ArticleTerm, Drug, SearchLog

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""

    def __init__(self, use_sqlite=True, config=None, sqlite_path=None):
        """
        初始化数据库连接

        Args:
            use_sqlite: 是否使用SQLite（用于测试）
            config: 数据库配置
            sqlite_path: 自定义SQLite文件路径（用于隔离测试环境）
        """
        self.use_sqlite = use_sqlite

        if use_sqlite:
            # 使用SQLite作为数据库
            db_path = Path(sqlite_path) if sqlite_path else Path("data/msd_manuals.db")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.engine = create_engine(f"sqlite:///{db_path}")
        else:
            # 使用MySQL
            if config:
                connection_string = f"mysql+mysqlconnector://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config['charset']}"
                self.engine = create_engine(connection_string)
            else:
                raise ValueError("MySQL配置缺失")
        
        # 创建会话
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """创建所有数据库表"""
        logger.info("正在创建数据库表...")
        
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
            
            # 创建全文搜索索引（SQLite）
            if self.use_sqlite:
                self._create_sqlite_indexes()
                
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def _create_sqlite_indexes(self):
        """为SQLite创建全文搜索索引"""
        session = self.SessionLocal()
        
        try:
            # 创建FTS5虚拟表用于全文搜索
            fts_sql = """
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                title, 
                content, 
                category, 
                content='articles', 
                content_rowid='id'
            );
            
            CREATE VIRTUAL TABLE IF NOT EXISTS terms_fts USING fts5(
                term,
                definition,
                content='medical_terms',
                content_rowid='id'
            );
            """
            
            for sql in fts_sql.split(';'):
                if sql.strip():
                    session.execute(text(sql))
            
            session.commit()
            logger.info("全文搜索索引创建成功")
            
        except Exception as e:
            logger.error(f"创建全文搜索索引失败: {e}")
        finally:
            session.close()
    
    def setup_sample_data(self):
        """设置示例数据"""
        session = self.SessionLocal()
        
        try:
            # 创建示例分类
            categories = [
                Category(name="心血管疾病", slug="cardiovascular-disorders", level=1, language="zh", version="home"),
                Category(name="神经系统疾病", slug="neurologic-disorders", level=1, language="zh", version="home"),
                Category(name="内分泌疾病", slug="endocrine-disorders", level=1, language="zh", version="home"),
                Category(name="高血压", slug="hypertension", level=2, parent_id=1, language="zh", version="home"),
                Category(name="糖尿病", slug="diabetes", level=2, parent_id=3, language="zh", version="home"),
            ]
            
            for category in categories:
                session.add(category)
            
            # 创建示例医学术语
            terms = [
                MedicalTerm(term="高血压", definition="动脉血压持续升高的疾病", category="症状", language="zh"),
                MedicalTerm(term="心率", definition="心脏每分钟跳动的次数", category="生理指标", language="zh"),
                MedicalTerm(term="糖尿病", definition="以高血糖为特征的代谢性疾病", category="疾病", language="zh"),
            ]
            
            for term in terms:
                session.add(term)
            
            session.commit()
            logger.info("示例数据创建成功")
            
        except Exception as e:
            session.rollback()
            logger.error(f"创建示例数据失败: {e}")
        finally:
            session.close()
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()

def setup_database(use_sqlite=True, sqlite_path=None):
    """设置数据库

    Args:
        use_sqlite: 是否使用SQLite
        sqlite_path: 自定义SQLite文件路径

    Returns:
        DatabaseManager: 数据库管理器实例
    """
    logger.info("开始设置数据库...")

    try:
        # 创建数据库管理器
        db_manager = DatabaseManager(use_sqlite=use_sqlite, sqlite_path=sqlite_path)
        
        # 创建表
        db_manager.create_tables()
        
        # 设置示例数据
        if use_sqlite:
            db_manager.setup_sample_data()
        
        logger.info("数据库设置完成")
        return db_manager
        
    except Exception as e:
        logger.error(f"数据库设置失败: {e}")
        raise

if __name__ == "__main__":
    # 测试数据库设置
    db_manager = setup_database(use_sqlite=True)
    
    # 测试插入数据
    session = db_manager.get_session()
    try:
        # 创建一个示例文章
        article = Article(
            url="https://www.msdmanuals.com/home/test-article",
            title="高血压概述",
            content="高血压是一种常见的慢性疾病，指动脉血压持续升高...",
            category="cardiovascular-disorders",
            language="zh",
            version="home"
        )
        
        session.add(article)
        session.commit()
        
        print("✅ 测试文章插入成功")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 测试失败: {e}")
    finally:
        session.close()
        db_manager.close()

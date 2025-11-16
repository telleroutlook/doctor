"""
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

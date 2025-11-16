#!/usr/bin/env python3
"""
完整的数据库设置和初始化脚本
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MedicalDatabase:
    """医学数据库管理器"""
    
    def __init__(self, db_path="data/msd_medical_knowledge.db"):
        """初始化数据库"""
        self.db_path = db_path
        self.db_dir = Path(db_path).parent
        self.db_dir.mkdir(exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库和表结构"""
        conn = self.get_connection()
        try:
            self._create_tables(conn)
            self._create_indexes(conn)
            self._create_functions(conn)
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def _create_tables(self, conn):
        """创建所有表"""
        
        # 文章表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                subtitle TEXT,
                category TEXT,
                subcategory TEXT,
                content TEXT,
                content_html TEXT,
                excerpt TEXT,
                version TEXT DEFAULT 'home',
                language TEXT DEFAULT 'en',
                author TEXT,
                last_reviewed TEXT,
                published_date TEXT,
                word_count INTEGER DEFAULT 0,
                content_hash TEXT UNIQUE,
                quality_score INTEGER DEFAULT 0,
                extracted_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 医学术语表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS medical_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                definition TEXT,
                synonyms TEXT,  -- JSON array
                category TEXT,  -- disease, drug, symptom, procedure, anatomy
                icd_code TEXT,
                umls_id TEXT,
                frequency_score REAL DEFAULT 0.0,
                related_articles TEXT,  -- JSON array of article IDs
                version TEXT DEFAULT 'home',
                language TEXT DEFAULT 'en',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(term, version, language)
            )
        ''')
        
        # 文章术语关联表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS article_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                term_id INTEGER NOT NULL,
                frequency INTEGER DEFAULT 1,
                positions TEXT,  -- JSON array of positions
                FOREIGN KEY (article_id) REFERENCES articles (id),
                FOREIGN KEY (term_id) REFERENCES medical_terms (id),
                UNIQUE(article_id, term_id)
            )
        ''')
        
        # 药物信息表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS drugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generic_name TEXT,
                brand_names TEXT,  -- JSON array
                drug_class TEXT,
                description TEXT,
                indications TEXT,
                contraindications TEXT,
                dosage TEXT,
                side_effects TEXT,
                interactions TEXT,
                article_id INTEGER,
                version TEXT DEFAULT 'home',
                language TEXT DEFAULT 'en',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')
        
        # 疾病症状关系表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS disease_symptoms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disease_term TEXT NOT NULL,
                symptom_term TEXT NOT NULL,
                relationship_type TEXT,  -- may_have, has_symptom, causes
                confidence_score REAL DEFAULT 1.0,
                article_id INTEGER,
                version TEXT DEFAULT 'home',
                language TEXT DEFAULT 'en',
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')
        
        # 搜索日志表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                results_count INTEGER DEFAULT 0,
                execution_time REAL DEFAULT 0.0,
                user_agent TEXT,
                ip_address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 质量检查记录表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS quality_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                check_type TEXT,
                passed BOOLEAN,
                score REAL,
                issues TEXT,  -- JSON array of issues
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')
        
        conn.commit()
    
    def _create_indexes(self, conn):
        """创建索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_articles_url ON articles (url)",
            "CREATE INDEX IF NOT EXISTS idx_articles_category ON articles (category)",
            "CREATE INDEX IF NOT EXISTS idx_articles_language ON articles (language)",
            "CREATE INDEX IF NOT EXISTS idx_articles_version ON articles (version)",
            "CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles (content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_terms_term ON medical_terms (term)",
            "CREATE INDEX IF NOT EXISTS idx_terms_category ON medical_terms (category)",
            "CREATE INDEX IF NOT EXISTS idx_terms_language ON medical_terms (language)",
            "CREATE INDEX IF NOT EXISTS idx_article_terms_article_id ON article_terms (article_id)",
            "CREATE INDEX IF NOT EXISTS idx_article_terms_term_id ON article_terms (term_id)",
            "CREATE INDEX IF NOT EXISTS idx_drugs_generic_name ON drugs (generic_name)",
            "CREATE INDEX IF NOT EXISTS idx_drugs_class ON drugs (drug_class)",
            "CREATE INDEX IF NOT EXISTS idx_disease_symptoms_disease ON disease_symptoms (disease_term)",
            "CREATE INDEX IF NOT EXISTS idx_disease_symptoms_symptom ON disease_symptoms (symptom_term)",
            "CREATE INDEX IF NOT EXISTS idx_search_logs_query ON search_logs (query)",
            "CREATE INDEX IF NOT EXISTS idx_quality_checks_article_id ON quality_checks (article_id)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
        
        # 创建全文搜索虚拟表
        self._create_fts_indexes(conn)
    
    def _create_fts_indexes(self, conn):
        """创建全文搜索索引"""
        try:
            # 文章全文搜索表
            conn.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                    title,
                    content,
                    subtitle,
                    category,
                    content='articles',
                    content_rowid='id'
                )
            ''')
            
            # 医学术语全文搜索表
            conn.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS terms_fts USING fts5(
                    term,
                    definition,
                    content='medical_terms',
                    content_rowid='id'
                )
            ''')
            
            conn.commit()
            logger.info("全文搜索索引创建成功")
            
        except sqlite3.Error as e:
            logger.warning(f"创建全文搜索索引失败: {e}")
    
    def _create_functions(self, conn):
        """创建自定义函数"""
        # 文本相似度函数（简单版本）
        def text_similarity(text1, text2):
            """计算两个文本的相似度"""
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 and not words2:
                return 1.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
        
        # 注册函数
        conn.create_function("text_similarity", 2, text_similarity)
        
        # 文本清理函数
        def clean_text(text):
            """清理文本"""
            if not text:
                return ""
            
            # 移除多余的空白
            import re
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        conn.create_function("clean_text", 1, clean_text)
    
    def insert_article(self, article_data):
        """插入文章数据"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute("SELECT id FROM articles WHERE url = ?", (article_data['url'],))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                article_id = existing[0]
                cursor.execute('''
                    UPDATE articles SET 
                        title = ?, subtitle = ?, content = ?, content_html = ?,
                        excerpt = ?, word_count = ?, quality_score = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    article_data.get('title', ''),
                    article_data.get('subtitle', ''),
                    article_data.get('content', ''),
                    article_data.get('content_html', ''),
                    article_data.get('summary', ''),
                    article_data.get('word_count', 0),
                    article_data.get('quality_score', 0),
                    article_id
                ))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO articles (
                        url, title, subtitle, content, content_html, excerpt,
                        category, subcategory, version, language,
                        author, last_reviewed, word_count, content_hash,
                        quality_score, extracted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_data['url'],
                    article_data.get('title', ''),
                    article_data.get('subtitle', ''),
                    article_data.get('content', ''),
                    article_data.get('content_html', ''),
                    article_data.get('summary', ''),
                    article_data.get('category', ''),
                    article_data.get('subcategory', ''),
                    article_data.get('version', 'home'),
                    article_data.get('language', 'en'),
                    article_data.get('metadata', {}).get('author', ''),
                    article_data.get('metadata', {}).get('last_reviewed', ''),
                    article_data.get('word_count', 0),
                    article_data.get('content_hash', ''),
                    article_data.get('quality_score', 0),
                    article_data.get('extracted_at', '')
                ))
                
                article_id = cursor.lastrowid
            
            conn.commit()
            return article_id
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"插入文章失败: {e}")
            raise
        finally:
            conn.close()
    
    def insert_medical_terms(self, article_id, medical_terms, language='zh', version='home'):
        """插入医学术语"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            for term_info in medical_terms:
                term = term_info.get('term', '')
                if not term:
                    continue
                
                # 检查术语是否已存在
                cursor.execute(
                    "SELECT id FROM medical_terms WHERE term = ? AND language = ? AND version = ?",
                    (term, language, version)
                )
                existing_term = cursor.fetchone()
                
                if existing_term:
                    term_id = existing_term[0]
                else:
                    # 创建新术语
                    cursor.execute('''
                        INSERT INTO medical_terms (
                            term, category, language, version, related_articles
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        term,
                        term_info.get('category', 'general'),
                        language,
                        version,
                        json.dumps([article_id])
                    ))
                    term_id = cursor.lastrowid
                
                # 创建文章术语关联
                cursor.execute('''
                    INSERT OR REPLACE INTO article_terms (
                        article_id, term_id, frequency, positions
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    article_id,
                    term_id,
                    term_info.get('frequency', 1),
                    json.dumps(term_info.get('positions', []))
                ))
            
            conn.commit()
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"插入医学术语失败: {e}")
        finally:
            conn.close()
    
    def search_articles(self, query, language='zh', category=None, limit=20):
        """搜索文章"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 构建查询条件
            where_conditions = []
            params = []
            
            if language:
                where_conditions.append("language = ?")
                params.append(language)
            
            if category:
                where_conditions.append("category = ?")
                params.append(category)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 全文搜索
            cursor.execute(f'''
                SELECT a.id, a.title, a.excerpt, a.category, a.language,
                       a.word_count, a.quality_score,
                       highlight(articles_fts, 0, '<mark>', '</mark>') as highlighted_title,
                       snippet(articles_fts, 1, '<mark>', '</mark>', '...', 20) as snippet
                FROM articles a
                JOIN articles_fts ON articles_fts.rowid = a.id
                {where_clause}
                AND articles_fts MATCH ?
                ORDER BY a.quality_score DESC, a.word_count DESC
                LIMIT ?
            ''', params + [query, limit])
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'title': row[1],
                    'excerpt': row[2],
                    'category': row[3],
                    'language': row[4],
                    'word_count': row[5],
                    'quality_score': row[6],
                    'highlighted_title': row[7],
                    'snippet': row[8]
                })
            
            return results
            
        except sqlite3.Error as e:
            logger.error(f"搜索文章失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_statistics(self):
        """获取数据库统计信息"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 基本统计
            stats = {}
            
            # 文章总数
            cursor.execute("SELECT COUNT(*) FROM articles")
            stats['total_articles'] = cursor.fetchone()[0]
            
            # 按语言统计
            cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language")
            stats['by_language'] = dict(cursor.fetchall())
            
            # 按版本统计
            cursor.execute("SELECT version, COUNT(*) FROM articles GROUP BY version")
            stats['by_version'] = dict(cursor.fetchall())
            
            # 按分类统计
            cursor.execute("SELECT category, COUNT(*) FROM articles WHERE category != '' GROUP BY category ORDER BY COUNT(*) DESC LIMIT 10")
            stats['top_categories'] = dict(cursor.fetchall())
            
            # 医学术语统计
            cursor.execute("SELECT COUNT(*) FROM medical_terms")
            stats['total_medical_terms'] = cursor.fetchone()[0]
            
            # 药物统计
            cursor.execute("SELECT COUNT(*) FROM drugs")
            stats['total_drugs'] = cursor.fetchone()[0]
            
            # 质量评分统计
            cursor.execute("SELECT AVG(quality_score) FROM articles")
            avg_quality = cursor.fetchone()[0]
            stats['average_quality_score'] = round(avg_quality, 2) if avg_quality else 0
            
            # 词数统计
            cursor.execute("SELECT AVG(word_count) FROM articles")
            avg_words = cursor.fetchone()[0]
            stats['average_word_count'] = round(avg_words, 0) if avg_words else 0
            
            return stats
            
        except sqlite3.Error as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
        finally:
            conn.close()
    
    def cleanup_data(self):
        """清理数据"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 删除重复文章（基于content_hash）
            cursor.execute('''
                DELETE FROM articles 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM articles 
                    GROUP BY content_hash
                )
            ''')
            
            # 删除孤立的医学术语
            cursor.execute('''
                DELETE FROM medical_terms 
                WHERE id NOT IN (
                    SELECT DISTINCT term_id 
                    FROM article_terms
                )
            ''')
            
            # 更新统计信息
            cursor.execute("VACUUM")
            
            conn.commit()
            logger.info("数据清理完成")
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"数据清理失败: {e}")
        finally:
            conn.close()

class VectorProcessor:
    """向量处理器（简化版）"""
    
    def __init__(self):
        self.word_vectors = {}
        self.term_frequencies = defaultdict(int)
    
    def process_text(self, text, language='zh'):
        """处理文本生成向量"""
        if not text:
            return []
        
        # 分词
        if language == 'zh':
            words = self._chinese_tokenize(text)
        else:
            words = self._english_tokenize(text)
        
        # 计算词频
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1
        
        # TF-IDF向量化（简化版本）
        vector = []
        total_words = len(words)
        
        for word, freq in word_freq.items():
            # 简单的TF（词频）
            tf = freq / total_words
            
            # 简化的IDF（逆文档频率）
            idf = 1.0  # 简化处理，所有词都使用相同的IDF
            
            vector.append((word, tf * idf))
        
        return vector
    
    def _chinese_tokenize(self, text):
        """中文分词（简化版）"""
        import re
        
        # 简单的中文字符分割
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        
        # 移除停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很', '到'}
        words = [word for word in words if word not in stop_words and len(word) >= 2]
        
        return words
    
    def _english_tokenize(self, text):
        """英文分词（简化版）"""
        import re
        
        # 简单的英文单词提取
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # 移除停用词
        stop_words = {'the', 'and', 'or', 'but', 'with', 'for', 'in', 'on', 'at', 'to', 'of', 'is', 'are', 'was', 'were'}
        words = [word for word in words if word not in stop_words]
        
        return words
    
    def calculate_similarity(self, vector1, vector2):
        """计算向量相似度（余弦相似度）"""
        if not vector1 or not vector2:
            return 0.0
        
        # 创建词汇表
        all_words = set()
        for word, _ in vector1 + vector2:
            all_words.add(word)
        
        # 创建向量
        vec1 = [0.0] * len(all_words)
        vec2 = [0.0] * len(all_words)
        
        word_to_idx = {word: i for i, word in enumerate(all_words)}
        
        for word, weight in vector1:
            vec1[word_to_idx[word]] = weight
        
        for word, weight in vector2:
            vec2[word_to_idx[word]] = weight
        
        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)

class QualityValidator:
    """数据质量验证器"""
    
    def __init__(self):
        self.quality_rules = {
            'title_min_length': 5,
            'content_min_length': 100,
            'word_count_min': 10,
            'max_repeated_chars': 0.3,
            'min_medical_terms': 1,
            'min_quality_score': 30
        }
    
    def validate_article(self, article_data):
        """验证文章质量"""
        issues = []
        score = 0
        
        # 标题验证
        title = article_data.get('title', '')
        if len(title) >= self.quality_rules['title_min_length']:
            score += 20
        else:
            issues.append(f"标题过短 ({len(title)} 字符)")
        
        # 内容验证
        content = article_data.get('content', '')
        content_length = len(content)
        
        if content_length >= self.quality_rules['content_min_length']:
            score += 30
        else:
            issues.append(f"内容过短 ({content_length} 字符)")
        
        # 词数验证
        word_count = article_data.get('word_count', 0)
        if word_count >= self.quality_rules['word_count_min']:
            score += 20
        else:
            issues.append(f"词数不足 ({word_count})")
        
        # 医学术语验证
        medical_terms = article_data.get('medical_terms', [])
        if len(medical_terms) >= self.quality_rules['min_medical_terms']:
            score += 15
        else:
            issues.append(f"医学术语不足 ({len(medical_terms)})")
        
        # URL验证
        url = article_data.get('url', '')
        if url and url.startswith('http'):
            score += 10
        else:
            issues.append("URL格式无效")
        
        # 元数据验证
        metadata = article_data.get('metadata', {})
        if metadata.get('category') and metadata.get('language'):
            score += 5
        else:
            issues.append("元数据不完整")
        
        # 重复内容检查
        if self._has_repeated_content(content):
            score -= 10
            issues.append("存在重复内容")
        
        # 可读性检查
        readability_score = self._calculate_readability(content)
        if readability_score >= 50:
            score += 5
        else:
            issues.append(f"可读性较差 ({readability_score})")
        
        # 限制最大分数
        score = min(100, score)
        
        return {
            'is_valid': score >= self.quality_rules['min_quality_score'],
            'quality_score': score,
            'issues': issues,
            'readability_score': readability_score
        }
    
    def _has_repeated_content(self, content):
        """检查是否有重复内容"""
        if not content:
            return False
        
        # 简单的重复检查
        lines = content.split('\n')
        if len(lines) < 3:
            return False
        
        # 检查是否有超过30%的行是重复的
        line_counts = defaultdict(int)
        for line in lines:
            if len(line.strip()) > 10:  # 只检查有意义的行
                line_counts[line.strip()] += 1
        
        repeated_lines = sum(1 for count in line_counts.values() if count > 1)
        return (repeated_lines / len(lines)) > self.quality_rules['max_repeated_chars']
    
    def _calculate_readability(self, content):
        """计算可读性评分"""
        if not content:
            return 0
        
        import re
        
        # 简单的可读性计算
        sentences = re.split(r'[.!?。！？]+', content)
        sentences = [s for s in sentences if s.strip()]
        
        if not sentences:
            return 0
        
        # 平均句子长度
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # 句子长度评分（30-50字符为最佳）
        if 30 <= avg_sentence_length <= 50:
            return 100
        elif avg_sentence_length < 30:
            return max(0, avg_sentence_length * 3)
        else:
            return max(0, 100 - (avg_sentence_length - 50) * 2)

def main():
    """主函数"""
    print("🗄️ 医学知识库数据处理和存储系统")
    print("=" * 50)
    
    # 初始化数据库
    db = MedicalDatabase()
    
    # 质量验证器
    validator = QualityValidator()
    
    # 向量处理器
    vector_processor = VectorProcessor()
    
    print("✅ 数据库初始化完成")
    print("✅ 质量验证器准备就绪")
    print("✅ 向量处理器准备就绪")
    
    # 如果有爬虫数据，尝试导入
    if Path("data/output/crawler_results.json").exists():
        print("\\n📥 正在导入爬虫数据...")
        
        with open("data/output/crawler_results.json", 'r', encoding='utf-8') as f:
            crawler_data = json.load(f)
        
        articles = crawler_data.get('articles', [])
        print(f"发现 {len(articles)} 篇爬取的文章")
        
        imported_count = 0
        for article_data in articles:
            try:
                # 质量验证
                validation = validator.validate_article(article_data)
                article_data['quality_score'] = validation['quality_score']
                
                # 向量处理
                if article_data.get('content'):
                    content_vector = vector_processor.process_text(
                        article_data['content'], 
                        article_data.get('language', 'zh')
                    )
                    # 在实际应用中，这里会将向量存储到向量数据库
                
                # 插入数据库
                article_id = db.insert_article(article_data)
                
                # 插入医学术语
                medical_terms = article_data.get('medical_terms', [])
                if medical_terms:
                    db.insert_medical_terms(
                        article_id, 
                        medical_terms,
                        article_data.get('language', 'zh'),
                        article_data.get('version', 'home')
                    )
                
                imported_count += 1
                
            except Exception as e:
                logger.error(f"导入文章失败: {e}")
        
        print(f"✅ 成功导入 {imported_count} 篇文章")
    
    # 获取统计信息
    print("\\n📊 数据库统计信息:")
    stats = db.get_statistics()
    
    for key, value in stats.items():
        if key == 'by_language':
            print(f"  按语言分布: {value}")
        elif key == 'by_version':
            print(f"  按版本分布: {value}")
        elif key == 'top_categories':
            print(f"  热门分类: {dict(list(value.items())[:5])}")
        elif key == 'average_quality_score':
            print(f"  平均质量评分: {value}")
        elif key == 'average_word_count':
            print(f"  平均词数: {int(value)}")
        elif isinstance(value, int):
            print(f"  {key}: {value:,}")
    
    # 测试搜索功能
    if stats.get('total_articles', 0) > 0:
        print("\\n🔍 测试搜索功能:")
        test_queries = ["高血压", "heart", "diabetes"]
        
        for query in test_queries:
            results = db.search_articles(query, limit=5)
            print(f"  查询 '{query}': 找到 {len(results)} 个结果")
            
            if results:
                for result in results[:3]:  # 显示前3个结果
                    print(f"    - {result['title']} (质量: {result['quality_score']})")
    
    print("\\n🎉 数据处理和存储系统设置完成！")

if __name__ == "__main__":
    main()

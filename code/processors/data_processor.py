#!/usr/bin/env python3
"""
数据处理器
"""

import re
import logging
import hashlib
from datetime import datetime
from collections import Counter
import jieba
import jieba.analyse

logger = logging.getLogger(__name__)

class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        """初始化处理器"""
        # 停用词列表
        self.stop_words = {
            'zh': set([
                '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '或', '但', '只', '可', '已', '应', '会', '并', '可', '于', '对', '由', '把', '而', '从', '以', '为', '与', '及', '向', '当', '将', '比', '等', '还', '此', '各', '所', '其', '之', '前', '后', '来', '还', '被', '过', '再', '用', '能', '使', '则', '么', '地', '得', '于', '关于', '根据', '通过', '因此', '所以', '但是', '然而', '另外', '此外', '例如', '比如', '特别是', '尤其是', '其中', '包括', '即', '也就是', '换句话说', '换言之', '总而言之', '综上所述'
            ]),
            'en': set([
                'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'
            ])
        }
        
        # 医学词典初始化
        jieba.initialize()
        
        # 文本长度阈值
        self.min_content_length = 50
        self.max_content_length = 50000
        
        # 质量检查规则
        self.quality_rules = {
            'min_word_count': 10,
            'min_sentence_count': 3,
            'min_paragraph_count': 1,
            'max_repeated_chars_ratio': 0.3,
            'min_readability_score': 30
        }
    
    def process(self, raw_data):
        """处理原始数据
        
        Args:
            raw_data: 解析后的原始数据
            
        Returns:
            dict: 处理后的数据
        """
        try:
            # 数据清洗
            cleaned_data = self._clean_data(raw_data)
            
            # 文本分析
            analyzed_data = self._analyze_content(cleaned_data)
            
            # 质量评估
            quality_assessed_data = self._assess_quality(analyzed_data)
            
            # 特征提取
            feature_extracted_data = self._extract_features(quality_assessed_data)
            
            # 格式标准化
            standardized_data = self._standardize_format(feature_extracted_data)
            
            return standardized_data
            
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            raise
    
    def _clean_data(self, data):
        """清洗数据"""
        cleaned = data.copy()
        
        # 清理标题
        if cleaned.get('title'):
            cleaned['title'] = self._clean_title(cleaned['title'])
        
        # 清理内容
        if cleaned.get('content'):
            cleaned['content'] = self._clean_content(cleaned['content'])
        
        # 清理元数据
        if cleaned.get('metadata'):
            cleaned['metadata'] = self._clean_metadata(cleaned['metadata'])
        
        # 验证并过滤医学术语
        if cleaned.get('medical_terms'):
            cleaned['medical_terms'] = self._filter_medical_terms(cleaned['medical_terms'])
        
        return cleaned
    
    def _clean_title(self, title):
        """清理标题"""
        # 移除多余的空格和标点
        title = re.sub(r'\s+', ' ', title.strip())
        title = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', title)
        
        # 移除导航和商标信息
        patterns = [
            r'\|.*MSD.*Manuals',
            r'\|.*默沙东.*诊疗手册',
            r'\|.*MSD.*Manual',
            r'\|.*专业版',
            r'\|.*消费者版'
        ]
        
        for pattern in patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        # 确保标题有意义
        if len(title) < 3:
            title = "未命名页面"
        
        return title.strip()
    
    def _clean_content(self, content):
        """清理内容"""
        # 移除重复的换行
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # 移除过长的空白
        content = re.sub(r'\s{5,}', ' ', content)
        
        # 移除不必要的分隔符
        separators = ['---', '===', '***', '___']
        for sep in separators:
            content = content.replace(sep, '')
        
        # 移除页面导航和脚注
        patterns_to_remove = [
            r'©\s*\d{4}.*?MSD.*?Manuals',
            r'Reviewed\s+by.*?\.',
            r'Modified\s+.*?\.',
            r'在.*?之前使用本.*?请阅读.*?条款',
            r'请阅读.*?使用条款'
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # 标准化段落
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 3:
                cleaned_lines.append(line)
        
        content = '\n\n'.join(cleaned_lines)
        
        return content
    
    def _clean_metadata(self, metadata):
        """清理元数据"""
        cleaned = metadata.copy()
        
        # 清理作者信息
        if cleaned.get('author'):
            cleaned['author'] = self._clean_author_info(cleaned['author'])
        
        # 验证分类信息
        if cleaned.get('category'):
            cleaned['category'] = self._normalize_category(cleaned['category'])
        
        # 验证语言
        if cleaned.get('language'):
            cleaned['language'] = self._normalize_language(cleaned['language'])
        
        return cleaned
    
    def _clean_author_info(self, author):
        """清理作者信息"""
        # 移除多余的空格
        author = re.sub(r'\s+', ' ', author.strip())
        
        # 移除职位信息
        author = re.sub(r',?\s*(MD|PH|DVM|MD|PHD|FACMP|DACVIM).*', '', author, flags=re.IGNORECASE)
        
        # 移除机构信息
        author = re.sub(r',?\s*(University|Hospital|College|Clinic).*', '', author, flags=re.IGNORECASE)
        
        return author.strip()
    
    def _normalize_category(self, category):
        """标准化分类"""
        # URL路径转可读格式
        category = category.replace('-', ' ').replace('_', ' ')
        
        # 首字母大写
        category = ' '.join(word.capitalize() for word in category.split())
        
        return category
    
    def _normalize_language(self, language):
        """标准化语言代码"""
        language_map = {
            'zh': 'zh',
            'zh-cn': 'zh',
            'zh-tw': 'zh',
            'en': 'en',
            'en-us': 'en',
            'en-gb': 'en',
            'fr': 'fr',
            'de': 'de',
            'es': 'es',
            'it': 'it',
            'ja': 'ja',
            'ko': 'ko',
            'pt': 'pt',
            'ru': 'ru'
        }
        
        return language_map.get(language.lower(), language.lower())
    
    def _filter_medical_terms(self, medical_terms):
        """过滤和验证医学术语"""
        filtered_terms = []
        
        for term_info in medical_terms:
            term = term_info.get('term', '').strip()
            
            # 过滤掉过短的术语
            if len(term) < 2:
                continue
            
            # 过滤掉纯数字
            if term.isdigit():
                continue
            
            # 过滤掉重复术语
            if term in [t['term'] for t in filtered_terms]:
                continue
            
            # 过滤掉通用词汇
            if self._is_common_term(term):
                continue
            
            # 验证术语质量
            if self._validate_term_quality(term):
                filtered_terms.append({
                    'term': term,
                    'context': term_info.get('context', ''),
                    'frequency': term_info.get('frequency', 1),
                    'category': self._classify_term(term)
                })
        
        return filtered_terms
    
    def _is_common_term(self, term):
        """检查是否为通用词汇"""
        common_terms = {
            'zh': ['的', '了', '在', '是', '和', '也', '有', '可', '能', '将', '要', '会', '说', '看', '做', '得'],
            'en': ['the', 'and', 'or', 'but', 'with', 'for', 'in', 'on', 'at', 'to', 'of', 'is', 'are', 'was', 'were']
        }
        
        return term.lower() in common_terms.get('zh', set()) or term.lower() in common_terms.get('en', set())
    
    def _validate_term_quality(self, term):
        """验证术语质量"""
        # 检查是否包含特殊字符
        if re.search(r'[<>{}[\]()]', term):
            return False
        
        # 检查是否过长
        if len(term) > 50:
            return False
        
        # 检查是否过短
        if len(term) < 2:
            return False
        
        return True
    
    def _classify_term(self, term):
        """分类医学术语"""
        # 基于模式分类
        if any(keyword in term.lower() for keyword in ['药', 'drug', 'medication', 'treatment']):
            return 'drug'
        elif any(keyword in term.lower() for keyword in ['病', '症', 'disease', 'syndrome', 'disorder']):
            return 'disease'
        elif any(keyword in term.lower() for keyword in ['症', 'symptom', 'sign']):
            return 'symptom'
        elif any(keyword in term.lower() for keyword in ['手术', 'procedure', 'surgery', 'operation']):
            return 'procedure'
        else:
            return 'general'
    
    def _analyze_content(self, data):
        """分析内容"""
        analyzed = data.copy()
        
        content = data.get('content', '')
        language = data.get('metadata', {}).get('language', 'en')
        
        if content:
            # 统计分析
            analyzed['statistics'] = self._calculate_statistics(content, language)
            
            # 关键词提取
            analyzed['keywords'] = self._extract_keywords(content, language)
            
            # 摘要生成
            analyzed['summary'] = self._generate_summary(content, language)
            
            # 可读性评分
            analyzed['readability_score'] = self._calculate_readability(content, language)
        
        return analyzed
    
    def _calculate_statistics(self, content, language):
        """计算内容统计信息"""
        stats = {
            'word_count': len(content.split()),
            'character_count': len(content),
            'sentence_count': len(re.findall(r'[.!?。！？]+', content)),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'avg_sentence_length': 0,
            'avg_paragraph_length': 0,
            'language': language
        }
        
        # 计算平均句子长度
        if stats['sentence_count'] > 0:
            stats['avg_sentence_length'] = stats['word_count'] / stats['sentence_count']
        
        # 计算平均段落长度
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        if paragraphs:
            stats['avg_paragraph_length'] = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
        
        return stats
    
    def _extract_keywords(self, content, language):
        """提取关键词"""
        keywords = []
        
        if language == 'zh':
            # 中文关键词提取
            keywords = jieba.analyse.extract_tags(
                content, 
                topK=20, 
                withWeight=True,
                allowPOS=['n', 'nr', 'ns', 'nt', 'nz']  # 名词相关词性
            )
        else:
            # 英文关键词提取（使用简单的TF-IDF替代）
            words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
            word_freq = Counter(words)
            
            # 移除停用词
            stop_words = self.stop_words.get('en', set())
            filtered_words = {word: freq for word, freq in word_freq.items() 
                            if word not in stop_words and freq > 1}
            
            # 按频率排序，取前20个
            keywords = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # 格式化为列表
        if isinstance(keywords, list) and keywords:
            if isinstance(keywords[0], tuple):
                # (word, weight) 格式
                return [{'keyword': word, 'weight': weight} for word, weight in keywords]
            else:
                # 字符串格式
                return [{'keyword': word, 'weight': 1.0} for word in keywords]
        
        return []
    
    def _generate_summary(self, content, language):
        """生成摘要"""
        # 简单的句子抽取摘要
        sentences = re.split(r'[.!?。！？]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) <= 3:
            return ' '.join(sentences)
        
        # 选择前3句话作为摘要
        summary_sentences = sentences[:3]
        
        if language == 'zh':
            return ''.join(summary_sentences)
        else:
            return ' '.join(summary_sentences)
    
    def _calculate_readability(self, content, language):
        """计算可读性评分"""
        if language == 'zh':
            return self._calculate_chinese_readability(content)
        else:
            return self._calculate_english_readability(content)
    
    def _calculate_chinese_readability(self, content):
        """计算中文可读性评分"""
        # 基于句长和段落结构的简单评分
        sentences = re.split(r'[。！？]+', content)
        sentences = [s for s in sentences if s.strip()]
        
        if not sentences:
            return 0
        
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        
        # 句子长度评分（20-40字符为最佳）
        if 20 <= avg_sentence_length <= 40:
            length_score = 100
        elif avg_sentence_length < 20:
            length_score = max(0, avg_sentence_length * 5)
        else:
            length_score = max(0, 100 - (avg_sentence_length - 40) * 2)
        
        return min(100, length_score)
    
    def _calculate_english_readability(self, content):
        """计算英文可读性评分"""
        # 简化的Flesch Reading Ease计算
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        if not words or not sentences:
            return 0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables = self._estimate_syllables(content) / len(words)
        
        # Flesch Reading Ease公式
        readability_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
        
        return max(0, min(100, readability_score))
    
    def _estimate_syllables(self, text):
        """估算音节数"""
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        total_syllables = 0
        
        for word in words:
            word = word.lower()
            # 简单的音节估算：元音组数
            syllables = len(re.findall(r'[aeiouy]+', word))
            # 至少1个音节
            total_syllables += max(1, syllables)
        
        return total_syllables
    
    def _assess_quality(self, data):
        """评估数据质量"""
        quality_assessed = data.copy()
        
        quality_score = 0
        quality_issues = []
        
        # 内容长度检查
        content = data.get('content', '')
        if len(content) < self.min_content_length:
            quality_issues.append("内容过短")
        elif len(content) > self.max_content_length:
            quality_issues.append("内容过长")
        else:
            quality_score += 20
        
        # 统计信息检查
        if data.get('statistics'):
            stats = data['statistics']
            
            # 词数检查
            if stats.get('word_count', 0) >= self.quality_rules['min_word_count']:
                quality_score += 20
            else:
                quality_issues.append("词数不足")
            
            # 句子数检查
            if stats.get('sentence_count', 0) >= self.quality_rules['min_sentence_count']:
                quality_score += 20
            else:
                quality_issues.append("句子数不足")
            
            # 可读性检查
            readability = data.get('readability_score', 0)
            if readability >= self.quality_rules['min_readability_score']:
                quality_score += 20
            else:
                quality_issues.append("可读性较差")
        
        # 标题质量检查
        title = data.get('title', '')
        if len(title) >= 5 and len(title) <= 100:
            quality_score += 10
        else:
            quality_issues.append("标题质量不佳")
        
        # 元数据完整性
        metadata = data.get('metadata', {})
        if metadata.get('category') and metadata.get('language'):
            quality_score += 10
        else:
            quality_issues.append("元数据不完整")
        
        quality_assessed['quality_score'] = quality_score
        quality_assessed['quality_issues'] = quality_issues
        
        return quality_assessed
    
    def _extract_features(self, data):
        """提取特征"""
        features = data.copy()
        
        # 计算内容hash用于去重
        content = data.get('content', '')
        if content:
            features['content_hash'] = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # 提取实体关系
        features['entities'] = self._extract_entities(data.get('medical_terms', []))
        
        # 提取主题标签
        features['tags'] = self._generate_tags(data)
        
        return features
    
    def _extract_entities(self, medical_terms):
        """提取实体"""
        entities = {
            'diseases': [],
            'drugs': [],
            'symptoms': [],
            'procedures': [],
            'anatomies': []
        }
        
        for term_info in medical_terms:
            term = term_info.get('term', '')
            category = term_info.get('category', 'general')
            
            if category == 'disease':
                entities['diseases'].append(term)
            elif category == 'drug':
                entities['drugs'].append(term)
            elif category == 'symptom':
                entities['symptoms'].append(term)
            elif category == 'procedure':
                entities['procedures'].append(term)
            else:
                entities['anatomies'].append(term)
        
        return entities
    
    def _generate_tags(self, data):
        """生成标签"""
        tags = []
        
        # 从关键词生成标签
        keywords = data.get('keywords', [])
        for kw_info in keywords:
            keyword = kw_info.get('keyword', '')
            if keyword and len(keyword) > 2:
                tags.append(keyword)
        
        # 从分类生成标签
        metadata = data.get('metadata', {})
        if metadata.get('category'):
            tags.append(metadata['category'])
        
        # 去重并限制数量
        unique_tags = list(set(tags))[:10]
        
        return unique_tags
    
    def _standardize_format(self, data):
        """标准化数据格式"""
        standardized = data.copy()
        
        # 确保所有字段存在
        required_fields = {
            'title': '',
            'content': '',
            'url': '',
            'category': '',
            'subcategory': '',
            'version': 'home',
            'language': 'en',
            'medical_terms': [],
            'keywords': [],
            'summary': '',
            'quality_score': 0,
            'quality_issues': [],
            'extracted_at': datetime.utcnow().isoformat()
        }
        
        for field, default_value in required_fields.items():
            if field not in standardized:
                standardized[field] = default_value
        
        # 数据类型转换
        if 'word_count' not in standardized:
            standardized['word_count'] = len(standardized['content'].split())
        
        if 'content_hash' not in standardized:
            content = standardized.get('content', '')
            standardized['content_hash'] = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        return standardized

if __name__ == "__main__":
    # 测试数据处理器
    import json
    
    # 模拟原始数据
    test_data = {
        'title': '高血压概述',
        'content': '高血压是一种常见的慢性疾病，指动脉血压持续升高。患者常伴有头痛、头晕等症状。',
        'url': 'https://www.msdmanuals.com/test',
        'metadata': {
            'category': 'cardiovascular-disorders',
            'language': 'zh'
        },
        'medical_terms': [
            {'term': '高血压', 'context': '高血压是一种...', 'frequency': 3},
            {'term': '慢性疾病', 'context': '高血压是一种...', 'frequency': 1}
        ],
        'links': [],
        'media': {}
    }
    
    # 测试处理
    processor = DataProcessor()
    processed_data = processor.process(test_data)
    
    print("处理后的数据:")
    print(json.dumps(processed_data, ensure_ascii=False, indent=2))

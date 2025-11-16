#!/usr/bin/env python3
"""
简化版默沙东诊疗手册爬虫（不依赖外部库）
"""

import os
import sys
import json
import re
import hashlib
import logging
import requests
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleContentParser:
    """简化版内容解析器"""
    
    def __init__(self):
        self.stop_words = {
            'zh': ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '上', '也', '很', '到'],
            'en': ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it', 'for', 'not']
        }
    
    def extract_title(self, html_content, url):
        """提取标题"""
        # 简单的标题提取
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            # 清理标题
            title = re.sub(r'\s*\|.*MSD.*Manuals\s*', '', title)
            title = re.sub(r'\s*\|.*专业版.*\s*', '', title)
            title = title.strip()
            return title if len(title) > 3 else ""
        
        # 尝试从h1提取
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content, re.IGNORECASE)
        if h1_match:
            return h1_match.group(1).strip()
        
        return "未命名页面"
    
    def extract_content(self, html_content):
        """提取正文内容"""
        # 移除脚本和样式
        content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除注释
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # 尝试提取主要内容区域
        main_patterns = [
            r'<main[^>]*>(.*?)</main>',
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in main_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                break
        
        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)
        
        # 解码HTML实体
        html_entities = {
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
            '&quot;': '"', '&#39;': "'", '&mdash;': '—', '&ndash;': '–'
        }
        for entity, char in html_entities.items():
            content = content.replace(entity, char)
        
        # 清理空白
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    def extract_metadata(self, html_content, url):
        """提取元数据"""
        metadata = {
            'url': url,
            'language': 'en',
            'category': '',
            'author': '',
            'version': self._determine_version(url)
        }
        
        # 从meta标签提取
        meta_patterns = [
            (r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', 'description'),
            (r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']*)["\']', 'author'),
            (r'<meta[^>]*name=["\']language["\'][^>]*content=["\']([^"\']*)["\']', 'language')
        ]
        
        for pattern, key in meta_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).strip()
        
        # 从URL提取分类
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        if len(path_parts) > 2:
            category_part = path_parts[2] if len(path_parts) > 2 else ''
            metadata['category'] = category_part
        
        return metadata
    
    def extract_links(self, html_content, base_url):
        """提取链接"""
        links = []
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        
        for match in re.finditer(link_pattern, html_content, re.IGNORECASE):
            href = match.group(1)
            text = match.group(2).strip()
            
            if href and text:
                # 构建完整URL
                full_url = urljoin(base_url, href)
                links.append({
                    'url': full_url,
                    'text': text
                })
        
        return links
    
    def extract_medical_terms(self, content, language='zh'):
        """提取医学术语"""
        terms = []
        
        # 中文医学术语
        if language == 'zh':
            medical_patterns = [
                '高血压', '低血压', '心脏病', '糖尿病', '癌症', '肿瘤', '炎症', '感染',
                '症状', '诊断', '治疗', '预防', '药物', '手术', '检查',
                '医生', '患者', '医院', '急救', '护理', '康复'
            ]
            
            for pattern in medical_patterns:
                if pattern in content:
                    terms.append({
                        'term': pattern,
                        'context': self._get_context(content, pattern),
                        'frequency': content.count(pattern)
                    })
        else:
            # 英文医学术语
            medical_patterns = [
                'disease', 'disorder', 'syndrome', 'diagnosis', 'treatment',
                'symptom', 'medication', 'surgery', 'examination', 'therapy',
                'pathology', 'physiology', 'anatomy', 'cardiology', 'neurology'
            ]
            
            for pattern in medical_patterns:
                if re.search(r'\b' + re.escape(pattern) + r'\b', content, re.IGNORECASE):
                    terms.append({
                        'term': pattern,
                        'context': self._get_context(content, pattern),
                        'frequency': len(re.findall(r'\b' + re.escape(pattern) + r'\b', content, re.IGNORECASE))
                    })
        
        return terms
    
    def _get_context(self, content, term):
        """获取术语上下文"""
        # 简单的上下文提取
        term_pos = content.find(term)
        if term_pos == -1:
            return ""
        
        start = max(0, term_pos - 50)
        end = min(len(content), term_pos + len(term) + 50)
        
        return content[start:end].strip()
    
    def _determine_version(self, url):
        """确定版本"""
        if '/home/' in url:
            return 'home'
        elif '/professional/' in url:
            return 'professional'
        elif 'msdvetmanual.com' in url:
            return 'veterinary'
        return 'home'
    
    def parse(self, url, html_content):
        """解析页面"""
        try:
            # 提取各个部分
            title = self.extract_title(html_content, url)
            content = self.extract_content(html_content)
            metadata = self.extract_metadata(html_content, url)
            links = self.extract_links(html_content, url)
            medical_terms = self.extract_medical_terms(content, metadata.get('language', 'zh'))
            
            # 构建结果
            result = {
                'url': url,
                'title': title,
                'content': content,
                'content_length': len(content),
                'word_count': len(content.split()),
                'metadata': metadata,
                'links': links,
                'medical_terms': medical_terms,
                'extracted_at': datetime.utcnow().isoformat(),
                'content_hash': hashlib.sha256(content.encode('utf-8')).hexdigest()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析失败 {url}: {e}")
            raise

class SimpleDataProcessor:
    """简化版数据处理器"""
    
    def __init__(self):
        self.quality_thresholds = {
            'min_content_length': 50,
            'min_word_count': 10,
            'min_title_length': 3
        }
    
    def process(self, parsed_data):
        """处理数据"""
        try:
            # 数据清洗
            cleaned_data = self._clean_data(parsed_data)
            
            # 质量评估
            quality_assessed_data = self._assess_quality(cleaned_data)
            
            # 特征提取
            feature_data = self._extract_features(quality_assessed_data)
            
            return feature_data
            
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
        
        return cleaned
    
    def _clean_title(self, title):
        """清理标题"""
        # 移除多余的空白
        title = re.sub(r'\s+', ' ', title.strip())
        # 移除商标信息
        title = re.sub(r'\|.*MSD.*Manuals', '', title, flags=re.IGNORECASE)
        return title.strip()
    
    def _clean_content(self, content):
        """清理内容"""
        # 移除重复的换行
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        # 移除过长的空白
        content = re.sub(r'\s{5,}', ' ', content)
        return content.strip()
    
    def _assess_quality(self, data):
        """评估质量"""
        quality_score = 0
        issues = []
        
        # 标题质量检查
        title = data.get('title', '')
        if len(title) >= self.quality_thresholds['min_title_length']:
            quality_score += 25
        else:
            issues.append("标题过短")
        
        # 内容质量检查
        content = data.get('content', '')
        word_count = data.get('word_count', 0)
        if len(content) >= self.quality_thresholds['min_content_length']:
            quality_score += 25
        else:
            issues.append("内容过短")
        
        if word_count >= self.quality_thresholds['min_word_count']:
            quality_score += 25
        else:
            issues.append("词数不足")
        
        # 医学术语质量
        medical_terms = data.get('medical_terms', [])
        if len(medical_terms) >= 3:
            quality_score += 25
        else:
            issues.append("医学术语不足")
        
        data['quality_score'] = quality_score
        data['quality_issues'] = issues
        
        return data
    
    def _extract_features(self, data):
        """提取特征"""
        # 计算关键词（简单版本）
        content = data.get('content', '')
        language = data.get('metadata', {}).get('language', 'zh')
        
        # 简单的关键词提取
        if language == 'zh':
            # 中文字符分词
            import jieba
            words = jieba.lcut(content)
            # 过滤停用词和短词
            stop_words = {'的', '了', '在', '是', '和', '有', '不', '一', '个', '上', '也', '很', '到', '说', '要'}
            keywords = [word for word in words if len(word) >= 2 and word not in stop_words]
        else:
            # 英文单词
            words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
            stop_words = {'the', 'and', 'or', 'but', 'with', 'for', 'in', 'on', 'at', 'to', 'of'}
            keywords = [word for word in words if word not in stop_words]
        
        # 统计频率
        from collections import Counter
        word_freq = Counter(keywords)
        top_keywords = word_freq.most_common(10)
        
        data['keywords'] = [{'keyword': word, 'frequency': freq} for word, freq in top_keywords]
        
        # 生成摘要
        sentences = re.split(r'[.!?。！？]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if sentences:
            data['summary'] = ' '.join(sentences[:3])
        else:
            data['summary'] = content[:200] + '...' if len(content) > 200 else content
        
        return data

class SimpleMSDCrawler:
    """简化版MSD手册爬虫"""
    
    def __init__(self):
        self.parser = SimpleContentParser()
        self.processor = SimpleDataProcessor()
        self.seen_urls = set()
        self.processed_count = 0
        
        # 创建输出目录
        os.makedirs('data/output', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    def is_allowed_url(self, url):
        """检查URL是否允许爬取"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # 允许的域名
        allowed_domains = [
            'www.msdmanuals.com',
            'www.msdmanuals.cn',
            'www.msdvetmanual.com'
        ]
        
        if domain not in allowed_domains:
            return False
        
        # 禁止的路径
        disallowed_paths = [
            '/sitecore/', '/custom/', '/news/external/',
            '/multimedia/zk/', '/downloadtextfile'
        ]
        
        for path in disallowed_paths:
            if path in parsed_url.path.lower():
                return False
        
        return True
    
    def crawl_url(self, url, delay=5):
        """爬取单个URL"""
        try:
            logger.info(f"正在爬取: {url}")
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 发送请求
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 解析内容
            parsed_data = self.parser.parse(url, response.text)
            
            # 处理数据
            processed_data = self.processor.process(parsed_data)
            
            # 保存数据
            self._save_data(processed_data)
            
            # 延迟
            import time
            time.sleep(delay)
            
            self.processed_count += 1
            logger.info(f"✅ 成功处理: {url} (共 {self.processed_count} 个)")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ 爬取失败 {url}: {e}")
            return None
    
    def _save_data(self, data):
        """保存数据"""
        try:
            # 生成文件名
            url_hash = hashlib.md5(data['url'].encode('utf-8')).hexdigest()[:8]
            filename = f"data/output/article_{url_hash}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 数据已保存: {filename}")
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
    
    def discover_urls(self, base_url, html_content):
        """发现新URL"""
        new_urls = []
        
        # 提取链接
        links = self.parser.extract_links(html_content, base_url)
        
        for link in links:
            url = link['url']
            text = link.get('text', '').lower()
            
            # 检查URL质量
            if not self.is_allowed_url(url):
                continue
            
            if url in self.seen_urls:
                continue
            
            # 过滤低质量链接
            skip_patterns = [
                'mailto:', 'tel:', 'javascript:', '#',
                'login', 'register', 'search?', 'subscribe'
            ]
            
            if any(pattern in url.lower() for pattern in skip_patterns):
                continue
            
            # 优先医学相关链接
            medical_keywords = [
                'health', 'medical', 'disease', 'disorder', 'symptom',
                'treatment', 'diagnosis', 'health-topics', 'cardiovascular',
                '神经', '心脏', '疾病', '症状', '治疗', '诊断'
            ]
            
            is_medical = any(keyword in text or keyword in url.lower() for keyword in medical_keywords)
            
            new_urls.append({
                'url': url,
                'priority': 1 if is_medical else 2,
                'source_url': base_url
            })
            
            self.seen_urls.add(url)
        
        # 按优先级排序
        new_urls.sort(key=lambda x: x['priority'])
        
        return new_urls
    
    def run(self, start_urls, max_pages=10):
        """运行爬虫"""
        logger.info(f"🚀 开始爬虫任务: {len(start_urls)} 个起始URL，最多处理 {max_pages} 页")
        
        url_queue = []
        for url in start_urls:
            url_queue.append({'url': url, 'priority': 1, 'source_url': None})
        
        processed_data = []
        
        try:
            while url_queue and self.processed_count < max_pages:
                current_url_info = url_queue.pop(0)
                current_url = current_url_info['url']
                
                # 爬取当前URL
                result = self.crawl_url(current_url, delay=5)
                
                if result:
                    processed_data.append(result)
                    
                    # 发现新URL（需要获取HTML内容）
                    try:
                        response = requests.get(current_url, timeout=30)
                        if response.status_code == 200:
                            new_urls = self.discover_urls(current_url, response.text)
                            url_queue.extend(new_urls)
                    except:
                        pass  # 忽略URL发现错误
                
                # 定期保存进度
                if self.processed_count % 5 == 0:
                    self._save_progress()
        
        except KeyboardInterrupt:
            logger.info("用户中断，保存当前进度...")
        
        except Exception as e:
            logger.error(f"爬虫运行错误: {e}")
        
        finally:
            # 保存最终结果
            self._save_final_results(processed_data)
            
            logger.info(f"🎉 爬虫完成! 总计处理 {self.processed_count} 个页面")
            return processed_data
    
    def _save_progress(self):
        """保存进度"""
        progress = {
            'processed_count': self.processed_count,
            'seen_urls_count': len(self.seen_urls),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        with open('logs/crawler_progress.json', 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def _save_final_results(self, data_list):
        """保存最终结果"""
        # 保存所有数据
        final_data = {
            'summary': {
                'total_pages': len(data_list),
                'crawled_at': datetime.utcnow().isoformat(),
                'quality_scores': [d.get('quality_score', 0) for d in data_list]
            },
            'articles': data_list
        }
        
        with open('data/output/crawler_results.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 最终结果已保存到: data/output/crawler_results.json")

def main():
    """主函数"""
    print("🔍 简化版默沙东诊疗手册爬虫")
    print("=" * 50)
    
    # 创建爬虫
    crawler = SimpleMSDCrawler()
    
    # 测试URLs
    test_urls = [
        'https://www.msdmanuals.com/home/',
        'https://www.msdmanuals.com/home/health-topics/'
    ]
    
    try:
        # 运行爬虫（只处理2页进行演示）
        results = crawler.run(test_urls, max_pages=2)
        
        print(f"\\n📊 爬取结果汇总:")
        print(f"- 处理页面数: {len(results)}")
        
        if results:
            print(f"- 平均质量评分: {sum(d.get('quality_score', 0) for d in results) / len(results):.1f}")
            print(f"- 总医学术语数: {sum(len(d.get('medical_terms', [])) for d in results)}")
            print(f"- 总词数: {sum(d.get('word_count', 0) for d in results)}")
        
        print(f"\\n📁 输出文件:")
        print(f"- 详细数据: data/output/")
        print(f"- 汇总结果: data/output/crawler_results.json")
        print(f"- 进度日志: logs/crawler_progress.json")
        
    except Exception as e:
        logger.error(f"爬虫运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

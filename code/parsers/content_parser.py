#!/usr/bin/env python3
"""
医学内容解析器
"""

import re
import html
import logging
from collections import Counter
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class MSDContentParser:
    """默沙东诊疗手册内容解析器"""
    
    def __init__(self):
        """初始化解析器"""
        # 医学术语模式
        self.medical_patterns = {
            'disease': [
                r'(?:病|症|综合征|疾病|失调|症状|异常)',
                r'disease|disorder|syndrome|symptom|condition'
            ],
            'drug': [
                r'(?:药物|药|片|丸|胶囊|注射|口服)',
                r'drug|medication|medicine|therapeutic|treatment'
            ],
            'procedure': [
                r'(?:手术|检查|测试|操作|程序)',
                r'surgery|procedure|examination|test|operation'
            ],
            'anatomy': [
                r'(?:心脏|肝脏|肾脏|肺部|大脑|血管|神经|肌肉)',
                r'heart|liver|kidney|lung|brain|vessel|nerve|muscle|organ'
            ]
        }
        
        # 日期模式
        self.date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(\d{4}-\d{1,2}-\d{1,2})',  # YYYY-MM-DD
            r'(reviewed\s+by\s+[\w\s,]+)',
            r'(modified\s+(\w+\s+\d{4}))'
        ]
        
        # 文本清理模式
        self.cleanup_patterns = [
            (r'<script[^>]*>.*?</script>', ''),  # 移除脚本
            (r'<style[^>]*>.*?</style>', ''),    # 移除样式
            (r'<!--.*?-->', ''),                 # 移除注释
            (r'\n\s*\n', '\n'),                  # 多个换行
            (r' +', ' ')                         # 多个空格
        ]
    
    def parse(self, response):
        """解析响应内容
        
        Args:
            response: requests响应对象
            
        Returns:
            dict: 解析后的数据
        """
        try:
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取基础信息
            title = self._extract_title(soup)
            content_info = self._extract_content(soup)
            if not content_info:
                content_info = {
                    'text': '',
                    'word_count': 0,
                    'is_landing_page': False
                }
            if content_info.get('is_landing_page'):
                return None
            content = content_info.get('text', '')
            metadata = self._extract_metadata(soup, response.url)
            metadata['language'] = self._deduce_language(
                metadata.get('language', ''), response.url, soup, content
            )
            navigation = self._extract_navigation(soup)
            links = self._extract_links_from_soup(soup, response.url)
            
            # 提取医学术语
            medical_terms = self._extract_medical_terms(content, metadata.get('language', 'en'))
            
            # 提取图片和媒体
            media = self._extract_media(soup, response.url)
            
            # 构建结果
            parsed_data = {
                'url': response.url,
                'title': title,
                'content': content,
                'content_html': str(soup.find('main') or soup.find('article') or soup),
                'metadata': metadata,
                'navigation': navigation,
                'links': links,
                'medical_terms': medical_terms,
                'media': media,
                'word_count': content_info.get('word_count', len(content.split())),
                'extracted_at': datetime.utcnow().isoformat()
            }
            valid, validation_issues = self._validate_data(parsed_data)
            parsed_data['validation'] = {
                'valid': valid,
                'issues': validation_issues,
                'metadata_snapshot': metadata.copy()
            }

            if not valid:
                metadata_summary = {
                    key: metadata.get(key)
                    for key in ('language', 'category', 'version')
                    if metadata.get(key)
                }
                logger.warning(
                    "数据验证失败: %s | issues=%s | metadata=%s",
                    response.url,
                    validation_issues,
                    metadata_summary or {}
                )

            return parsed_data
            
        except Exception as e:
            logger.error(f"解析页面失败 {response.url}: {e}")
            raise
    
    def _extract_title(self, soup):
        """提取标题"""
        # 尝试多种标题选择器
        title_selectors = [
            'h1',
            '.page-title',
            '.article-title',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                # 清理标题文本
                title = title_elem.get_text().strip()
                title = self._clean_text(title)
                if len(title) > 10:  # 确保标题有意义
                    return title
        
        # 如果没有找到，返回空字符串
        return ""
    
    def _extract_content(self, soup):
        """提取正文内容"""
        # 尝试多种内容选择器
        content_selectors = [
            'main .content',
            'article .content',
            '.main-content',
            '.article-body',
            'main',
            'article'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = self._extract_text_content(content_elem)
                word_count = len(content.split())
                if len(content) > 100:  # 确保内容有意义
                    return {
                        'text': content,
                        'word_count': word_count,
                        'selector': selector,
                        'fallback': False,
                        'is_landing_page': False
                    }
        
        # 如果没有找到主要内容区域，尝试获取body
        body = soup.find('body')
        if body:
            text = self._extract_text_content(body)
            word_count = len(text.split())
            return {
                'text': text,
                'word_count': word_count,
                'selector': 'body',
                'fallback': True,
                'is_landing_page': self._is_nav_heavy_fallback(soup, text, word_count)
            }
        
        return {
            'text': '',
            'word_count': 0,
            'selector': None,
            'fallback': False,
            'is_landing_page': False
        }

    def _is_nav_heavy_fallback(self, soup, text, word_count):
        """判断在回退到 body 时是否为导航/摘要页面"""
        if not text or word_count == 0:
            return True

        if soup.find('main') or soup.find('article'):
            return False

        nav_words = []
        for nav in soup.find_all('nav'):
            nav_text = self._clean_text(nav.get_text())
            if nav_text:
                nav_words.extend([token for token in nav_text.split() if token])

        nav_word_count = len(nav_words)
        nav_ratio = nav_word_count / max(word_count, 1)
        repeated_ratio = self._max_token_repeat_ratio(text.lower().split())

        low_word_content = word_count < 32
        nav_dominated = nav_word_count > 0 and nav_ratio > 0.45
        repeated_pattern = repeated_ratio > 0.55

        return low_word_content and (nav_dominated or repeated_pattern)

    def _max_token_repeat_ratio(self, tokens):
        """计算最常见词在文本中所占比例"""
        tokens = [token for token in tokens if token]
        if not tokens:
            return 1.0

        counter = Counter(tokens)
        most_common = counter.most_common(1)[0][1]
        return most_common / len(tokens)
    
    def _extract_text_content(self, element):
        """从元素中提取文本内容"""
        # 移除不需要的元素
        for unwanted in element.find_all(['script', 'style', 'nav', 'footer', 'aside']):
            unwanted.decompose()
        
        # 获取文本
        text = element.get_text()
        
        # 清理文本
        text = self._clean_text(text)
        
        return text
    
    def _clean_text(self, text):
        """清理文本"""
        # HTML解码
        text = html.unescape(text)
        
        # 应用清理模式
        for pattern, replacement in self.cleanup_patterns:
            text = re.sub(pattern, replacement, text, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _extract_metadata(self, soup, url):
        """提取元数据"""
        metadata = {
            'url': url,
            'language': 'en',  # 默认语言
            'version': self._determine_version(url),
            'category': '',
            'subcategory': '',
            'author': '',
            'last_reviewed': None,
            'published_date': None,
            'description': '',
            'keywords': []
        }
        
        # 从meta标签提取
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            content = meta.get('content', '')
            
            if name == 'description':
                metadata['description'] = self._clean_text(content)
            elif name == 'keywords':
                keywords = [k.strip() for k in content.split(',')]
                metadata['keywords'] = keywords
            elif name == 'language':
                metadata['language'] = content
        
        # 从URL提取分类信息
        path_parts = urlparse(url).path.split('/')
        if len(path_parts) > 2:
            # URL模式: /[version]/[category]/[subcategory]/[topic]
            version_part = path_parts[1] if len(path_parts) > 1 else ''
            category_part = path_parts[2] if len(path_parts) > 2 else ''
            
            metadata['version'] = version_part or metadata['version']
            metadata['category'] = category_part
        
        # 从页面内容提取作者和日期
        page_text = soup.get_text()
        
        # 提取审核信息
        review_match = re.search(r'reviewed\s+by\s+([^.]+)', page_text, re.IGNORECASE)
        if review_match:
            metadata['author'] = review_match.group(1).strip()
        
        # 提取修改日期
        for pattern in self.date_patterns:
            date_match = re.search(pattern, page_text, re.IGNORECASE)
            if date_match:
                try:
                    metadata['last_reviewed'] = self._parse_date(date_match.group())
                    break
                except:
                    continue
        
        return metadata

    def _deduce_language(self, declared_language, url, soup, content):
        """基于元数据、HTML lang或文本内容推断语言"""
        normalized = (declared_language or '').strip().lower()
        if normalized.startswith('zh'):
            return 'zh'

        html_lang = self._get_html_lang(soup)
        if html_lang and html_lang.startswith('zh'):
            return 'zh'

        parsed_url = urlparse(url)
        netloc = parsed_url.netloc.lower()
        if netloc.endswith('.cn') or 'msdmanuals.cn' in netloc:
            return 'zh'

        if self._has_chinese_text(content):
            return 'zh'

        return 'en'

    def _get_html_lang(self, soup):
        """提取HTML标签中的lang属性"""
        html_tag = soup.find('html')
        if html_tag:
            lang = html_tag.get('lang', '')
            if lang:
                return lang.strip().lower()
        return ''

    def _has_chinese_text(self, content, min_chars=20, ratio=0.15):
        """判断文本中是否包含足够的中文字符"""
        if not content:
            return False

        chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
        if len(chinese_chars) < min_chars:
            return False

        return len(chinese_chars) / max(len(content), 1) >= ratio

    def _determine_version(self, url):
        """从URL确定版本"""
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        
        if '/home/' in url:
            return 'home'
        elif '/professional/' in url:
            return 'professional'
        elif 'msdvetmanual.com' in parsed_url.netloc:
            return 'veterinary'
        
        return 'home'
    
    def _extract_navigation(self, soup):
        """提取导航信息"""
        navigation = {
            'breadcrumb': [],
            'related_links': [],
            'next_previous': {'next': None, 'previous': None}
        }
        
        # 面包屑导航
        breadcrumb_elem = soup.find('nav', class_=re.compile(r'breadcrumb|nav')) or \
                         soup.find(class_=re.compile(r'breadcrumb|nav'))
        
        if breadcrumb_elem:
            breadcrumb_links = breadcrumb_elem.find_all('a')
            for link in breadcrumb_links:
                text = self._clean_text(link.get_text())
                href = link.get('href')
                if text and href:
                    navigation['breadcrumb'].append({
                        'text': text,
                        'url': href
                    })
        
        # 相关链接
        related_elem = soup.find(class_=re.compile(r'related|suggested|related-articles'))
        if related_elem:
            related_links = related_elem.find_all('a')
            for link in related_links:
                text = self._clean_text(link.get_text())
                href = link.get('href')
                if text and href:
                    navigation['related_links'].append({
                        'text': text,
                        'url': href
                    })
        
        return navigation
    
    def _extract_links_from_soup(self, soup, base_url):
        """从soup对象提取链接"""
        links = []
        
        # 查找所有链接
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            text = self._clean_text(a_tag.get_text())
            
            if href and text:
                # 构建完整URL
                full_url = urljoin(base_url, href)
                
                # 确定链接类型
                link_type = self._classify_link(href, text)
                
                links.append({
                    'url': full_url,
                    'text': text,
                    'type': link_type,
                    'source_element': str(a_tag.parent.name) if a_tag.parent else 'unknown'
                })
        
        return links
    
    def _classify_link(self, href, text):
        """分类链接类型"""
        href_lower = href.lower()
        text_lower = text.lower()
        
        # 基于URL和文本内容分类
        if 'multimedia' in href_lower or 'video' in text_lower:
            return 'media'
        elif any(keyword in text_lower for keyword in ['download', 'pdf']):
            return 'download'
        elif any(keyword in text_lower for keyword in ['related', 'similar', 'more']):
            return 'related'
        elif 'home' in href_lower or 'professional' in href_lower:
            return 'navigation'
        else:
            return 'content'
    
    def _extract_medical_terms(self, content, language):
        """提取医学术语"""
        medical_terms = []
        
        # 按语言使用不同的处理方式
        if language == 'zh':
            # 中文医学术语处理
            medical_terms = self._extract_chinese_terms(content)
        else:
            # 英文医学术语处理
            medical_terms = self._extract_english_terms(content)
        
        return medical_terms
    
    def _extract_chinese_terms(self, content):
        """提取中文医学术语"""
        terms = []
        
        # 常见医学术语模式
        patterns = [
            r'(?:高血压|低血压|心脏病|糖尿病|癌症|肿瘤|炎症|感染)',
            r'(?:症状|诊断|治疗|预防|药物|手术|检查)',
            r'(?:医生|患者|医院|诊所|急救|护理)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) > 2:  # 确保术语有意义
                    terms.append({
                        'term': match,
                        'context': self._extract_context(content, match),
                        'frequency': content.count(match)
                    })
        
        return terms
    
    def _extract_english_terms(self, content):
        """提取英文医学术语"""
        terms = []
        
        # 使用医学术语词典
        medical_keywords = [
            'disease', 'disorder', 'syndrome', 'diagnosis', 'treatment',
            'symptom', 'medication', 'surgery', 'examination', 'therapy',
            'pathology', 'physiology', 'anatomy', 'cardiology', 'neurology'
        ]
        
        for keyword in medical_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                terms.append({
                    'term': keyword,
                    'context': self._extract_context(content, keyword),
                    'frequency': len(matches)
                })
        
        return terms
    
    def _extract_context(self, content, term):
        """提取术语周围的上下文"""
        # 找到术语在文本中的位置
        start_pos = content.lower().find(term.lower())
        if start_pos == -1:
            return ""
        
        # 提取前后各50个字符作为上下文
        context_start = max(0, start_pos - 50)
        context_end = min(len(content), start_pos + len(term) + 50)
        
        context = content[context_start:context_end].strip()
        return context
    
    def _extract_media(self, soup, base_url):
        """提取媒体资源"""
        media = {
            'images': [],
            'videos': [],
            'downloads': []
        }
        
        # 提取图片
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            alt = img.get('alt', '')
            if src:
                full_url = urljoin(base_url, src)
                media['images'].append({
                    'url': full_url,
                    'alt': self._clean_text(alt),
                    'type': 'image'
                })
        
        # 提取视频
        for video in soup.find_all(['video', 'iframe']):
            src = video.get('src') or video.get('data-src')
            if src:
                full_url = urljoin(base_url, src)
                media['videos'].append({
                    'url': full_url,
                    'type': 'video'
                })
        
        # 提取下载链接
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and any(ext in href.lower() for ext in ['.pdf', '.doc', '.xls']):
                full_url = urljoin(base_url, href)
                media['downloads'].append({
                    'url': full_url,
                    'text': self._clean_text(link.get_text())
                })
        
        return media
    
    def _parse_date(self, date_str):
        """解析日期字符串"""
        # 简单的日期解析
        try:
            # 尝试多种日期格式
            import dateparser
            
            # 使用dateparser库解析
            parsed_date = dateparser.parse(date_str)
            if parsed_date:
                return parsed_date.isoformat()
            
        except:
            pass
        
        # 如果解析失败，返回当前日期
        return datetime.utcnow().isoformat()
    
    def _validate_data(self, data):
        """验证解析数据的质量"""
        issues = []

        # 检查必需字段
        if not data.get('title') or len(data['title']) < 5:
            issues.append('标题缺失或长度不足')
        
        if not data.get('content') or len(data['content']) < 50:
            issues.append('内容缺失或长度不足')
        
        # 检查内容质量
        word_count = data.get('word_count', 0)
        if word_count < 10:  # 至少10个词
            issues.append('词数不足')

        return len(issues) == 0, issues
    
    def extract_links(self, response):
        """提取链接（兼容性方法）"""
        soup = BeautifulSoup(response.content, 'html.parser')
        return {
            'links': self._extract_links_from_soup(soup, response.url)
        }

if __name__ == "__main__":
    # 测试解析器
    import requests
    
    # 测试URL
    test_urls = [
        'https://www.msdmanuals.com/home/',
        'https://www.msdmanuals.com/home/health-topics/'
    ]
    
    parser = MSDContentParser()
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            parsed_data = parser.parse(response)
            
            print(f"\\n=== URL: {url} ===")
            print(f"标题: {parsed_data['title']}")
            print(f"内容长度: {len(parsed_data['content'])} 字符")
            print(f"医学术语: {len(parsed_data['medical_terms'])} 个")
            print(f"链接数量: {len(parsed_data['links'])} 个")
            
        except Exception as e:
            print(f"测试失败 {url}: {e}")

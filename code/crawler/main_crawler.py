#!/usr/bin/env python3
"""
默沙东诊疗手册主爬虫类
"""

import os
import sys
import json
import time
import hashlib
import logging
import requests
import random
from urllib.parse import urljoin, urlparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from config.crawler_config import *
from database.setup_database import DatabaseManager
from database.models import Article as ArticleModel
from parsers.content_parser import MSDContentParser
from processors.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class CrawlerState:
    """爬虫状态管理"""

    def __init__(self, state_file="crawler_state.json"):
        self.state_file = state_file
        self.state = self._default_state()
        self.load_state()

    def _default_state(self):
        """生成默认状态结构"""
        return {
            "last_saved": None,
            "urls_processed": 0,
            "successful_downloads": 0,
            "landing_pages_skipped": 0,
            "failed_downloads": 0,
            "parse_errors": 0,
            "duplicates_found": 0,
            "new_articles_created": 0,
            "existing_articles_updated": 0,
            "processing_time": 0.0,
            "current_url": None,
            "error_log": [],
            "processed_urls": set(),
            "failed_urls": set(),
            "checkpoint_urls": []
        }
    
    def save_state(self):
        """保存爬虫状态"""
        try:
            self.state["last_saved"] = datetime.now().isoformat()
            # 将set转换为list用于JSON序列化
            state_copy = self.state.copy()
            state_copy["processed_urls"] = list(self.state["processed_urls"])
            state_copy["failed_urls"] = list(self.state["failed_urls"])

            state_dir = os.path.dirname(self.state_file)
            if state_dir:
                os.makedirs(state_dir, exist_ok=True)

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_copy, f, ensure_ascii=False, indent=2)

            logger.info(f"状态已保存: {self.state_file}")
            
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def load_state(self):
        """加载爬虫状态"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    saved_state = json.load(f)
                
                # 恢复set类型
                self.state.update(saved_state)
                self.state["processed_urls"] = set(self.state["processed_urls"])
                self.state["failed_urls"] = set(self.state["failed_urls"])

                logger.info(f"已加载状态: 已处理 {len(self.state['processed_urls'])} 个URL")
                
        except Exception as e:
            logger.warning(f"加载状态失败: {e}，使用默认状态")
    
    def update_stats(self, **kwargs):
        """更新统计数据"""
        for key, value in kwargs.items():
            if key in self.state:
                self.state[key] += value
    
    def add_processed_url(self, url):
        """添加已处理的URL"""
        self.state["processed_urls"].add(url)
        self.state["urls_processed"] = len(self.state["processed_urls"])
    
    def add_failed_url(self, url, error_msg=""):
        """添加失败的URL"""
        self.state["failed_urls"].add(url)
        self.state["error_log"].append({
            "url": url,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        })

    def reset(self):
        """重置状态，便于重新开始爬取"""
        self.state = self._default_state()
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except OSError as exc:
                logger.warning(f"删除旧状态文件失败: {exc}")
        logger.info("爬虫状态已重置")

class MSDManualsCrawler:
    """默沙东诊疗手册爬虫"""
    
    def __init__(self, config_path=None):
        """初始化爬虫"""
        self.config = self._load_config(config_path)
        self.db_manager = DatabaseManager(use_sqlite=True)
        self.content_parser = MSDContentParser()
        self.data_processor = DataProcessor()

        # 状态管理
        state_config = self.config.get('state', {})
        self.state_manager = CrawlerState(state_file=state_config.get('state_file', 'crawler_state.json'))

        # 支持的语言-版本配置
        self.language_versions = self.config.get('language_versions', {})
        
        # 请求会话
        self.session = requests.Session()
        self._setup_session()
        
        # URL队列和去重
        self.url_queue = []
        self.seen_urls = set()
        
        # 性能监控
        self.start_time = None
        self.stats = defaultdict(int)
        self._landing_page_skip_logged = False
        
        logger.info("爬虫初始化完成")
    
    def _load_config(self, config_path):
        """加载配置文件"""
        if config_path and os.path.exists(config_path):
            # 动态导入配置文件
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)

            return {
                'crawler': config_module.CRAWLER_CONFIG,
                'user_agents': config_module.USER_AGENTS,
                'headers': config_module.DEFAULT_HEADERS,
                'domain_configs': config_module.DOMAIN_CONFIGS,
                'retry': config_module.RETRY_CONFIG,
                'state': config_module.STATE_CONFIG,
                'language_versions': getattr(config_module, 'LANGUAGE_VERSION_URLS', {})
            }
        else:
            # 使用默认配置
            return {
                'crawler': CRAWLER_CONFIG,
                'user_agents': USER_AGENTS,
                'headers': DEFAULT_HEADERS,
                'domain_configs': DOMAIN_CONFIGS,
                'retry': RETRY_CONFIG,
                'state': STATE_CONFIG,
                'language_versions': LANGUAGE_VERSION_URLS
            }
    
    def _setup_session(self):
        """设置请求会话"""
        # 设置默认头部
        self.session.headers.update(self.config['headers'])
        
        # 设置Cookie处理
        self.session.cookies.clear()
    
    def _get_random_user_agent(self):
        """获取随机用户代理"""
        return random.choice(self.config['user_agents'])
    
    def _get_domain_delay(self, url):
        """获取域名特定的延迟时间"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # 默认延迟
        delay = self.config['crawler']['delay_between_requests']
        
        # 域名特定配置
        if domain in self.config['domain_configs']:
            delay = self.config['domain_configs'][domain].get('delay', delay)
        
        # 添加随机化
        if self.config['crawler']['randomize_download_delay']:
            import random
            min_delay, max_delay = self.config['crawler']['download_delay_range']
            delay = random.uniform(min_delay, max_delay)
        
        return delay
    
    def _is_allowed_url(self, url):
        """检查URL是否允许爬取"""
        parsed_url = urlparse(url)
        
        # 检查域名
        domain = parsed_url.netloc.lower()
        allowed_domains = [cfg.lower() for cfg in self.config['domain_configs'].keys()]
        
        if domain not in allowed_domains:
            return False
        
        # 检查路径
        path = parsed_url.path.lower()
        disallowed_paths = [
            '/sitecore/',
            '/custom/',
            '/news/external/',
            '/multimedia/zk/',
            '/downloadtextfile',
            '/pagerevalidation',
            '/bigqueryexport'
        ]
        
        for disallowed in disallowed_paths:
            if disallowed in path:
                return False
        
        return True
    
    def _download_page(self, url):
        """下载网页"""
        try:
            # 设置用户代理
            self.session.headers['User-Agent'] = self._get_random_user_agent()
            
            # 获取延迟时间
            delay = self._get_domain_delay(url)
            
            logger.debug(f"正在下载: {url}")
            
            # 发送请求
            response = self.session.get(
                url,
                timeout=self.config['crawler']['timeout'],
                allow_redirects=True
            )
            
            # 检查响应
            response.raise_for_status()
            
            # 延迟
            time.sleep(delay)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"下载失败 {url}: {e}")
            raise
    
    def _parse_page(self, response):
        """解析页面内容"""
        try:
            # 使用内容解析器解析
            parsed_data = self.content_parser.parse(response)

            if parsed_data is None:
                self.stats['landing_pages_skipped'] += 1
                if not self._landing_page_skip_logged:
                    logger.info(
                        "跳过疑似导航/概览页: %s (本次运行只记录首次跳过事件)", response.url
                    )
                    self._landing_page_skip_logged = True
                return None
            
            # 处理和验证数据
            processed_data = self.data_processor.process(parsed_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"解析失败 {response.url}: {e}")
            raise
    
    def _save_to_database(self, data):
        """保存数据到数据库"""
        session = self.db_manager.get_session()

        try:
            existing_article = session.query(ArticleModel).filter_by(url=data['url']).first()

            content_hash = hashlib.sha256(data.get('content', '').encode('utf-8')).hexdigest()

            if existing_article:
                existing_article.title = data.get('title', existing_article.title)
                existing_article.content = data.get('content', existing_article.content)
                existing_article.category = data.get('category', existing_article.category)
                existing_article.subcategory = data.get('subcategory', existing_article.subcategory)
                existing_article.language = data.get('language', existing_article.language)
                existing_article.version = data.get('version', existing_article.version)
                existing_article.hash_content = content_hash
                existing_article.word_count = len(data.get('content', '').split()) if data.get('content') else existing_article.word_count
                existing_article.updated_at = datetime.utcnow()
                self.state_manager.update_stats(existing_articles_updated=1)
            else:
                article = ArticleModel(
                    url=data['url'],
                    title=data.get('title', ''),
                    content=data.get('content', ''),
                    category=data.get('category', ''),
                    subcategory=data.get('subcategory', ''),
                    version=data.get('version', 'home'),
                    language=data.get('language', 'en'),
                    hash_content=content_hash,
                    word_count=len(data.get('content', '').split()) if data.get('content') else 0
                )
                session.add(article)
                self.state_manager.update_stats(new_articles_created=1)

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"保存数据失败: {e}")
            raise
        finally:
            session.close()
    
    def discover_urls(self, response):
        """发现新的URL"""
        parsed_data = self.content_parser.extract_links(response)
        
        urls = []
        for link_data in parsed_data.get('links', []):
            url = link_data.get('url')
            text = link_data.get('text', '')
            
            if url and self._is_allowed_url(url):
                # 构建完整URL
                full_url = urljoin(response.url, url)
                
                if full_url not in self.seen_urls and full_url not in self.state_manager.state['processed_urls']:
                    urls.append({
                        'url': full_url,
                        'text': text,
                        'source_url': response.url
                    })
                    self.seen_urls.add(full_url)
        
        return urls
    
    def get_language_version_pairs(self, language=None, version=None):
        """获取支持的语言-版本组合"""
        pairs = []

        for version_name, languages in self.language_versions.items():
            if version and version not in ('all', version_name):
                continue

            for lang_code in languages.keys():
                if language and language not in ('all', lang_code):
                    continue
                pairs.append((lang_code, version_name))

        return pairs

    def run(self, language='en', version='home', max_pages=1000, output_dir=None, reset_state=False):
        """运行爬虫"""
        logger.info(f"开始爬取: 语言={language}, 版本={version}, 最大页面={max_pages}")

        self.start_time = time.time()

        if reset_state:
            self.state_manager.reset()

        # 清理队列和已见URL，确保多次运行互不影响
        self.url_queue = []
        self.seen_urls.clear()

        # 初始化目标URLs
        self._initialize_urls(language, version)
        
        pages_crawled = 0
        
        try:
            while self.url_queue and pages_crawled < max_pages:
                current_url_info = self.url_queue.pop(0)
                current_url = current_url_info['url']
                
                # 检查是否已处理
                if current_url in self.state_manager.state['processed_urls']:
                    continue
                
                try:
                    logger.info(f"正在处理 ({pages_crawled + 1}/{max_pages}): {current_url}")
                    
                    # 下载页面
                    response = self._download_page(current_url)
                    
                    # 解析内容
                    parsed_data = self._parse_page(response)
                    landing_skipped = parsed_data is None

                    # 保存数据（导航/概览页不保存）
                    if not landing_skipped:
                        self._save_to_database(parsed_data)

                    # 发现新URLs
                    new_urls = self.discover_urls(response)
                    self.url_queue.extend(new_urls)

                    # 更新统计
                    stats_update = {'urls_processed': 1}
                    if landing_skipped:
                        stats_update['landing_pages_skipped'] = 1
                    else:
                        stats_update['successful_downloads'] = 1
                    self.state_manager.update_stats(**stats_update)

                    pages_crawled += 1
                    
                    # 定期保存状态
                    if pages_crawled % self.config['state']['save_interval'] == 0:
                        self.state_manager.save_state()
                        logger.info(f"已保存状态，已处理 {pages_crawled} 页")
                    
                except Exception as e:
                    logger.error(f"处理URL失败 {current_url}: {e}")
                    self.state_manager.add_failed_url(current_url, str(e))
                    self.state_manager.update_stats(failed_downloads=1)
                
                # 强制保存已处理URL
                self.state_manager.add_processed_url(current_url)
        
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在保存状态...")
        
        except Exception as e:
            logger.error(f"爬虫运行错误: {e}")
        
        finally:
            # 计算处理时间
            processing_time = time.time() - self.start_time
            self.state_manager.state["processing_time"] = processing_time
            
            # 保存最终状态
            self.state_manager.save_state()
            
            # 生成报告
            self._generate_report()
            
            logger.info(f"爬虫完成: 总计处理 {pages_crawled} 页，耗时 {processing_time:.2f} 秒")
    
    def _initialize_urls(self, language, version):
        """初始化目标URLs"""
        version_config = self.language_versions.get(version, {})
        language_entry = version_config.get(language)

        if not language_entry:
            raise ValueError(f"不支持的语言-版本组合: {language}-{version}")

        if isinstance(language_entry, str):
            language_entry = {'start_url': language_entry}

        start_url = language_entry['start_url']

        self.url_queue.append({
            'url': start_url,
            'text': '主页',
            'source_url': None
        })

        for extra_url in language_entry.get('extra_urls', []):
            target_url = extra_url if extra_url.startswith('http') else urljoin(start_url, extra_url)
            if target_url == start_url:
                continue
            self.url_queue.append({
                'url': target_url,
                'text': '附加入口',
                'source_url': start_url
            })

        logger.info(f"已初始化起始URLs: {len(self.url_queue)} 个")
    
    def _generate_report(self):
        """生成爬取报告"""
        state = self.state_manager.state
        
        report = f"""
        📊 爬虫执行报告
        ================
        
        总体统计:
        - 开始时间: {self.start_time}
        - 处理时间: {state['processing_time']:.2f} 秒
        - 已处理URLs: {state['urls_processed']}
        - 成功下载: {state['successful_downloads']}
        - 跳过导航页: {state['landing_pages_skipped']}
        - 下载失败: {state['failed_downloads']}
        - 解析错误: {state['parse_errors']}
        - 重复发现: {state['duplicates_found']}
        - 新建文章: {state['new_articles_created']}
        - 更新文章: {state['existing_articles_updated']}
        
        性能指标:
        - 平均响应时间: {state['processing_time'] / max(state['urls_processed'], 1):.2f} 秒/页
        - 错误率: {(state['failed_downloads'] / max(state['urls_processed'], 1)) * 100:.2f}%
        - 成功率: {(state['successful_downloads'] / max(state['urls_processed'], 1)) * 100:.2f}%
        
        错误详情:
        """
        
        if state['error_log']:
            report += "\\n最近的错误:"
            for error in state['error_log'][-10:]:  # 显示最近10个错误
                report += f"\\n  - {error['url']}: {error['error']}"
        
        logger.info(report)
        
        # 保存报告到文件
        report_file = f"logs/crawler_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"报告已保存到: {report_file}")

if __name__ == "__main__":
    # 测试爬虫
    crawler = MSDManualsCrawler()
    
    # 爬取少量页面进行测试
    crawler.run(language='zh', version='home', max_pages=10)

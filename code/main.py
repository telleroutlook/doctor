#!/usr/bin/env python3
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

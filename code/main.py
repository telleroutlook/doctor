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
from quality.data_quality_checker import DataQualityChecker

def setup_logging():
    """设置日志配置"""
    log_dir = project_root / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'crawler.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='默沙东诊疗手册爬虫系统')
    parser.add_argument('command', choices=['crawl', 'setup-db', 'api', 'search', 'test', 'quality-check'],
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
    parser.add_argument('--reset-state', action='store_true',
                       help='运行前清空爬虫状态以重新开始')
    parser.add_argument('--sample-size', type=int, default=50,
                       help='质量检查抽样数量，仅 quality-check 命令使用')
    parser.add_argument('--min-title-length', type=int, default=5,
                       help='质量检查最小标题长度')
    parser.add_argument('--min-word-count', type=int, default=150,
                       help='质量检查最小字数阈值')

    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if args.command == 'crawl':
        logger.info("开始爬取数据...")
        crawler = MSDManualsCrawler(config_path=args.config)
        target_languages = args.language
        target_versions = args.version

        if args.language == 'all' or args.version == 'all':
            combos = crawler.get_language_version_pairs(
                language=None if args.language == 'all' else args.language,
                version=None if args.version == 'all' else args.version
            )

            if not combos:
                logger.error("未找到匹配的语言-版本组合，请检查配置")
                sys.exit(1)

            reset_consumed = False
            for lang, ver in combos:
                logger.info(f"批量爬取任务: language={lang}, version={ver}")
                crawler.run(
                    language=lang,
                    version=ver,
                    max_pages=args.max_pages,
                    output_dir=args.output,
                    reset_state=args.reset_state and not reset_consumed
                )
                reset_consumed = reset_consumed or args.reset_state
        else:
            crawler.run(
                language=target_languages,
                version=target_versions,
                max_pages=args.max_pages,
                output_dir=args.output,
                reset_state=args.reset_state
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

    elif args.command == 'quality-check':
        logger.info("开始数据质量检查...")
        checker = DataQualityChecker(
            min_title_length=args.min_title_length,
            min_word_count=args.min_word_count
        )
        results = checker.run_checks(sample_size=args.sample_size)
        logger.info("\n%s", results['report'])
        report_file = checker.save_report(results['report'])
        logger.info("质量检查完成，报告已保存到 %s", report_file)

if __name__ == '__main__':
    main()

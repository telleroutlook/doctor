"""数据质量检查工具"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List

from database.models import Article as ArticleModel
from database.setup_database import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class ArticleQualityResult:
    article_id: int
    url: str
    title: str
    language: str
    version: str
    word_count: int
    issues: List[str]

    @property
    def passed(self) -> bool:
        return not self.issues


class DataQualityChecker:
    """针对爬取结果的质量检查器"""

    def __init__(self, sqlite_path=None, min_title_length=5, min_word_count=150):
        self.db_manager = DatabaseManager(use_sqlite=True, sqlite_path=sqlite_path)
        self.min_title_length = min_title_length
        self.min_word_count = min_word_count

    def run_checks(self, sample_size=50) -> Dict[str, object]:
        """执行质量检查并返回详细报告"""
        articles = self._fetch_articles(sample_size)
        evaluations = [self._evaluate(article) for article in articles]
        summary = self._summarize(evaluations)
        report = self._render_report(summary, evaluations)
        return {
            'evaluations': evaluations,
            'summary': summary,
            'report': report
        }

    def _fetch_articles(self, sample_size):
        session = self.db_manager.get_session()
        try:
            query = session.query(ArticleModel).order_by(ArticleModel.updated_at.desc())
            if sample_size:
                query = query.limit(sample_size)
            return query.all()
        finally:
            session.close()

    def _evaluate(self, article: ArticleModel) -> ArticleQualityResult:
        title = (article.title or '').strip()
        content = (article.content or '').strip()
        language = (article.language or '').strip()
        version = (article.version or '').strip()
        word_count = article.word_count or len(content.split())

        issues = []
        if len(title) < self.min_title_length:
            issues.append('标题过短或缺失')
        if not content:
            issues.append('正文缺失')
        if word_count < self.min_word_count:
            issues.append('字数不足')
        if not language:
            issues.append('语言缺失')
        if not version:
            issues.append('版本缺失')
        if not article.category:
            issues.append('分类缺失')
        if not article.url:
            issues.append('URL缺失')
        elif not article.url.startswith('http'):
            issues.append('URL格式异常')

        return ArticleQualityResult(
            article_id=article.id,
            url=article.url or '',
            title=title or '（空标题）',
            language=language or '未标注',
            version=version or '未标注',
            word_count=word_count,
            issues=issues
        )

    def _summarize(self, evaluations: List[ArticleQualityResult]) -> Dict[str, object]:
        total = len(evaluations)
        passed = sum(1 for item in evaluations if item.passed)
        failed = total - passed
        avg_words = round(mean([item.word_count for item in evaluations]) if evaluations else 0, 2)

        issue_counter = Counter()
        for item in evaluations:
            for issue in item.issues:
                issue_counter[issue] += 1

        return {
            'total_checked': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round((passed / total) * 100, 2) if total else 0,
            'average_word_count': avg_words,
            'issue_breakdown': dict(issue_counter)
        }

    def _render_report(self, summary: Dict[str, object], evaluations: List[ArticleQualityResult]) -> str:
        lines = [
            '🩺 数据质量检查报告',
            '====================',
            f"检查时间: {datetime.now().isoformat(timespec='seconds')}",
            f"抽样数量: {summary['total_checked']}",
            f"通过条目: {summary['passed']} ({summary['pass_rate']}%)",
            f"未通过条目: {summary['failed']}",
            f"平均字数: {summary['average_word_count']}",
            '',
            '问题分布:'
        ]

        if summary['issue_breakdown']:
            for issue, count in summary['issue_breakdown'].items():
                lines.append(f"- {issue}: {count}")
        else:
            lines.append('- 未发现质量问题')

        failing_items = [item for item in evaluations if not item.passed]
        if failing_items:
            lines.append('\n示例问题条目:')
            for item in failing_items[:5]:
                lines.append(f"- [{item.article_id}] {item.title} ({item.url}) -> {', '.join(item.issues)}")

        return '\n'.join(lines)

    def save_report(self, report_text: str, output_dir='logs') -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_file = output_dir / f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.write_text(report_text, encoding='utf-8')
        logger.info("质量报告已保存: %s", report_file)
        return report_file

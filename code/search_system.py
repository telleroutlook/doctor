#!/usr/bin/env python3
"""
医学知识库搜索API
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from complete_data_system import MedicalDatabase

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchAPI:
    """搜索API类"""
    
    def __init__(self):
        """初始化搜索API"""
        self.db = MedicalDatabase()
        self.search_history = []
        
    def search(self, query, language=None, category=None, limit=20, offset=0):
        """执行搜索"""
        start_time = time.time()
        
        try:
            results, total_matches = self.db.search_articles(
                query=query,
                language=language,
                category=category,
                limit=limit,
                offset=offset
            )
            
            # 记录搜索历史
            self._log_search(query, len(results), time.time() - start_time)

            next_offset = offset + len(results) if offset + len(results) < total_matches else None
            meta = {
                'limit': limit,
                'offset': offset,
                'returned_results': len(results),
                'total_results': total_matches,
                'has_more': next_offset is not None,
                'next_offset': next_offset
            }

            response = {
                'success': True,
                'query': query,
                'total_results': total_matches,
                'returned_results': len(results),
                'meta': meta,
                'execution_time': round(time.time() - start_time, 3),
                'results': results,
                'suggestions': self._generate_suggestions(query),
                'timestamp': datetime.utcnow().isoformat()
            }

            return response

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def advanced_search(self, query, filters=None, sort_by='relevance', limit=20):
        """高级搜索"""
        if filters is None:
            filters = {}
        
        start_time = time.time()
        
        try:
            # 基础搜索
            raw_results, _ = self.db.search_articles(
                query=query,
                language=filters.get('language'),
                category=filters.get('category'),
                limit=limit * 2,  # 获取更多结果以便筛选
                count_total=False
            )
            
            filtered_results = raw_results
            
            # 应用额外筛选
            if filters.get('min_quality_score'):
                filtered_results = [r for r in filtered_results if r.get('quality_score', 0) >= filters['min_quality_score']]
                
            if filters.get('min_word_count'):
                filtered_results = [r for r in filtered_results if r.get('word_count', 0) >= filters['min_word_count']]
            
            # 排序
            if sort_by == 'relevance':
                filtered_results.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            elif sort_by == 'date':
                filtered_results.sort(key=lambda x: x.get('extracted_at', ''), reverse=True)
            elif sort_by == 'word_count':
                filtered_results.sort(key=lambda x: x.get('word_count', 0), reverse=True)
            
            # 应用限制
            final_results = filtered_results[:limit]
            
            # 记录搜索
            self._log_search(query, len(final_results), time.time() - start_time)
            
            meta = {
                'filters_applied': filters,
                'sort_by': sort_by,
                'limit': limit,
                'returned_results': len(final_results),
                'candidate_pool': len(filtered_results)
            }
            
            return {
                'success': True,
                'query': query,
                'meta': meta,
                'total_results': len(filtered_results),
                'returned_results': len(final_results),
                'execution_time': round(time.time() - start_time, 3),
                'results': final_results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"高级搜索失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_suggestions(self, partial_query, limit=10):
        """获取搜索建议"""
        try:
            # 获取数据库统计信息
            stats = self.db.get_statistics()
            
            suggestions = []
            
            # 基于分类的建议
            if stats.get('top_categories'):
                for category, count in list(stats['top_categories'].items())[:5]:
                    if partial_query.lower() in category.lower():
                        suggestions.append({
                            'type': 'category',
                            'text': category,
                            'count': count
                        })
            
            # 基于热门词汇的建议（简化版）
            common_terms = ['高血压', '心脏病', '糖尿病', '治疗', '症状', '诊断', '药物', '预防']
            for term in common_terms:
                if partial_query.lower() in term.lower():
                    suggestions.append({
                        'type': 'term',
                        'text': term,
                        'count': 100  # 模拟计数
                    })
            
            # 移除重复并限制数量
            unique_suggestions = []
            seen_texts = set()
            for suggestion in suggestions:
                if suggestion['text'] not in seen_texts:
                    unique_suggestions.append(suggestion)
                    seen_texts.add(suggestion['text'])
                
                if len(unique_suggestions) >= limit:
                    break
            
            return {
                'success': True,
                'query': partial_query,
                'suggestions': unique_suggestions,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取建议失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_search_statistics(self):
        """获取搜索统计"""
        try:
            stats = self.db.get_statistics()
            
            # 添加搜索历史统计
            if self.search_history:
                recent_queries = [log['query'] for log in self.search_history[-10:]]
                query_frequency = {}
                for query in recent_queries:
                    query_frequency[query] = query_frequency.get(query, 0) + 1
                
                stats['recent_popular_queries'] = sorted(
                    query_frequency.items(), key=lambda x: x[1], reverse=True
                )[:5]
            
            return {
                'success': True,
                'statistics': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _generate_suggestions(self, query):
        """生成搜索建议"""
        suggestions = []
        
        # 基于查询词的建议
        if '高血压' in query:
            suggestions.extend(['血压', '心血管', '心脏'])
        elif 'diabetes' in query.lower():
            suggestions.extend(['blood sugar', 'insulin', 'diet'])
        elif 'heart' in query.lower():
            suggestions.extend(['cardiac', 'blood pressure', 'circulation'])
        
        return suggestions[:5]
    
    def _log_search(self, query, result_count, execution_time):
        """记录搜索日志"""
        self.search_history.append({
            'query': query,
            'result_count': result_count,
            'execution_time': execution_time,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # 保持最近100次搜索记录
        if len(self.search_history) > 100:
            self.search_history = self.search_history[-100:]
        
        # 记录到数据库
        try:
            conn = self.db.get_connection()
            conn.execute('''
                INSERT INTO search_logs (query, results_count, execution_time)
                VALUES (?, ?, ?)
            ''', (query, result_count, execution_time))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"记录搜索日志失败: {e}")

def create_simple_api():
    """创建简单的API服务"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse
    
    class SearchHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.search_api = SearchAPI()
            super().__init__(*args, **kwargs)
        
        def do_GET(self):
            """处理GET请求"""
            try:
                parsed_path = urllib.parse.urlparse(self.path)
                path = parsed_path.path
                
                if path == '/':
                    self.serve_homepage()
                elif path == '/search':
                    self.handle_search(parsed_path)
                elif path == '/suggestions':
                    self.handle_suggestions(parsed_path)
                elif path == '/stats':
                    self.handle_statistics()
                elif path.startswith('/api/'):
                    self.handle_api_request(path, parsed_path)
                else:
                    self.send_error(404, "Page Not Found")
                    
            except Exception as e:
                logger.error(f"请求处理失败: {e}")
                self.send_error(500, f"Internal Server Error: {e}")
        
        def serve_homepage(self):
            """服务主页"""
            html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>默沙东诊疗手册搜索系统</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .search-container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .search-box {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .search-button {
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-right: 10px;
        }
        .search-button:hover {
            background: #5a6fd8;
        }
        .results {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .result-item {
            border-bottom: 1px solid #eee;
            padding: 15px 0;
        }
        .result-title {
            color: #667eea;
            text-decoration: none;
            font-size: 18px;
            font-weight: bold;
        }
        .result-title:hover {
            text-decoration: underline;
        }
        .result-excerpt {
            color: #666;
            margin: 10px 0;
        }
        .result-meta {
            font-size: 12px;
            color: #999;
        }
        .suggestions {
            display: none;
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-top: 5px;
            max-height: 200px;
            overflow-y: auto;
        }
        .suggestion-item {
            padding: 10px;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
        }
        .suggestion-item:hover {
            background: #f5f5f5;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 20px;
        }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 默沙东诊疗手册搜索系统</h1>
        <p>专业的医学知识搜索和检索平台</p>
    </div>
    
    <div class="search-container">
        <input type="text" id="searchInput" class="search-box" placeholder="输入医学术语、症状、疾病名称进行搜索...">
        <div id="suggestions" class="suggestions"></div>
        <br>
        <button onclick="performSearch()" class="search-button">🔍 搜索</button>
        <button onclick="showStats()" class="search-button">📊 统计</button>
    </div>
    
    <div id="results" class="results" style="display: none;">
        <h3>搜索结果</h3>
        <div id="resultsContent"></div>
    </div>
    
    <div id="statsPanel" class="stats" style="display: none;">
        <h3>系统统计</h3>
        <div id="statsContent"></div>
    </div>

    <script>
        let searchTimeout;
        const searchInput = document.getElementById('searchInput');
        const suggestionsDiv = document.getElementById('suggestions');
        
        // 搜索建议
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length > 1) {
                searchTimeout = setTimeout(() => {
                    getSuggestions(query);
                }, 300);
            } else {
                hideSuggestions();
            }
        });
        
        // 回车搜索
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        function getSuggestions(query) {
            fetch(`/suggestions?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.suggestions.length > 0) {
                        showSuggestions(data.suggestions);
                    } else {
                        hideSuggestions();
                    }
                })
                .catch(error => {
                    console.error('获取建议失败:', error);
                    hideSuggestions();
                });
        }
        
        function showSuggestions(suggestions) {
            const html = suggestions.map(s => 
                `<div class="suggestion-item" onclick="selectSuggestion('${s.text}')">
                    ${s.text} (${s.type})
                </div>`
            ).join('');
            
            suggestionsDiv.innerHTML = html;
            suggestionsDiv.style.display = 'block';
        }
        
        function hideSuggestions() {
            suggestionsDiv.style.display = 'none';
        }
        
        function selectSuggestion(text) {
            searchInput.value = text;
            hideSuggestions();
            performSearch();
        }
        
        function performSearch() {
            const query = searchInput.value.trim();
            if (!query) return;
            
            showLoading();
            
            fetch(`/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    displayResults(data);
                })
                .catch(error => {
                    console.error('搜索失败:', error);
                    document.getElementById('resultsContent').innerHTML = 
                        '<div class="error">搜索失败，请稍后重试</div>';
                });
        }
        
        function showLoading() {
            document.getElementById('results').style.display = 'block';
            document.getElementById('statsPanel').style.display = 'none';
            document.getElementById('resultsContent').innerHTML = 
                '<div class="loading">正在搜索...</div>';
        }
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            const contentDiv = document.getElementById('resultsContent');
            
            if (!data.success) {
                contentDiv.innerHTML = `<div class="error">搜索失败: ${data.error}</div>`;
                return;
            }
            
            if (data.total_results === 0) {
                contentDiv.innerHTML = '<div class="no-results">未找到相关结果</div>';
                return;
            }
            
            const resultsHtml = data.results.map(result => `
                <div class="result-item">
                    <a href="#" class="result-title">${result.title || '无标题'}</a>
                    <div class="result-excerpt">${result.excerpt || '无摘要'}</div>
                    <div class="result-meta">
                        分类: ${result.category || '未分类'} | 
                        语言: ${result.language} | 
                        质量评分: ${result.quality_score} | 
                        词数: ${result.word_count}
                    </div>
                </div>
            `).join('');
            
            contentDiv.innerHTML = `
                <p>找到 ${data.total_results} 个结果 (耗时 ${data.execution_time} 秒)</p>
                ${resultsHtml}
            `;
            
            resultsDiv.style.display = 'block';
        }
        
        function showStats() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayStats(data.statistics);
                    } else {
                        document.getElementById('statsContent').innerHTML = 
                            `<div class="error">获取统计失败: ${data.error}</div>`;
                    }
                })
                .catch(error => {
                    console.error('获取统计失败:', error);
                });
        }
        
        function displayStats(stats) {
            const statsDiv = document.getElementById('statsPanel');
            const contentDiv = document.getElementById('statsContent');
            
            let html = '<h4>数据库统计</h4>';
            html += `<p>总文章数: ${stats.total_articles || 0}</p>`;
            html += `<p>医学术语数: ${stats.total_medical_terms || 0}</p>`;
            html += `<p>药物信息数: ${stats.total_drugs || 0}</p>`;
            html += `<p>平均质量评分: ${stats.average_quality_score || 0}</p>`;
            html += `<p>平均词数: ${Math.round(stats.average_word_count || 0)}</p>`;
            
            if (stats.by_language) {
                html += '<h4>语言分布</h4>';
                html += '<ul>';
                for (lang, count of Object.entries(stats.by_language)) {
                    html += `<li>${lang}: ${count}</li>`;
                }
                html += '</ul>';
            }
            
            if (stats.by_version) {
                html += '<h4>版本分布</h4>';
                html += '<ul>';
                for (version, count of Object.entries(stats.by_version)) {
                    html += `<li>${version}: ${count}</li>`;
                }
                html += '</ul>';
            }
            
            contentDiv.innerHTML = html;
            statsDiv.style.display = 'block';
            document.getElementById('results').style.display = 'none';
        }
        
        // 点击外部隐藏建议
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-container')) {
                hideSuggestions();
            }
        });
    </script>
</body>
</html>
            """
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        
        def handle_search(self, parsed_path):
            """处理搜索请求"""
            query_params = urllib.parse.parse_qs(parsed_path.query)
            query = query_params.get('q', [''])[0]
            
            if not query:
                self.send_error(400, "Missing query parameter 'q'")
                return
            
            # 获取搜索参数
            language = query_params.get('lang', [None])[0]
            category = query_params.get('category', [None])[0]
            limit = int(query_params.get('limit', [20])[0])
            
            # 执行搜索
            result = self.search_api.search(
                query=query,
                language=language,
                category=category,
                limit=limit
            )
            
            self.send_json_response(result)
        
        def handle_suggestions(self, parsed_path):
            """处理搜索建议请求"""
            query_params = urllib.parse.parse_qs(parsed_path.query)
            query = query_params.get('q', [''])[0]
            
            if not query:
                self.send_error(400, "Missing query parameter 'q'")
                return
            
            result = self.search_api.get_suggestions(query)
            self.send_json_response(result)
        
        def handle_statistics(self):
            """处理统计请求"""
            result = self.search_api.get_search_statistics()
            self.send_json_response(result)
        
        def handle_api_request(self, path, parsed_path):
            """处理API请求"""
            if path == '/api/search':
                self.handle_search(parsed_path)
            elif path == '/api/suggestions':
                self.handle_suggestions(parsed_path)
            elif path == '/api/stats':
                self.handle_statistics()
            else:
                self.send_error(404, "API endpoint not found")
        
        def send_json_response(self, data):
            """发送JSON响应"""
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
        
        def log_message(self, format, *args):
            """自定义日志格式"""
            logger.info(f"{self.address_string()} - {format % args}")
    
    return SearchHandler

def start_server(host='localhost', port=8000):
    """启动搜索服务器"""
    try:
        handler = create_simple_api()
        server = HTTPServer((host, port), handler)
        
        print(f"🚀 医学知识库搜索服务器已启动")
        print(f"📍 访问地址: http://{host}:{port}")
        print(f"🔍 搜索API: http://{host}:{port}/search")
        print(f"📊 统计信息: http://{host}:{port}/stats")
        print(f"🌐 按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\\n👋 服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")

def main():
    """主函数"""
    print("🔍 默沙东诊疗手册检索系统")
    print("=" * 50)
    
    # 检查数据库是否存在
    if not Path("data/msd_medical_knowledge.db").exists():
        print("❌ 数据库文件不存在，请先运行 complete_data_system.py 初始化数据库")
        return
    
    # 启动服务器
    start_server(host='0.0.0.0', port=8000)

if __name__ == "__main__":
    main()

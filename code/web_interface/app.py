"""Super simple web UI to demo the MSD search helpers."""

import logging
from flask import Flask, request, jsonify, render_template_string, abort
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, HTTPException

from search_system import SearchAPI
from api.security import (
    extract_api_key,
    get_client_identifier,
    get_expected_api_key,
    is_valid_api_key,
    rate_limiter,
)

logger = logging.getLogger(__name__)

TEMPLATE = """
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>MSD 手册搜索</title>
  <style>
    body {
      font-family: 'Noto Sans SC', 'Segoe UI', sans-serif;
      margin: 0;
      background: #f4f6fb;
      color: #1f2a44;
    }
    header {
      background: linear-gradient(135deg, #0d3b66, #0d9c83);
      color: #fff;
      text-align: center;
      padding: 1.5rem 1rem;
    }
    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 1.5rem 1.25rem 2.5rem;
    }
    form {
      display: flex;
      gap: 0.65rem;
      flex-wrap: wrap;
      margin-bottom: 1rem;
    }
    input,
    select {
      flex: 1;
      min-width: 180px;
      padding: 0.65rem;
      font-size: 1rem;
      border-radius: 0.55rem;
      border: 1px solid #d1d5db;
      background: #fff;
    }
    button {
      border: none;
      border-radius: 0.55rem;
      padding: 0.65rem 1.25rem;
      font-size: 1rem;
      background: #0d3b66;
      color: #fff;
      cursor: pointer;
      transition: background 0.2s ease;
    }
    button:disabled {
      background: #94a3b8;
      cursor: not-allowed;
    }
    .status-meta {
      min-height: 3.5rem;
    }
    .meta-info {
      margin: 0;
      font-size: 0.95rem;
      color: #0d3b66;
    }
    .status-message {
      margin: 0.25rem 0 0;
      font-size: 0.9rem;
      color: #0d3b66;
    }
    .status-message.status-error {
      color: #b91c1c;
    }
    .results-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1rem;
    }
    .card {
      background: #fff;
      border-radius: 0.65rem;
      padding: 1.1rem;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .card h3 {
      margin: 0;
      font-size: 1.15rem;
      color: #0d3b66;
    }
    .card p {
      margin: 0;
      color: #475467;
      line-height: 1.45;
      font-size: 0.95rem;
    }
    .card small {
      color: #6b7280;
    }
    .pagination {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 0.75rem;
      flex-wrap: wrap;
    }
    .pagination button {
      background: #0d9c83;
      min-width: 90px;
      border: none;
      border-radius: 0.55rem;
      color: #fff;
      cursor: pointer;
    }
    .pagination button:disabled {
      background: #a7b3c8;
    }
    .loading,
    .empty {
      text-align: center;
      color: #475467;
      font-size: 0.95rem;
      padding: 1rem 0;
    }
    .error {
      color: #b91c1c;
      text-align: center;
      padding: 1rem 0;
    }
  </style>
</head>
<body>
<header>
  <h1>默沙东诊疗手册搜索</h1>
  <p>专业知识库演示 — 只展示已授权内容</p>
</header>
<main>
  <form id="search-form">
    <input type="text" name="q" placeholder="输入关键词（例如高血压）" required />
    <select name="language">
      <option value="">语言不限</option>
      <option value="zh">中文</option>
      <option value="en">英文</option>
    </select>
    <button type="submit">搜索</button>
  </form>
  <div class="status-meta">
    <p id="meta-info" class="meta-info" aria-live="polite"></p>
    <p id="status-message" class="status-message">填写关键词并提交搜索即可看到结果。</p>
  </div>
  <section id="results"></section>
  <div class="pagination">
    <button type="button" id="prev-page" disabled>上一页</button>
    <button type="button" id="next-page" disabled>下一页</button>
  </div>
</main>
<script>
const API_KEY = {{ api_key | tojson }};
const form = document.getElementById('search-form');
const resultsEl = document.getElementById('results');
const metaEl = document.getElementById('meta-info');
const statusEl = document.getElementById('status-message');
const prevBtn = document.getElementById('prev-page');
const nextBtn = document.getElementById('next-page');

const headers = { 'Accept': 'application/json' };
if (API_KEY) {
  headers['Authorization'] = `Bearer ${API_KEY}`;
  headers['X-API-Key'] = API_KEY;
}

const state = {
  query: '',
  language: '',
  limit: 10,
  offset: 0
};

const escapeHTML = (value) => {
  if (!value) {
    return '';
  }
  return value.replace(/[&<>"]/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;'
  })[char]);
};

const displayStatus = (message = '', isError = false) => {
  statusEl.textContent = message;
  statusEl.classList.toggle('status-error', isError);
};

const updateNavigation = (meta) => {
  if (!meta) {
    metaEl.textContent = '';
    prevBtn.disabled = true;
    nextBtn.disabled = true;
    return;
  }
  const start = meta.offset + 1;
  const end = meta.offset + meta.returned_results;
  metaEl.textContent = `显示 ${start}-${end} / ${meta.total_results} 条结果`;
  prevBtn.disabled = meta.offset === 0;
  nextBtn.disabled = !meta.has_more;
};

const renderResults = (payload) => {
  const items = payload.results || [];
  if (!items.length) {
    resultsEl.innerHTML = '<p class="empty">未找到匹配结果。</p>';
    return;
  }
  const cards = items.map((item) => {
    const title = escapeHTML(item.highlighted_title || item.title || '无标题');
    const snippet = escapeHTML(item.snippet || item.excerpt || '暂无摘要');
    return `
      <article class="card">
        <h3>${title}</h3>
        <p>${snippet}</p>
        <small>${escapeHTML(item.category || '无分类')} · ${escapeHTML(item.language || '未知语言')}</small>
      </article>
    `;
  }).join('');
  resultsEl.innerHTML = `<div class="results-grid">${cards}</div>`;
};

const fetchResults = async (offsetOverride = state.offset) => {
  if (!state.query) {
    displayStatus('请输入搜索词后再执行搜索', true);
    return;
  }
  const offset = Math.max(offsetOverride, 0);
  const params = new URLSearchParams({
    q: state.query,
    limit: state.limit,
    offset
  });
  if (state.language) {
    params.append('language', state.language);
  }
  resultsEl.innerHTML = '<p class="loading">正在搜索...</p>';
  try {
    const response = await fetch(`/api/search?${params.toString()}`, { headers });
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      throw new Error(payload.error || '请求失败，请稍候重试');
    }
    state.offset = payload.meta?.offset ?? offset;
    renderResults(payload);
    updateNavigation(payload.meta);
    displayStatus(`耗时 ${payload.execution_time || 0}s`, false);
  } catch (err) {
    resultsEl.innerHTML = `<p class="error">${escapeHTML(err.message)}</p>`;
    metaEl.textContent = '';
    prevBtn.disabled = true;
    nextBtn.disabled = true;
    displayStatus(err.message || '请求失败', true);
  }
};

prevBtn.addEventListener('click', () => {
  const nextOffset = Math.max(state.offset - state.limit, 0);
  fetchResults(nextOffset);
});
nextBtn.addEventListener('click', () => {
  fetchResults(state.offset + state.limit);
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const data = new FormData(form);
  state.query = (data.get('q') || '').trim();
  state.language = data.get('language') || '';
  if (!state.query) {
    displayStatus('请输入查询词', true);
    resultsEl.innerHTML = '';
    metaEl.textContent = '';
    return;
  }
  state.offset = 0;
  fetchResults(0);
});
</script>
</body>
</html>
"""



def _clamp_limit(value, default=20, min_value=1, max_value=50):
    try:
        value = int(value)
        return max(min(value, max_value), min_value)
    except (TypeError, ValueError):
        return default


def _parse_offset(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise BadRequest("offset 参数必须是非负整数")
    return max(parsed, 0)


def create_search_interface(host="127.0.0.1", port=8050, debug=False):
    """启动一个简易的搜索界面。"""

    app = Flask("msd_search_ui")
    CORS(app)

    search_api = SearchAPI()
    ui_api_key = get_expected_api_key()

    def _ensure_security():
        client_id = get_client_identifier(request, scope="ui_search")
        if not rate_limiter.allow(client_id):
            abort(429, description="请求频率过高，请稍后再试")

        if not is_valid_api_key(extract_api_key(request)):
            abort(401, description="缺少有效的 API Key")

    @app.errorhandler(HTTPException)
    def _http_error(exc):
        response = jsonify({
            "success": False,
            "error": exc.description or exc.name
        })
        response.status_code = exc.code
        return response

    @app.route("/api/search", methods=["GET"])
    def _search():
        _ensure_security()
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"success": False, "error": "请输入查询词"}), 400

        language = request.args.get("language")
        category = request.args.get("category")
        limit = _clamp_limit(request.args.get("limit"), default=10, max_value=30)
        offset = _parse_offset(request.args.get("offset", 0))

        logger.info("界面搜索: %s", query)
        return jsonify(search_api.search(
            query=query,
            language=language,
            category=category,
            limit=limit,
            offset=offset
        ))

    @app.route("/")
    def _index():
        return render_template_string(TEMPLATE, api_key=ui_api_key)

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    create_search_interface()

"""Simple Flask API around the project search helpers."""

import logging
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, HTTPException

from search_system import SearchAPI
from api.security import (
    extract_api_key,
    get_client_identifier,
    is_valid_api_key,
    rate_limiter,
)

logger = logging.getLogger(__name__)


def create_api_app(search_api=None):
    """Create the Flask application that wraps the search helpers."""

    app = Flask("msd_api")
    CORS(app)

    search_api = search_api or SearchAPI()
    PROTECTED_ENDPOINTS = {"search", "advanced_search", "suggestions", "stats"}

    def _parse_int_query(name, value, default, min_value=None, max_value=None):
        if value is None:
            return default

        try:
            parsed = int(value)
        except (TypeError, ValueError):
            raise BadRequest(f"{name} 参数必须是整数")

        if min_value is not None:
            parsed = max(parsed, min_value)
        if max_value is not None:
            parsed = min(parsed, max_value)

        return parsed

    @app.before_request
    def _enforce_security():
        if request.endpoint not in PROTECTED_ENDPOINTS:
            return

        client_id = get_client_identifier(request, scope=request.endpoint)
        if not rate_limiter.allow(client_id):
            logger.warning("Rate limit exceeded for %s", client_id)
            abort(429, description="请求频率过高，请稍后再试")

        if not is_valid_api_key(extract_api_key(request)):
            abort(401, description="缺少有效的 API Key")

    @app.errorhandler(HTTPException)
    def _handle_http_error(exc):
        response = jsonify({
            "success": False,
            "error": exc.description or exc.name,
            "code": exc.code
        })
        response.status_code = exc.code
        return response

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "version": "1.0",
            "database": search_api.db.db_path
        })

    @app.route("/search", methods=["GET"])
    def search():
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"success": False, "error": "缺少 q 参数"}), 400

        language = request.args.get("language")
        category = request.args.get("category")
        limit = _parse_int_query("limit", request.args.get("limit"), 20, min_value=1, max_value=50)
        offset = _parse_int_query("offset", request.args.get("offset"), 0, min_value=0)

        logger.info("搜索请求: %s", query)
        response = search_api.search(
            query=query,
            language=language,
            category=category,
            limit=limit,
            offset=offset
        )
        return jsonify(response)

    @app.route("/search/advanced", methods=["POST"])
    def advanced_search():
        payload = request.get_json(force=True, silent=True) or {}
        query = payload.get("query", "").strip()
        if not query:
            return jsonify({"success": False, "error": "需要提供 query 字段"}), 400

        filters = payload.get("filters", {})
        limit = _parse_int_query("limit", payload.get("limit", 20), 20, min_value=1, max_value=100)
        sort_by = payload.get("sort_by", "relevance")

        logger.info("高级搜索: %s", query)
        response = search_api.advanced_search(query=query, filters=filters, sort_by=sort_by, limit=limit)
        return jsonify(response)

    @app.route("/suggestions", methods=["GET"])
    def suggestions():
        partial = request.args.get("q", "").strip()
        limit = _parse_int_query("limit", request.args.get("limit"), 10, min_value=1, max_value=50)
        logger.debug("建议请求: %s", partial)
        return jsonify(search_api.get_suggestions(partial, limit=limit))

    @app.route("/stats", methods=["GET"])
    def stats():
        return jsonify(search_api.get_search_statistics())

    return app


def start_api_server(host="0.0.0.0", port=5050, debug=False):
    app = create_api_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    start_api_server()

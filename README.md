# MSD Crawler System

本仓库包含默沙东诊疗手册相关的医学文献抓取、处理与检索工具，核心代码位于 `code/`，支持多语言、增量更新、日志记录与 API 服务。

## 快速起步
1. 安装依赖： `pip install -r code/requirements.txt`
2. 初始化数据库： `python code/main.py setup-db`
3. 运行爬虫： `python code/main.py crawl --language en --version home --max-pages 1000`（可选 `--output`、`--max-pages` 限制调试）
4. 启动服务： `python code/main.py api`（或 `python code/main.py search` 用于前端界面）
5. 本地调试测试： `python code/main.py test` 或直接 `pytest code/test_crawler.py`

## 项目目录概览
- `code/`: 主要应用（爬虫、解析器、数据处理、API、搜索）
- `code/config/`, `code/database/`, `code/data/`: 配置、数据库脚本、静态数据/样例
- `docs/`: 站点分析、爬虫策略与数据库架构设计等报告
- `AGENTS.md`: 贡献者指南（由代理贡献者维护）

## 运行说明
- `python code/main.py crawl ...` 中 `--language` 与 `--version` 控制目标站点版本，建议调试时加 `--max-pages` 与 `--output` 限制采集范围。
- `code/main.py` 的 `api`/`search` 子命令分别启动 Flask API 与界面，测试新功能可结合 `curl` 或浏览器手动验证。
- `python code/main.py test` 是快速验证；修改爬虫后请运行 `pytest code/test_crawler.py` 并检查日志输出。

## 贡献与规范
- 参照 `AGENTS.md` 了解项目结构、编码风格、测试与 PR 要求。
- 修改前查看 `docs/爬虫策略与数据库架构设计.md`，确保新爬虫行为符合 robots.txt 友好策略。
- 保持 `code/` 内配置在 `config/` 管理，避免将敏感信息直接提交；可借助 `.env` 加载运行环境。

欢迎通过 Issues/PR 参与改进；完成功能后附带执行命令、截图或数据样本帮助复现。

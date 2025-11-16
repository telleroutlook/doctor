# 默沙东诊疗手册爬虫系统

一个高效、合规的医学文献数据抓取与检索系统。

## 🚀 功能特性

- **合规抓取**: 严格遵守robots.txt政策，智能频率控制
- **医学解析**: 专门优化的医学内容解析器
- **多语言支持**: 支持16种语言版本的抓取
- **智能搜索**: 基于自然语言处理的全文检索
- **增量更新**: 支持断点续传和增量更新
- **质量保证**: 完整的数据质量检查机制

## 📦 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 初始化数据库
python main.py setup-db
```

## 🕷️ 快速开始

### 爬取数据
```bash
# 爬取英文消费者版数据
python main.py crawl --language en --version home --max-pages 1000

# 爬取中文专业版数据
python main.py crawl --language zh --version professional --max-pages 500

# 指定输出目录
python main.py crawl --language en --version home --output ./output --max-pages 2000
```

### 启动服务
```bash
# 启动搜索API
python main.py api

# 启动搜索界面
python main.py search
```

### 运行测试
```bash
python main.py test
```

## 📁 项目结构

```
msd_crawler_project/
├── config/                 # 配置文件
├── database/               # 数据库相关
├── crawler/                # 爬虫核心代码
├── parsers/                # 内容解析器
├── processors/             # 数据处理器
├── api/                    # API服务
├── web_interface/          # Web界面
├── tests/                  # 测试代码
├── data/                   # 数据文件
├── docs/                   # 文档
└── scripts/                # 脚本工具
```

## ⚙️ 配置说明

### 数据库配置
- 支持MySQL和SQLite
- 自动创建必要的表结构
- 支持全文搜索索引

### 爬虫配置
- 可配置并发数和延迟
- 智能重试机制
- 断点续传支持

## 📊 数据结构

### 主要表
- `articles`: 文章内容
- `categories`: 医学分类
- `medical_terms`: 医学术语
- `drugs`: 药物信息
- `search_logs`: 搜索日志

### 搜索功能
- 全文搜索
- 按分类筛选
- 关键词高亮
- 相关性排序

## 🛠️ 技术栈

- **爬虫框架**: Scrapy
- **数据库**: MySQL/SQLite
- **文本处理**: NLTK, spaCy
- **Web框架**: Flask
- **前端**: HTML5 + JavaScript

## 📄 许可证

本项目仅用于学术研究目的。请遵守相关法律法规和网站使用条款。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📞 联系方式

如有问题，请通过GitHub Issues联系我们。

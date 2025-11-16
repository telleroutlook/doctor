# 默沙东诊疗手册（MSD Manuals）网站结构深度分析报告

## 📋 项目概述

**分析时间：** 2025年11月16日  
**分析目标：** 为构建默沙东诊疗手册爬虫系统提供技术基础  
**网站地址：** https://www.msdmanuals.com  
**分析范围：** 完整网站架构、URL模式、内容分类、爬虫策略

---

## 🏗️ 网站整体架构

### 版本划分
MSD手册采用三版本分栏设计：

1. **专业版 (Professional Version)**
   - 目标用户：医疗专业人员、学生
   - 内容特点：更高级的医学内容
   - URL前缀：`/professional/`

2. **消费者版 (Consumer Version)**
   - 目标用户：普通公众、患者
   - 内容特点：通俗易懂的信息
   - URL前缀：`/home/`

3. **兽医版 (Veterinary Manual)**
   - 目标用户：兽医专业人员、学生
   - 内容特点：动物医学专业内容
   - 独立域名：`msdvetmanual.com`

---

## 🗂️ 内容分类体系

### 主要导航结构（消费者版）

#### 核心分类（7大主类）
```
HEALTH TOPICS          # 健康话题主分类
├── /home/health-topics
├── 内容：按医学专科分类
└── 包含：26个主要医学专科

HEALTHY LIVING         # 健康生活方式
├── /home/healthy-living
├── 内容：预防保健、健康习惯
└── 包含：营养、运动、心理健康

SYMPTOMS              # 症状分类
├── /home/symptoms
├── 内容：按症状查找疾病
└── 包含：系统化症状索引

EMERGENCIES           # 急救和紧急情况
├── /home/first-aid
├── 内容：急救指导、紧急处理
└── 包含：各种急救场景

RESOURCES             # 资源分类
├── /home/resource
├── 内容：工具、参考资料
└── 包含：临床计算器、正常数值等

COMMENTARY            # 评论和专栏
├── /home/pages-with-widgets/news-list
├── 内容：专家观点、专栏文章
└── 包含：医学评论、新闻

ABOUT US              # 关于我们
├── /home/resourcespages/about-the-manuals
├── 内容：网站介绍、版权信息
└── 包含：历史、团队信息
```

### 快速链接（Quick Links）
```
FIRST AID AND EMERGENCIES    # 急救和紧急情况
NORMAL LAB VALUES           # 正常实验室数值
VIDEOS                     # 视频资源
QUICK FACTS                # 快速事实
```

### 医学专科分类（26大类）
```
1. 过敏反应和免疫缺陷病
2. 心血管疾病
3. 皮肤病学
4. 内分泌和代谢紊乱
5. 消化道疾病
6. 血液学
7. 感染性疾病
8. 肾脏和尿路疾病
9. 神经系统疾病
10. 妇科和产科
11. 眼科学
12. 骨科和风湿病学
13. 耳鼻喉科
14. 儿科
15. 精神病学
16. 肺科
17. 放射学
18. 泌尿科
19. 癌症
20. 药理学
21. 康复医学
22. 移植学
23. 创伤和急症
24. 老年医学
25. 遗传学
26. 环境健康
```

---

## 🔗 URL模式分析

### URL结构模式
```
基础模式：
https://www.msdmanuals.com/[版本]/[分类]/[子分类]/[具体主题]

示例URL：
https://www.msdmanuals.com/home/cardiovascular-disorders/hypertension
https://www.msdmanuals.com/professional/infectious-diseases/syphilis
https://www.msdmanuals.com/home/blood-disorders/iron-deficiency-anemia

层级结构：
第1层：/home/ (版本前缀)
第2层：/cardiovascular-disorders/ (主分类)
第3层：/hypertension/ (具体主题)

双语支持：
https://www.msdmanuals.cn/... (中文版)
https://www.msdmanuals.com/... (英文版)
```

### URL编码规范
- 英文短横线连接 (`hypertension` 非 `Hypertension`)
- 小写字母
- 多词使用短横线连接 (`iron-deficiency-anemia`)
- 不包含特殊字符和空格

---

## 📄 页面结构分析

### 内容页面通用结构
```html
<!DOCTYPE html>
<html>
<head>
    <title>页面标题 - 分类 - 默沙东诊疗手册</title>
    <meta name="description" content="页面描述">
    <meta name="keywords" content="关键词">
    <!-- 结构化数据 -->
    <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "MedicalWebPage",
            "mainEntity": {
                "@type": "Article"
            }
        }
    </script>
</head>
<body>
    <!-- 导航面包屑 -->
    <nav class="breadcrumb">
        <a href="/home/">主页</a> >
        <a href="/home/cardiovascular-disorders/">心血管疾病</a> >
        <span>高血压</span>
    </nav>
    
    <!-- 主标题 -->
    <h1>高血压</h1>
    
    <!-- 文章内容 -->
    <article>
        <!-- 正文内容 -->
        <section>疾病概述</section>
        <section>症状</section>
        <section>诊断</section>
        <section>治疗</section>
    </article>
    
    <!-- 相关链接 -->
    <aside>
        <h3>相关主题</h3>
        <ul>
            <li><a href="/home/...">相关内容</a></li>
        </ul>
    </aside>
</body>
</html>
```

### 关键数据字段
```json
{
    "title": "文章标题",
    "category": "医学分类",
    "subcategory": "子分类",
    "author": "作者信息",
    "review_date": "审核日期",
    "content": "正文内容",
    "synonyms": "同义词",
    "related_topics": ["相关主题链接"],
    "images": ["图片URL"],
    "videos": ["视频URL"],
    "tables": ["表格数据"],
    "references": ["参考文献"]
}
```

---

## 🤖 爬虫策略分析

### robots.txt 分析
```text
User-agent: *
Crawl-delay: 5 seconds
Disallow: */sitecore/
Disallow: */custom/
Disallow: */news/external/
Disallow: */professional/drug-names-generic-and-brand
Disallow: */home/drug-names-generic-and-brand
Disallow: */home/monograph/*
Disallow: */professional/monograph/*
```

**关键发现：**
- ✅ 全局爬虫延迟：5秒（重要！）
- ❌ 禁止抓取药品名称和药物概述页面
- ❌ 禁止抓取自定义和CMS路径
- ✅ 官方 sitemap 覆盖多语言，但本系统仅保留简体中文与英文入口

### Sitemap结构
```
支持语言版本：
en, zh

Sitemap URL模式：
https://www.msdmanuals.com/[语言]/sitemap.xml
```

### 反爬虫机制
1. **访问频率限制**
   - 全局5秒延迟
   - 防止过度抓取

2. **内容保护**
   - 特定路径禁止抓取
   - 药品信息受保护

3. **地理位置限制**
   - 百度爬虫无法抓取中文内容
   - 其他搜索引擎有特殊限制

---

## 📊 数据结构设计建议

### 数据库表结构
```sql
-- 文章表
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    content TEXT,
    url VARCHAR(1000) UNIQUE,
    version VARCHAR(20), -- 'professional', 'home', 'veterinary'
    language VARCHAR(10) DEFAULT 'en',
    author VARCHAR(200),
    review_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 医学术语表
CREATE TABLE medical_terms (
    id INTEGER PRIMARY KEY,
    term VARCHAR(200) NOT NULL,
    definition TEXT,
    synonyms TEXT, -- JSON array
    category VARCHAR(100),
    related_articles JSON -- JSON array of article IDs
);

-- 分类表
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    parent_id INTEGER,
    description TEXT,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

-- 关键词索引表
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY,
    article_id INTEGER,
    keyword VARCHAR(100),
    weight FLOAT DEFAULT 1.0,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
```

### 搜索索引设计
```python
# 全文搜索配置
SEARCH_CONFIG = {
    "tokenizer": "medical_tokenizer",
    "stop_words": "medical_stopwords",
    "stemmer": "porter",
    "fields": [
        {"field": "title", "boost": 10},
        {"field": "content", "boost": 1},
        {"field": "synonyms", "boost": 5},
        {"field": "category", "boost": 3}
    ]
}
```

---

## ⚙️ 技术实施建议

### 爬虫架构
```
爬虫系统架构：
├── 调度器 (Scheduler)
│   ├── URL管理器
│   ├── 请求频率控制
│   └── 任务队列管理
├── 下载器 (Downloader)
│   ├── HTTP客户端
│   ├── 代理管理
│   └── 会话管理
├── 解析器 (Parser)
│   ├── HTML解析
│   ├── 内容提取
│   └── 数据清洗
├── 存储器 (Storage)
│   ├── 数据库操作
│   ├── 文件存储
│   └── 索引管理
└── 监控 (Monitor)
    ├── 性能监控
    ├── 错误处理
    └── 进度跟踪
```

### 并发策略
```python
CONCURRENT_CONFIG = {
    "max_workers": 3,  # 考虑5秒延迟
    "delay_between_requests": 5,
    "retry_times": 3,
    "timeout": 30,
    "respect_robots_txt": True
}
```

### 数据处理流程
```python
DATA_PROCESSING_PIPELINE = [
    "content_extraction",    # 内容提取
    "text_cleaning",        # 文本清洗
    "html_to_text",         # HTML转文本
    "medical_term_extraction", # 医学术语提取
    "keyword_analysis",     # 关键词分析
    "category_classification", # 分类
    "quality_check",        # 质量检查
    "database_storage",     # 数据库存储
    "index_creation"        # 索引创建
]
```

---

## 📈 预期抓取规模

### 内容统计
- **总页面数：** 估计50,000-100,000页
- **医学主题：** 约26个主分类，每个分类200-500个主题
- **语言版本：** 2种语言（简体中文、英文）
- **文件类型：** HTML文本、图片、PDF下载、视频

### 数据容量估算
```
预估数据量：
- 文本内容：约2-5 GB
- 图片资源：约10-20 GB
- 数据库大小：约5-10 GB
- 索引文件：约1-2 GB

抓取时间估算：
- 每日抓取：1000-2000页
- 总耗时：30-60天
- 存储空间：20-40 GB
```

---

## ⚠️ 风险评估

### 技术风险
1. **反爬虫机制升级**
   - 风险：检测并封禁爬虫IP
   - 缓解：使用代理池，遵守robots.txt

2. **网站结构变更**
   - 风险：URL模式或页面结构变化
   - 缓解：监控网站更新，及时调整爬虫

3. **访问限制**
   - 风险：地域或频率限制
   - 缓解：分布式爬取，智能限速

### 法律合规
1. **版权问题**
   - 风险：大规模数据抓取可能涉及版权
   - 缓解：仅抓取公开信息，用于学术研究

2. **robots.txt遵守**
   - 风险：不遵守网站爬取政策
   - 缓解：严格遵守robots.txt限制

---

## ✅ 结论与建议

### 主要发现
1. **网站结构清晰**：采用标准的三版本架构，内容组织合理
2. **URL模式规律**：遵循清晰的层级结构，便于程序解析
3. **反爬虫控制**：有明确的robots.txt政策，需要严格遵守
4. **双语支持**：支持简体中文与英文内容，覆盖关键医学主题

### 实施建议
1. **优先抓取策略**
   - 先抓取英文版（内容最完整）
   - 再抓取中文版（使用需求最高）
   - 最后对中英文差异内容进行校验与补充

2. **分阶段实施**
   - 第一阶段：主页和分类页
   - 第二阶段：核心医学主题
   - 第三阶段：具体疾病页面
   - 第四阶段：补充内容

3. **质量保障**
   - 建立数据质量检查机制
   - 实现断点续传功能
   - 添加异常处理和恢复机制

4. **合规性确保**
   - 严格遵守robots.txt
   - 控制访问频率
   - 仅用于学术研究目的

这个分析为构建默沙东诊疗手册爬虫系统提供了全面的技术基础，确保能够高效、合规地完成数据抓取任务。
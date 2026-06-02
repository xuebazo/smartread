# 📖 SmartRead · 个人 AI 英语阅读助手

<p align="center">
  <strong>SmartRead — Your Personal AI-Powered English Reading Workbench</strong>
  <br>
  面向 CET-4/6 备考者的智能英语阅读工具 | AI-Driven English Reading Tool for Chinese Learners
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Framework-Streamlit-red?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/AI-DeepSeek-purple&logoColor=white" alt="DeepSeek">
  <img src="https://img.shields.io/badge/DB-SQLite-lightgreen?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## 📑 Table of Contents | 目录

- [✨ Features | 功能特性](#-features--功能特性)
- [🚀 Quick Start | 快速开始](#-quick-start--快速开始)
  - [💻 Local | 本地运行](#-local--本地运行)
  - [☁️ Streamlit Cloud | 云端部署 (推荐手机使用)](#-streamlit-cloud--云端部署-推荐手机使用)
- [🏗️ Architecture | 架构设计](#-architecture--架构设计)
- [📁 Project Structure | 项目结构](#-project-structure--项目结构)
- [🗄️ Database | 数据库设计](#-database--数据库设计)
- [🔧 Tech Stack | 技术栈](#-tech-stack--技术栈)
- [🔮 Roadmap | 路线图](#-roadmap--路线图)
- [⚠️ Privacy & Security | 隐私安全](#-privacy--security)
- [📄 License | 许可证](#-license--许可证)

---

## ✨ Features | 功能特性

### 📰 Daily Reading | 每日外刊精选
> Automatically fetches latest articles from 5 curated RSS sources (NYT, The Guardian, Scientific American, BBC News, NPR), with deduplication, source filtering, and read-status tracking.

自动从 **5 个精选外刊 RSS 源** 拉取最新文章，支持去重、来源筛选和已读标记。一键跳转阅读。

### 📖 AI Reading & Translation | 智能阅读分析
> **4 concurrent AI agents** run in parallel: translation, vocabulary extraction, grammar analysis, and difficulty assessment. Fully parallelized for 50%+ faster results.

**4 个 AI Agent 并发执行**：中英逐段对照翻译、核心词汇提取、长难句语法分析、文章难度评级。分析完成后自动计时，记录阅读时长。

### 📝 Vocabulary Book | 生词本
> Save words with phonetics, definitions, and original sentence context. Track mastery level, review with **flashcard mode**, and monitor vocabulary growth over time.

收藏单词（含音标、释义、原文例句），追踪掌握程度，支持 **🃏 闪卡复习模式**，可视化词汇增长曲线。

### 🧠 Grammar Analysis | 长难句拆解
> AI detects complex sentences and provides structural breakdowns with Chinese explanations — perfect for CET-4/6 candidates.

AI 自动识别长难句，提供语法拆解和中文解析，精准定位四六级考点。

### 🎯 Difficulty Assessment | 难度评级
> Dual-mode assessment: AI-powered primary + rule-based fallback (500+ CET-6 vocabulary base). Classifies articles into CET4 / CET6 / 考研 / IELTS levels.

AI + 规则双模式评级，将文章分类为 CET4 / CET6 / 考研 / IELTS 四个等级，附带星级展示。

### 📚 Reading History & Stats | 阅读记录与统计
> Dashboard with total articles, daily count, cumulative word count, **true consecutive-day streak**, difficulty distribution chart, and source filtering.

统计仪表盘：总阅读篇数、今日阅读、累计词数、🔥 **真连续打卡天数**、难度分布柱状图、来源筛选。

### 💾 State Recovery | 状态自动恢复
> Analysis results persist across page refreshes and app restarts. No API re-calls needed.

刷新页面或重启后自动恢复上次阅读状态和分析结果，不重复消耗 API 额度。

### 🛡️ Auto Backup | 数据库自动备份
> Daily backup of the SQLite database on app startup, with 7-day rotation. Data safety without manual intervention.

每次启动自动备份数据库，保留 7 天备份记录，数据安全无忧。

---

## 🚀 Quick Start | 快速开始

### 💻 Local | 本地运行

**Prerequisites | 前置条件**
- Python 3.10+
- DeepSeek API Key → [Get one here](https://platform.deepseek.com/api_keys) | [在此获取](https://platform.deepseek.com/api_keys)

```bash
# 1. Clone & enter project | 克隆并进入项目
git clone https://github.com/YOUR_USERNAME/smartread.git
cd smartread

# 2. Create virtual environment | 创建虚拟环境 (recommended)
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies | 安装依赖
pip install -r requirements.txt

# 4. Configure API key | 配置 API 密钥
# Create a .env file in the project root | 在项目根目录创建 .env 文件：
# DEEPSEEK_API_KEY=sk-your-key-here

# 5. Launch | 启动
streamlit run app.py

# 6. Open browser | 浏览器访问
# http://localhost:8501
```

| Dependency | 依赖 | Version | Purpose | 用途 |
|---|---|---|---|---|
| `streamlit` | ≥1.28.0 | Web UI framework | Web 界面框架 |
| `requests` | ≥2.28.0 | HTTP requests | HTTP 请求 |
| `python-dotenv` | ≥1.0.0 | .env variable loading | 环境变量管理 |
| `feedparser` | ≥6.0.0 | RSS parsing | RSS 解析 |
| `beautifulsoup4` | ≥4.12.0 | HTML parsing | HTML 解析 |
| `newspaper3k` | ≥0.2.8 | Article body extraction | 正文提取引擎 |
| `lxml_html_clean` | ≥0.4.0 | Required by newspaper3k | newspaper3k 依赖 |

### ☁️ Streamlit Cloud | 云端部署 (推荐手机使用)

> **The easiest way to use SmartRead on your phone.** Deploy once to Streamlit Cloud for free, then access from any device browser — no server, no VPN, no setup.
>
> **手机上使用 SmartRead 的最简单方式。** 免费部署到 Streamlit Cloud，手机/平板/电脑浏览器均可访问，无需服务器、无需翻墙。

**Deployment Steps | 部署步骤：**

| Step | Action | 操作 |
|:---:|---|---|
| 1 | Push this repo to **GitHub** | 将本仓库推送到 GitHub |
| 2 | Visit [share.streamlit.io](https://share.streamlit.io) | 访问 Streamlit Cloud 控制台 |
| 3 | Click **"New app"** → select repo & branch | 点击「New app」→ 选择仓库和分支 |
| 4 | Set main file path to `app.py` | 主文件路径设为 `app.py` |
| 5 | Go to **⚙️ Settings → Secrets** | 进入应用设置 → Secrets 管理 |
| 6 | Add your API key as a secret | 添加 API 密钥 |

```toml
# Streamlit Cloud Secrets 格式
DEEPSEEK_API_KEY = "sk-your-key-here"
```

| Step | Action | 操作 |
|:---:|---|---|
| 7 | Click **"Deploy!"** → app live at `https://your-app.streamlit.app` | 点击部署，应用上线 |
| 8 | **Optional**: On phone → browser menu → "Add to Home Screen" for app-like icon | 手机浏览器打开 → 菜单 → 添加到主屏幕 |

> **⚠️ Free Tier Notes | 免费版须知：**
> - Apps sleep after ~5 days of inactivity → cold start takes 10-30 seconds | 5 天无人访问后休眠，冷启动约 10-30 秒
> - 1 GB RAM limit (plenty for this app) | 1 GB 内存限制（本应用绰绰有余）
> - Domain is accessible from China without VPN | `streamlit.app` 域名国内可直接访问，无需翻墙

---

## 🏗️ Architecture | 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                    │
│         app.py (4 pages · session state manager)         │
│             4 页面 · Session State 状态管理               │
├─────────────────────────────────────────────────────────┤
│                Agents · 业务逻辑层                        │
│    translator / vocabulary / grammar / difficulty        │
│         4 Agent ThreadPoolExecutor 并发执行               │
├─────────────────────────────────────────────────────────┤
│                Services · 服务层                          │
│        AIService (unified DeepSeek API calls)            │
│        BackupService (daily auto-backup)                 │
├─────────────────────────────────────────────────────────┤
│              Data · 数据仓储层                             │
│     vocab_repository / history_repository                │
│            article_cache / cache.db                      │
└─────────────────────────────────────────────────────────┘
```

**Data Flow | 数据流：**

```
User Action → app.py
    │
    ├─ Daily Reading → rss_fetcher.py → article_cache.py → cache.db
    │                    └─ get_read_links() for read-status tracking
    │
    ├─ Reading Analysis → ThreadPoolExecutor(max_workers=4)
    │      ├── translator.py  ─┐
    │      ├── vocabulary.py  ─┤──→ AIService → DeepSeek API
    │      ├── grammar.py     ─┤
    │      └── difficulty.py  ─┘
    │      └─ Timer → history_repository
    │
    ├─ Vocab Book → vocab_repository → cache.db
    │      └─ Flashcard Review
    │
    ├─ Reading History → history_repository → cache.db
    │      └─ Chart Data
    │
    └─ On Startup → backup_service.py → backups/
```

---

## 📁 Project Structure | 项目结构

```
smartread/
│
├── app.py                       # Main Streamlit app (~880 lines) | Streamlit 主程序
├── config.py                    # API key manager | API 密钥管理
├── rss_fetcher.py               # RSS aggregator (5 sources) | 5 源 RSS 聚合
├── article_cache.py             # Article cache + read-status | 文章缓存 + 已读状态
├── utils.py                     # Text extraction (dual-engine) | 正文提取（双引擎）
├── requirements.txt             # Dependencies (7 packages) | 依赖清单
├── SmartRead.bat                # Windows quick launcher | Windows 一键启动
│
├── agents/                      # AI Agents | AI 智能体
│   ├── __init__.py
│   ├── translator.py            # Translation agent | 翻译官
│   ├── vocabulary.py            # Vocabulary extraction | 词汇导师
│   ├── grammar.py               # Grammar analysis | 语法教练
│   └── difficulty.py            # Difficulty assessment (AI + rule) | 难度评级
│
├── services/                    # Shared Services | 共享服务
│   ├── __init__.py
│   ├── ai_service.py            # Unified DeepSeek API client | 统一 API 客户端
│   └── backup_service.py        # Daily DB backup | 数据库每日备份
│
├── database/                    # Data Layer | 数据层
│   ├── __init__.py
│   ├── vocab_repository.py      # Vocab CRUD + flashcard | 生词本 CRUD + 闪卡
│   └── history_repository.py    # History + stats + state recovery | 阅读记录 + 统计
│
├── backups/                     # Auto-backup directory | 自动备份目录 (auto-created)
├── cache.db                     # SQLite database | SQLite 数据库 (auto-created)
└── .env                         # API key | API 密钥 (gitignored)
```

---

## 🗄️ Database | 数据库设计

All data stored in `cache.db` (SQLite), auto-created on first run.

| Table | 表名 | Purpose | 用途 | Key Fields | 关键字段 |
|---|---|---|---|---|---|
| `articles` | 文章缓存 | Cached RSS articles | 缓存外刊文章 | `title`, `link`(UNIQUE), `source` |
| `saved_words` | 生词本 | User-saved vocabulary | 用户收藏的单词 | `word`, `phonetic`, `meaning`, `known_level`(0-2) |
| `reading_history` | 阅读记录 | Reading logs + stats | 阅读历史 + 统计 | `word_count`, `difficulty`, `reading_minutes`, `favorite` |
| `reading_state` | 状态恢复 | Auto-saved analysis state | 自动恢复分析状态 | Single-row, stores `analysis_results` JSON |

---

## 🔧 Tech Stack | 技术栈

| Layer | 层 | Technology | 技术 |
|---|---|---|---|
| **UI Framework** | 界面框架 | Streamlit 1.28+ |
| **Language** | 编程语言 | Python 3.10+ |
| **AI Model** | AI 模型 | DeepSeek Chat API |
| **Database** | 数据库 | SQLite (auto-managed) |
| **RSS Parsing** | RSS 解析 | feedparser |
| **HTML Parsing** | HTML 解析 | BeautifulSoup 4 |
| **Article Extraction** | 正文提取 | newspaper3k |
| **Concurrency** | 并发 | `concurrent.futures.ThreadPoolExecutor` |
| **Deployment** | 部署 | Streamlit Community Cloud (free) |

---

## 🔮 Roadmap | 路线图

- [ ] **Mobile PWA Support** — Add manifest.json + service worker for installable mobile experience | PWA 移动端支持
- [ ] **Article Bookmarking** — Save interesting articles for later | 文章收藏夹
- [ ] **Reading Goals** — Daily/weekly reading targets with streak tracking | 阅读目标设定
- [ ] **Export** — Export vocabulary to Anki / Quizlet | 生词导出到第三方工具
- [ ] **Custom RSS Sources** — User-defined RSS feed URLs | 自定义 RSS 源
- [ ] **Dark Mode** — Full dark theme support | 深色模式
- [ ] **AI Summary** — Article summarization via AI | AI 文章摘要生成

---

## ⚠️ Privacy & Security | 隐私安全

> **Your data stays local.** SmartRead is designed with privacy-first principles:
>
> **你的数据只在你手中。** SmartRead 遵循隐私优先设计原则：

| Aspect | 方面 | Detail | 说明 |
|---|---|---|---|
| **API Key** | API 密钥 | Never hardcoded, gitignored via `.env`, managed via Streamlit Secrets on cloud | 不存代码，`.env` 排除，云端用 Secrets |
| **Reading Data** | 阅读数据 | All data in local SQLite. Backups auto-rotated after 7 days | 本地 SQLite，备份 7 天自动轮转 |
| **Network** | 网络请求 | Only calls to DeepSeek API + RSS sources. No third-party tracking | 仅调用 DeepSeek API 和 RSS 源 |
| **No Telemetry** | 零追踪 | Zero analytics, zero tracking, zero data collection | 零分析、零追踪、零数据收集 |

**Security Checklist before deployment | 部署前安全检查：**
- [x] `.env` in `.gitignore` — API key not committed | API 密钥不入库
- [x] `cache.db` in `.gitignore` — local database not committed | 本地数据库不入库
- [x] `backups/` in `.gitignore` — backup databases not committed | 备份数据库不入库
- [x] No hardcoded credentials in source code | 源代码无硬编码凭据
- [ ] **Regenerate API key** after any potential exposure | 如有泄露风险，立即重新生成 API 密钥

---

## 📄 License | 许可证

[MIT License](LICENSE) — Free for personal and educational use.

---

<p align="center">
  <sub>Built with ❤️ for English learners | 为英语学习者而建</sub>
  <br>
  <sub>Powered by <a href="https://streamlit.io">Streamlit</a> & <a href="https://deepseek.com">DeepSeek</a></sub>
</p>

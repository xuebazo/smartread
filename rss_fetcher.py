"""
RSS 源解析与聚合模块
使用 feedparser 解析预置的四六级核心题源 RSS
"""
import logging
import requests
import feedparser

logger = logging.getLogger(__name__)

# 浏览器标识，避免被 RSS 源拒绝
FEED_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# 预置四六级核心题源（免费公开 RSS）
SOURCES = {
    # 综合新闻 · 美式英语（NYT World RSS）
    "纽约时报": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    # 综合新闻 · 英式英语（卫报 World RSS）
    "卫报": "https://www.theguardian.com/world/rss",
    # 科学短讯 · 四六级科普阅读（Science News RSS）
    "科学美国人": "https://www.sciencenews.org/feed",
    # 综合新闻 · 四六级高频题源，国内访问稳定（BBC World RSS）
    "BBC News": "https://feeds.bbci.co.uk/news/world/rss.xml",
    # 综合新闻 · 美式英语（NPR Top Stories RSS）
    "NPR": "https://feeds.npr.org/1001/rss.xml",
}


def fetch_feed(url: str, source_name: str) -> list[dict]:
    """
    解析单个 RSS 源，提取文章列表
    返回 [{"title": "", "summary": "", "link": "", "published": "", "source": ""}, ...]
    单个源失败时返回空列表，不中断整体流程
    """
    articles = []
    try:
        # 使用 requests 先获取内容（带浏览器 UA），再传给 feedparser 解析
        response = requests.get(url, headers=FEED_HEADERS, timeout=30)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        if feed.bozo and not feed.entries:
            logger.warning(f"RSS 源 {source_name} 解析异常: {feed.bozo_exception}")
            return articles

        for entry in feed.entries[:20]:  # 每个源最多取 20 篇
            summary = entry.get("summary", entry.get("description", ""))
            # 去除 HTML 标签
            import re
            summary_clean = re.sub(r"<[^>]+>", "", summary)
            # 截断至 200 字符
            if len(summary_clean) > 200:
                summary_clean = summary_clean[:200] + "..."

            articles.append({
                "title": entry.get("title", "无标题"),
                "summary": summary_clean,
                "link": entry.get("link", ""),
                "published": entry.get("published", "未知日期"),
                "source": source_name,
            })

        logger.info(f"成功拉取 {source_name}: {len(articles)} 篇文章")

    except Exception as e:
        logger.warning(f"RSS 源 {source_name} 抓取失败: {str(e)}")

    return articles


def fetch_all_feeds() -> list[dict]:
    """
    遍历所有 RSS 源，合并结果返回
    返回合并后的文章列表
    """
    all_articles = []
    for source_name, url in SOURCES.items():
        articles = fetch_feed(url, source_name)
        all_articles.extend(articles)
    return all_articles

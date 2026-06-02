r"""
文章缓存模块 - 使用 SQLite 存储文章记录
数据库文件自动生成在 D:\smartread\cache.db
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent / "cache.db"


def _get_connection() -> sqlite3.Connection:
    """获取数据库连接，自动建表"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE,
            source TEXT,
            published TEXT,
            difficulty TEXT DEFAULT '',
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 旧表迁移：新增 difficulty 字段
    try:
        conn.execute("ALTER TABLE articles ADD COLUMN difficulty TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # 字段已存在则跳过
    conn.commit()
    return conn


def is_duplicate(link: str) -> bool:
    """根据 link 查重，存在返回 True"""
    conn = _get_connection()
    cursor = conn.execute("SELECT 1 FROM articles WHERE link = ?", (link,))
    result = cursor.fetchone() is not None
    conn.close()
    return result


def save_article(article: dict) -> bool:
    """
    插入新文章，link 重复则忽略
    返回 True 表示成功插入，False 表示重复忽略
    """
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO articles (title, link, source, published) VALUES (?, ?, ?, ?)",
            (article["title"], article["link"], article["source"], article["published"]),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_all_articles(source: str = None) -> list[dict]:
    """
    获取所有文章，支持按来源筛选，按 fetched_at 倒序
    """
    conn = _get_connection()
    if source and source != "全部":
        rows = conn.execute(
            "SELECT * FROM articles WHERE source = ? ORDER BY fetched_at DESC",
            (source,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM articles ORDER BY fetched_at DESC"
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_article(link: str) -> None:
    """删除指定文章"""
    conn = _get_connection()
    conn.execute("DELETE FROM articles WHERE link = ?", (link,))
    conn.commit()
    conn.close()


def prune_old_articles(days: int = 30) -> int:
    """
    清理指定天数前的旧记录
    返回删除的记录数
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_connection()
    cursor = conn.execute(
        "DELETE FROM articles WHERE fetched_at < ?", (cutoff,)
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def get_latest_fetch_date() -> str | None:
    """获取最近一次拉取文章的日期"""
    conn = _get_connection()
    row = conn.execute(
        "SELECT fetched_at FROM articles ORDER BY fetched_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        return row["fetched_at"][:10]  # 返回日期部分 YYYY-MM-DD
    return None


def get_read_links() -> set[str]:
    """
    从 reading_history 表获取所有已读文章 link 集合
    用于在每日推荐页标记已读状态
    """
    conn = _get_connection()
    # 确保 reading_history 表存在
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reading_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT DEFAULT ''
        )
    """)
    rows = conn.execute(
        "SELECT DISTINCT link FROM reading_history WHERE link != ''"
    ).fetchall()
    conn.close()
    return {row["link"] for row in rows}


def update_article_difficulty(link: str, difficulty: str) -> None:
    """根据 link 更新文章的难度标签"""
    conn = _get_connection()
    conn.execute(
        "UPDATE articles SET difficulty = ? WHERE link = ?",
        (difficulty, link),
    )
    conn.commit()
    conn.close()

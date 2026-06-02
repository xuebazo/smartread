"""
阅读历史数据仓储 — reading_history 表的 CRUD 封装
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent.parent / "cache.db"


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接，自动建表"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reading_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT '',
            source TEXT DEFAULT '',
            link TEXT DEFAULT '',
            article_text TEXT DEFAULT '',
            word_count INTEGER DEFAULT 0,
            difficulty TEXT DEFAULT '',
            difficulty_score INTEGER DEFAULT 0,
            difficulty_stars TEXT DEFAULT '',
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reading_minutes INTEGER DEFAULT 0,
            favorite INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reading_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            article_text TEXT DEFAULT '',
            article_source TEXT DEFAULT '',
            analysis_results TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 确保 reading_state 只有一行
    conn.execute("INSERT OR IGNORE INTO reading_state (id) VALUES (1)")
    conn.commit()
    return conn


def save_reading_history(
    title: str = "",
    source: str = "",
    link: str = "",
    article_text: str = "",
    word_count: int = 0,
    difficulty: str = "",
    difficulty_score: int = 0,
    difficulty_stars: str = "",
    reading_minutes: int = 0,
) -> int:
    """保存阅读记录，返回记录 ID"""
    conn = _get_conn()
    cursor = conn.execute(
        """INSERT INTO reading_history
           (title, source, link, article_text, word_count,
            difficulty, difficulty_score, difficulty_stars, reading_minutes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, source, link, article_text, word_count,
         difficulty, difficulty_score, difficulty_stars, reading_minutes),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_reading_history(source: str = None, favorite_only: bool = False) -> list[dict]:
    """获取阅读历史，支持按来源和收藏筛选"""
    conn = _get_conn()
    query = "SELECT * FROM reading_history WHERE 1=1"
    params: list = []
    if source and source != "全部":
        query += " AND source = ?"
        params.append(source)
    if favorite_only:
        query += " AND favorite = 1"
    query += " ORDER BY read_at DESC LIMIT 100"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_favorite(record_id: int) -> bool:
    """切换收藏状态，返回新状态"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT favorite FROM reading_history WHERE id = ?", (record_id,)
    ).fetchone()
    if row:
        new_val = 0 if row["favorite"] else 1
        conn.execute(
            "UPDATE reading_history SET favorite = ? WHERE id = ?", (new_val, record_id)
        )
        conn.commit()
        conn.close()
        return bool(new_val)
    conn.close()
    return False


def delete_history(record_id: int) -> None:
    """删除阅读记录"""
    conn = _get_conn()
    conn.execute("DELETE FROM reading_history WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


def get_reading_stats() -> dict:
    """获取阅读统计数据"""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) as cnt FROM reading_history").fetchone()
    today = conn.execute(
        "SELECT COUNT(*) as cnt FROM reading_history WHERE date(read_at) = date('now', 'localtime')"
    ).fetchone()
    total_words = conn.execute(
        "SELECT COALESCE(SUM(word_count), 0) as cnt FROM reading_history"
    ).fetchone()
    # ── 真连续打卡天数 ──
    dates = conn.execute(
        "SELECT DISTINCT date(read_at) as d FROM reading_history ORDER BY d DESC"
    ).fetchall()
    conn.close()

    consecutive = 0
    if dates:
        date_list = [row["d"] for row in dates]
        cursor_date = date_list[0]
        for d in date_list:
            if d == cursor_date:
                consecutive += 1
                cursor_date = (
                    datetime.strptime(cursor_date, "%Y-%m-%d") - timedelta(days=1)
                ).strftime("%Y-%m-%d")
            else:
                break

    return {
        "total": total["cnt"] if total else 0,
        "today": today["cnt"] if today else 0,
        "total_words": total_words["cnt"] if total_words else 0,
        "consecutive_days": consecutive,
    }


def get_difficulty_distribution() -> list[dict]:
    """
    获取阅读难度分布数据（用于柱状图）
    返回 [{"difficulty": "CET4", "count": 10}, ...]
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT difficulty, COUNT(*) as cnt FROM reading_history "
        "WHERE difficulty != '' GROUP BY difficulty"
    ).fetchall()
    conn.close()
    # 按固定顺序排列
    order = {"CET4": 0, "CET6": 1, "考研": 2, "IELTS": 3}
    result = [{"difficulty": d, "count": 0} for d in ["CET4", "CET6", "考研", "IELTS"]]
    for row in rows:
        diff = row["difficulty"]
        if diff in order:
            result[order[diff]]["count"] = row["cnt"]
    return result


# ─── 阅读状态恢复 ─────────────────────────────────────────

def save_reading_state(
    article_text: str = "",
    article_source: str = "",
    analysis_results: str = "",
) -> None:
    """保存当前阅读状态到 SQLite"""
    conn = _get_conn()
    conn.execute(
        """UPDATE reading_state
           SET article_text = ?, article_source = ?,
               analysis_results = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = 1""",
        (article_text, article_source, analysis_results),
    )
    conn.commit()
    conn.close()


def load_reading_state() -> dict:
    """从 SQLite 加载上次阅读状态"""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM reading_state WHERE id = 1").fetchone()
    conn.close()
    if row:
        return {
            "article_text": row["article_text"] or "",
            "article_source": row["article_source"] or "",
            "analysis_results": row["analysis_results"] or "",
        }
    return {}


def clear_reading_state() -> None:
    """清空阅读状态（退出文章时调用，避免刷新后自动恢复旧文章）"""
    conn = _get_conn()
    conn.execute("DELETE FROM reading_state WHERE id = 1")
    conn.execute("INSERT OR IGNORE INTO reading_state (id) VALUES (1)")
    conn.commit()
    conn.close()

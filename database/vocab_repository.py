"""
生词本数据仓储 — saved_words 表的 CRUD 封装
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "cache.db"


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接，自动建表"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            phonetic TEXT DEFAULT '',
            meaning TEXT DEFAULT '',
            example TEXT DEFAULT '',
            source_article TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            review_count INTEGER DEFAULT 0,
            known_level INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        DELETE FROM saved_words
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM saved_words
            GROUP BY lower(trim(word))
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_words_word_norm
        ON saved_words (lower(trim(word)))
    """)
    conn.commit()
    return conn


def _normalize_word(word: str) -> str:
    """统一单词格式，避免 Apple/apple/ apple 被当成不同词。"""
    return " ".join((word or "").strip().lower().split())


def save_word(word_data: dict) -> bool:
    """
    收藏单词，重复则忽略
    word_data: {"word", "phonetic", "meaning", "sentence"(作为example), "source_article"}
    """
    word = _normalize_word(word_data.get("word", ""))
    if not word:
        return False

    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO saved_words (word, phonetic, meaning, example, source_article)
               VALUES (?, ?, ?, ?, ?)""",
            (
                word,
                word_data.get("phonetic", ""),
                word_data.get("meaning", ""),
                word_data.get("sentence", word_data.get("example", "")),
                word_data.get("source_article", ""),
            ),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def is_saved(word: str) -> bool:
    """检查单词是否已收藏"""
    word = _normalize_word(word)
    if not word:
        return False
    conn = _get_conn()
    row = conn.execute(
        "SELECT 1 FROM saved_words WHERE lower(trim(word)) = ?",
        (word,),
    ).fetchone()
    conn.close()
    return row is not None


def get_all_words(search: str = None) -> list[dict]:
    """获取所有生词，支持搜索，按创建时间倒序"""
    conn = _get_conn()
    if search:
        rows = conn.execute(
            "SELECT * FROM saved_words WHERE word LIKE ? OR meaning LIKE ? ORDER BY created_at DESC",
            (f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM saved_words ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_word(word_id: int) -> None:
    """删除生词"""
    conn = _get_conn()
    conn.execute("DELETE FROM saved_words WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()


def mark_known(word_id: int, level: int = 2) -> None:
    """
    标记掌握程度：0=新词, 1=认识, 2=掌握
    """
    conn = _get_conn()
    conn.execute(
        "UPDATE saved_words SET known_level = ?, review_count = review_count + 1 WHERE id = ?",
        (level, word_id),
    )
    conn.commit()
    conn.close()


def get_word_count() -> int:
    """获取生词总数"""
    conn = _get_conn()
    row = conn.execute("SELECT COUNT(*) as cnt FROM saved_words").fetchone()
    conn.close()
    return row["cnt"] if row else 0


def get_word_growth() -> list[dict]:
    """
    获取每日累积生词数（用于折线图）
    返回 [{"date": "2026-05-01", "count": 15}, ...]
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT date(created_at) as d, COUNT(*) as cnt "
        "FROM saved_words GROUP BY d ORDER BY d"
    ).fetchall()
    conn.close()
    if not rows:
        return []
    cumulative = 0
    result = []
    for row in rows:
        cumulative += row["cnt"]
        result.append({"date": row["d"], "count": cumulative})
    return result


def get_due_words(limit: int = 10) -> list[dict]:
    """
    获取待复习单词（闪卡模式用）
    优先返回 known_level=0（新词），其次 known_level=1（认识），排除 known_level=2（已掌握）
    按 review_count ASC 排序，取前 limit 条
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM saved_words WHERE known_level < 2 "
        "ORDER BY known_level ASC, review_count ASC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

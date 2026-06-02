"""
SmartRead · 个人 AI 英语阅读助手 — Streamlit 主程序
"""
import sys
from pathlib import Path
import html

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import requests
import time
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import get_api_key
from agents.translator import translate_article
from agents.vocabulary import extract_vocabulary
from agents.grammar import analyze_grammar
from agents.difficulty import analyze_difficulty
from agents.difficulty import _rule_based_difficulty as rule_difficulty
from rss_fetcher import fetch_all_feeds, SOURCES
from article_cache import (
    is_duplicate,
    save_article,
    get_all_articles,
    get_latest_fetch_date,
    prune_old_articles,
    get_read_links,
    update_article_difficulty,
)
from utils import extract_article_text
from services.backup_service import run_backup
from database.vocab_repository import (
    save_word,
    is_saved as is_word_saved,
    get_all_words,
    delete_word,
    mark_known,
    get_word_count,
    get_word_growth,
    get_due_words,
)
from database.history_repository import (
    save_reading_history,
    get_reading_history,
    toggle_favorite,
    delete_history,
    get_reading_stats,
    get_difficulty_distribution,
    save_reading_state,
    load_reading_state,
    clear_reading_state,
)

# ─── 页面配置 ────────────────────────────────────────────
st.set_page_config(
    page_title="SmartRead · 个人 AI 英语阅读助手",
    page_icon="📖",
    layout="wide",
)

# ─── 样式 ────────────────────────────────────────────────
st.markdown("""
<style>
    .source-tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 8px;
    }
    .source-lutoushe { background-color: #dbeafe; color: #1e40af; }
    .source-weibao { background-color: #dcfce7; color: #166534; }
    .source-kexuemeiguoren { background-color: #f3e8ff; color: #6b21a8; }
    .source-bbcnews { background-color: #fef3c7; color: #92400e; }
    .source-npr { background-color: #fce7f3; color: #9d174d; }
    .diff-tag {
        display: inline-block;
        padding: 1px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-left: 4px;
    }
    .diff-cet4 { background-color: #dcfce7; color: #166534; }
    .diff-cet6 { background-color: #dbeafe; color: #1e40af; }
    .diff-kaoyan { background-color: #fef3c7; color: #92400e; }
    .diff-ielts { background-color: #fce7f3; color: #9d174d; }
    .diff-unknown { background-color: #f3f4f6; color: #9ca3af; }
    .article-card {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        transition: box-shadow 0.2s;
    }
    .article-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .original-text {
        background-color: #f3f4f6;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .translated-text {
        background-color: #eff6ff;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


# ─── 来源颜色映射 ────────────────────────────────────────
def get_source_class(source_name: str) -> str:
    mapping = {
        "纽约时报": "lutoushe",
        "卫报": "weibao",
        "科学美国人": "kexuemeiguoren",
        "BBC News": "bbcnews",
        "NPR": "npr",
    }
    return mapping.get(source_name, "lutoushe")


# ─── 数据库自动备份 ────────────────────────────
run_backup()

# ─── 状态初始化 ──────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "📰 每日推荐"
if "article_text" not in st.session_state:
    st.session_state.article_text = ""
if "article_source" not in st.session_state:
    st.session_state.article_source = ""
if "feeds_loaded" not in st.session_state:
    st.session_state.feeds_loaded = False
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "extraction_failed" not in st.session_state:
    st.session_state.extraction_failed = False
if "failed_article_link" not in st.session_state:
    st.session_state.failed_article_link = ""
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}
if "read_start_time" not in st.session_state:
    st.session_state.read_start_time = 0.0
if "reading_history_id" not in st.session_state:
    st.session_state.reading_history_id = None
if "review_words" not in st.session_state:
    st.session_state.review_words = []
if "review_index" not in st.session_state:
    st.session_state.review_index = 0
if "review_known" not in st.session_state:
    st.session_state.review_known = 0
if "review_unknown" not in st.session_state:
    st.session_state.review_unknown = 0
if "review_show_answer" not in st.session_state:
    st.session_state.review_show_answer = False
if "current_article_title" not in st.session_state:
    st.session_state.current_article_title = ""
if "current_article_source_name" not in st.session_state:
    st.session_state.current_article_source_name = ""
if "current_article_link" not in st.session_state:
    st.session_state.current_article_link = ""

# ─── 自动恢复阅读状态 ──────
if not st.session_state.article_text and not st.session_state.analysis_results:
    saved = load_reading_state()
    if saved.get("article_text"):
        st.session_state.article_text = saved["article_text"]
        st.session_state.article_source = saved.get("article_source", "")
        st.session_state.analysis_done = False
        st.session_state.analysis_results = {}
        import json
        try:
            st.session_state.saved_results = json.loads(saved.get("analysis_results", "{}"))
        except (json.JSONDecodeError, TypeError):
            st.session_state.saved_results = {}


# ─── API 状态检查 ────────────────────────────────────────
def check_api_status() -> tuple[bool, str]:
    """测试 DeepSeek API 连通性"""
    try:
        api_key = get_api_key()
        response = requests.get(
            "https://api.deepseek.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "已连接"
        else:
            return False, f"状态码 {response.status_code}"
    except RuntimeError:
        return False, "未配置密钥"
    except Exception as e:
        return False, f"连接失败: {str(e)[:30]}"


def _save_reading_time() -> None:
    """保存当前阅读时长到最新阅读记录"""
    if st.session_state.read_start_time > 0 and st.session_state.reading_history_id:
        elapsed = int((time.time() - st.session_state.read_start_time) / 60)
        if elapsed > 0:
            from database.history_repository import _get_conn
            conn = _get_conn()
            conn.execute(
                "UPDATE reading_history SET reading_minutes = ? WHERE id = ?",
                (elapsed, st.session_state.reading_history_id),
            )
            conn.commit()
            conn.close()
        st.session_state.read_start_time = 0.0
        st.session_state.reading_history_id = None


def _load_article_into_state(article: dict, full_text: str) -> None:
    """保存当前文章的正文和元数据，供分析、历史记录、已读判断复用。"""
    st.session_state.article_text = full_text
    st.session_state.current_article_title = article.get("title", "")
    st.session_state.current_article_source_name = article.get("source", "")
    st.session_state.current_article_link = article.get("link", "")
    st.session_state.article_source = (
        f"{st.session_state.current_article_source_name} · "
        f"{st.session_state.current_article_title}"
    ).strip(" ·")
    st.session_state.page = "📖 阅读工具"
    st.session_state.analysis_done = False
    st.session_state.extraction_failed = False
    st.session_state.failed_article_link = ""


def _set_article_extraction_failed(article: dict) -> None:
    """保存抓取失败的文章元数据，方便用户手动粘贴后仍能记录来源。"""
    st.session_state.article_text = ""
    st.session_state.current_article_title = article.get("title", "")
    st.session_state.current_article_source_name = article.get("source", "")
    st.session_state.current_article_link = article.get("link", "")
    st.session_state.article_source = (
        f"{st.session_state.current_article_source_name} · "
        f"{st.session_state.current_article_title}"
    ).strip(" ·")
    st.session_state.page = "📖 阅读工具"
    st.session_state.analysis_done = False
    st.session_state.extraction_failed = True
    st.session_state.failed_article_link = article.get("link", "")


def _start_flashcard_review() -> None:
    """初始化闪卡复习会话"""
    due = get_due_words(limit=10)
    if due:
        st.session_state.review_words = due
        st.session_state.review_index = 0
        st.session_state.review_known = 0
        st.session_state.review_unknown = 0
        st.session_state.review_show_answer = False
        st.rerun()


def _render_flashcard_review() -> None:
    """渲染闪卡复习界面"""
    total_cards = len(st.session_state.review_words)
    idx = st.session_state.review_index

    if idx >= total_cards:
        # 复习完成 → 显示报告
        known = st.session_state.review_known
        unknown = st.session_state.review_unknown
        st.success("🎉 复习完成！")
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("总共复习", total_cards)
        col_r2.metric("✅ 认识", known)
        col_r3.metric("❌ 还需努力", unknown)
        if st.button("🔙 返回生词本", use_container_width=True):
            st.session_state.review_words = []
            st.rerun()
        return

    card = st.session_state.review_words[idx]

    # 进度条
    progress = (idx + 1) / total_cards
    st.progress(progress, text=f"第 {idx + 1} / {total_cards} 张")

    # 闪卡
    with st.container():
        st.markdown("### " + card["word"])
        if card.get("phonetic"):
            st.caption(card["phonetic"])

        if not st.session_state.review_show_answer:
            if st.button("👁️ 显示答案", key=f"show_{idx}", use_container_width=True):
                st.session_state.review_show_answer = True
                st.rerun()
        else:
            st.markdown(f"**释义**：{card.get('meaning', '')}")
            if card.get("example"):
                st.caption(f"📝 {card['example']}")

            col_k, col_u, col_q = st.columns([1, 1, 2])
            with col_k:
                if st.button("✅ 认识了", key=f"known_{idx}", use_container_width=True):
                    mark_known(card["id"], level=min(card.get("known_level", 0) + 1, 2))
                    st.session_state.review_known += 1
                    st.session_state.review_index += 1
                    st.session_state.review_show_answer = False
                    st.rerun()
            with col_u:
                if st.button("❌ 还不会", key=f"unknown_{idx}", use_container_width=True):
                    mark_known(card["id"], level=card.get("known_level", 0))
                    st.session_state.review_unknown += 1
                    st.session_state.review_index += 1
                    st.session_state.review_show_answer = False
                    st.rerun()
            with col_q:
                if st.button("🛑 结束复习", key=f"quit_{idx}", use_container_width=True):
                    st.session_state.review_words = []
                    st.rerun()


# ─── 侧边栏 ──────────────────────────────────────────────
with st.sidebar:
    st.title("📖 SmartRead")
    st.caption("个人 AI 英语阅读助手")

    # 导航
    page = st.radio(
        "导航",
        ["📰 每日推荐", "📖 阅读工具", "🧠 生词本", "📚 阅读记录"],
        index=0 if st.session_state.page == "📰 每日推荐"
        else (1 if st.session_state.page == "📖 阅读工具"
        else (2 if st.session_state.page == "🧠 生词本" else 3)),
        label_visibility="collapsed",
    )

    # 页面切换时先保存阅读时长再更新状态
    if page != st.session_state.page:
        _save_reading_time()
        st.session_state.page = page
        st.rerun()

    st.divider()

    # 底部信息
    st.caption("**版本**: v2.0")
    st.caption("**路径**: D:\\\\smartread")

    # API 状态指示器
    api_ok, api_msg = check_api_status()
    if api_ok:
        st.success(f"🟢 API {api_msg}")
    else:
        st.error(f"🔴 API {api_msg}")


# ═══════════════════════════════════════════════════════════
# 页面 1：📰 每日推荐
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "📰 每日推荐":
    st.title("📰 每日外刊精选")

    # ── 刷新按钮 ──
    col1, col2 = st.columns([2, 10])
    with col1:
        refresh_clicked = st.button("🔄 刷新文章列表", use_container_width=True)

    if refresh_clicked:
        with st.spinner("正在从各外刊拉取最新文章..."):
            articles = fetch_all_feeds()
            new_count = 0
            for article in articles:
                if not is_duplicate(article["link"]):
                    save_article(article)
                    new_count += 1
            st.session_state.feeds_loaded = True

        if new_count > 0:
            st.success(f"✅ 本次新增 {new_count} 篇文章")
        else:
            st.info("暂无新文章，所有文章已在缓存中。")

        # 清理 30 天前的旧记录
        deleted = prune_old_articles(days=30)
        if deleted > 0:
            st.caption(f"已自动清理 {deleted} 条过期记录")

    # ── 来源筛选器 ──
    col_src, col_unread, col_diff = st.columns([3, 2, 2])
    with col_src:
        source_options = ["全部"] + list(SOURCES.keys())
        selected_source = st.selectbox("按来源筛选", source_options)
    with col_unread:
        show_unread_only = st.checkbox("仅显示未读", key="unread_filter")
    with col_diff:
        diff_options = ["全部", "CET4", "CET6", "考研", "IELTS", "未知"]
        selected_difficulty = st.selectbox("难度筛选", diff_options, key="diff_filter")

    # ── 文章列表 ──
    read_links = get_read_links()
    articles = get_all_articles(source=selected_source if selected_source != "全部" else None)

    # 过滤已读
    if show_unread_only:
        articles = [a for a in articles if a["link"] not in read_links]

    # 过滤难度
    if selected_difficulty != "全部":
        if selected_difficulty == "未知":
            articles = [a for a in articles if not a.get("difficulty")]
        else:
            articles = [a for a in articles if selected_difficulty in a.get("difficulty", "")]

    if not articles:
        if show_unread_only:
            st.info("所有文章已读完 🎉")
        else:
            st.info("暂无推荐文章，请点击「🔄 刷新文章列表」获取最新外刊文章。")
    else:
        st.caption(f"共 {len(articles)} 篇文章")

        for article in articles:
            with st.container():
                st.markdown(f'<div class="article-card">', unsafe_allow_html=True)

                # 标题
                st.markdown(f"**{article['title']}**")

                # 来源标签 + 日期
                col_tag, col_date, col_btn = st.columns([2, 3, 2])
                source_class = get_source_class(article["source"])
                diff_raw = article.get("difficulty", "")
                if diff_raw:
                    # 从 "CET6 ★★★☆☆" 提取难度标签
                    diff_parts = diff_raw.split()
                    diff_level = diff_parts[0] if diff_parts else ""
                    diff_stars = diff_parts[1] if len(diff_parts) > 1 else diff_raw
                    diff_css = {
                        "CET4": "diff-cet4", "CET6": "diff-cet6",
                        "考研": "diff-kaoyan", "IELTS": "diff-ielts"
                    }.get(diff_level, "diff-unknown")
                    diff_html = f'<span class="diff-tag {diff_css}">{html.escape(diff_raw)}</span>'
                else:
                    diff_html = '<span class="diff-tag diff-unknown">— 未知</span>'
                col_tag.markdown(
                    f'<span class="source-tag source-{source_class}">{html.escape(article["source"])}</span>{diff_html}',
                    unsafe_allow_html=True,
                )
                col_date.caption(article.get("published", "未知日期"))

                # 摘要
                if article.get("summary"):
                    st.caption(article["summary"][:200])

                # 开始阅读按钮
                read_key = f"read_{article['id']}"
                is_read = article["link"] in read_links
                if is_read:
                    if col_btn.button("✅ 已读 / 重读", key=read_key, use_container_width=True):
                        _save_reading_time()
                        link = article["link"]
                        with st.spinner("正在获取文章全文..."):
                            full_text = extract_article_text(link)
                        if full_text:
                            # 规则模式计算难度（不调用 AI，不增加等待）
                            try:
                                diff = rule_difficulty(full_text)
                                diff_label = f"{diff.get('level','')} {diff.get('stars','')}"
                                update_article_difficulty(link, diff_label)
                            except Exception:
                                pass
                            _load_article_into_state(article, full_text)
                            st.success("✅ 已自动获取全文，正在跳转到阅读工具...")
                            st.rerun()
                        else:
                            _set_article_extraction_failed(article)
                            st.rerun()
                else:
                    if col_btn.button("📖 开始阅读", key=read_key, use_container_width=True):
                        _save_reading_time()
                        link = article["link"]
                        with st.spinner("正在获取文章全文..."):
                            full_text = extract_article_text(link)

                        if full_text:
                            # 规则模式计算难度（不调用 AI，不增加等待）
                            try:
                                diff = rule_difficulty(full_text)
                                diff_label = f"{diff.get('level','')} {diff.get('stars','')}"
                                update_article_difficulty(link, diff_label)
                            except Exception:
                                pass
                            _load_article_into_state(article, full_text)
                            st.success("✅ 已自动获取全文，正在跳转到阅读工具...")
                            st.rerun()
                        else:
                            _set_article_extraction_failed(article)
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# 页面 2：📖 阅读工具
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "📖 阅读工具":
    has_article = bool(st.session_state.article_source or st.session_state.article_text.strip())

    if has_article:
        st.title("📖 文章阅读分析")
    else:
        st.title("📖 文章阅读 / 翻译工具")

    # ── 来源提示 + 退出按钮 ──
    if st.session_state.article_source:
        col_src, col_exit = st.columns([8, 2])
        with col_src:
            st.info(f"📌 来源：{st.session_state.article_source}")
        with col_exit:
            if st.button("✖ 退出文章", use_container_width=True):
                st.session_state.article_text = ""
                st.session_state.article_source = ""
                st.session_state.current_article_title = ""
                st.session_state.current_article_source_name = ""
                st.session_state.current_article_link = ""
                st.session_state.analysis_results = {}
                st.session_state.analysis_done = False
                st.session_state.extraction_failed = False
                st.session_state.failed_article_link = ""
                clear_reading_state()
                st.rerun()

    # ── 难度评级 ──（有分析结果且无错误时才显示）
    if st.session_state.analysis_results and has_article:
        difficulty = st.session_state.analysis_results.get("difficulty", {})
        if isinstance(difficulty, dict) and "level" in difficulty:
            level = difficulty.get("level", "CET4")
            stars = difficulty.get("stars", "★★☆☆☆")
            reason = difficulty.get("reason", "")
            col_d1, col_d2 = st.columns([2, 8])
            with col_d1:
                st.markdown(f"### 难度：{level} {stars}")
            with col_d2:
                st.caption(reason)

    # ── 自动提取失败降级提示 ──
    if st.session_state.extraction_failed:
        st.warning(
            "⚠️ 无法自动获取文章全文（可能为付费内容或网站限制）。"
            "请点击下方链接打开原文，复制正文后粘贴到文本框中。"
        )
        if st.session_state.failed_article_link:
            st.markdown(f"📎 [打开原文链接]({st.session_state.failed_article_link})")

    # ── 文章输入区 ──
    placeholder_text = (
        "在此粘贴英语文章（建议 500-2000 词）" if has_article
        else "粘贴任意英文段落，进行翻译、词汇提取或语法分析"
    )
    article_text = st.text_area(
        "在此粘贴英语文章（建议 500-2000 词）",
        value=st.session_state.article_text,
        height=250,
        placeholder="在此粘贴英语文章...\n\n也可从每日推荐页面选择文章自动填充。",
    )
    # 同步到 session_state
    st.session_state.article_text = article_text

    # ── 开始分析按钮 ──
    analyze_clicked = st.button(
        "🚀 开始智能阅读" if has_article else "🚀 开始分析",
        type="primary", use_container_width=True)

    if analyze_clicked:
        if not article_text.strip():
            st.warning("请先输入或粘贴英语文章。")
        else:
            st.session_state.analysis_done = True
            st.session_state.analysis_results = {}  # 清空旧结果

    # ── 并发执行分析 ──
    if (
        st.session_state.analysis_done
        and article_text.strip()
        and not st.session_state.analysis_results
    ):
        # 检查 API Key
        try:
            get_api_key()
        except RuntimeError as e:
            st.error(f"❌ 未找到 DEEPSEEK_API_KEY，请在 D:\\smartread\\.env 文件中配置后重试。")
            st.stop()

        with st.spinner("🤖 三个 AI Agent 正在并发分析中（翻译 + 词汇 + 语法）..."):
            results = {}
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(translate_article, article_text): "translation",
                    executor.submit(extract_vocabulary, article_text): "vocabulary",
                    executor.submit(analyze_grammar, article_text): "grammar",
                    executor.submit(analyze_difficulty, article_text): "difficulty",
                }
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        results[key] = future.result()
                    except Exception as e:
                        results[key] = {"_error": str(e)}
            st.session_state.analysis_results = results

            # ── 保存阅读历史 ──
            difficulty = results.get("difficulty", {})
            word_count_val = len(article_text.split()) if article_text else 0
            history_id = save_reading_history(
                title=st.session_state.current_article_title or "手动输入",
                source=st.session_state.current_article_source_name or "手动输入",
                link=st.session_state.current_article_link or "",
                article_text=article_text[:5000],
                word_count=word_count_val,
                difficulty=difficulty.get("level", "") if isinstance(difficulty, dict) else "",
                difficulty_score=difficulty.get("score", 0) if isinstance(difficulty, dict) else 0,
                difficulty_stars=difficulty.get("stars", "") if isinstance(difficulty, dict) else "",
            )
            st.session_state.reading_history_id = history_id
            st.session_state.read_start_time = time.time()
            # ── 保存阅读状态（恢复用）──
            import json
            save_reading_state(
                article_text=article_text,
                article_source=st.session_state.article_source,
                analysis_results=json.dumps(results, ensure_ascii=False),
            )
            st.rerun()

    # ── 显示分析结果 ──
    if st.session_state.analysis_done and st.session_state.analysis_results:
        st.divider()

        tab1, tab2, tab3 = st.tabs(["📖 中英对照", "📝 核心词汇", "🧠 长难句分析"])

        # ── Tab 1：翻译 ──
        with tab1:
            translation = st.session_state.analysis_results.get("translation", {})
            if isinstance(translation, dict) and "_error" in translation:
                st.error(f"翻译失败：{translation['_error']}")
            elif translation and "paragraphs" in translation:
                for i, para in enumerate(translation["paragraphs"]):
                    st.markdown(f"**段落 {i + 1}**")
                    if para.get("original"):
                        st.markdown(
                            f'<div class="original-text">{html.escape(para["original"])}</div>',
                            unsafe_allow_html=True,
                        )
                    if para.get("translated"):
                        st.markdown(
                            f'<div class="translated-text">{html.escape(para["translated"])}</div>',
                            unsafe_allow_html=True,
                        )
            elif translation and "raw_translation" in translation:
                st.text_area("翻译结果（原始格式）", translation["raw_translation"], height=300)
            else:
                st.warning("翻译结果为空，请重试。")

        # ── Tab 2：词汇 ──
        with tab2:
            vocab = st.session_state.analysis_results.get("vocabulary", [])
            if isinstance(vocab, dict) and "_error" in vocab:
                st.error(f"词汇提取失败：{vocab['_error']}")
            elif vocab and isinstance(vocab, list):
                table_data = []
                for i, v in enumerate(vocab):
                    word = v.get("word", "")
                    already_saved = is_word_saved(word)
                    col_t1, col_t2 = st.columns([10, 1])
                    with col_t1:
                        st.markdown(f"**{word}**  {v.get('phonetic', '')}  —  *{v.get('meaning', '')}*")
                        st.caption(v.get("sentence", ""))
                    with col_t2:
                        if already_saved:
                            st.button("⭐", key=f"star_{i}_{word[:8]}", disabled=True, help="已收藏")
                        else:
                            if st.button("☆", key=f"star_{i}_{word[:8]}", help="点击收藏"):
                                word_data = {
                                    "word": word,
                                    "phonetic": v.get("phonetic", ""),
                                    "meaning": v.get("meaning", ""),
                                    "sentence": v.get("sentence", ""),
                                    "source_article": st.session_state.article_source,
                                }
                                if save_word(word_data):
                                    st.success(f"已收藏「{word}」")
                                    st.rerun()
                    st.divider()
                st.caption(f"共提取 {len(vocab)} 个核心词汇")
            else:
                st.info("未提取到四六级核心词汇")

        # ── Tab 3：语法 ──
        with tab3:
            grammar = st.session_state.analysis_results.get("grammar", [])
            if isinstance(grammar, dict) and "_error" in grammar:
                st.error(f"语法分析失败：{grammar['_error']}")
            elif grammar and isinstance(grammar, list):
                for i, item in enumerate(grammar):
                    with st.container():
                        st.markdown(f"**原句 {i + 1}：**")
                        st.markdown(
                            f'<div class="original-text">{html.escape(item.get("sentence", ""))}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown("**语法分析：**")
                        st.markdown(item.get("analysis", ""))
                        st.divider()
            else:
                st.info("未发现复杂长难句")

    elif not st.session_state.analysis_done:
        # 未分析时的提示
        if st.session_state.article_source:
            btn_label = "🚀 开始智能阅读" if has_article else "🚀 开始分析"
            st.info(f"👆 文章已自动填充，点击上方「{btn_label}」按钮开始分析。")


# ═══════════════════════════════════════════════════════════
# 页面 3：🧠 生词本
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "🧠 生词本":
    st.title("🧠 我的生词本")

    total = get_word_count()
    st.caption(f"共收藏 {total} 个生词")

    # ── 闪卡复习模式 ──
    if st.session_state.review_words:
        _render_flashcard_review()
    else:
        # 正常生词本视图
        # 复习按钮
        if total > 0:
            st.button("🃏 开始复习", on_click=_start_flashcard_review, use_container_width=True)

        # 搜索
        search_term = st.text_input("🔍 搜索单词或释义", placeholder="输入关键词筛选...")

        words = get_all_words(search=search_term if search_term else None)

        if not words:
            if search_term:
                st.info(f"未找到匹配「{search_term}」的生词")
            else:
                st.info("还没有收藏过生词。在「阅读工具」中分析文章后，点击词汇旁的 ⭐ 即可收藏。")
        else:
            for w in words:
                with st.expander(f"**{w['word']}**  {w.get('phonetic', '')}  —  {w.get('meaning', '')}"):
                    st.caption(f"📝 例句：{w.get('example', '')}")
                    if w.get("source_article"):
                        st.caption(f"📌 来源：{w['source_article']}")
                    st.caption(f"📅 收藏时间：{w.get('created_at', '')[:10]}")
                    st.caption(f"🔁 复习次数：{w.get('review_count', 0)}")

                    col_k1, col_k2, col_k3 = st.columns([1, 1, 2])
                    with col_k1:
                        if st.button("✅ 认识", key=f"know_{w['id']}"):
                            mark_known(w["id"], level=1)
                            st.rerun()
                    with col_k2:
                        if st.button("🎓 掌握", key=f"master_{w['id']}"):
                            mark_known(w["id"], level=2)
                            st.rerun()
                    with col_k3:
                        if st.button("🗑️ 删除", key=f"del_{w['id']}"):
                            delete_word(w["id"])
                            st.rerun()

    # ── 词汇增长折线图 ──
    st.divider()
    growth = get_word_growth()
    if growth and len(growth) >= 3:
        import pandas as pd
        df = pd.DataFrame(growth)
        df = df.set_index("date")
        st.subheader("📈 词汇增长趋势")
        st.line_chart(df["count"])
    elif growth:
        st.caption("📈 数据点不足，继续积累后生成趋势图")
    else:
        st.caption("📈 暂无数据，开始收藏生词后自动生成")


# ═══════════════════════════════════════════════════════════
# 页面 4：📚 阅读记录
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "📚 阅读记录":
    st.title("📚 阅读记录")

    # ── 统计卡片 ──
    stats = get_reading_stats()
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("📖 总阅读篇数", stats["total"])
    with col_s2:
        st.metric("📅 今日阅读", stats["today"])
    with col_s3:
        st.metric("📝 累计词数", f"{stats['total_words']:,}")
    with col_s4:
        st.metric("🔥 连续天数", f"{stats['consecutive_days']}天")

    st.divider()

    # ── 难度分布柱状图 ──
    diff_data = get_difficulty_distribution()
    if diff_data and any(d["count"] > 0 for d in diff_data):
        import pandas as pd
        df_diff = pd.DataFrame(diff_data)
        df_diff = df_diff.set_index("difficulty")
        st.subheader("📊 阅读难度分布")
        st.bar_chart(df_diff["count"])
    else:
        st.caption("📊 暂无数据，开始阅读后自动生成")

    st.divider()

    # ── 筛选 ──
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        source_options = ["全部"] + list(SOURCES.keys())
        hist_source = st.selectbox("按来源筛选", source_options, key="hist_source")
    with col_f2:
        fav_only = st.checkbox("⭐ 仅收藏", key="fav_only")

    histories = get_reading_history(
        source=hist_source if hist_source != "全部" else None,
        favorite_only=fav_only,
    )

    if not histories:
        st.info("暂无阅读记录。分析文章后自动记录。")
    else:
        st.caption(f"共 {len(histories)} 条记录")
        for h in histories:
            with st.container():
                st.markdown(f'<div class="article-card">', unsafe_allow_html=True)
                col_h1, col_h2 = st.columns([8, 2])
                with col_h1:
                    title_display = h.get("title", "无标题")[:80]
                    st.markdown(f"**{title_display}**")
                    minutes = h.get('reading_minutes', 0) or 0
                    time_str = f"⏱️ {minutes}分钟" if minutes > 0 else "⏱️ —"
                    st.caption(
                        f"📅 {h.get('read_at', '')[:10]}"
                        f"  ·  {time_str}"
                        f"  ·  📝 {h.get('word_count', 0)}词"
                        f"  ·  难度 {h.get('difficulty', '?')} {h.get('difficulty_stars', '')}"
                    )
                with col_h2:
                    fav = h.get("favorite", 0)
                    if h.get("article_text"):
                        if st.button("📖 重新阅读", key=f"reread_{h['id']}", help="在阅读工具中打开"):
                            _save_reading_time()
                            st.session_state.article_text = h.get("article_text", "")
                            st.session_state.current_article_title = h.get("title", "")
                            st.session_state.current_article_source_name = h.get("source", "")
                            st.session_state.current_article_link = h.get("link", "")
                            st.session_state.article_source = (
                                f"{h.get('source', '')} · {h.get('title', '')}"
                            ).strip(" ·")
                            st.session_state.analysis_results = {}
                            st.session_state.analysis_done = False
                            st.session_state.extraction_failed = False
                            st.session_state.failed_article_link = ""
                            st.session_state.page = "📖 阅读工具"
                            st.rerun()
                    if st.button("⭐" if fav else "☆", key=f"fav_{h['id']}", help="收藏/取消"):
                        toggle_favorite(h["id"])
                        st.rerun()
                    if st.button("🗑️", key=f"histdel_{h['id']}", help="删除"):
                        delete_history(h["id"])
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

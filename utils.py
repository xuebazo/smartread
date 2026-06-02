"""
工具函数模块 - 网页正文提取与文本清理
支持 newspaper3k + BeautifulSoup 双引擎提取
"""
import re
import ipaddress
import socket
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# ── 请求头配置 ──────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_REDIRECTS = 3
MAX_HTML_BYTES = 3 * 1024 * 1024


# ═══════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════

def _extract_with_newspaper(url: str, html: str = "") -> str:
    """
    使用 newspaper3k 库提取文章正文（可选依赖）
    成功返回 article.text，未安装或失败返回空字符串
    """
    try:
        import newspaper
        article = newspaper.Article(url)
        if html:
            article.set_html(html)
        else:
            article.download()
        article.parse()
        text = article.text
        return text if text else ""
    except ImportError:
        return ""  # newspaper3k 未安装，静默跳过
    except Exception:
        return ""


def _is_safe_public_url(url: str) -> bool:
    """只允许抓取公网 http/https URL，避免 RSS 异常链接访问本机或内网。"""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False

        host = parsed.hostname.strip().lower()
        if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
            return False

        try:
            ip = ipaddress.ip_address(host)
            return not (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            )
        except ValueError:
            pass

        try:
            for result in socket.getaddrinfo(host, None):
                ip = ipaddress.ip_address(result[4][0])
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_multicast
                    or ip.is_reserved
                    or ip.is_unspecified
                ):
                    return False
        except OSError:
            return False

        return True
    except Exception:
        return False


def _safe_get(url: str) -> requests.Response | None:
    """带 URL 校验、重定向校验和响应大小限制的 GET。"""
    current_url = url
    for _ in range(MAX_REDIRECTS + 1):
        if not _is_safe_public_url(current_url):
            return None

        response = requests.get(
            current_url,
            headers=HEADERS,
            timeout=15,
            allow_redirects=False,
            stream=True,
        )
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            response.close()
            if not location:
                return None
            current_url = urljoin(current_url, location)
            continue

        response.raise_for_status()
        content = response.raw.read(MAX_HTML_BYTES + 1, decode_content=True)
        response.close()
        if len(content) > MAX_HTML_BYTES:
            return None
        response._content = content
        return response

    return None


def _extract_with_bs4(html: str) -> str:
    """
    使用 BeautifulSoup 多选择器策略提取正文
    按优先级尝试多种选择器，返回拼接后的段落文本
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        # 移除干扰标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
            tag.decompose()

        candidates = []

        # 策略 a：<article> 标签
        article_tag = soup.find("article")
        if article_tag:
            candidates.append(article_tag)

        # 策略 b：常见正文容器 class
        selectors_b = [
            "[class*='article-content']",
            "[class*='article-body']",
            "[class*='story-body']",
            "[class*='post-content']",
        ]
        for sel in selectors_b:
            container = soup.select_one(sel)
            if container:
                candidates.append(container)
                break  # 找到第一个即停止

        # 策略 c：次要正文容器 class
        selectors_c = [
            "[class*='main-content']",
            "[class*='entry-content']",
        ]
        for sel in selectors_c:
            container = soup.select_one(sel)
            if container and container not in candidates:
                candidates.append(container)
                break

        # 策略 d：<section> 内包含较多 <p> 的区块
        sections = soup.find_all("section")
        if sections:
            best_section = None
            best_count = 0
            for sec in sections:
                p_count = len(sec.find_all("p"))
                if p_count > best_count:
                    best_count = p_count
                    best_section = sec
            if best_section and best_count >= 2:
                candidates.append(best_section)

        # 从候选区块提取段落文本
        for container in candidates:
            texts = []
            for p in container.find_all("p"):
                text = p.get_text(strip=True)
                if len(text) > 20:  # 过滤短段落（导航、广告等）
                    texts.append(text)
            if texts:
                return "\n\n".join(texts)

        # 最后一招：从整个页面提取所有合格 <p> 标签
        all_paragraphs = soup.find_all("p")
        texts = []
        for p in all_paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 20:
                texts.append(text)
        if texts:
            return "\n\n".join(texts)

        return ""

    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════

def extract_article_text(url: str) -> str:
    """
    从网页 URL 提取正文内容
    优先使用 newspaper3k，失败则降级为 BeautifulSoup 多选择器提取
    若均失败或提取内容不足 200 字符，返回空字符串
    """
    try:
        if not _is_safe_public_url(url):
            return ""

        response = _safe_get(url)
        if response is None:
            return ""
        response.encoding = response.apparent_encoding

        # 先尝试 newspaper3k（使用已安全下载的 HTML，不让 newspaper 自行请求）
        text = _extract_with_newspaper(url, response.text)
        if text and len(text) >= 200:
            return text

        # newspaper 失败或内容太短，用 BS4 尝试
        text = _extract_with_bs4(response.text)
        if text and len(text) >= 200:
            return text

        return ""

    except requests.exceptions.RequestException:
        return ""
    except Exception:
        return ""


def clean_text(text: str) -> str:
    """
    清理多余空白和换行，保留段落结构
    - 合并多个连续换行为两个换行（保留段落分隔）
    - 合并多个连续空格为一个空格
    - 去除首尾空白
    """
    # 替换 3 个以上连续换行为双换行（保留段落分隔）
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 移除行内多余空白
    text = re.sub(r"[ \t]+", " ", text)
    # 去除首尾空白
    text = text.strip()
    return text

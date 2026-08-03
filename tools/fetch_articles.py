# -*- coding: utf-8 -*-
"""
刘晓菲 · 文章抓取脚本
=====================
用法:
    python tools/fetch_articles.py <url> [--id ID] [--category 分类] [--source 来源名]
    python tools/fetch_articles.py --manual

功能:
    1. 抓取链接 → 提取标题 / 摘要 / 正文(段落/小标题/配图/金句)
    2. 下载封面与正文图片到 images/articles/
    3. 写入 data/articles.json(规范源)并同步生成 data/articles.js(浏览器版)

依赖三级降级:
    A. requests + beautifulsoup4   (解析最准,推荐 pip install requests beautifulsoup4)
    B. requests                     (仅缺 bs4)
    C. 纯标准库 urllib + HTMLParser (零安装必能跑)

说明:仅收录本人自有或已获授权的文章内容。
"""

import argparse
import gzip
import hashlib
import html
import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

# ---------- 路径 ----------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IMGD = ROOT / "images" / "articles"
DATA.mkdir(parents=True, exist_ok=True)
IMGD.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# ---------- 依赖探测 ----------
try:
    import requests
    from bs4 import BeautifulSoup
    ENGINE = "bs4"
except ImportError:
    try:
        import requests
        ENGINE = "requests"
    except ImportError:
        import urllib.request
        ENGINE = "stdlib"

# HTMLParser 是标准库,无条件导入(_StdlibExtractor 类始终存在)
from html.parser import HTMLParser


# ============================================================
#  请求层
# ============================================================
def fetch(url: str) -> str:
    """返回页面 HTML 文本。"""
    if ENGINE in ("bs4", "requests"):
        resp = requests.get(url, headers={
            "User-Agent": UA,
            "Referer": "https://www.baidu.com/",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }, timeout=20)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
    else:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Referer": "https://www.baidu.com/",
            "Accept-Encoding": "gzip",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            enc = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(enc, errors="replace")


def download_img(url: str, dest: Path):
    """下载图片到 dest。成功返回最终路径(带扩展名),失败返回 None(调用方回落远程 URL)。"""
    if not url or url.startswith("data:"):
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        if ENGINE in ("bs4", "requests"):
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
            r.raise_for_status()
            raw = r.content
        else:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
        # 用响应内容的前几个字节猜测扩展名
        ext = guess_ext(raw, url)
        target = dest.with_suffix(ext)
        target.write_bytes(raw)
        return target
    except Exception:
        return None


def guess_ext(raw: bytes, url: str) -> str:
    if raw[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if raw[:5] == b"%PDF-":
        return ".pdf"
    if b"<svg" in raw[:400].lower():
        return ".svg"
    if raw[:3] == b"\x89JF":
        return ".jpg"
    p = urlparse(url).path
    m = re.search(r"\.(jpe?g|png|gif|webp|svg|avif)$", p, re.I)
    if m:
        return "." + m.group(1).lower()
    return ".jpg"


# ============================================================
#  解析层
# ============================================================
def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()


# 公众号/博客常见页脚噪音
NOISE_RE = re.compile(
    r"(点击阅读原文|阅读原文|微信扫一扫|扫码|长按识别|"
    r"下载.{0,15}(票神|APP|软件|客户端)|领取.{0,12}优惠券|"
    r"—————|—{2,}end|end.{0,2}—{0,2}end|"
    r"关注该公众号|使用完整服务|作者头像|赞赏|推荐阅读|"
    r"图\s*[/|:]\s*片|图\s*片\s*[/|·、:]|编\s*辑|策划\s*[/|·、:]|"
    r"点个.{0,4}(在看|赞)|欢迎分享|长按.{0,6}(二维码|识别)|"
    r"关注.{0,12}(票神|公众号|账号))", re.I)

NOISE_IMG_RE = re.compile(r"(作者头像|cover_image|头像|二维码|qrcode|logo)", re.I)


def clean_noise(blocks):
    """过滤页脚噪音文本块与尾部噪音图片。"""
    cleaned = []
    for b in blocks:
        if b["type"] in ("p", "h2", "blockquote"):
            if NOISE_RE.search(b.get("text", "")):
                continue
            cleaned.append(b)
        elif b["type"] == "img":
            if NOISE_IMG_RE.search(b.get("alt", "") or ""):
                continue
            cleaned.append(b)
    # 截断:最后一个有意义的文本块之后的图片(尾部二维码/头像)全部去掉
    last_text = -1
    for i, b in enumerate(cleaned):
        if b["type"] in ("p", "h2", "blockquote"):
            last_text = i
    if 0 <= last_text < len(cleaned) - 1:
        cleaned = cleaned[: last_text + 1]
    return cleaned


def extract_meta_bs4(soup, html_text):
    meta = {"title": "", "description": "", "image": "", "site": ""}
    og = {
        "og:title": "title", "og:description": "description",
        "og:image": "image", "og:site_name": "site",
    }
    for tag in soup.find_all("meta"):
        prop = (tag.get("property") or "").lower()
        name = (tag.get("name") or "").lower()
        content = tag.get("content") or ""
        key = og.get(prop) or (og.get(name) if name in og else None)
        if key and not meta[key]:
            meta[key] = _clean_text(content)
    if not meta["title"]:
        t = soup.find("title")
        if t:
            meta["title"] = _clean_text(t.get_text())
    return meta


def extract_content_bs4(soup):
    """返回块列表 [{type, text|src|alt|caption}]。"""
    blocks = []
    # 选择容器,按优先级尝试
    container = None
    for sel in ("article", ".rich_media_content", ".article-content", ".post-content",
                ".entry-content", "main", "[class*=content]", "[class*=article]"):
        found = soup.select_one(sel)
        if found:
            container = found
            break
    if container is None:
        container = soup.body
    if container is None:
        return blocks

    seen_text = set()
    for el in container.find_all(["p", "h2", "h3", "img", "blockquote"], recursive=True):
        if el.name == "img":
            src = el.get("data-src") or el.get("data-original") or el.get("src")
            if not src or src.startswith("data:"):
                continue
            blocks.append({"type": "img", "src": src,
                           "alt": el.get("alt", ""), "caption": ""})
            continue
        text = _clean_text(el.get_text())
        if not text or text in seen_text:
            continue
        seen_text.add(text)
        # 跳过纯链接行 / 过短噪音
        if el.find("img") and el.name != "blockquote":
            continue
        if el.name == "p" and len(text) < 4:
            continue
        blocks.append({"type": "h2" if el.name == "h3" else el.name, "text": text})
    return blocks


class _StdlibExtractor(HTMLParser):
    """纯标准库解析:整页扫 p/h2/h3/img/blockquote。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self._cur = None
        self._text = []
        self._stack = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            d = dict(attrs)
            src = d.get("data-src") or d.get("data-original") or d.get("src")
            if src and not src.startswith("data:"):
                self.blocks.append({"type": "img", "src": src,
                                    "alt": d.get("alt", ""), "caption": ""})
        if tag in ("p", "h2", "h3", "blockquote"):
            self._cur = tag
            self._text = []

    def handle_endtag(self, tag):
        if tag in ("p", "h2", "h3", "blockquote") and self._cur == tag:
            t = _clean_text("".join(self._text))
            if len(t) >= 4:
                self.blocks.append({"type": "h2" if tag == "h3" else tag, "text": t})
            self._cur = None

    def handle_data(self, data):
        if self._cur:
            self._text.append(data)


def extract_meta_stdlib(html_text):
    meta = {"title": "", "description": "", "image": "", "site": ""}
    for m in re.finditer(r'<meta[^>]*property=["\'](og:title|og:description|og:image|og:site_name)["\'][^>]*content=["\']([^"\']*)["\']', html_text, re.I):
        meta[m.group(1)[3:]] = _clean_text(m.group(2))
    for m in re.finditer(r'<meta[^>]*name=["\'](description)["\'][^>]*content=["\']([^"\']*)["\']', html_text, re.I):
        if not meta["description"]:
            meta["description"] = _clean_text(m.group(2))
    if not meta["title"]:
        m = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
        if m:
            meta["title"] = _clean_text(m.group(1))
    return meta


def extract_content_stdlib(html_text):
    p = _StdlibExtractor()
    p.feed(html_text)
    return p.blocks


# ============================================================
#  校验 / 去重 / 写入
# ============================================================
def looks_like_paywall(blocks, meta):
    text_len = sum(len(b.get("text", "")) for b in blocks if b["type"] == "p")
    combined = meta.get("title", "") + meta.get("description", "")
    if text_len < 60:
        return True
    if re.search(r"(验证|登录后|请点击|扫一扫|请登录|滑动验证)", combined):
        return True
    return False


def load_articles():
    p = DATA / "articles.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 1, "updatedAt": "", "articles": []}


def save_articles(data):
    data["updatedAt"] = time_today()
    (DATA / "articles.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "articles.js").write_text(
        "window.ARTICLES = " + json.dumps(data, ensure_ascii=False, indent=2) + ";",
        encoding="utf-8")


def time_today():
    try:
        import datetime
        return datetime.date.today().isoformat()
    except Exception:
        return "2026-01-01"


def make_id(url, title):
    m = re.search(r"(\d{8})", url)
    if m:
        base = m.group(1)
    else:
        base = time_today().replace("-", "")
    # 用 URL 最后一段作为 slug,保证唯一(中文标题会退化为空,故优先 URL)
    seg = [s for s in urlparse(url).path.split("/") if s]
    slug = re.sub(r"[^a-zA-Z0-9_-]", "", seg[-1] if seg else "") or "article"
    return f"{base}-{slug[:40]}"


def abs_url(base, src):
    if not src:
        return src
    if src.startswith("//"):
        return "https:" + src
    if src.startswith(("http://", "https://")):
        return src
    return urljoin(base, src)


# ============================================================
#  抓取主流程
# ============================================================
def scrape(url: str, category="", source_name=""):
    print(f"[1/4] 抓取 {url} ...")
    html_text = fetch(url)
    base = url

    if ENGINE == "bs4":
        soup = BeautifulSoup(html_text, "html.parser")
        meta = extract_meta_bs4(soup, html_text)
        blocks = extract_content_bs4(soup)
    else:
        meta = extract_meta_stdlib(html_text)
        blocks = extract_content_stdlib(html_text)

    title = meta["title"] or "未命名文章"
    print(f"[2/4] 标题: {title}  解析引擎: {ENGINE}  内容块: {len(blocks)}")

    # 反爬 / 登录墙降级
    if looks_like_paywall(blocks, meta):
        print("[!] 警告: 未能提取到有效正文(可能遇到登录墙/反爬)。")
        print("    将仅写入摘要+原文链接占位条目,可稍后运行 --manual 手动补充。")
        return build_placeholder(url, title, meta, category, source_name)

    art_id = make_id(url, title)

    # 预过滤:先去掉噪音文本块并截断尾部图片,避免下载无用图片
    blocks = [b for b in blocks
              if not (b["type"] in ("p", "h2", "blockquote") and NOISE_RE.search(b.get("text", "")))]
    _last = -1
    for _i, _b in enumerate(blocks):
        if _b["type"] in ("p", "h2", "blockquote"):
            _last = _i
    if 0 <= _last < len(blocks) - 1:
        blocks = blocks[: _last + 1]

    print(f"[3/4] 下载图片 → images/articles/ ...")
    cover_src = abs_url(base, meta["image"]) if meta["image"] else ""
    cover_file = ""
    if cover_src:
        cover_final = download_img(cover_src, IMGD / f"{art_id}_cover")
        if cover_final and cover_final.stat().st_size >= 2000:
            cover_file = f"images/articles/{cover_final.name}"
            print("      封面 ✓")
        else:
            print("      封面下载失败/过小,回落远程 URL")

    new_blocks = []
    img_idx = 1
    for b in blocks:
        if b["type"] == "img":
            src = abs_url(base, b["src"])
            final = download_img(src, IMGD / f"{art_id}_img_{img_idx}")
            if final and final.stat().st_size >= 2000:
                new_blocks.append({**b, "src": f"images/articles/{final.name}"})
                img_idx += 1
            else:
                print("      跳过 1 张图片(下载失败或过小)")
        else:
            new_blocks.append(b)

    new_blocks = clean_noise(new_blocks)

    excerpt = meta["description"] or ""
    if not excerpt or len(excerpt) < 6:
        first_p = next((b["text"] for b in new_blocks if b["type"] == "p"), "")
        excerpt = first_p[:60]

    article = {
        "id": art_id,
        "title": title,
        "date": time_today(),
        "category": category or "文章",
        "featured": False,
        "source": {"name": source_name or meta["site"] or "来源", "url": url},
        "cover": {"src": cover_file or "", "alt": title},
        "excerpt": excerpt,
        "content": new_blocks,
    }

    data = load_articles()
    data["articles"] = [a for a in data["articles"] if a.get("source", {}).get("url") != url]
    data["articles"].insert(0, article)

    print(f"[4/4] 已写入 data/articles.json (当前共 {len(data['articles'])} 篇)")
    save_articles(data)
    return article


def build_placeholder(url, title, meta, category, source_name):
    excerpt = meta["description"] or "点击阅读原文查看全文(自动抓取未能获得正文)。"
    article = {
        "id": make_id(url, title),
        "title": title,
        "date": time_today(),
        "category": category or "文章",
        "featured": False,
        "source": {"name": source_name or "来源", "url": url},
        "cover": {"src": "", "alt": title},
        "excerpt": excerpt,
        "content": [],
    }
    data = load_articles()
    data["articles"] = [a for a in data["articles"] if a.get("source", {}).get("url") != url]
    data["articles"].insert(0, article)
    save_articles(data)
    return article


# ============================================================
#  手动录入模式
# ============================================================
def manual_mode():
    print("== 手动录入文章 ==")
    title = input("标题: ").strip() or "未命名文章"
    url = input("原文链接(可留空): ").strip()
    category = input("分类(如 影评/书评/短视频文案,可留空): ").strip() or "文章"
    source_name = input("来源名(如 公众号/小红书,可留空): ").strip() or "来源"
    excerpt = input("一句话摘要(可留空): ").strip()
    has_body = input("是否录入正文? (y/n, 默认 n): ").strip().lower() == "y"

    content = []
    if has_body:
        print("请逐段粘贴正文,每段按回车;输入 'IMG <图片url>' 插配图;空行结束。")
        while True:
            line = input("> ")
            if not line:
                break
            if line.upper().startswith("IMG "):
                content.append({"type": "img", "src": line[4:].strip(), "alt": "", "caption": ""})
            else:
                content.append({"type": "p", "text": line})

    art_id = make_id(url or title, title)
    article = {
        "id": art_id,
        "title": title,
        "date": time_today(),
        "category": category,
        "featured": False,
        "source": {"name": source_name, "url": url},
        "cover": {"src": "", "alt": title},
        "excerpt": excerpt or title,
        "content": content,
    }
    data = load_articles()
    if url:
        data["articles"] = [a for a in data["articles"] if a.get("source", {}).get("url") != url]
    data["articles"].insert(0, article)
    save_articles(data)
    print(f"已写入 data/articles.json (当前共 {len(data['articles'])} 篇)")


# ============================================================
#  入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="文章抓取脚本")
    parser.add_argument("url", nargs="?", help="文章链接")
    parser.add_argument("--id", help="自定义文章 id(默认自动生成)")
    parser.add_argument("--category", default="", help="文章分类")
    parser.add_argument("--source", default="", help="来源名,如 公众号/小红书")
    parser.add_argument("--manual", action="store_true", help="手动录入模式")
    args = parser.parse_args()

    print(f"解析引擎: {ENGINE}  (建议: pip install requests beautifulsoup4 可获得更好解析)")
    if args.manual:
        manual_mode()
        return
    if not args.url:
        parser.print_help()
        sys.exit(1)
    try:
        art = scrape(args.url, args.category, args.source)
        print("\n完成 ✓  文章 ID:", art["id"])
    except Exception as e:
        print(f"\n[!] 抓取失败: {e}")
        print("    可尝试: python tools/fetch_articles.py --manual")
        sys.exit(1)


if __name__ == "__main__":
    main()

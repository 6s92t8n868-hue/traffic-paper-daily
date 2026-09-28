# -*- coding: utf-8 -*-
"""
交通领域 arXiv 论文每日抓取
关键词口径：精准（事故预测 / 道路安全 / 交通预测 / SHAP可解释性）
输出：index.html（供 GitHub Pages 展示）
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import datetime
import re
import sys
import time

NS = {"a": "http://www.w3.org/2005/Atom", "ar": "http://arxiv.org/schemas/atom"}

# ============ 配置区（想改关键词就改这里） ============
# 每组是一个 (组名, arXiv 查询式) 。查询式语法：all:"词" 组合 AND / OR / 括号
KEYWORD_GROUPS = [
    ("交通事故与道路安全", '(all:"traffic accident" OR all:"road accident" OR all:"road safety" OR all:"crash risk" OR all:"crash prediction" OR all:"accident prediction" OR all:"accident risk" OR all:"traffic safety")'),
    ("交通预测", '(all:"traffic prediction" OR all:"traffic forecasting")'),
    ("可解释性 × 交通（SHAP）", '(all:"SHAP" AND (all:"traffic" OR all:"transportation" OR all:"accident" OR all:"road" OR all:"crash"))'),
]

DAYS = 7          # 抓最近几天的论文（细分领域产出不密集，7天窗口保证页面不空）
MAX_PER_GROUP = 100
# =====================================================


def fetch_query(query, max_results=100):
    """调用 arXiv API，返回 entry 列表"""
    entries = []
    start = 0
    while start < max_results:
        n = min(50, max_results - start)
        params = urllib.parse.urlencode({
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": n,
            "start": start,
        })
        url = "https://export.arxiv.org/api/query?" + params
        req = urllib.request.Request(url, headers={"User-Agent": "arxiv-daily/1.0 (research use)"})
        data = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = resp.read()
                break
            except Exception as e:
                print("fetch attempt %d failed: %s" % (attempt + 1, e), file=sys.stderr)
                time.sleep(10)
        if data is None:
            break
        root = ET.fromstring(data)
        batch = root.findall("a:entry", NS)
        entries.extend(batch)
        if len(batch) < n:
            break
        start += n
        time.sleep(3)  # arXiv API 礼貌间隔
    return entries


def parse_entry(e):
    def txt(tag):
        node = e.find("a:" + tag, NS)
        return node.text.strip() if node is not None and node.text else ""
    published = txt("published")           # 2026-09-20T...Z
    date_str = published[:10] if published else ""
    authors = [a.find("a:name", NS).text for a in e.findall("a:author", NS) if a.find("a:name", NS) is not None]
    cats = [c.get("term") for c in e.findall("a:category", NS)]
    link = ""
    for l in e.findall("a:link", NS):
        if l.get("type") == "application/pdf":
            link = l.get("href")
    alt = txt("id")  # abs 页面链接
    comment_node = e.find("ar:comment", NS)
    comment = comment_node.text.strip() if comment_node is not None and comment_node.text else ""
    return {
        "id": alt,
        "title": re.sub(r"\s+", " ", txt("title")),
        "abstract": re.sub(r"\s+", " ", txt("summary")),
        "authors": authors,
        "cats": cats,
        "pdf": link,
        "abs": alt,
        "date": date_str,
        "comment": comment,
    }


def main():
    today = datetime.date.today()
    earliest = today - datetime.timedelta(days=DAYS)
    seen = set()
    groups = []  # [(组名, [papers])]
    total = 0
    for name, query in KEYWORD_GROUPS:
        papers = []
        for e in fetch_query(query, MAX_PER_GROUP):
            p = parse_entry(e)
            if p["date"] and datetime.datetime.strptime(p["date"], "%Y-%m-%d").date() >= earliest:
                if p["id"] not in seen:
                    seen.add(p["id"])
                    papers.append(p)
        papers.sort(key=lambda x: x["date"], reverse=True)
        print("[%s] %d papers" % (name, len(papers)))
        total += len(papers)
        groups.append((name, papers))

    html = render_html(groups, total, today)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("total %d papers -> index.html" % total)


HTML_HEAD = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>交通论文日报</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1a2233;--sub:#6b7280;--accent:#1a56db;--line:#e5e7eb;--tag:#eef4ff;}
*{box-sizing:border-box;}
body{margin:0;font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);}
.wrap{max-width:900px;margin:0 auto;padding:32px 16px 64px;}
h1{font-size:26px;margin:0 0 4px;}
.meta{color:var(--sub);font-size:14px;margin-bottom:24px;}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px;}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 16px;font-size:13px;}
.stat b{display:block;font-size:20px;color:var(--accent);}
h2{font-size:18px;margin:32px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--accent);}
.paper{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin-bottom:12px;}
.paper h3{font-size:16px;margin:0 0 8px;line-height:1.45;}
.paper h3 a{color:var(--ink);text-decoration:none;}
.paper h3 a:hover{color:var(--accent);}
.authors{font-size:13px;color:var(--sub);margin-bottom:8px;}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;}
.tag{background:var(--tag);color:var(--accent);border-radius:4px;padding:1px 8px;font-size:12px;}
.date{color:var(--accent);font-weight:600;font-size:13px;}
details{margin-top:6px;}
summary{cursor:pointer;font-size:13px;color:var(--accent);user-select:none;}
.abs{font-size:13.5px;line-height:1.7;color:#374151;margin-top:8px;}
.links{margin-top:8px;font-size:13px;}
.links a{color:var(--accent);text-decoration:none;margin-right:14px;}
.empty{color:var(--sub);font-size:14px;background:var(--card);border:1px dashed var(--line);border-radius:10px;padding:20px;text-align:center;}
footer{margin-top:40px;color:var(--sub);font-size:12px;text-align:center;}
</style>
</head>
<body>
<div class="wrap">
<h1>交通论文日报</h1>
<p class="meta">事故预测 · 道路安全 · 交通预测 · SHAP 可解释性 &nbsp;|&nbsp; 数据源 arXiv，每日自动更新</p>
"""

HTML_FOOT = """<footer>由 GitHub Actions 每日自动抓取生成 · 关键词可在仓库 scripts/fetch_arxiv.py 中修改</footer>
</div>
</body>
</html>
"""


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def render_html(groups, total, today):
    parts = [HTML_HEAD]
    parts.append('<div class="stats">')
    parts.append('<div class="stat"><b>%d</b>近 %d 天论文总数</div>' % (total, DAYS))
    for name, papers in groups:
        parts.append('<div class="stat"><b>%d</b>%s</div>' % (len(papers), esc(name)))
    parts.append('<div class="stat"><b>%s</b>最后更新</div>' % today.strftime("%Y-%m-%d"))
    parts.append("</div>")

    for name, papers in groups:
        parts.append("<h2>%s（%d 篇）</h2>" % (esc(name), len(papers)))
        if not papers:
            parts.append('<div class="empty">近 %d 天没有新论文</div>' % DAYS)
            continue
        for p in papers:
            parts.append('<div class="paper">')
            parts.append('<h3><a href="%s" target="_blank">%s</a></h3>' % (esc(p["abs"]), esc(p["title"])))
            shown = ", ".join(p["authors"][:4]) + (" 等" if len(p["authors"]) > 4 else "")
            parts.append('<div class="authors">%s</div>' % esc(shown))
            parts.append('<div class="tags"><span class="tag date">%s</span>%s</div>' % (
                esc(p["date"]),
                "".join('<span class="tag">%s</span>' % esc(c) for c in p["cats"][:4])))
            parts.append('<details><summary>摘要</summary><div class="abs">%s</div></details>' % esc(p["abstract"]))
            parts.append('<div class="links"><a href="%s" target="_blank">arXiv 页面</a><a href="%s" target="_blank">PDF</a></div>' % (
                esc(p["abs"]), esc(p["pdf"])))
            parts.append("</div>")
    parts.append(HTML_FOOT)
    return "\n".join(parts)


if __name__ == "__main__":
    main()

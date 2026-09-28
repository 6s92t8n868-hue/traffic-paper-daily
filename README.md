# 交通论文日报（arXiv 自动抓取）

每日自动从 arXiv 抓取交通领域最新论文，生成网页。研究方向：宁波市道路交通事故预测（机器学习 + SHAP）。

## 查看方式

打开 GitHub Pages 页面：`https://<你的用户名>.github.io/traffic-paper-daily/`

（也可以直接在本仓库首页看 index.html 渲染效果）

## 抓取关键词（精准口径）

| 分组 | 覆盖内容 |
|------|----------|
| 交通事故与道路安全 | traffic accident / road safety / crash risk / accident prediction 等 |
| 交通预测 | traffic prediction / traffic forecasting |
| 可解释性 × 交通（SHAP） | SHAP 与 traffic / transportation / accident / road / crash 的组合 |

- 时间窗口：最近 3 天（每天运行一次，防止漏抓）
- 运行时间：每天北京时间上午 10 点左右（GitHub Actions 定时任务可能有延迟）

## 修改关键词

编辑 `scripts/fetch_arxiv.py` 顶部的 `KEYWORD_GROUPS` 配置区即可，语法示例：

```python
KEYWORD_GROUPS = [
    ("组名", '(all:"关键词1" OR all:"关键词2")'),
]
```

改完推送到 main 分支，会自动触发一次抓取。

## 手动触发

进入仓库 Actions 页 → 选择「每日论文抓取」→ Run workflow。

## 目录结构

```
├── .github/workflows/daily.yml   # 定时任务：抓取 + 提交 + 发布 Pages
├── scripts/fetch_arxiv.py        # 抓取脚本（纯标准库，无第三方依赖）
└── index.html                    # 自动生成的论文页面
```

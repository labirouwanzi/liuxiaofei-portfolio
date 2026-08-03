# 刘晓菲 · 个人作品展示网页

文艺/杂志风的个人介绍与作品展示页,融入电影元素,部署于 GitHub Pages,任何人均可通过网址访问。

## 本地预览

**方式一**:双击 `index.html` 直接打开浏览器。

**方式二**(更接近线上环境):
```bash
cd "C:\Users\丸子\Desktop\liuxiaofei-portfolio"
python -m http.server 8765
```
浏览器访问 http://127.0.0.1:8765

## 页面结构

| 板块 | 说明 |
|------|------|
| ACT I · 关于我 | 自我介绍(自我评价三段式) |
| ACT II · 小红书 | 账号截图 + 主页链接按钮 |
| ACT III · 过往文章 | 文章卡片,点击弹窗查看全文 |

## 修改指南

### 1. 自我介绍 / 文案
直接编辑 `index.html` 中对应板块的文本即可。

### 2. 小红书主页
- **链接**:编辑 `index.html`,把 `#xhsLink` 的 `href="#"` 改为你的小红书主页 URL
- **截图**:用你的主页截图替换 `images/xhs.svg`(或改名放入,再改 `index.html` 里的引用)

### 3. 添加文章(推荐:抓取脚本)

```bash
# 抓取链接自动生成(推荐先装依赖,解析更准)
python -m pip install requests beautifulsoup4
python tools/fetch_articles.py "https://文章链接" --category 影评 --source 公众号

# 遇登录墙/抓不到正文时,手动录入
python tools/fetch_articles.py --manual
```

脚本会:
1. 提取标题/摘要/正文(段落、小标题、配图、金句)
2. 下载封面与正文图到 `images/articles/`
3. 写入 `data/articles.json`(规范源)并同步生成 `data/articles.js`(浏览器版)

**手动编辑**:也可直接改 `data/articles.json`,字段结构见文件内示例。

### 文章数据格式(简版)

```json
{
  "id": "20260803-xxx",            // 唯一 id
  "title": "标题",
  "date": "2026-08-03",
  "category": "影评",
  "source": { "name": "公众号", "url": "原文链接" },
  "cover": { "src": "images/articles/xxx_cover.jpg", "alt": "" },
  "excerpt": "一句话摘要",
  "content": [
    { "type": "p",  "text": "段落" },
    { "type": "h2", "text": "小标题" },
    { "type": "img", "src": "images/articles/xxx_1.jpg", "alt": "", "caption": "" },
    { "type": "blockquote", "text": "金句" }
  ]
}
```

## 部署到 GitHub Pages

1. **创建仓库**:浏览器打开 github.com → New repository → 仓库名填 `liuxiaofei-portfolio`(英文)→ **不要**勾选 "Add a README" → Create
2. **本地初始化并推送**:
   ```bash
   cd "C:\Users\丸子\Desktop\liuxiaofei-portfolio"
   git config user.name  "你的GitHub用户名"
   git config user.email "你的GitHub邮箱"
   git init
   git branch -M main
   git add .
   git commit -m "init portfolio"
   git remote add origin https://github.com/你的用户名/liuxiaofei-portfolio.git
   git push -u origin main
   ```
3. **开启 Pages**:仓库页面 → Settings → Pages → Source 选 **Deploy from a branch** → Branch 选 `main` / root → Save
4. 等 30–60 秒,访问:
   `https://你的用户名.github.io/liuxiaofei-portfolio/`

**推送认证失败时**(三选一):
- Windows 会自动弹出 GitHub 登录窗口(Git Credential Manager),直接登录即可
- 或用 **GitHub Desktop**(图形化工具)导入本文件夹后 Publish
- 或生成 Personal Access Token,推送时当作密码输入

**以后每次修改内容后**:
```bash
git add .
git commit -m "update"
git push
```
Pages 会自动重新构建,约 1 分钟生效。

## 注意事项

- 网页仅收录**本人自有或已授权**的文章
- 大文件(视频/PPT/PDF)请勿放进本文件夹,已在 `.gitignore` 排除
- 图片建议单张 ≤ 500KB,页面加载更快

# 回望灯火阑珊

一个基于 Hugo 静态网站生成器的博客/小说站点。

## 📖 项目简介

一部长篇小说的阅读站，Hugo 构建。版面是本仓库自己的一套模板（`layouts/` + `assets/`），
不依赖任何外部主题——「灯火／纸页」：暖纸面、宋体正文、琥珀色重音，夜间模式把那盏灯留在暗处。

## 🚀 部署

网站已部署到 GitHub Pages:
- 🌐 访问地址: https://luoli523.github.io/huiwang/

## 🛠️ 本地开发

### 前置要求

- [Hugo](https://gohugo.io) (推荐使用 Extended 版本)

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/luoli523/huiwang.git
cd huiwang
```

2. 启动本地服务器（无需初始化子模块，本项目已不使用外部主题）：
```bash
hugo server
```

3. 在浏览器中访问: http://localhost:1313/huiwang/

## 📝 内容结构

| 路径 | 作用 |
|---|---|
| `content/docs/` | 各章正文，靠 front matter 的 `weight` 排序 |
| `content/_index.md` | 首页题记 |
| `content/about/` | 关于（人物表与时代背景） |
| `layouts/` | 本站版面模板（首页书衣、章节页、目录、全文索引） |
| `assets/css/book.css` | 全部样式，含昼夜双主题 |
| `assets/js/reader.js` | 进度条、目录抽屉、全文检索、字号、续读、背景音乐 |
| `static/` | 封面图与背景音乐 |
| `hugo.toml` | 站点配置（书名、副题、封面、音乐） |

新增一章：在 `content/docs/` 放一个 `N-章名.md`，front matter 写 `title: "N.章名"` 与 `weight: N`，
目录、上下章、全文索引都会自动跟上。正文里的 `---` 会渲染成 ❖ 场景分隔。

## 🤖 自动化部署

项目使用 GitHub Actions 自动构建和部署到 GitHub Pages。

每当你向 `main` 分支推送代码时，GitHub Actions 会：
1. 自动构建 Hugo 网站
2. 部署到 GitHub Pages

查看工作流状态: https://github.com/luoli523/huiwang/actions

## 📄 许可证

MIT License

## 👤 作者

Luoli523

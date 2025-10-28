# 回望灯火阑珊

一个基于 Hugo 静态网站生成器的博客/小说站点。

## 📖 项目简介

这是一个使用 Hugo + Hugo Book 主题构建的静态网站项目。

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

2. 初始化子模块：
```bash
git submodule update --init --recursive
```

3. 启动本地服务器：
```bash
hugo server
```

4. 在浏览器中访问: http://localhost:1313

## 📝 内容结构

- `content/docs/` - 主要内容章节
- `hugo.toml` - Hugo 配置文件
- `themes/` - 主题文件（Git 子模块）

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

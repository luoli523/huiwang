# GitHub Pages 部署说明

## 方案一：使用 GitHub Actions（推荐）

GitHub Actions 已配置，会自动化构建和部署。

### 手动触发部署

在工作目录运行：
```bash
# 触发一次新的部署
git commit --allow-empty -m "Trigger GitHub Pages deployment"
git push origin main
```

或者在 GitHub 网页上：
1. 进入 https://github.com/luoli523/huiwang
2. 点击 "Actions" 标签
3. 选择 "GitHub Pages" workflow
4. 点击 "Run workflow" 按钮手动触发

## 方案二：手动部署到 gh-pages 分支

### 步骤 1: 构建网站

```bash
# 安装 Hugo（如果还没有）
# macOS: brew install hugo
# 或访问: https://gohugo.io/installation/

# 确保子模块已初始化
git submodule update --init --recursive

# 构建网站
hugo --minify

# public 目录现在包含构建好的网站
```

### 步骤 2: 推送到 gh-pages 分支

```bash
# 进入 public 目录
cd public

# 初始化 git（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "Deploy to GitHub Pages"

# 添加 gh-pages 分支为远程源
git remote add origin https://github.com/luoli523/huiwang.git

# 推送到 gh-pages 分支
git push -f origin main:gh-pages
```

或者更简单的方法：
```bash
# 使用 hugo deploy 命令（如果已配置）
hugo deploy
```

## 步骤 3: 在 GitHub 启用 Pages

1. 访问 https://github.com/luoli523/huiwang/settings/pages
2. 在 "Source" 下选择：
   - **Deploy from a branch**（如果使用手动部署）
   - **GitHub Actions**（如果使用自动化部署）
3. 选择分支：`gh-pages` 或 `main`
4. 点击 "Save"

## 验证部署

部署成功后，访问：https://luoli523.github.io/huiwang/

## 故障排查

### 如果页面空白或 404

1. 检查 baseURL 配置
   - 确保 `hugo.toml` 中的 `baseURL` 正确
   - 应该是：`baseURL = 'https://luoli523.github.io/huiwang/'`

2. 检查 GitHub Actions 状态
   - 访问：https://github.com/luoli523/huiwang/actions
   - 查看是否有错误

3. 清除缓存
   - 浏览器硬刷新：Ctrl+F5 或 Cmd+Shift+R

### 重新触发部署

```bash
git commit --allow-empty -m "Redeploy site"
git push origin main
```


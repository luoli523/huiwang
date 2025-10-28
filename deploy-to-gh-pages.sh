#!/bin/bash

# 切换到 gh-pages 分支
git checkout gh-pages || git checkout -b gh-pages

# 从 main 分支获取最新的构建文件（如果存在）
git merge main --no-commit --no-ff

# 如果 public 目录存在，复制内容
if [ -d "public" ]; then
    cp -r public/* .
fi

# 提交
git add .
git commit -m "Deploy to GitHub Pages" || true

# 推送到远程
git push origin gh-pages

# 切换回 main
git checkout main

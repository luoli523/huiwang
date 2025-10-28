# 背景音乐配置指南

## 📁 文件要求
将音乐文件命名并放置如下：
- 文件名：`background.mp3`（必须）
- 位置：`static/music/background.mp3`

## 🎵 自动播放设置
- 网站加载后自动播放背景音乐
- 初始音量：30%（可在代码中调整）
- 循环播放：已启用
- 控制按钮：页面左下角

## 🎛️ 如何修改
编辑 `layouts/partials/docs/inject/content-after.html`：

### 修改音量
找到 `player.volume = 0.3;` 改为你想要的值（0.0 - 1.0）

### 修改自动播放
找到 `autoplay` 属性，改为以下之一：
- `autoplay` - 自动播放（需用户交互）
- 删除 `autoplay` - 需要手动点击

## ⚠️ 注意事项
- 文件大小建议 < 5MB，确保快速加载
- MP3格式兼容性最好
- 浏览器可能阻止自动播放（Chrome、Safari等需要用户交互）
- 如需不同格式，参考原有 M4A/OGG 支持代码

## 📝 示例
```bash
# 将你的音乐文件放到这个位置
cp /path/to/your/music.mp3 static/music/background.mp3
```

## 🎨 播放器控制
- 左下角按钮：播放/暂停音乐
- 双击按钮：暂停播放


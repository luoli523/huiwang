# 背景音乐播放器使用说明

## 🎵 已添加的功能

网站现在在右下角有一个固定位置的音乐播放器，包含以下功能：

### 功能特点
- ✅ 播放/暂停按钮
- ✅ 音量控制滑块
- ✅ 显示当前播放的音乐名称
- ✅ 可关闭播放器
- ✅ 循环播放
- ✅ 响应式设计（移动端适配）
- ✅ 不自动播放（需要用户点击）

## 📝 如何添加音乐

### 1. 准备音乐文件
将音乐文件（MP3 格式）放到：
```
static/music/
```

### 2. 修改音频源
编辑 `layouts/partials/docs/inject/content-after.html`，找到：
```html
<audio id="background-music" loop preload="auto" volume="0.5">
  <!-- 音乐文件需要放在 static/music/ 目录下 -->
  <!-- <source src="/music/hotel-california.mp3" type="audio/mpeg"> -->
</audio>
```

修改为：
```html
<audio id="background-music" loop preload="auto" volume="0.5">
  <source src="/music/你的音乐文件名.mp3" type="audio/mpeg">
</audio>
```

### 3. 更新音乐标题
找到这行：
```html
<div id="music-title" style="font-size: 14px; font-weight: bold; margin-top: 2px;">加州旅馆 - Hotel California</div>
```

改为你的音乐名称：
```html
<div id="music-title" style="font-size: 14px; font-weight: bold; margin-top: 2px;">你的音乐名称</div>
```

## 🎨 自定义样式

可以修改播放器的位置、颜色等样式。编辑 `layouts/partials/docs/inject/content-after.html` 中的 `<style>` 部分。

### 修改位置
```css
position: fixed; 
bottom: 20px;    /* 距离底部 */
right: 20px;     /* 距离右边 */
```

### 修改颜色
```css
background: rgba(255, 255, 255, 0.9);  /* 背景色 */
color: #666;                           /* 文字颜色 */
```

## 🚀 查看效果

运行本地服务器：
```bash
hugo server
```

访问网站，右下角会看到播放器。

## 📦 文件说明

- `layouts/partials/docs/inject/content-after.html` - 播放器代码
- `static/music/` - 存放音乐文件的目录
- `static/music/README.md` - 使用说明

## ⚠️ 注意事项

1. **音乐文件大小**：建议小于 5MB，确保快速加载
2. **版权**：确保你有权使用该音乐
3. **浏览器兼容性**：现代浏览器都支持
4. **移动端**：播放器会自动适配小屏幕

## 🎯 下一步

1. 将音乐文件放到 `static/music/` 目录
2. 修改 `content-after.html` 中的音频源路径
3. 测试播放功能
4. 如需调整样式，编辑相关 CSS


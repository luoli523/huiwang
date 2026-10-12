# 背景音乐播放器说明

播放器内置在版面里，位置是**右下角那盏灯泡**。点亮＝播放，熄灭＝暂停。

## 现状

| 项 | 值 |
|---|---|
| 播放器代码 | `layouts/_default/baseof.html`（`.bulb` 按钮 + `<audio id="bgm">`） |
| 交互逻辑 | `assets/js/reader.js` 末段 |
| 外观 | `assets/css/book.css` 的 `.bulb` 一节 |
| 音频文件 | `static/music/background.mp3`（用户指定 BGM 的前 10 分钟，轻淡入淡出） |
| 配置 | `hugo.toml` 里的 `params.bgm` 与 `params.bgmTitle` |
| 自动播放 | **没有**。浏览器普遍拦截自动播放，读者没点之前也不该出声 |
| 初始音量 | 0.28 |

当前曲目：[深度睡眠，放松和治愈睡眠音乐（BGM）](https://www.youtube.com/watch?v=ADvyiXJOS-s)。
全站背景音和各章口播使用同一来源，播放口播时全站背景音暂停。

## 换一首曲子

把文件放进 `static/music/`，然后改 `hugo.toml`：

```toml
[params]
  bgm = 'music/你的文件名.mp3'
  bgmTitle = '曲名 · 显示在按钮的 tooltip 上'
```

`params.bgm` 留空就整体去掉播放器（模板里有 `{{ with site.Params.bgm }}` 包着）。

## 调音量

改 `assets/js/reader.js`：

```js
audio.volume = 0.28;   // 0.0 – 1.0
```

## 注意

- 文件建议小于 5MB。`preload="none"`，读者不点就不下载，不拖慢首屏。
- 确认自己有权使用这首曲子。

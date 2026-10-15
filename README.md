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

## 有声版制作

使用相邻 `local-tts` 项目的本地服务（`127.0.0.1:8091`），音色为已有的
`guige`。服务需预先启动；生成过程不调用云端，不需要 API key。

```bash
python3 scripts/narrate.py 1
python3 scripts/mix-chapter.py
# 继续生成剩余章节，完成检查后每四章发布一次
python3 scripts/narrate-batch.py --first 2 --last 29 --publish-every 4
hugo server
```

`narrate.py` 支持指定章节编号，按自然段和场景分批，缓存路径为
`.audio-work/NN/`。再次执行会复用相同正文、声音版本与参数的已完成片段。
脚本不会自动重试失败的请求，遇到连接中断时先确认服务已结束当前请求再续跑。
`manifest.json` 记录原文摘要、声音版本、朗读文字和音频时长。
原文修订后需要重新生成并更新目录元数据。
朗读稿把 `T2次`、`诺基亚6610` 展开为明确的中文读法，网站正文保留原样。

混音脚本支持 `python3 scripts/mix-chapter.py N`，各章统一使用用户指定的背景音乐，
配合音量压低、淡入淡出输出配乐版。WAV 工作文件留在本机；公开 MP3 位于 `static/audio/`。
第 20 章在约 8:21 的歌词段用叶蒨文《潇洒走一回》替换歌词口播，
歌曲从 43 秒起完整唱完这一段，在 90–96 秒处淡出，然后恢复章末口播和轻背景音乐。
`data/audio-cues.json` 保存替换区间、淡出时间与原文摘要；歌曲源音轨放在
`.audio-work/bgm/chapter20-song.m4a`。正文变化后需重新定位切入点再混音。
第 23 章口播结束后接入用户指定的《Hotel California》1994 不插电现场版，
从歌曲第 5 秒播放至结束，末尾 6 秒淡出；源音轨放在 `.audio-work/bgm/chapter23-song.m4a`。
第 29 章口播结束后接入用户指定的 Beyond《海阔天空》，从歌曲开头播放至结束，
末尾 6 秒淡出；源音轨放在 `.audio-work/bgm/chapter29-song.m4a`。
批量脚本固定第一集的参考录音版本，检查朗读稿覆盖，逐章抽查开头、结尾的本地
Whisper 转写并保存结果。续跑会复用已完成章节和片段。
`--publish-every` 会提交并推送完成的章节，通过现有 GitHub Pages 工作流部署；
省略这个参数只生成本地文件。后续章节的纯人声通过 `--archive-voice` 留在工作目录。
`data/audio.json` 决定哪些章节显示播放器，路径也可以替换为对象存储的 HTTPS 地址。
网站显示播放／暂停按钮、可拖动进度条和时间；默认不自动播放，自动保存本机进度。
一集结束后，同一播放器自动接着播放已上线的下一集，并显示当前收听章节的正文链接。
章节播放列表由 Hugo 输出为 `audio/playlist.json`，每次接播读取最新列表。
朗读与原有全站背景音乐互斥。未生成音频的章节保持普通阅读。

音色来源：作者已有参考录音的本地 AI 合成。
BGM：用户指定的《深度睡眠，放松和治愈睡眠音乐（BGM）》，来自
[Relaxing Music Productions](https://www.youtube.com/watch?v=ADvyiXJOS-s)。
本地源文件放在 `.audio-work/bgm/source.m4a`，混音时降低音量并随人声压低，首尾淡入淡出。
制作源文件不进入 Git；每集公开音频为混音后的 MP3。

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

# Scribe Transcribe

微信视频号下载 + 音视频转写工具。Python CLI 实现，轻量简洁。

基于 [autogame-17/scribe-studio](https://github.com/autogame-17/scribe-studio) 的视频号下载核心，用 Python 重新封装。

## 功能

- **视频号下载** — MITM 代理拦截，自动注入下载按钮到微信客户端
- **音视频转写** — 基于 faster-whisper 的本地语音转文字（可选）
- **多格式导出** — SRT 字幕 + 纯文本

## 架构

```
wx-dl.exe (Go, MITM代理+API服务)
    ↕ HTTP API (localhost:2022)
main.py (Python CLI, 总控)
    ├── 启动/管理代理服务
    ├── ffmpeg 抽音轨 (16kHz WAV)
    ├── faster-whisper 本地转写
    └── 导出 SRT / TXT
```

## 前置条件

| 依赖 | 版本要求 | 用途 | 安装方式 |
|------|---------|------|---------|
| **Go** | 1.21+ | 编译视频号下载器 | `winget install GoLang.Go` |
| **Python** | 3.10+ | 运行主程序 | [python.org](https://python.org) |
| **ffmpeg** | 任意版本 | 音频提取 | [ffmpeg.org](https://ffmpeg.org) 或 `winget install Gyan.FFmpeg` |
| **Git** | 任意版本 | 克隆上游下载器源码 | `winget install Git.Git` |

## 安装

### 1. 克隆本项目

```bash
git clone https://github.com/<your-username>/scribe-transcribe.git
cd scribe-transcribe
```

### 2. 编译 Go 下载器

需要先克隆上游的 scribe-studio（本项目已包含其 `backend/core` 作为参考）：

```bash
# 如果你是从 scribe-studio 旁边克隆的，直接编译：
cd scribe-studio/backend/core

# 设置国内代理加速
go env -w GOPROXY=https://goproxy.cn,direct

# 编译
go build -o ../../../scribe-transcribe/bin/wx-dl.exe .
```

编译完成后 `bin/wx-dl.exe` 约 36MB。

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

首次转写时 faster-whisper 会自动下载模型（约 462MB），后续复用缓存。

## 使用

### 方式一：双击启动（仅下载）

直接双击 `start.bat`，按提示操作即可。

### 方式二：命令行

```bash
# 启动视频号代理服务（下载 + 自动转写）
python main.py serve --download-dir ./downloads

# 对本地音视频文件转写
python main.py transcribe ./some-video.mp4

# 查看已下载的任务
python main.py tasks
```

### 手机配置代理

启动代理服务后，需要在手机上配置 HTTP 代理才能拦截视频号：

1. 手机和电脑连同一个 WiFi
2. 手机 WiFi 设置 → HTTP 代理 → 手动
3. 服务器填电脑 IP（启动脚本会显示）
4. 端口填 `2023`
5. 打开微信视频号，页面会自动注入下载按钮

## 项目结构

```
scribe-transcribe/
├── main.py              # CLI 入口（serve / transcribe / tasks）
├── downloader.py        # Go 代理服务管理
├── transcriber.py       # faster-whisper 转写 + 幻觉清理
├── audio.py             # ffmpeg 音频提取
├── exporter.py          # SRT / TXT 导出
├── config.py            # 配置管理 + 转写缓存
├── start.bat            # Windows 一键启动脚本
├── requirements.txt     # Python 依赖
└── bin/                 # 编译产物（gitignore）
    └── wx-dl.exe
```

## 常见问题

**Q: 代理启动后手机无法上网？**
A: 检查手机代理配置的 IP 和端口是否正确，确保手机和电脑在同一局域网。

**Q: 转写很慢？**
A: 默认使用 CPU + int8 量化。如果有 NVIDIA 显卡，修改 `config.py` 中的 `WHISPER_DEVICE = "cuda"` 可大幅加速。

**Q: 权限不够无法启动代理？**
A: 右键 `start.bat` → 以管理员身份运行。

## 致谢

- [autogame-17/scribe-studio](https://github.com/autogame-17/scribe-studio) — 视频号下载核心和整体架构
- [ltaoo/wx_channels_download](https://github.com/ltaoo/wx_channels_download) — 视频号 MITM 拦截实现

## License

GPL-3.0-or-later（与上游 scribe-studio 保持一致）

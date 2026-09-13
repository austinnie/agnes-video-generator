# Agnes Video Generator（Fork）

> **本仓库 fork 自 [lcy362/agnes-video-generator](https://github.com/lcy362/agnes-video-generator)**。
> 原项目完全免费、开源，基于 Agnes AI 的免费模型。

**完全免费的 AI 视频生成器 —— 无需订阅、无需高端 GPU、无使用次数限制。**
输入一个文字创意，自动生成带旁白和字幕的多场景 AI 视频。支持文本转视频、图片转视频、关键帧动画、数字主播等。所有 AI 计算在云端完成，普通笔记本即可运行。

---

## 它是什么

Agnes Video Generator 是一个本地运行的开源 AI 视频生成工具，基于 Agnes AI 的免费模型。你只需要一个免费的 Agnes API Key 和一台能跑 Python 的普通电脑，就能零成本制作 AI 视频。

核心能力：

- **多场景自动生成** —— 输入一段创意，AI 自动拆分场景，逐场景生成视频
- **TTS 旁白** —— 内置免费的 AI 语音合成
- **自动字幕** —— 生成词级 SRT 字幕
- **数字主播** —— 内置数字人播报模式
- **多种创作模式** —— 创意视频 / 长文转视频 / 图生视频 / 关键帧动画
- **断点续传** —— 每个中间结果都持久化，中断后可恢复
- **多语言 Web UI**

## 运行环境

- Python 3.10+
- **ffmpeg**（必须，确保 `ffmpeg -version` 能正常运行）
- 一个 Agnes AI API Key —— [免费注册](https://platform.agnes-ai.com)

## 安装与运行

### 方式 1：Docker（推荐）

多架构镜像（linux/amd64、linux/arm64）发布在 GHCR 和 Docker Hub。

**拉取：**

```bash
# GHCR
docker pull ghcr.io/lcy362/free-short-video:6.4.6

# Docker Hub
docker pull lcy362/free-short-video:v6.4.6
```

**运行：**

容器内的 `/app/.working_dir` 和 `/app/.agnes_config` 用于持久化生成结果和设置。**必须挂载卷**，否则容器重建后数据全部丢失。

方式 A —— 绑定挂载到宿主机目录（推荐）：

```bash
mkdir -p ~/agnes-data/working ~/agnes-data/config
docker run -d -p 8765:8765 \
  -e AGNES_API_KEY=<your-key> \
  -v ~/agnes-data/working:/app/.working_dir \
  -v ~/agnes-data/config:/app/.agnes_config \
  ghcr.io/lcy362/free-short-video:6.4.6
```

视频会出现在宿主机的 `~/agnes-data/working/` 目录。

方式 B —— 使用命名卷：

```bash
docker volume create agnes-working
docker volume create agnes-config
docker run -d -p 8765:8765 \
  -e AGNES_API_KEY=<your-key> \
  -v agnes-working:/app/.working_dir \
  -v agnes-config:/app/.agnes_config \
  ghcr.io/lcy362/free-short-video:6.4.6
```

从命名卷导出文件：

```bash
docker run --rm -v agnes-working:/data -v "$PWD":/out busybox cp -r /data/. /out/agnes-export
```

启动后打开 http://localhost:8765。

> 镜像已声明 `VOLUME`，如果不加 `-v`，数据只在容器 stop/start 期间保留；重建容器会从头开始。
> `AGNES_API_KEY` 也可以在 Web UI 中稍后设置，会存入挂载的 config 卷。

### 方式 2：npm

一次性运行或全局安装：

```bash
# 一次性运行（无需安装）
npx free-short-video

# 全局安装
npm install -g free-short-video
free-short-video
```

需要系统已安装 Python 3.10+ 和 ffmpeg。首次运行会自动创建虚拟环境并安装依赖。

### 方式 3：从源码运行

```bash
git clone https://github.com/austinnie/agnes-video-generator.git
cd agnes-video-generator
```

Linux / macOS：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./start.sh
```

Windows：

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
start.bat
```

## 配置

所有配置都通过环境变量完成，无需配置文件。从模板开始：

```bash
cp .env.example .env    # 然后编辑里面的 AGNES_API_KEY
```

`.env.example` 列出了所有支持的变量及其默认值：API Key、多 Key 轮换、限流、端口、模型覆盖、维护选项等。

**多 Key 轮换**：如果你有多个 API Key，设置为 `AGNES_API_KEY`、`AGNES_API_KEY_2`、`AGNES_API_KEY_3` …（编号必须连续）。限流额度随 Key 数量提升，遇到 429 会自动切换到下一个 Key，并发上限也相应提高。

## 使用方式

启动后浏览器打开 http://localhost:8765，Web UI 中：

1. 首次进入配置 Agnes API Key（也可通过环境变量预先设置）
2. 选择创作模式（创意视频 / 长文转视频 / 图生视频等）
3. 输入创意或粘贴文稿
4. 选择分辨率（9:16 / 16:9 / 1:1）
5. 启动生成，等待完成

生成结果保存在 `.working_dir/`（或容器内挂载的卷）中。

## 更新日志

### v6.4.6

**Bug 修复**

- 修复了 Docker 中数字人（anchor）视频在拼接/合成步骤失败的问题。原因是容器内只带了 ffmpeg、没有 ffprobe，而探测片段时长时未处理 ffprobe 缺失的情况。现在当 ffprobe 不可用时改用 ffmpeg 探测媒体时长，并有安全默认值兜底，数字人视频合成可在 Docker 等最小化环境中正常完成。

## 与商业工具的对比

| 特性 | Agnes Video Generator | Runway Gen-3 | Pika 2.0 | OpenAI Sora | Kling 1.6 |
|---|---|---|---|---|---|
| 价格 | 免费 | $15–$95/月 | $10–$95/月 | $20+/月（有限） | 免费额度，之后按秒计费 |
| 开源 | ✅ MIT | ❌ | ❌ | ❌ | ❌ |
| 自托管 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 单片段最长 | 20 秒，场景数不限 | 10 秒 | 10 秒 | 20 秒 | 10 秒 |
| 多场景流水线 | ✅ 内置 | ❌ 手动 | ❌ 手动 | ❌ 手动 | ❌ 手动 |
| AI 旁白 (TTS) | ✅ 免费内置 | ❌ 需第三方 | ❌ 需第三方 | ❌ | ❌ |
| 自动字幕 | ✅ 词级 SRT | ❌ | ❌ | ❌ | ❌ |
| 数字主播 | ✅ 内置 | ❌ | ❌ | ❌ | ❌ |
| 分辨率 | 9:16 / 16:9 / 1:1 | 多种 | 多种 | 多种 | 多种 |
| 图生视频 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 关键帧动画 | ✅ | ✅ | ✅ | ❌ | ✅ |
| 需要本地 GPU | ❌ 云端 API | ❌ 云端 | ❌ 云端 | ❌ 云端 | ❌ 云端 |
| 水印 | 无 | 有 | 有 | C2PA 元数据 | 有 |
| 使用限制 | 无（16 请求/分钟限流） | 按算力计费 | 按次计费 | 按次计费 | 按次计费 |

## 项目结构

```
## 项目结构
agnes-video-generator/
├── server.py                 # 服务入口
├── core/                     # 核心生成流水线
├── models/                   # 模型适配层
├── web/                      # Web UI 后端
├── frontend/                 # Vue 3 + Vite + TypeScript 前端
├── utils/                    # 工具函数
├── static/                   # 静态资源
├── resource/                 # 字体等资源
├── bin/                      # 启动器
├── scripts/                  # 辅助脚本
├── docs/                     # 文档
├── tests/                    # 测试
├── Dockerfile
├── docker-compose.yml
├── docker-run.sh
├── requirements.txt
├── requirements-dev.txt
├── package.json
├── start.sh                  # Linux/macOS 启动脚本
├── start.bat                 # Windows 启动脚本
├── .env.example              # 环境变量模板
└── LICENSE
```

## 致谢

- [lcy362/agnes-video-generator](https://github.com/lcy362/agnes-video-generator) —— 本 fork 的直接上游
- [Agnes AI](https://platform.agnes-ai.com) —— AI 生成 API

## 许可证

MIT
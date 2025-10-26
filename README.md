# B站视频逐字稿提取系统

一个免费的Web应用，自动从B站视频中提取完整逐字稿。

## 🎯 功能特点

- ✅ **智能降级策略**：优先使用CC字幕 → AI字幕 → 语音识别
- ✅ **完全免费**：使用开源工具和免费API
- ✅ **简单易用**：输入视频链接即可获取逐字稿
- ✅ **多种格式**：支持纯文本、SRT字幕、JSON格式导出
- ✅ **现代界面**：基于 Tailwind CSS 的响应式设计

## 📋 当前部署状态

### ✅ 已完成功能

1. **前端界面**
   - ✅ 视频链接输入
   - ✅ 格式选择（TXT/SRT/JSON）
   - ✅ 进度显示
   - ✅ 结果展示
   - ✅ 复制和下载功能

2. **后端API**
   - ✅ FastAPI 框架
   - ✅ 视频信息获取
   - ✅ CC字幕提取
   - ✅ AI字幕提取
   - ✅ 异步任务处理
   - ✅ SSL证书问题修复

3. **服务模块**
   - ✅ B站API封装（bilibili_api.py）
   - ✅ 字幕处理器（subtitle_processor.py）
   - ✅ 可选依赖处理（优雅降级）

### ⚠️ 可选功能（需要额外安装）

- ⏸ **视频下载**：需要安装 Playwright
- ⏸ **语音识别**：需要安装 bcut-asr 或 faster-whisper
- ⏸ **AI总结**：DeepSeek集成（预留接口）

## 🚀 快速开始

### 1. 安装依赖

已提供自动安装脚本：

```bash
chmod +x install.sh
./install.sh
```

或手动安装：

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装核心依赖
pip install fastapi uvicorn aiohttp pydantic pydantic-settings
pip install python-multipart aiofiles python-dotenv loguru

# 可选：安装完整功能依赖
pip install playwright && playwright install chromium
pip install faster-whisper
```

### 2. 启动服务

```bash
# 开发模式（自动重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload
```

服务将在 `http://localhost:8000` 启动

### 3. 访问应用

- **Web界面**: http://localhost:8000
- **API文档**: http://localhost:8000/api/docs
- **API调试**: http://localhost:8000/api/redoc

## 📖 使用方法

### 通过Web界面

1. 打开浏览器访问 http://localhost:8000
2. 输入B站视频链接（例如：`https://www.bilibili.com/video/BV1xx411c7XZ`）
3. 选择输出格式（纯文本/SRT/JSON）
4. 点击"提取逐字稿"按钮
5. 等待处理完成，查看结果
6. 可以复制文本或下载文件

### 通过API调用

```bash
# 提取逐字稿
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BV1xx411c7XZ",
    "format": "txt"
  }'

# 查询ASR任务进度（如果需要语音识别）
curl http://localhost:8000/api/progress/{task_id}
```

## 🏗️ 项目结构

```
bilibili-text/
├── app/
│   ├── api/
│   │   ├── models.py          # Pydantic数据模型
│   │   └── routes.py          # API路由
│   ├── core/
│   │   ├── config.py          # 配置管理
│   │   └── logger.py          # 日志配置
│   └── services/
│       ├── bilibili_api.py    # B站API封装
│       ├── subtitle_processor.py  # 字幕处理
│       ├── video_downloader.py    # 视频下载（可选）
│       └── asr_engine.py      # 语音识别（可选）
├── frontend/
│   └── index.html             # Web界面
├── main.py                    # 应用入口
├── install.sh                 # 自动安装脚本
├── requirements.txt           # 依赖列表
├── CLAUDE.md                  # Claude Code 指南
└── README.md                  # 本文件
```

## 🔧 配置说明

在项目根目录创建 `.env` 文件：

```bash
# 环境设置
APP_ENV=development
DEBUG=True

# B站API（可选，提高访问成功率）
BILIBILI_COOKIE=your_cookie_here

# ASR配置
ASR_PROVIDER=bcut  # 或 whisper
WHISPER_MODEL=base

# 文件存储
UPLOAD_DIR=./data/uploads
TEMP_DIR=./data/temp
MAX_FILE_SIZE=500MB

# 日志
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# 任务限制
MAX_VIDEO_DURATION=7200  # 2小时
REQUEST_TIMEOUT=1800     # 30分钟
MAX_RETRY=3
```

## 📝 API端点

### POST /api/extract
提取视频逐字稿

**请求示例**:
```json
{
  "url": "https://www.bilibili.com/video/BV1xx411c7XZ",
  "format": "txt"  // txt, srt, json
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "bvid": "BV1xx411c7XZ",
    "title": "视频标题",
    "duration": 600,
    "method": "subtitle",  // subtitle, ai_subtitle, asr
    "transcript": "完整的逐字稿文本...",
    "utterances": [
      {
        "text": "这是第一句话",
        "start": 0.0,
        "end": 3.5
      }
    ]
  }
}
```

### GET /api/progress/{task_id}
查询ASR任务进度

**响应示例**:
```json
{
  "task_id": "uuid",
  "status": "processing",  // pending, processing, completed, failed
  "progress": 50,
  "message": "正在语音识别...",
  "result": null  // 完成后包含 TranscriptData
}
```

## 🧪 测试

### 测试有字幕的视频

大多数官方UP主的视频都有CC字幕或AI字幕，这些视频可以快速提取逐字稿（<3秒）。

### 测试无字幕的视频

需要安装 Playwright 和 ASR 引擎才能处理无字幕视频。

## ⚠️ 已知限制

1. **短链接**: `b23.tv` 短链接解析尚未实现
2. **视频下载**: 需要 Playwright，且 snapany.com 选择器可能需要更新
3. **语音识别**:
   - bcut-asr 需要手动从 GitHub 安装
   - faster-whisper 处理速度较慢
4. **任务存储**: 当前使用内存存储，重启后丢失
5. **多P视频**: 暂不支持分P视频
6. **DeepSeek总结**: 预留接口，未实现

## 🔐 安全说明

当前版本禁用了 SSL 证书验证（仅用于开发环境），生产环境部署时应：
1. 安装正确的 SSL 证书
2. 启用证书验证
3. 添加请求限流
4. 配置 CORS 白名单

## 📄 许可证

本项目基于开源协议，仅用于个人学习研究。请遵守B站使用条款。

## 🙏 致谢

- [bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect) - B站API文档
- [bcut-asr](https://github.com/SocialSisterYi/bcut-asr) - 必剪ASR接口
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Whisper优化版本
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Web框架

## 📞 支持

如遇问题，请查看：
- API文档：http://localhost:8000/api/docs
- 日志文件：`./logs/app.log`
- 开发文档：`requirement.md`
- Claude指南：`CLAUDE.md`

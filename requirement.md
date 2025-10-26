# B 站视频逐字稿提取系统 - 需求文档

## 一、项目概述

### 1.1 项目名称

B 站视频逐字稿提取系统（Bilibili Transcript Extractor）

### 1.2 项目目标

构建一个免费的 Web 应用，用户输入 B 站视频链接，自动提取或生成完整的逐字稿文本。

### 1.3 核心价值

- **完全免费**：使用免费 API 和开源工具
- **智能降级**：优先使用已有字幕，无字幕时自动语音识别
- **高准确率**：使用必剪 ASR（中文识别率 90%+）
- **简单易用**：输入链接即可获取逐字稿

---

## 二、技术架构

### 2.1 技术栈

**后端**

- Python 3.10+
- FastAPI（Web 框架）
- aiohttp（异步 HTTP 请求）
- bcut-asr（必剪 ASR 接口封装）
- faster-whisper（备选语音识别）
- playwright（浏览器自动化）
- ffmpeg（音视频处理）

**前端**

- HTML5 + CSS3 + JavaScript
- Tailwind CSS（样式框架）
- Fetch API（与后端交互）

**部署**

- Docker 容器化部署
- Nginx 反向代理

### 2.2 系统架构图

```
用户 → 前端界面
         ↓
    FastAPI后端
         ↓
    ┌────┴────┐
    ↓         ↓
字幕提取    视频下载
    ↓         ↓
  返回    语音识别
    ↓         ↓
    └────┬────┘
         ↓
    格式化输出
         ↓
      返回前端
```

---

## 三、功能需求

### 3.1 核心功能

#### 功能 1：B 站链接解析

**输入**: B 站视频 URL（支持多种格式）

- `https://www.bilibili.com/video/BV1xx411c7XZ`
- `https://b23.tv/xxxxx`（短链接）

**处理流程**:

1. 提取 BV 号
2. 调用 B 站 API 获取视频基本信息（标题、UP 主、时长等）
3. 获取 CID

**输出**: 视频元数据 + CID

#### 功能 2：字幕提取（优先级最高）

**2.1 CC 字幕提取**

- API: `https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}`
- 检查 `data.subtitle.subtitles` 字段
- 如有字幕，下载 JSON 并解析

**2.2 AI 字幕提取**

- 检查 B 站 AI 生成的字幕
- URL 格式: `https://aisubtitle.hdslb.com/bfs/subtitle/{hash}.json`

**2.3 字幕格式转换**

- 输入: B 站字幕 JSON 格式
- 输出: 纯文本逐字稿（带时间戳可选）

#### 功能 3：视频下载（字幕不存在时）

**方案 A：Playwright MCP 自动化**（推荐）

- 使用 Playwright MCP 访问 `https://snapany.com/zh/bilibili`
- 自动化流程：
  1. 输入 B 站链接
  2. 点击下载按钮
  3. 等待处理完成
  4. 获取下载链接
  5. 下载音频文件（优先）或视频文件

**方案 B：直接调用 B 站 API**（备选）

- 使用 B 站视频流 API 直接下载
- 需要处理鉴权和防盗链

**输出**: 音频文件（MP3/M4A）或视频文件（MP4）

#### 功能 4：语音识别

**方案 A：必剪 ASR**（主方案）

- 使用 `bcut-asr` 库
- 优势：
  - 完全免费
  - 中文识别准确率高（90%+）
  - 云端处理，速度快
  - 自动断句

**处理流程**:

```python
from bcut_asr import BcutASR

# 初始化
asr = BcutASR()

# 上传音频并识别
result = asr.recognize(audio_file)

# 获取结果
transcript = result['utterances']
```

**方案 B：Faster-Whisper**（备选）

- 本地运行的开源模型
- 优势：
  - 完全离线
  - 支持多语言
  - 高准确率
- 劣势：
  - 需要 GPU 加速（可选）
  - 处理速度较慢

**输出**: 带时间戳的逐字稿

#### 功能 5：结果展示与导出

**展示格式**:

- 纯文本（默认）
- 带时间戳的文本
- SRT 字幕格式
- JSON 格式

**导出功能**:

- 复制到剪贴板
- 下载为 TXT 文件
- 下载为 SRT 字幕文件

### 3.2 辅助功能

#### 功能 6：进度提示

- 解析视频信息：5%
- 检查字幕：15%
- 下载视频：50%（如需要）
- 语音识别：85%（如需要）
- 完成：100%

#### 功能 7：错误处理

- 无效链接提示
- 视频不存在/已删除
- 下载失败重试（最多 3 次）
- 识别失败提示
- 网络错误提示

#### 功能 8：历史记录（可选）

- 保存最近 10 条记录
- 快速重新获取

---

## 四、技术实现方案

### 4.1 核心模块

#### 模块 1：API 服务层

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class VideoRequest(BaseModel):
    url: str

@app.post("/api/extract")
async def extract_transcript(request: VideoRequest):
    """提取逐字稿主接口"""
    pass
```

#### 模块 2：B 站 API 封装

```python
# bilibili_api.py
class BilibiliAPI:
    async def get_video_info(self, bvid: str):
        """获取视频信息"""
        pass

    async def get_subtitle(self, bvid: str, cid: int):
        """获取字幕"""
        pass

    async def get_ai_subtitle(self, bvid: str, cid: int):
        """获取AI字幕"""
        pass
```

#### 模块 3：视频下载器

```python
# video_downloader.py
class VideoDownloader:
    async def download_with_playwright(self, url: str):
        """使用Playwright从snapany下载"""
        pass

    async def download_audio_only(self, url: str):
        """优先下载音频"""
        pass
```

#### 模块 4：语音识别引擎

```python
# asr_engine.py
class ASREngine:
    async def recognize_with_bcut(self, audio_path: str):
        """使用必剪ASR识别"""
        pass

    async def recognize_with_whisper(self, audio_path: str):
        """使用Whisper识别（备选）"""
        pass
```

#### 模块 5：字幕处理器

```python
# subtitle_processor.py
class SubtitleProcessor:
    def parse_bilibili_subtitle(self, subtitle_json):
        """解析B站字幕JSON"""
        pass

    def format_transcript(self, utterances, format_type='txt'):
        """格式化输出"""
        pass

    def to_srt(self, utterances):
        """转换为SRT格式"""
        pass
```

### 4.2 处理流程

```python
async def process_video(url: str):
    """
    完整处理流程
    """
    # 步骤1：解析BV号
    bvid = extract_bvid(url)

    # 步骤2：获取视频信息
    video_info = await bilibili_api.get_video_info(bvid)
    cid = video_info['cid']

    # 步骤3：尝试获取字幕
    subtitle = await bilibili_api.get_subtitle(bvid, cid)
    if subtitle:
        return format_subtitle(subtitle)

    # 步骤4：尝试获取AI字幕
    ai_subtitle = await bilibili_api.get_ai_subtitle(bvid, cid)
    if ai_subtitle:
        return format_subtitle(ai_subtitle)

    # 步骤5：下载视频/音频
    audio_path = await downloader.download_audio_only(url)

    # 步骤6：语音识别
    try:
        transcript = await asr.recognize_with_bcut(audio_path)
    except Exception:
        # 备选方案
        transcript = await asr.recognize_with_whisper(audio_path)

    # 步骤7：格式化并返回
    return format_transcript(transcript)
```

---

## 五、接口设计

### 5.1 RESTful API

#### 接口 1：提取逐字稿

**请求**

```http
POST /api/extract
Content-Type: application/json

{
  "url": "https://www.bilibili.com/video/BV1xx411c7XZ",
  "format": "txt"  // txt, srt, json
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "bvid": "BV1xx411c7XZ",
    "title": "视频标题",
    "duration": 600,
    "method": "subtitle", // subtitle, ai_subtitle, asr
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

#### 接口 2：检查进度（WebSocket 可选）

```http
GET /api/progress/{task_id}
```

### 5.2 错误码

| 错误码 | 说明         |
| ------ | ------------ |
| 0      | 成功         |
| 1001   | 无效的 URL   |
| 1002   | 视频不存在   |
| 1003   | 视频无法访问 |
| 2001   | 下载失败     |
| 2002   | 识别失败     |
| 5000   | 服务器错误   |

---

## 六、数据库设计（可选）

如需要历史记录功能：

```sql
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bvid VARCHAR(20) NOT NULL,
    title TEXT,
    method VARCHAR(20),  -- subtitle, ai_subtitle, asr
    transcript TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bvid (bvid)
);
```

---

## 七、部署方案

### 7.1 Docker 部署

**Dockerfile**

```dockerfile
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    chromium \
    chromium-driver

# 安装Python依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制代码
COPY . /app
WORKDIR /app

# 启动服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**

```yaml
version: "3.8"

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend:/usr/share/nginx/html
    depends_on:
      - backend
    restart: unless-stopped
```

### 7.2 环境变量配置

```bash
# .env
APP_ENV=production
DEBUG=False

# B站API配置（如需要Cookie）
BILIBILI_COOKIE=your_cookie_here

# ASR配置
ASR_PROVIDER=bcut  # bcut or whisper
WHISPER_MODEL=base  # tiny, base, small, medium, large

# 文件存储
UPLOAD_DIR=/app/data/uploads
TEMP_DIR=/app/data/temp
MAX_FILE_SIZE=500MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
```

---

## 八、性能要求

### 8.1 响应时间

- 字幕提取：< 3 秒
- 视频下载：取决于视频大小
- 语音识别：
  - 必剪 ASR：~1 分钟/10 分钟视频
  - Whisper：~2-5 分钟/10 分钟视频（CPU）

### 8.2 并发处理

- 支持至少 10 个并发请求
- 使用任务队列管理识别任务
- 限流：同一 IP 每小时最多 20 次请求

### 8.3 资源限制

- 单个视频最大时长：2 小时
- 单个文件最大大小：500MB
- 临时文件定期清理（每小时）

---

## 九、安全考虑

### 9.1 输入验证

- URL 格式验证
- 防止 SSRF 攻击
- 文件类型检查

### 9.2 资源保护

- 请求频率限制
- 文件大小限制
- 超时保护（30 分钟）

### 9.3 隐私保护

- 临时文件加密存储
- 处理完成后自动删除
- 不保存用户个人信息

---

## 十、开发计划

### Phase 1：核心功能（1-2 周）

- ✅ 搭建 FastAPI 框架
- ✅ 实现 B 站 API 调用
- ✅ 实现字幕提取功能
- ✅ 基础前端页面

### Phase 2：视频下载（1 周）

- ✅ 集成 Playwright
- ✅ 实现 snapany 自动化下载
- ✅ 音频提取功能

### Phase 3：语音识别（1-2 周）

- ✅ 集成必剪 ASR
- ✅ 集成 Whisper（备选）
- ✅ 优化识别准确率

### Phase 4：优化与部署（1 周）

- ✅ 性能优化
- ✅ Docker 打包
- ✅ 部署文档

### Phase 5：扩展功能（可选）

- 批量处理
- 字幕翻译
- API 调用统计

---

## 十一、成本分析

### 11.1 服务器成本

- 基础配置：2 核 4G（月费约 50-100 元）
- 推荐配置：4 核 8G + GPU（月费约 200-500 元）

### 11.2 API 成本

- B 站 API：免费
- 必剪 ASR：免费
- Whisper：免费（开源）
- **总计：0 元/月**

### 11.3 带宽成本

- 视频下载会消耗大量带宽
- 建议：按需计费，估计月费 50-200 元

---

## 十二、风险与应对

### 12.1 技术风险

| 风险               | 影响 | 应对方案              |
| ------------------ | ---- | --------------------- |
| B 站 API 变更      | 高   | 定期检查，及时更新    |
| 必剪 ASR 限流/关闭 | 中   | 提供 Whisper 备选方案 |
| snapany 不可用     | 中   | 开发直接下载方案      |
| 识别准确率低       | 中   | 提供手动校正功能      |

### 12.2 法律风险

- 遵守 B 站使用条款
- 仅用于个人学习研究
- 不提供批量下载功能
- 添加免责声明

---

## 十三、测试计划

### 13.1 单元测试

- API 调用测试
- 字幕解析测试
- 格式转换测试

### 13.2 集成测试

- 完整流程测试
- 错误处理测试
- 并发测试

### 13.3 测试用例

1. 有 CC 字幕的视频
2. 有 AI 字幕的视频
3. 无字幕视频（需要识别）
4. 长视频（>1 小时）
5. 多 P 视频
6. 已删除/无权限视频

---

## 十四、文档清单

### 14.1 开发文档

- [ ] API 文档
- [ ] 架构设计文档
- [ ] 数据库设计文档
- [ ] 部署文档

### 14.2 用户文档

- [ ] 使用指南
- [ ] FAQ
- [ ] 常见问题解决

### 14.3 运维文档

- [ ] 服务器配置指南
- [ ] 监控告警配置
- [ ] 故障排查手册

---

## 十五、附录

### 15.1 相关资源

- B 站 API 文档：https://socialsisteryi.github.io/bilibili-API-collect/
- bcut-asr 项目：https://github.com/SocialSisterYi/bcut-asr
- Faster-Whisper：https://github.com/guillaumekln/faster-whisper
- Playwright 文档：https://playwright.dev/python/

### 15.2 参考项目

- BibiGPT: https://bibigpt.co
- VideoCaptioner: https://github.com/WEIFENG2333/VideoCaptioner

---

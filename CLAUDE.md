# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bilibili Transcript Extractor (B站视频逐字稿提取系统) - A free web application that extracts or generates complete transcripts from Bilibili videos.

**Core Value Proposition**:
- Completely free (uses free APIs and open-source tools)
- Intelligent degradation: prioritizes existing subtitles, auto ASR when unavailable
- High accuracy: uses Bcut ASR (90%+ Chinese recognition rate)
- Simple to use: just input a Bilibili video link

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for video downloading)
playwright install chromium

# Optional: Install bcut-asr (primary ASR engine)
# git clone https://github.com/SocialSisterYi/bcut-asr
# cd bcut-asr
# poetry lock && poetry build -f wheel
# pip install dist/bcut_asr-*.whl
```

### Running the Application
```bash
# Development mode (with auto-reload)
python main.py

# Production mode with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000

# The API will be available at:
# - Main API: http://localhost:8000/api
# - API Docs: http://localhost:8000/api/docs
# - Health Check: http://localhost:8000/health
```

### Environment Configuration
Create a `.env` file with:
```bash
# Environment
APP_ENV=development
DEBUG=True

# Bilibili API (optional, for better access)
BILIBILI_COOKIE=your_cookie_here

# ASR Configuration
ASR_PROVIDER=bcut  # or whisper
WHISPER_MODEL=base  # if using whisper: tiny, base, small, medium, large

# File Storage
UPLOAD_DIR=./data/uploads
TEMP_DIR=./data/temp
MAX_FILE_SIZE=500MB

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# Task Configuration
MAX_VIDEO_DURATION=7200  # seconds (2 hours)
REQUEST_TIMEOUT=1800     # seconds (30 minutes)
MAX_RETRY=3
```

## Architecture Overview

**Tech Stack**:
- Backend: FastAPI + asyncio
- HTTP Client: aiohttp (async Bilibili API calls)
- Browser Automation: Playwright (for video downloading via snapany.com)
- ASR Engines:
  - Primary: bcut-asr (free cloud-based, high accuracy for Chinese)
  - Fallback: faster-whisper (local, open-source)
- File Processing: ffmpeg-python

**Project Structure**:
```
bilibili-text/
├── app/
│   ├── api/
│   │   ├── models.py          # Pydantic models for API requests/responses
│   │   └── routes.py          # API endpoints and business logic
│   ├── core/
│   │   ├── config.py          # Application configuration (Settings class)
│   │   └── logger.py          # Logging setup
│   └── services/
│       ├── bilibili_api.py    # Bilibili API wrapper (video info, subtitles)
│       ├── subtitle_processor.py  # Subtitle parsing and format conversion
│       ├── video_downloader.py    # Playwright-based video/audio downloader
│       └── asr_engine.py      # ASR recognition (bcut/whisper)
├── frontend/
│   └── index.html             # Static frontend (served by FastAPI)
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
└── requirement.md             # Detailed requirements documentation (Chinese)
```

## Key Technical Patterns

### 1. Intelligent Transcript Extraction Pipeline

The system follows a cascading fallback strategy:

```python
# routes.py: extract_transcript() flow
1. Parse BV ID from URL
2. Fetch video metadata (title, duration, CID) via Bilibili API
3. Try CC subtitles → return if found
4. Try AI-generated subtitles → return if found
5. No subtitles → create async background task for ASR
   - Download audio via Playwright (snapany.com)
   - Run ASR recognition (bcut → whisper fallback)
   - Return task_id for progress tracking
```

### 2. Bilibili API Integration

**BilibiliAPI class** (`bilibili_api.py`):
- `extract_bvid()`: Supports multiple URL formats (full URL, short link b23.tv, direct BV ID)
- `get_video_info()`: Fetches metadata via `/x/web-interface/view`
- `get_subtitle()`: Retrieves CC subtitles from `/x/player/v2` → downloads subtitle JSON
- `get_ai_subtitle()`: Checks for AI-generated subtitles (same endpoint, different field)
- All methods use async/await with aiohttp

**Important**: Subtitles are returned as JSON arrays with format:
```json
[{"from": 0.0, "to": 3.5, "content": "这是第一句话"}, ...]
```

### 3. ASR Engine Architecture

**ASREngine class** (`asr_engine.py`):
- Main interface: `recognize(audio_path)` → returns `List[Utterance]`
- Provider selection via config: `settings.ASR_PROVIDER` ("bcut" or "whisper")
- Automatic fallback: if bcut fails → try whisper
- Returns normalized `Utterance` objects: `{text, start, end}`

**Bcut ASR specifics**:
- Cloud-based, requires network
- Result format: `{"utterances": [{"text": "...", "start_time": 0.0, "end_time": 3.5}]}`

**Whisper specifics**:
- Local model, runs on CPU (int8 quantization)
- Model sizes configurable: tiny, base, small, medium, large
- Uses VAD (Voice Activity Detection) for better segmentation

### 4. Video Downloading with Playwright

**VideoDownloader class** (`video_downloader.py`):
- Uses Playwright to automate snapany.com (https://snapany.com/zh/bilibili)
- Workflow:
  1. Launch headless Chromium browser
  2. Navigate to snapany
  3. Fill input with Bilibili URL
  4. Click download button
  5. Wait for download link (up to 120s timeout)
  6. Download audio file via aiohttp
- Stores files in `TEMP_DIR` with hash-based filenames

**Note**: The snapany selectors may need updates if the website changes. Key selectors:
- Input: `input[type="text"]`
- Download button: `button:has-text("下载")`
- Download link: `.download-link`

### 5. Subtitle Format Conversion

**SubtitleProcessor class** (`subtitle_processor.py`):
- `parse_bilibili_subtitle()`: Converts Bilibili JSON to `Utterance` objects
- `format_transcript()`: Supports 3 output formats:
  - `txt`: Plain text (all utterances joined)
  - `srt`: Standard SRT subtitle format with timestamps
  - `json`: JSON array of utterances
- Timestamp formatting follows SRT conventions: `HH:MM:SS,mmm`

### 6. Background Task Processing

Uses FastAPI's `BackgroundTasks` for async ASR:
- `process_video_with_asr()`: Long-running task for download + ASR
- Task storage: in-memory dict (production should use Redis)
- Progress tracking: `/api/progress/{task_id}` endpoint
- States: pending → processing → completed/failed
- Progress percentages: 10% (download start) → 50% (ASR start) → 90% (formatting) → 100%

## API Endpoints

```
POST /api/extract
  Request: {"url": "https://bilibili.com/video/BV...", "format": "txt|srt|json"}
  Response: {
    "code": 0,
    "message": "success",
    "data": {
      "bvid": "BV...",
      "title": "...",
      "duration": 600,
      "method": "subtitle|ai_subtitle|asr",
      "transcript": "完整文本...",
      "utterances": [{"text": "...", "start": 0.0, "end": 3.5}]
    }
  }

GET /api/progress/{task_id}
  Response: {
    "task_id": "...",
    "status": "pending|processing|completed|failed",
    "progress": 0-100,
    "message": "...",
    "result": TranscriptData (when completed)
  }

POST /api/summarize
  Status: Not implemented (reserved for DeepSeek integration)
  Returns: 501 Not Implemented

GET /health
  Response: {"status": "healthy"}
```

## Error Codes (as per requirement.md)

| Code | Description |
|------|-------------|
| 0    | Success |
| 1001 | Invalid URL |
| 1002 | Video not found |
| 1003 | Video inaccessible |
| 2001 | Download failed |
| 2002 | Recognition failed |
| 5000 | Server error |

## Development Phases (from requirement.md)

- ✅ Phase 1: Core functionality (FastAPI framework, Bilibili API, subtitle extraction, basic frontend)
- ✅ Phase 2: Video downloading (Playwright integration, snapany automation, audio extraction)
- ✅ Phase 3: Speech recognition (bcut ASR, Whisper fallback, accuracy optimization)
- ✅ Phase 4: Optimization & deployment (performance tuning, Docker packaging, deployment docs)
- ⏸ Phase 5: Extended features (batch processing, subtitle translation, API statistics) - Optional

## Known Limitations and TODOs

1. **Short URL (b23.tv) parsing**: Not implemented in `extract_bvid()` - needs redirect following
2. **Snapany selectors**: Hardcoded and fragile - may break if website updates
3. **Direct Bilibili download**: `_download_with_bilibili_api()` not implemented (requires auth handling)
4. **Task storage**: Uses in-memory dict - production needs Redis/database
5. **bcut-asr installation**: Not in requirements.txt (requires manual install from GitHub)
6. **DeepSeek summarization**: `/api/summarize` endpoint stubbed out (501 Not Implemented)
7. **Temporary file cleanup**: `cleanup_temp_files()` exists but not called automatically - should add periodic cleanup job
8. **Multi-part videos**: No handling for multi-P (分P) Bilibili videos
9. **Rate limiting**: No IP-based rate limiting implemented (requirement.md suggests 20 requests/hour/IP)

## Configuration Best Practices

1. **ASR Provider Selection**:
   - Use `bcut` for production (free, fast, high accuracy for Chinese)
   - Use `whisper` for offline scenarios or non-Chinese content
   - Set `WHISPER_MODEL=base` for balance of speed/accuracy (faster than small/medium/large)

2. **Resource Limits**:
   - `MAX_VIDEO_DURATION=7200` (2 hours) prevents abuse
   - `REQUEST_TIMEOUT=1800` (30 min) allows for large video processing
   - `MAX_FILE_SIZE=500MB` limits storage usage

3. **Logging**:
   - Development: `LOG_LEVEL=DEBUG` for detailed troubleshooting
   - Production: `LOG_LEVEL=INFO` to reduce noise
   - Logs rotate automatically (see `logger.py`)

4. **Bilibili Cookie** (optional):
   - Not required for public videos
   - Needed for member-only or login-required content
   - Extract from browser DevTools → Application → Cookies

## Testing Recommendations

Use these test cases (from requirement.md Section 13.3):
1. Video with CC subtitles (fastest path)
2. Video with AI-generated subtitles
3. Video without subtitles (full ASR pipeline)
4. Long video (>1 hour) - tests timeout handling
5. Multi-part (多P) video - currently not supported
6. Deleted/private video - tests error handling

## Docker Deployment (from requirement.md)

```dockerfile
FROM python:3.10-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    chromium \
    chromium-driver

# Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt && playwright install chromium

# Application
COPY . /app
WORKDIR /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Note**: Production deployment should use docker-compose with nginx reverse proxy (see requirement.md Section 7.1)

## Reference Documentation

- Bilibili API Collection: https://socialsisteryi.github.io/bilibili-API-collect/
- bcut-asr GitHub: https://github.com/SocialSisterYi/bcut-asr
- faster-whisper GitHub: https://github.com/guillaumekln/faster-whisper
- Playwright Python Docs: https://playwright.dev/python/
- Full requirements: See `requirement.md` (Chinese, comprehensive spec)

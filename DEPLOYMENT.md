# B站视频逐字稿提取系统 - 部署指南

## 为什么不能部署到 Vercel？

Vercel 是 Serverless 平台，**不支持**以下需求：
- ❌ 系统级依赖（FFmpeg, Chromium）
- ❌ 长时间运行任务（视频下载、ASR 需要数分钟）
- ❌ 大内存占用（Whisper 模型加载）
- ❌ 文件写入操作（临时音频文件）

## 推荐部署方案

### 🚀 方案 1：Railway.app（最简单，推荐）

**优势**：
- ✅ 原生支持 Docker
- ✅ 自动从 GitHub 部署
- ✅ 免费额度（每月 $5 credit）
- ✅ 内置环境变量管理
- ✅ 自动 HTTPS 域名

**部署步骤**：

1. **注册 Railway**
   - 访问 https://railway.app
   - 使用 GitHub 账号登录

2. **创建新项目**
   ```
   New Project → Deploy from GitHub repo → 选择 bili-pro
   ```

3. **配置环境变量**
   ```
   Settings → Variables → Add Variables
   ```
   添加以下变量：
   ```
   DEEPSEEK_API_KEY=sk-b7f4afd268664e4582e33a60305fff34
   DEEPSEEK_API_URL=https://api.deepseek.com/v1
   ASR_PROVIDER=whisper
   WHISPER_MODEL=base
   APP_ENV=production
   DEBUG=False
   ```

4. **设置端口**
   ```
   Settings → Networking → Port = 8000
   ```

5. **部署**
   - Railway 会自动检测 Dockerfile
   - 自动构建并部署
   - 等待 5-10 分钟（首次构建较慢）

6. **访问应用**
   - Railway 会提供一个域名：`https://your-app.up.railway.app`

---

### 🐳 方案 2：Render.com（稳定可靠）

**优势**：
- ✅ 免费套餐（有限制）
- ✅ 自动从 GitHub 部署
- ✅ 内置 SSL 证书

**部署步骤**：

1. **注册 Render**
   - 访问 https://render.com
   - 连接 GitHub 账号

2. **创建 Web Service**
   ```
   New → Web Service → Connect bili-pro repo
   ```

3. **配置服务**
   ```
   Name: bilibili-transcript
   Environment: Docker
   Region: Singapore (离中国近)
   Branch: main
   ```

4. **添加环境变量**（同 Railway）

5. **部署**
   - 点击 "Create Web Service"
   - 等待构建完成

---

### ☁️ 方案 3：传统 VPS（腾讯云/阿里云）

**适合场景**：
- 需要完全控制
- 长期稳定运行
- 国内访问速度要求高

**部署步骤**：

1. **购买服务器**
   - 配置建议：2核4G，40GB SSD
   - 系统：Ubuntu 22.04

2. **安装 Docker**
   ```bash
   # 安装 Docker
   curl -fsSL https://get.docker.com | bash

   # 启动 Docker
   systemctl start docker
   systemctl enable docker
   ```

3. **克隆代码**
   ```bash
   git clone git@github.com:JxcChen/bili-pro.git
   cd bili-pro
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   nano .env  # 编辑配置文件
   ```

5. **构建并运行**
   ```bash
   # 构建镜像
   docker build -t bilibili-transcript .

   # 运行容器
   docker run -d \
     --name bili-app \
     -p 8000:8000 \
     --env-file .env \
     --restart unless-stopped \
     bilibili-transcript
   ```

6. **配置 Nginx 反向代理（可选）**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

### 🌐 方案 4：Fly.io（全球分布）

**优势**：
- ✅ 免费额度（3个共享 CPU 应用）
- ✅ 全球边缘节点
- ✅ 快速部署

**部署步骤**：

1. **安装 Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **登录 Fly**
   ```bash
   flyctl auth login
   ```

3. **初始化项目**
   ```bash
   cd bili-pro
   flyctl launch
   ```
   配置：
   ```
   App name: bilibili-transcript
   Region: Hong Kong (hkg)
   ```

4. **设置环境变量**
   ```bash
   flyctl secrets set DEEPSEEK_API_KEY=sk-b7f4afd268664e4582e33a60305fff34
   flyctl secrets set DEEPSEEK_API_URL=https://api.deepseek.com/v1
   ```

5. **部署**
   ```bash
   flyctl deploy
   ```

---

## 本地 Docker 测试

在部署到云端前，建议本地先测试：

```bash
# 构建镜像
docker build -t bilibili-transcript .

# 运行容器
docker run -p 8000:8000 --env-file .env bilibili-transcript

# 访问测试
curl http://localhost:8000/health
```

---

## 环境变量说明

| 变量 | 说明 | 必填 | 示例 |
|------|------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | ✅ | `sk-xxx` |
| `DEEPSEEK_API_URL` | DeepSeek API 地址 | ✅ | `https://api.deepseek.com/v1` |
| `ASR_PROVIDER` | 语音识别引擎 | ❌ | `whisper` (默认) |
| `WHISPER_MODEL` | Whisper 模型大小 | ❌ | `base` (默认) |
| `APP_ENV` | 运行环境 | ❌ | `production` |
| `DEBUG` | 调试模式 | ❌ | `False` |

---

## 故障排查

### 1. 构建失败 - FFmpeg 依赖错误
**问题**：`Package 'libavformat' not found`

**解决**：使用 Dockerfile 部署，不要用 Vercel

---

### 2. 视频下载超时
**问题**：`Download timeout after 120s`

**解决**：
- 检查服务器网络
- 确保 yt-dlp 正常工作
- 调大 `REQUEST_TIMEOUT` 环境变量

---

### 3. Whisper 模型加载慢
**问题**：首次启动很慢

**解决**：
- 使用更小的模型（`tiny` 或 `base`）
- 预先下载模型到镜像中

---

## 性能优化建议

1. **使用更快的 ASR 引擎**
   - `bcut-asr`（云端，速度快）优于 `faster-whisper`（本地）

2. **调整 Whisper 模型大小**
   ```
   tiny   - 最快，准确率略低
   base   - 平衡（推荐）
   small  - 较慢，准确率高
   medium - 慢，高准确率
   large  - 很慢，最高准确率
   ```

3. **使用 Redis 存储任务状态**（生产环境）
   - 当前使用内存字典，重启丢失
   - 建议配置 Redis 做持久化

---

## 成本估算

| 平台 | 免费额度 | 付费价格 |
|------|---------|---------|
| Railway | $5/月 credit | $0.000463/GB-hr |
| Render | 750 小时/月 | $7/月起 |
| Fly.io | 3 个应用 | $1.94/月起 |
| 腾讯云 | 无 | ¥50-100/月 |

---

## 下一步

1. ✅ 选择部署平台（推荐 Railway）
2. ✅ 配置环境变量
3. ✅ 部署应用
4. ✅ 测试完整流程
5. ⏳ 监控日志和性能

有问题随时提问！

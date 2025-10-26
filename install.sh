#!/bin/bash

# B站视频逐字稿提取系统 - 安装脚本

echo "开始安装依赖..."

# 激活虚拟环境
source venv/bin/activate

# 尝试禁用代理
export NO_PROXY="*"
export no_proxy="*"
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY

# 升级 pip
echo "升级 pip..."
python -m pip install --upgrade pip --no-proxy

# 安装核心依赖（分批安装避免网络问题）
echo "安装核心依赖..."

# 第一批：Web 框架
echo "安装 FastAPI 和 Uvicorn..."
pip install --no-cache-dir fastapi uvicorn || {
    echo "尝试使用国内镜像..."
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn
}

# 第二批：HTTP 客户端
echo "安装 HTTP 客户端..."
pip install --no-cache-dir aiohttp httpx requests || {
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple aiohttp httpx requests
}

# 第三批：数据处理
echo "安装数据处理库..."
pip install --no-cache-dir pydantic pydantic-settings || {
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple pydantic pydantic-settings
}

# 第四批：其他依赖
echo "安装其他依赖..."
pip install --no-cache-dir python-multipart aiofiles python-dotenv loguru || {
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple python-multipart aiofiles python-dotenv loguru
}

echo "基础依赖安装完成！"
echo ""
echo "注意：以下依赖是可选的，用于完整功能："
echo "  - playwright: 用于视频下载（pip install playwright && playwright install chromium）"
echo "  - faster-whisper: 用于语音识别备选方案（pip install faster-whisper）"
echo "  - bcut-asr: 用于主要语音识别（需要从 GitHub 手动安装）"
echo ""
echo "现在可以运行: python main.py"

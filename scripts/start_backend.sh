#!/bin/bash

# LoRA Ad Creative Copy Generation System - Startup Script

echo "========================================"
echo "LoRA广告文案生成系统启动脚本"
echo "========================================"

# Check Python version
python_version=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python版本: $python_version"

# Create necessary directories
echo "创建必要目录..."
mkdir -p data/datasets data/splits data/exports logs output models

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    echo "检测到NVIDIA GPU:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "未检测到GPU，将使用CPU模式"
fi

# Install dependencies (if needed)
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
fi

echo "激活虚拟环境..."
source venv/Scripts/activate

echo "安装依赖..."
pip install -r requirements.txt --quiet

# Check hardware mode
echo ""
echo "检测硬件配置..."
python -c "from utils.hardware_detect import detect_hardware, print_hardware_info; print_hardware_info()"

echo ""
echo "========================================"
echo "启动服务..."
echo "========================================"
echo "后端API: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""

# Start backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

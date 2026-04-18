@echo off
REM LoRA Ad Creative Copy Generation System - Windows Startup Script

echo ========================================
echo LoRA广告文案生成系统启动脚本
echo ========================================

REM Create directories
echo 创建必要目录...
if not exist "data\datasets" mkdir data\datasets
if not exist "data\splits" mkdir data\splits
if not exist "data\exports" mkdir data\exports
if not exist "logs" mkdir logs
if not exist "output" mkdir output
if not exist "models" mkdir models

REM Check Python
python --version

REM Install dependencies
echo.
echo 检查依赖...
pip install -r requirements.txt --quiet

REM Hardware info
echo.
echo 检测硬件...
python -c "from utils.hardware_detect import print_hardware_info; print_hardware_info()"

echo.
echo ========================================
echo 启动后端服务...
echo ========================================
echo 后端API: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.

REM Start backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

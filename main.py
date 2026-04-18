"""
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.dataset import router as dataset_router
from api.lora import router as lora_router
from api.generate import router as generate_router
from api.system import router as system_router
from utils.hardware_detect import detect_hardware, get_gpu_info, get_cpu_info


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("=" * 50)
    print("LoRA Ad Creative Copy Generation System")
    print("=" * 50)

    try:
        mode = detect_hardware()
        print(f"Hardware Mode: {mode}")

        if mode in ["GPU", "QLoRA"]:
            gpu_info = get_gpu_info()
            print(f"GPU: {gpu_info['name']}")
            print(f"VRAM: {gpu_info['vram_gb']:.1f}GB")
        else:
            cpu_info = get_cpu_info()
            print(f"CPU: {cpu_info['physical_cores']} cores")
            print(f"RAM: {cpu_info['memory_total_gb']:.1f}GB")

    except Exception as e:
        print(f"Hardware detection: {e}")

    print("=" * 50)
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="LoRA Ad Creative Copy Generation System",
    description="基于LoRA轻量微调技术的广告创意文案生成系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dataset_router)
app.include_router(lora_router)
app.include_router(generate_router)
app.include_router(system_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "LoRA Ad Creative Copy Generation System",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        mode = detect_hardware()
        info = get_gpu_info() if mode in ["GPU", "QLoRA"] else get_cpu_info()

        return {
            "status": "healthy",
            "mode": mode,
            "hardware_info": info
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

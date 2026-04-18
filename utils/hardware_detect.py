"""
Hardware detection utility for auto-selecting GPU/CPU mode
"""

import psutil
import torch
from pathlib import Path
from typing import Literal

HardwareMode = Literal["GPU", "CPU", "QLoRA"]


def detect_hardware() -> HardwareMode:
    """
    Auto-detect hardware and return recommended mode.

    Returns:
        "GPU": CUDA available, use GPU training + inference
        "CPU": No GPU, but enough RAM (>=16GB), use CPU training
        "QLoRA": GPU available but VRAM limited (<8GB), use quantized training
    """
    cuda_available = torch.cuda.is_available()

    if cuda_available:
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if vram_gb >= 8:
            return "GPU"
        else:
            return "QLoRA"
    else:
        ram_gb = psutil.virtual_memory().total / (1024**3)
        if ram_gb >= 16:
            return "CPU"
        else:
            raise Exception(f"Insufficient memory: {ram_gb:.1f}GB (minimum 16GB required)")


def get_device() -> str:
    """Get PyTorch device string"""
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_gpu_info() -> dict:
    """Get GPU info if available"""
    if not torch.cuda.is_available():
        return {"available": False}

    props = torch.cuda.get_device_properties(0)
    return {
        "available": True,
        "name": torch.cuda.get_device_name(0),
        "vram_gb": props.total_memory / (1024**3),
        "vram_allocated_gb": torch.cuda.memory_allocated() / (1024**3),
        "vram_reserved_gb": torch.cuda.memory_reserved() / (1024**3),
        "compute_capability": f"{props.major}.{props.minor}",
    }


def get_cpu_info() -> dict:
    """Get CPU info"""
    return {
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "memory_total_gb": psutil.virtual_memory().total / (1024**3),
        "memory_available_gb": psutil.virtual_memory().available / (1024**3),
    }


def print_hardware_info():
    """Print hardware info to console"""
    mode = detect_hardware()
    print(f"Hardware Mode: {mode}")

    if mode == "GPU" or mode == "QLoRA":
        gpu_info = get_gpu_info()
        print(f"GPU: {gpu_info['name']}")
        print(f"VRAM: {gpu_info['vram_gb']:.1f}GB")
        if mode == "QLoRA":
            print("  -> Using QLoRA (4-bit quantization)")
    else:
        cpu_info = get_cpu_info()
        print(f"CPU: {cpu_info['physical_cores']} cores / {cpu_info['logical_cores']} threads")
        print(f"RAM: {cpu_info['memory_total_gb']:.1f}GB")


if __name__ == "__main__":
    print_hardware_info()

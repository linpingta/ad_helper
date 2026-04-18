# LoRA轻量微调广告创意文案生成系统

基于LoRA（Low-Rank Adaptation）轻量微调技术的广告创意文案生成系统，支持本地部署，保障数据安全。

## 功能特性

- **数据集管理**: 上传、清洗、拆分配对数据集（低CTR→高CTR）
- **LoRA微调**: 支持Qwen/Qwen2.5-0.5B基座模型，QLoRA 4-bit量化
- **文案生成**: 单条/批量生成行业专属高转化广告文案
- **模型管理**: 保存、加载、删除微调模型
- **本地部署**: 纯本地运行，无需云端

## 技术栈

| 组件 | 技术 |
|------|------|
| 基座模型 | Qwen/Qwen2.5-0.5B |
| 微调框架 | PEFT (LoRA/QLoRA) |
| 深度学习 | PyTorch 2.0+ |
| API服务 | FastAPI |
| 前端 | Vue3 + WeUI |
| 数据库 | SQLite |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端

```bash
# Windows
.\scripts\start_backend.ps1

# Linux/Mac
bash scripts/start_backend.sh
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问系统

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 使用流程

### 1. 上传数据集

上传JSON或JSONL格式的配对数据集：

```json
{
  "source_content": "低CTR原文",
  "target_content": "高CTR优化文",
  "industry_tag": "industry_beauty",
  "copy_type": "title"
}
```

### 2. 数据预处理

- **清洗**: 去除重复、违规、低质量数据
- **拆分**: 按比例拆分为训练集和验证集

### 3. 训练模型

配置LoRA参数并开始训练：

- `r`: 低秩维度（默认8）
- `Alpha`: 缩放系数（默认16）
- `学习率`: 2e-4
- `Epochs`: 3

### 4. 生成文案

输入低CTR文案，生成优化后的高CTR文案。

## 硬件要求

| 方案 | 显存要求 | 内存要求 | 适用场景 |
|------|----------|----------|----------|
| GPU | ≥8GB | ≥16GB | 有GPU环境 |
| QLoRA | ≥4GB | ≥12GB | 显存受限 |
| CPU | - | ≥16GB | 无GPU环境 |

## 项目结构

```
ad_helper/
├── api/                  # FastAPI路由
│   ├── dataset.py
│   ├── lora.py
│   ├── generate.py
│   └── system.py
├── dataset/              # 数据集处理
│   └── process.py
├── lora/                 # LoRA微调
│   └── trainer.py
├── generate/             # 文案生成
│   └── infer.py
├── system/               # 系统管理
├── utils/                # 工具函数
│   └── hardware_detect.py
├── frontend/             # Vue3前端
│   └── src/
│       ├── views/
│       └── api/
├── data/                 # 数据存储
├── output/               # 模型输出
├── scripts/              # 启动脚本
├── config.yaml           # 配置文件
└── main.py               # 应用入口
```

## 技术亮点（简历用）

- **LoRA轻量微调**: 仅调整模型0.4%参数，实现轻量化训练
- **QLoRA量化训练**: 4-bit精度量化，降低显存占用至原来的1/4
- **领域自适应**: 基于行业配对数据微调，模型具备行业专家能力
- **低秩矩阵原理**: 通过低秩矩阵分解替代全参数更新
- **本地部署保障数据安全**: 纯本地运行，无云端依赖

## License

MIT

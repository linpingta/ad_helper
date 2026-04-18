<template>
  <div class="page">
    <div class="page-title">模型训练</div>

    <!-- Hardware Info -->
    <div class="card hardware-info">
      <div class="hardware-mode">
        <span class="mode-label">运行模式:</span>
        <span class="mode-value">{{ hardwareMode }}</span>
      </div>
      <div v-if="gpuInfo.available" class="gpu-details">
        <div>GPU: {{ gpuInfo.name }}</div>
        <div>显存: {{ gpuInfo.vram_gb.toFixed(1) }} GB</div>
      </div>
      <div v-else class="cpu-details">
        <div>CPU: {{ cpuInfo.physical_cores }} 核</div>
        <div>内存: {{ cpuInfo.memory_total_gb.toFixed(1) }} GB</div>
      </div>
    </div>

    <!-- Training Config -->
    <div class="card">
      <div class="card-title">训练配置</div>

      <div class="config-form">
        <div class="form-item">
          <label>数据集</label>
          <select v-model="config.datasetId" class="weui-input">
            <option value="">选择数据集</option>
            <option v-for="ds in readyDatasets" :key="ds.id" :value="ds.id">
              {{ ds.name }} ({{ ds.valid_records }}条)
            </option>
          </select>
        </div>

        <div class="form-item">
          <label>模型名称</label>
          <input v-model="config.name" class="weui-input" placeholder="给模型起个名字" />
        </div>

        <div class="form-item">
          <label>行业标签</label>
          <select v-model="config.industryTag" class="weui-input">
            <option value="">通用</option>
            <option value="industry_beauty">美妆</option>
            <option value="industry_fashion">服装</option>
            <option value="industry_game">游戏</option>
          </select>
        </div>

        <div class="form-row">
          <div class="form-item">
            <label>LoRA r</label>
            <input v-model.number="config.loraR" type="number" class="weui-input" />
          </div>
          <div class="form-item">
            <label>Alpha</label>
            <input v-model.number="config.loraAlpha" type="number" class="weui-input" />
          </div>
        </div>

        <div class="form-item">
          <label>学习率: {{ config.learningRate }}</label>
          <input v-model.number="config.learningRate" type="range" min="1e-5" max="1e-3" step="1e-5" class="weui-slider" />
        </div>

        <div class="form-row">
          <div class="form-item">
            <label>Epochs</label>
            <input v-model.number="config.epochs" type="number" class="weui-input" />
          </div>
          <div class="form-item">
            <label>Batch Size</label>
            <input v-model.number="config.batchSize" type="number" class="weui-input" />
          </div>
        </div>
      </div>

      <div class="weui-btn-area">
        <button
          v-if="!isTraining"
          class="weui-btn weui-btn_primary"
          @click="startTraining"
          :disabled="!canStart"
        >开始训练</button>
        <button
          v-else
          class="weui-btn weui-btn_warn"
          @click="stopTraining"
        >停止训练</button>
      </div>
    </div>

    <!-- Training Progress -->
    <div v-if="isTraining" class="card training-progress">
      <div class="card-title">训练进度</div>

      <div class="progress-info">
        <div class="progress-step">Step {{ status.currentStep }} / {{ status.totalSteps }}</div>
        <div class="progress-percent">{{ status.progress.toFixed(1) }}%</div>
      </div>

      <div class="weui-progress">
        <div class="weui-progress__bar">
          <div class="weui-progress__inner-bar" :style="{ width: status.progress + '%' }"></div>
        </div>
      </div>

      <div class="loss-info">
        <div v-if="status.trainLoss !== null">
          <span>训练损失:</span>
          <span class="loss-value">{{ status.trainLoss.toFixed(4) }}</span>
        </div>
        <div v-if="status.evalLoss !== null">
          <span>验证损失:</span>
          <span class="loss-value">{{ status.evalLoss.toFixed(4) }}</span>
        </div>
      </div>

      <div class="time-info">
        <div>已用时间: {{ formatTime(status.elapsedTime) }}</div>
        <div v-if="status.eta">预计剩余: {{ formatTime(status.eta) }}</div>
      </div>
    </div>

    <!-- Trained Models -->
    <div class="card">
      <div class="card-title">已训练的模型</div>
      <div v-if="models.length === 0" class="empty-tip">暂无训练好的模型</div>
      <div v-for="model in models" :key="model.id" class="model-item">
        <div class="model-header">
          <span class="model-name">{{ model.name }}</span>
          <span class="model-status" :class="'status-' + model.status">{{ model.status }}</span>
        </div>
        <div class="model-info">
          <span>基座: {{ model.base_model }}</span>
          <span>r={{ model.lora_r }}</span>
        </div>
        <div v-if="model.train_loss" class="model-loss">
          最终损失: {{ model.train_loss.toFixed(4) }}
        </div>
        <div class="model-meta">
          <span>{{ model.train_samples }} 训练样本</span>
          <span v-if="model.training_time">{{ formatTime(model.training_time) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { loraAPI, datasetAPI, systemAPI } from '../api'

export default {
  name: 'Train',
  setup() {
    const hardwareMode = ref('检测中...')
    const gpuInfo = ref({ available: false })
    const cpuInfo = ref({})
    const datasets = ref([])
    const models = ref([])
    const isTraining = ref(false)
    const status = ref({
      status: 'idle',
      progress: 0,
      currentStep: 0,
      totalSteps: 0,
      trainLoss: null,
      evalLoss: null,
      elapsedTime: 0,
      eta: null
    })

    const config = ref({
      datasetId: '',
      name: '',
      industryTag: '',
      loraR: 8,
      loraAlpha: 16,
      learningRate: 0.0002,
      epochs: 3,
      batchSize: 2
    })

    let pollInterval = null

    const readyDatasets = computed(() =>
      datasets.value.filter(ds => ds.status === 'split')
    )

    const canStart = computed(() =>
      config.value.datasetId && config.value.name
    )

    const loadHardwareInfo = async () => {
      try {
        const res = await systemAPI.hardware()
        hardwareMode.value = res.mode
        if (res.info.name) {
          gpuInfo.value = res.info
        } else {
          cpuInfo.value = res.info
        }
      } catch (e) {
        hardwareMode.value = '检测失败'
      }
    }

    const loadDatasets = async () => {
      try {
        datasets.value = await datasetAPI.list()
      } catch (e) {
        console.error('Failed to load datasets:', e)
      }
    }

    const loadModels = async () => {
      try {
        models.value = await loraAPI.list()
      } catch (e) {
        console.error('Failed to load models:', e)
      }
    }

    const pollStatus = async () => {
      try {
        status.value = await loraAPI.status()
        isTraining.value = status.value.status === 'running'
      } catch (e) {
        console.error('Failed to poll status:', e)
      }
    }

    const startTraining = async () => {
      try {
        await loraAPI.train({
          dataset_id: config.value.datasetId,
          name: config.value.name,
          industry_tag: config.value.industryTag,
          lora_r: config.value.loraR,
          lora_alpha: config.value.loraAlpha,
          lora_dropout: 0.1,
          num_train_epochs: config.value.epochs,
          per_device_batch_size: config.value.batchSize,
          learning_rate: config.value.learningRate
        })
        isTraining.value = true
        pollInterval = setInterval(pollStatus, 1000)
      } catch (e) {
        alert('启动训练失败: ' + (e.message || '未知错误'))
      }
    }

    const stopTraining = async () => {
      try {
        await loraAPI.stop()
        isTraining.value = false
        if (pollInterval) clearInterval(pollInterval)
      } catch (e) {
        console.error('Failed to stop training:', e)
      }
    }

    const formatTime = (seconds) => {
      if (!seconds) return '-'
      const h = Math.floor(seconds / 3600)
      const m = Math.floor((seconds % 3600) / 60)
      const s = Math.floor(seconds % 60)
      return h > 0 ? `${h}h ${m}m` : `${m}m ${s}s`
    }

    onMounted(() => {
      loadHardwareInfo()
      loadDatasets()
      loadModels()
      pollInterval = setInterval(pollStatus, 2000)
    })

    onUnmounted(() => {
      if (pollInterval) clearInterval(pollInterval)
    })

    return {
      hardwareMode,
      gpuInfo,
      cpuInfo,
      datasets,
      models,
      isTraining,
      status,
      config,
      readyDatasets,
      canStart,
      startTraining,
      stopTraining,
      formatTime
    }
  }
}
</script>

<style scoped>
.hardware-info {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.hardware-mode {
  display: flex;
  gap: 10px;
  font-size: 16px;
  margin-bottom: 8px;
}

.mode-label {
  color: #666;
}

.mode-value {
  font-weight: 600;
  color: #1890ff;
}

.gpu-details, .cpu-details {
  font-size: 13px;
  color: #666;
}

.config-form {
  margin-bottom: 15px;
}

.form-item {
  margin-bottom: 12px;
}

.form-item label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.form-item input, .form-item select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.form-row {
  display: flex;
  gap: 15px;
}

.form-row .form-item {
  flex: 1;
}

.training-progress {
  border-left: 3px solid #52c41a;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.progress-step {
  color: #666;
  font-size: 14px;
}

.progress-percent {
  font-size: 20px;
  font-weight: 600;
  color: #52c41a;
}

.weui-progress {
  margin-bottom: 15px;
}

.loss-info, .time-info {
  font-size: 13px;
  color: #666;
  margin-top: 10px;
}

.loss-value {
  color: #1890ff;
  font-weight: 600;
  margin-left: 5px;
}

.model-item {
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.model-item:last-child {
  border-bottom: none;
}

.model-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.model-name {
  font-weight: 600;
  color: #333;
}

.model-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #f0f0f0;
  color: #666;
}

.model-status.status-completed {
  background: #f6ffed;
  color: #52c41a;
}

.model-status.status-training {
  background: #e6f7ff;
  color: #1890ff;
}

.model-status.status-error {
  background: #fff2f0;
  color: #fa5151;
}

.model-info {
  font-size: 13px;
  color: #999;
  margin-bottom: 5px;
}

.model-info span {
  margin-right: 15px;
}

.model-loss {
  font-size: 13px;
  color: #1890ff;
}

.model-meta {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.model-meta span {
  margin-right: 15px;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 30px 0;
}
</style>

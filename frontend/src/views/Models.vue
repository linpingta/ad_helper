<template>
  <div class="page">
    <div class="page-title">模型管理</div>

    <!-- Loading -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- Model List -->
    <div v-if="!loading" class="card">
      <div class="card-title">我的模型</div>
      <div v-if="models.length === 0" class="empty-tip">暂无模型</div>
      <div v-for="model in models" :key="model.id" class="model-item">
        <div class="model-header">
          <span class="model-name">{{ model.name }}</span>
          <span class="model-status" :class="'status-' + model.status">{{ model.status }}</span>
        </div>

        <div class="model-details">
          <div class="detail-row">
            <span class="detail-label">基座模型:</span>
            <span class="detail-value">{{ model.base_model }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">LoRA r:</span>
            <span class="detail-value">{{ model.lora_r }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">行业:</span>
            <span class="detail-value">{{ model.industry_tag || '通用' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">训练样本:</span>
            <span class="detail-value">{{ model.train_samples }} / {{ model.eval_samples }}</span>
          </div>
          <div v-if="model.train_loss" class="detail-row">
            <span class="detail-label">最终损失:</span>
            <span class="detail-value loss">{{ model.train_loss.toFixed(4) }}</span>
          </div>
          <div v-if="model.training_time" class="detail-row">
            <span class="detail-label">训练时间:</span>
            <span class="detail-value">{{ formatTime(model.training_time) }}</span>
          </div>
        </div>

        <div class="model-path">
          <span class="path-label">路径:</span>
          <code class="path-value">{{ model.lora_path }}</code>
        </div>

        <div class="model-actions">
          <button
            class="weui-btn weui-btn_mini weui-btn_primary"
            @click="useModel(model.id)"
          >使用</button>
          <button
            class="weui-btn weui-btn_mini weui-btn_warn"
            @click="deleteModel(model.id)"
          >删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { loraAPI } from '../api'

export default {
  name: 'Models',
  setup() {
    const router = useRouter()
    const models = ref([])
    const loading = ref(false)

    const loadModels = async () => {
      loading.value = true
      try {
        models.value = await loraAPI.list()
      } catch (e) {
        console.error('Failed to load models:', e)
      } finally {
        loading.value = false
      }
    }

    const useModel = (id) => {
      router.push({ path: '/generate', query: { modelId: id } })
    }

    const deleteModel = async (id) => {
      if (!confirm('确定要删除这个模型吗？')) return

      try {
        await loraAPI.delete(id)
        await loadModels()
      } catch (e) {
        alert('删除失败: ' + (e.message || '未知错误'))
      }
    }

    const formatTime = (seconds) => {
      if (!seconds) return '-'
      const h = Math.floor(seconds / 3600)
      const m = Math.floor((seconds % 3600) / 60)
      const s = Math.floor(seconds % 60)
      return h > 0 ? `${h}h ${m}m ${s}s` : `${m}m ${s}s`
    }

    onMounted(() => {
      loadModels()
    })

    return {
      models,
      loading,
      useModel,
      deleteModel,
      formatTime
    }
  }
}
</script>

<style scoped>
.model-item {
  padding: 15px 0;
  border-bottom: 1px solid #eee;
}

.model-item:last-child {
  border-bottom: none;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.model-name {
  font-size: 16px;
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

.model-details {
  background: #f8f8f8;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 3px 0;
}

.detail-label {
  color: #666;
}

.detail-value {
  color: #333;
}

.detail-value.loss {
  color: #1890ff;
  font-weight: 600;
}

.model-path {
  margin-bottom: 10px;
  font-size: 12px;
}

.path-label {
  color: #666;
}

.path-value {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  color: #666;
  word-break: break-all;
}

.model-actions {
  display: flex;
  gap: 10px;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 30px 0;
}

.loading {
  text-align: center;
  padding: 50px;
  color: #999;
}
</style>

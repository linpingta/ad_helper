<template>
  <div class="page">
    <div class="page-title">文案生成</div>

    <!-- Error Message -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- Generation Form -->
    <div class="card">
      <div class="card-title">生成配置</div>

      <div class="form-item">
        <label>选择模型</label>
        <select v-model="selectedModelId" class="weui-input">
          <option value="">选择模型</option>
          <option v-for="m in models" :key="m.id" :value="m.id">
            {{ m.name }} ({{ m.industry_tag || '通用' }})
          </option>
        </select>
      </div>

      <div class="form-item">
        <label>行业标签</label>
        <select v-model="form.industryTag" class="weui-input">
          <option value="">不指定</option>
          <option value="industry_beauty">美妆</option>
          <option value="industry_fashion">服装</option>
          <option value="industry_game">游戏</option>
        </select>
      </div>

      <div class="form-item">
        <label>文案类型</label>
        <select v-model="form.copyType" class="weui-input">
          <option value="">不指定</option>
          <option value="title">标题</option>
          <option value="detail">详情页</option>
          <option value="banner">Banner</option>
          <option value="short_video">短视频</option>
        </select>
      </div>

      <div class="form-item">
        <label>低CTR文案</label>
        <textarea
          v-model="form.sourceContent"
          class="weui-textarea"
          rows="4"
          placeholder="输入要优化的低CTR广告文案..."
        ></textarea>
      </div>

      <div class="weui-btn-area">
        <button
          class="weui-btn weui-btn_primary"
          @click="generateSingle"
          :disabled="!canGenerate || loading"
        >生成文案</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">生成中...</div>

    <!-- Generated Result -->
    <div v-if="result && !loading" class="card result-card">
      <div class="card-title">生成结果</div>

      <div class="result-section">
        <div class="result-label">原文:</div>
        <div class="result-content original">{{ result.source_content }}</div>
      </div>

      <div class="result-section">
        <div class="result-label">生成文案:</div>
        <div class="result-content generated">{{ result.generated_content }}</div>
      </div>

      <div class="result-actions">
        <button class="weui-btn weui-btn_mini weui-btn_default" @click="copyResult">复制</button>
        <button class="weui-btn weui-btn_mini weui-btn_default" @click="regenerate">重新生成</button>
      </div>
    </div>

    <!-- Batch Generation -->
    <div class="card">
      <div class="card-title">批量生成</div>
      <p class="tip">可粘贴多行文案，每行一条</p>

      <div class="form-item">
        <textarea
          v-model="batchInput"
          class="weui-textarea"
          rows="6"
          placeholder="输入多条文案，每行一条..."
        ></textarea>
      </div>

      <div class="weui-btn-area">
        <button
          class="weui-btn weui-btn_default"
          @click="generateBatch"
          :disabled="!batchInput.trim() || loading"
        >批量生成</button>
      </div>
    </div>

    <!-- Batch Results -->
    <div v-if="batchResults.length > 0" class="card">
      <div class="card-title">批量结果 ({{ batchResults.length }}条)</div>
      <div v-for="(r, idx) in batchResults" :key="idx" class="batch-item">
        <div class="batch-original">{{ r.source_content }}</div>
        <div class="batch-generated">{{ r.generated_content }}</div>
      </div>
    </div>

    <!-- Stats -->
    <div class="card stats-card">
      <div class="card-title">生成统计</div>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ stats.total_generations }}</div>
          <div class="stat-label">总生成数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.edited_count }}</div>
          <div class="stat-label">已编辑</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ (stats.avg_bleu * 100).toFixed(1) }}%</div>
          <div class="stat-label">平均BLEU</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ (stats.avg_rouge_l * 100).toFixed(1) }}%</div>
          <div class="stat-label">平均ROUGE-L</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { loraAPI, generateAPI } from '../api'

export default {
  name: 'Generate',
  setup() {
    const models = ref([])
    const selectedModelId = ref('')
    const loading = ref(false)
    const error = ref('')
    const result = ref(null)
    const batchInput = ref('')
    const batchResults = ref([])
    const stats = ref({
      total_generations: 0,
      edited_count: 0,
      avg_bleu: 0,
      avg_rouge_l: 0
    })

    const form = ref({
      industryTag: '',
      copyType: '',
      sourceContent: ''
    })

    const canGenerate = computed(() =>
      selectedModelId.value && form.value.sourceContent.trim()
    )

    const loadModels = async () => {
      try {
        models.value = await loraAPI.list()
        // Auto-select first completed model
        const completed = models.value.find(m => m.status === 'completed')
        if (completed) {
          selectedModelId.value = completed.id
        }
      } catch (e) {
        console.error('Failed to load models:', e)
      }
    }

    const loadStats = async () => {
      try {
        stats.value = await generateAPI.stats()
      } catch (e) {
        console.error('Failed to load stats:', e)
      }
    }

    const generateSingle = async () => {
      if (!canGenerate.value) return

      loading.value = true
      error.value = ''
      try {
        result.value = await generateAPI.single({
          model_id: selectedModelId.value,
          source_content: form.value.sourceContent,
          industry_tag: form.value.industryTag || undefined,
          copy_type: form.value.copyType || undefined
        })
        await loadStats()
      } catch (e) {
        error.value = e.message || '生成失败'
      } finally {
        loading.value = false
      }
    }

    const regenerate = () => {
      generateSingle()
    }

    const copyResult = () => {
      if (result.value) {
        navigator.clipboard.writeText(result.value.generated_content)
      }
    }

    const generateBatch = async () => {
      if (!batchInput.value.trim() || !selectedModelId.value) return

      loading.value = true
      error.value = ''
      try {
        const lines = batchInput.value.trim().split('\n').filter(l => l.trim())
        const records = lines.map(content => ({
          source_content: content,
          industry_tag: form.value.industryTag || undefined,
          copy_type: form.value.copyType || undefined
        }))

        const res = await generateAPI.batch({
          model_id: selectedModelId.value,
          records
        })

        batchResults.value = res.results
        await loadStats()
      } catch (e) {
        error.value = e.message || '批量生成失败'
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadModels()
      loadStats()
    })

    return {
      models,
      selectedModelId,
      loading,
      error,
      result,
      batchInput,
      batchResults,
      stats,
      form,
      canGenerate,
      generateSingle,
      regenerate,
      copyResult,
      generateBatch
    }
  }
}
</script>

<style scoped>
.form-item {
  margin-bottom: 15px;
}

.form-item label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.form-item input, .form-item select, .form-item textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.result-card {
  border-left: 3px solid #52c41a;
}

.result-section {
  margin-bottom: 15px;
}

.result-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 5px;
}

.result-content {
  padding: 10px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
}

.original {
  background: #f5f5f5;
  color: #999;
}

.generated {
  background: #f6ffed;
  border: 1px solid #d9f7be;
  color: #333;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.tip {
  font-size: 13px;
  color: #999;
  margin-bottom: 10px;
}

.batch-item {
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.batch-item:last-child {
  border-bottom: none;
}

.batch-original {
  font-size: 13px;
  color: #999;
  margin-bottom: 5px;
}

.batch-generated {
  font-size: 14px;
  color: #333;
  background: #f6ffed;
  padding: 8px;
  border-radius: 4px;
}

.stats-card {
  background: #fff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.stat-item {
  text-align: center;
  padding: 10px;
  background: #f8f8f8;
  border-radius: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.loading {
  text-align: center;
  padding: 30px;
  color: #999;
}

.error {
  background: #fff2f0;
  border-left: 3px solid #fa5151;
  padding: 10px 15px;
  margin-bottom: 15px;
  color: #fa5151;
}
</style>

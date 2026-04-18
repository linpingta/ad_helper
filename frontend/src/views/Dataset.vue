<template>
  <div class="page">
    <div class="page-title">数据集管理</div>

    <!-- Upload Section -->
    <div class="card">
      <div class="card-title">上传数据集</div>
      <div class="weui-cells">
        <div class="weui-cell">
          <div class="weui-cell__bd">
            <input
              type="file"
              accept=".json,.jsonl"
              @change="handleFileSelect"
              class="weui-input"
            />
          </div>
        </div>
        <div class="weui-cell">
          <div class="weui-cell__bd">
            <input
              v-model="datasetName"
              class="weui-input"
              placeholder="数据集名称"
            />
          </div>
        </div>
      </div>
      <div class="weui-btn-area">
        <button class="weui-btn weui-btn-primary" @click="uploadDataset" :disabled="!selectedFile || !datasetName">
          上传
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- Error Message -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- Dataset List -->
    <div v-if="!loading" class="card">
      <div class="card-title">已上传的数据集</div>
      <div v-if="datasets.length === 0" class="empty-tip">暂无数据集</div>
      <div v-for="ds in datasets" :key="ds.id" class="dataset-item">
        <div class="dataset-header">
          <span class="dataset-name">{{ ds.name }}</span>
          <span class="dataset-status" :class="'status-' + ds.status">{{ ds.status }}</span>
        </div>
        <div class="dataset-info">
          <span>格式: {{ ds.format }}</span>
          <span>有效: {{ ds.valid_records }}/{{ ds.total_records }}</span>
        </div>
        <div class="dataset-tags">
          <span v-for="tag in ds.industry_tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
        <div class="dataset-actions">
          <button
            v-if="ds.status === 'uploaded'"
            class="weui-btn weui-btn_mini weui-btn_default"
            @click="cleanDataset(ds.id)"
          >清洗</button>
          <button
            v-if="ds.status === 'cleaned'"
            class="weui-btn weui-btn_mini weui-btn_default"
            @click="splitDataset(ds.id)"
          >拆分</button>
          <button
            class="weui-btn weui-btn_mini weui-btn_warn"
            @click="deleteDataset(ds.id)"
          >删除</button>
        </div>
      </div>
    </div>

    <!-- Split Dialog -->
    <div v-if="showSplitDialog" class="dialog-overlay">
      <div class="dialog">
        <div class="dialog-hd">
          <strong class="dialog-title">设置拆分比例</strong>
        </div>
        <div class="dialog-bd">
          <div class="weui-cells">
            <div class="weui-cell">
              <div class="weui-cell__bd">
                <input
                  v-model.number="splitRatio"
                  type="number"
                  min="0.5"
                  max="0.9"
                  step="0.1"
                  class="weui-input"
                />
              </div>
              <div class="weui-cell__ft">训练集比例</div>
            </div>
          </div>
        </div>
        <div class="dialog-ft">
          <button class="weui-btn weui-btn_default" @click="showSplitDialog = false">取消</button>
          <button class="weui-btn weui-btn_primary" @click="confirmSplit">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { datasetAPI } from '../api'

export default {
  name: 'Dataset',
  setup() {
    const datasets = ref([])
    const loading = ref(false)
    const error = ref('')
    const selectedFile = ref(null)
    const datasetName = ref('')
    const showSplitDialog = ref(false)
    const splitRatio = ref(0.8)
    const currentDatasetId = ref(null)

    const loadDatasets = async () => {
      loading.value = true
      error.value = ''
      try {
        datasets.value = await datasetAPI.list()
      } catch (e) {
        error.value = e.message || '加载数据集失败'
      } finally {
        loading.value = false
      }
    }

    const handleFileSelect = (e) => {
      selectedFile.value = e.target.files[0]
    }

    const uploadDataset = async () => {
      if (!selectedFile.value || !datasetName.value) return

      const formData = new FormData()
      formData.append('file', selectedFile.value)
      formData.append('name', datasetName.value)

      loading.value = true
      error.value = ''
      try {
        await datasetAPI.upload(formData)
        await loadDatasets()
        datasetName.value = ''
        selectedFile.value = null
      } catch (e) {
        error.value = e.message || '上传失败'
      } finally {
        loading.value = false
      }
    }

    const cleanDataset = async (id) => {
      try {
        await datasetAPI.clean(id)
        await loadDatasets()
      } catch (e) {
        error.value = e.message || '清洗失败'
      }
    }

    const splitDataset = (id) => {
      currentDatasetId.value = id
      showSplitDialog.value = true
    }

    const confirmSplit = async () => {
      try {
        await datasetAPI.split(currentDatasetId.value, splitRatio.value)
        showSplitDialog.value = false
        await loadDatasets()
      } catch (e) {
        error.value = e.message || '拆分失败'
      }
    }

    const deleteDataset = async (id) => {
      if (!confirm('确定要删除这个数据集吗？')) return
      try {
        await datasetAPI.delete(id)
        await loadDatasets()
      } catch (e) {
        error.value = e.message || '删除失败'
      }
    }

    onMounted(() => {
      loadDatasets()
    })

    return {
      datasets,
      loading,
      error,
      selectedFile,
      datasetName,
      showSplitDialog,
      splitRatio,
      handleFileSelect,
      uploadDataset,
      cleanDataset,
      splitDataset,
      confirmSplit,
      deleteDataset
    }
  }
}
</script>

<style scoped>
.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #333;
}

.dataset-item {
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.dataset-item:last-child {
  border-bottom: none;
}

.dataset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.dataset-name {
  font-weight: 600;
  color: #333;
}

.dataset-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #e6e6e6;
  color: #666;
}

.dataset-status.status-cleaned {
  background: #e6f7ff;
  color: #1890ff;
}

.dataset-status.status-split {
  background: #f6ffed;
  color: #52c41a;
}

.dataset-info {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}

.dataset-info span {
  margin-right: 15px;
}

.dataset-tags {
  margin-bottom: 8px;
}

.tag {
  display: inline-block;
  font-size: 11px;
  padding: 2px 6px;
  background: #f0f0f0;
  color: #666;
  border-radius: 3px;
  margin-right: 5px;
}

.dataset-actions {
  display: flex;
  gap: 8px;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: #fff;
  border-radius: 8px;
  width: 80%;
  max-width: 300px;
}

.dialog-hd {
  padding: 15px;
  text-align: center;
  border-bottom: 1px solid #eee;
}

.dialog-bd {
  padding: 20px 15px;
}

.dialog-ft {
  padding: 10px 15px;
  display: flex;
  justify-content: space-around;
  border-top: 1px solid #eee;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 30px 0;
}
</style>

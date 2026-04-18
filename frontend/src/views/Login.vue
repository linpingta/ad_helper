<template>
  <div class="login-page">
    <div class="login-header">
      <h1>LoRA广告文案系统</h1>
      <p>基于LoRA轻量微调技术的广告创意文案生成</p>
    </div>

    <div class="login-form">
      <div class="weui-cells">
        <div class="weui-cell">
          <div class="weui-cell__hd">
            <label class="weui-label">用户名</label>
          </div>
          <div class="weui-cell__bd">
            <input
              v-model="username"
              class="weui-input"
              type="text"
              placeholder="请输入用户名"
            />
          </div>
        </div>
        <div class="weui-cell">
          <div class="weui-cell__hd">
            <label class="weui-label">密码</label>
          </div>
          <div class="weui-cell__bd">
            <input
              v-model="password"
              class="weui-input"
              type="password"
              placeholder="请输入密码"
            />
          </div>
        </div>
      </div>

      <div class="weui-btn-area">
        <button class="weui-btn weui-btn_primary" @click="login" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div class="login-footer">
      <p>默认账号: admin / admin123</p>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { systemAPI } from '../api'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const username = ref('')
    const password = ref('')
    const loading = ref(false)
    const error = ref('')

    const login = async () => {
      if (!username.value || !password.value) {
        error.value = '请输入用户名和密码'
        return
      }

      loading.value = true
      error.value = ''

      try {
        const res = await systemAPI.login({
          username: username.value,
          password: password.value
        })

        localStorage.setItem('token', res.token)
        localStorage.setItem('username', res.username)
        router.push('/dataset')
      } catch (e) {
        error.value = e.message || '登录失败'
      } finally {
        loading.value = false
      }
    }

    return {
      username,
      password,
      loading,
      error,
      login
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-header {
  text-align: center;
  color: #fff;
  margin-bottom: 40px;
}

.login-header h1 {
  font-size: 24px;
  margin-bottom: 10px;
}

.login-header p {
  font-size: 14px;
  opacity: 0.8;
}

.login-form {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  color: #fff;
  font-size: 13px;
  opacity: 0.8;
}

.error {
  background: #fff2f0;
  border-left: 3px solid #fa5151;
  padding: 10px 15px;
  margin-top: 15px;
  color: #fa5151;
  font-size: 14px;
}
</style>

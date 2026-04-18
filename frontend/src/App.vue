<template>
  <div class="app">
    <!-- Header -->
    <div class="weui-header">
      <div class="weui-header-left" @click="goBack" v-if="showBack">
        <i class="weui-icon-back"></i>
      </div>
      <h1 class="weui-header-title">{{ title }}</h1>
      <div class="weui-header-right">
        <slot name="header-right"></slot>
      </div>
    </div>

    <!-- Content -->
    <div class="weui-content">
      <router-view />
    </div>

    <!-- TabBar -->
    <div class="weui-tabbar" v-if="showTabBar">
      <router-link to="/dataset" class="weui-tabbar__item" :class="{ 'weui-bar__item_on': $route.path === '/dataset' }">
        <span class="weui-tabbar__icon">
          <i class="weui-icon-form"></i>
        </span>
        <p class="weui-tabbar__label">数据集</p>
      </router-link>
      <router-link to="/train" class="weui-tabbar__item" :class="{ 'weui-bar__item_on': $route.path === '/train' }">
        <span class="weui-tabbar__icon">
          <i class="weui-icon-download"></i>
        </span>
        <p class="weui-tabbar__label">训练</p>
      </router-link>
      <router-link to="/generate" class="weui-tabbar__item" :class="{ 'weui-bar__item_on': $route.path === '/generate' }">
        <span class="weui-tabbar__icon">
          <i class="weui-icon-speaker"></i>
        </span>
        <p class="weui-tabbar__label">生成</p>
      </router-link>
      <router-link to="/models" class="weui-tabbar__item" :class="{ 'weui-bar__item_on': $route.path === '/models' }">
        <span class="weui-tabbar__icon">
          <i class="weui-icon-settings"></i>
        </span>
        <p class="weui-tabbar__label">模型</p>
      </router-link>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export default {
  name: 'App',
  setup() {
    const route = useRoute()
    const router = useRouter()

    const title = computed(() => {
      const titles = {
        '/dataset': '数据集管理',
        '/train': '模型训练',
        '/generate': '文案生成',
        '/models': '模型管理'
      }
      return titles[route.path] || 'LoRA广告文案系统'
    })

    const showBack = computed(() => route.path !== '/' && !['/dataset', '/train', '/generate', '/models'].includes(route.path))
    const showTabBar = computed(() => ['/dataset', '/train', '/generate', '/models'].includes(route.path))

    const goBack = () => router.back()

    return { title, showBack, showTabBar, goBack }
  }
}
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f8f8f8;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.weui-content {
  flex: 1;
  padding-bottom: 60px;
}

.page {
  padding: 15px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #333;
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.loading {
  text-align: center;
  padding: 50px;
  color: #999;
}

.error {
  background: #fff2f0;
  border-left: 3px solid #fa5151;
  padding: 10px 15px;
  margin-bottom: 15px;
  color: #fa5151;
}

.success {
  background: #f6ffed;
  border-left: 3px solid #52c41a;
  padding: 10px 15px;
  margin-bottom: 15px;
  color: #52c41a;
}
</style>

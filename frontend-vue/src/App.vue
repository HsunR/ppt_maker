<template>
  <div id="app-root">
    <transition name="toast">
      <div v-if="store.toast.show" :class="['toast', store.toast.type]">{{ store.toast.msg }}</div>
    </transition>

    <header>
      <div class="header-inner">
        <div class="logo" @click="$router.push('/')">
          <span class="logo-icon">&#9670;</span>
          <span class="logo-text">PPT Master</span>
        </div>
        <div class="header-project" v-if="store.currentProject">{{ store.currentProject.name }}</div>
        <button v-if="$route.path !== '/'" class="btn btn-sm" @click="goHome">&larr; 首页</button>
      </div>
    </header>

    <div class="steps-bar" v-if="$route.path !== '/'">
      <div v-for="(s, i) in stepLabels" :key="i"
           :class="['step', { cur: stepIdx === i + 1, done: stepIdx > i + 1, disabled: stepIdx === 5 }]"
           @click="canClickStep(i) ? goToStep(i) : null">
        <div class="step-num" v-html="stepIdx > i + 1 ? '&#10003;' : (i + 1)"></div>
        <div class="step-label">{{ s }}</div>
      </div>
    </div>

    <main><router-view /></main>
    <footer>PPT Master Service</footer>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { store } from './api'

const stepLabels = ['内容输入', 'AI大纲', '视觉风格', '确认生成', '生成进度']
const routeStepMap = { input: 1, outline: 2, style: 3, confirm: 4, progress: 5 }

export default {
  setup() {
    const router = useRouter()
    const route = useRoute()
    const stepIdx = computed(() => routeStepMap[route.name] || 0)

    function goHome() { router.push('/') }
    function goToStep(i) {
      const pages = ['/input', '/outline', '/style', '/confirm', '/progress']
      if (i >= 0 && i < pages.length) router.push(pages[i])
    }
    function canClickStep(i) {
      const pageStep = stepIdx.value
      // Can click completed steps (stepIdx > current), but NOT during progress (stepIdx === 5)
      return pageStep > i + 1 && pageStep < 5
    }

    return { store, stepLabels, stepIdx, goHome, goToStep, canClickStep }
  }
}
</script>
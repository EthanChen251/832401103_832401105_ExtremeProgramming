<script setup>
import { language, t, toggleLanguage } from './language.js'
import { onMounted, onUnmounted, ref } from 'vue'
import Directory from './App.vue'

const themeKey = 'directory-theme'
const theme = ref(localStorage.getItem(themeKey) || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))
document.documentElement.dataset.theme = theme.value
function switchTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.dataset.theme = theme.value
  localStorage.setItem(themeKey, theme.value)
}

const user = ref(null)
const checking = ref(true)
const busy = ref(false)
const registering = ref(false)
const name = ref('')
const password = ref('')
const confirmation = ref('')
const message = ref('')
const channel = 'BroadcastChannel' in window ? new BroadcastChannel('contact-account') : null
let version = 0

async function request(action, data) {
  const options = data === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  }
  const response = await fetch('/api/v1/auth/' + action, options)
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error('无法连接账号服务，请检查后端是否已启动。')
  }
  const result = await response.json()
  if (!response.ok) throw new Error(result?.error?.message || result?.message || '请求失败，请重试。')
  return result.user
}

function toggleMode() {
  registering.value = !registering.value
  password.value = confirmation.value = message.value = ''
}

async function restore() {
  const current = ++version
  checking.value = true
  try {
    const account = await request('session')
    if (version === current) user.value = account
  } catch {
    if (version === current) {
      user.value = null
      message.value = '无法连接账号服务，请检查后端是否已启动。'
    }
  } finally {
    if (version === current) checking.value = false
  }
}

async function submit(action) {
  if (busy.value) return
  if (action === 'register' && password.value !== confirmation.value) {
    message.value = '两次输入的密码不一致。'
    return
  }
  busy.value = true
  message.value = ''
  try {
    user.value = await request(action, action === 'logout' ? {} : { name: name.value, password: password.value })
    registering.value = false
    password.value = confirmation.value = ''
    channel?.postMessage('changed')
  } catch (error) {
    message.value = error instanceof TypeError ? '网络连接失败，请重试。' : error.message
  } finally {
    busy.value = false
  }
}

onMounted(() => {
  if (channel) channel.onmessage = restore
  restore()
})
onUnmounted(() => channel?.close())
</script>

<template>
  <header class="masthead">
    <span class="brand"><span class="book-mark" aria-hidden="true"></span>{{ t('通讯录') }}</span>
    <span v-if="user" class="account-name">{{ user.name }}</span>
    <button v-if="user" class="text-button" :disabled="busy" @click="submit('logout')">{{ t('退出登录') }}</button>
    <button type="button" class="language-toggle" :lang="language === 'en' ? 'zh-CN' : 'en'" @click="toggleLanguage">{{ language === 'en' ? '中文' : 'English' }}</button>
    <button type="button" class="theme-toggle" :aria-label="t(theme === 'dark' ? '切换至浅色模式' : '切换至深色模式')"
      :title="t(theme === 'dark' ? '切换至浅色模式' : '切换至深色模式')" @click="switchTheme"><span aria-hidden="true">◐</span></button>
  </header>
  <main v-if="checking" class="directory"><p class="status" role="status">{{ t('正在读取账号…') }}</p></main>
  <template v-else-if="user">
    <Directory :key="user.id" @expired="restore" />
    <p v-if="message" class="auth-error" role="alert">{{ t(message) }}</p>
  </template>
  <main v-else class="directory">
    <div class="auth-layout">
      <div class="auth-intro">
        <div class="card-art" aria-hidden="true">
          <i class="back-card"></i><i class="front-card"><b></b></i>
        </div>
        <h1 lang="en">Address <em>Book.</em></h1>
        <p>{{ t('你的个人通讯录') }}</p>
      </div>
      <form class="auth-form" @submit.prevent="submit(registering ? 'register' : 'login')">
        <h2>{{ t(registering ? '注册账号' : '登录') }}</h2>
        <label>{{ t('用户名') }}<input v-model.trim="name" name="username" autocomplete="username" maxlength="40" required></label>
        <label>{{ t('密码') }}<input v-model="password" name="password" type="password" :autocomplete="registering ? 'new-password' : 'current-password'" minlength="8" maxlength="128" required></label>
        <template v-if="registering">
          <p class="hint">{{ t('密码长度为 8–128 个字符。') }}</p>
          <label>{{ t('确认密码') }}<input v-model="confirmation" name="confirmation" type="password" autocomplete="new-password" required></label>
        </template>
        <p v-if="message" class="auth-error" role="alert">{{ t(message) }}</p>
        <button class="retry" :disabled="busy">{{ t(busy ? '正在处理…' : registering ? '注册并登录' : '登录') }}</button>
        <button type="button" class="text-button" :disabled="busy" @click="toggleMode">{{ t(registering ? '已有账号，去登录' : '创建新账号') }}</button>
      </form>
    </div>
  </main>
</template>

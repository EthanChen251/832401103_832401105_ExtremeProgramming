<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import Directory from './App.vue'

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
  if (!response.ok) throw new Error(result.message || '请求失败，请重试。')
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
  <main v-if="checking" class="directory"><p class="status" role="status">正在读取账号…</p></main>
  <template v-else-if="user">
    <Directory :key="user.id" :username="user.name" :busy="busy" @logout="submit('logout')" @expired="restore" />
    <p v-if="message" class="auth-error" role="alert">{{ message }}</p>
  </template>
  <main v-else class="directory">
    <header><span class="book-mark" aria-hidden="true"></span><h1>通讯录</h1></header>
    <div class="auth-layout">
      <div class="auth-intro"><div class="folio" aria-hidden="true"><i></i></div><h2>个人通讯录</h2>
        <p>登录后查看你的联系人与收藏。</p>
      </div>
      <form class="auth-form" @submit.prevent="submit(registering ? 'register' : 'login')">
        <h2>{{ registering ? '注册账号' : '登录' }}</h2>
        <label>用户名<input v-model.trim="name" name="username" autocomplete="username" maxlength="40" required></label>
        <label>密码<input v-model="password" name="password" type="password" :autocomplete="registering ? 'new-password' : 'current-password'" minlength="8" maxlength="128" required></label>
        <template v-if="registering">
          <p class="hint">密码长度为 8–128 个字符。</p>
          <label>确认密码<input v-model="confirmation" name="confirmation" type="password" autocomplete="new-password" required></label>
        </template>
        <p v-if="message" class="auth-error" role="alert">{{ message }}</p>
        <button class="retry" :disabled="busy">{{ busy ? '正在处理…' : registering ? '注册并登录' : '登录' }}</button>
        <button type="button" class="text-button" :disabled="busy" @click="toggleMode">{{ registering ? '已有账号，去登录' : '创建新账号' }}</button>
      </form>
    </div>
  </main>
</template>

<style>
.account-name { margin-left: auto; max-width: 40%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.text-button { background: transparent; border: 0; color: var(--accent); padding: 10px 0; }
.text-button:hover { text-decoration: underline; }
.auth-layout { margin: clamp(32px, 8vw, 110px) auto; max-width: 800px; display: grid; grid-template-columns: 1fr 1fr; gap: clamp(32px, 7vw, 96px); }
.auth-intro { border-left: 3px solid var(--accent); padding-left: 25px; align-self: start; }
.auth-intro p, .hint { color: var(--muted); margin-top: 10px; }
.auth-form { display: grid; gap: 16px; align-content: start; }
.auth-form h2 { font-size: 30px; }
.auth-form label { display: grid; gap: 6px; font-size: 14px; }
.auth-form input { width: 100%; padding: 11px; border: 1px solid #938f81; border-radius: 4px; background: #fffefa; color: var(--ink); font: inherit; }
.auth-form input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.auth-error { color: #923522; }
.hint { font-size: 13px; margin: -8px 0 0; }
@media (max-width: 680px) {
  .auth-layout { grid-template-columns: 1fr; max-width: 420px; }
  .auth-intro .folio { display: none; }
}
</style>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ContactEditor from './ContactEditor.vue'

const emit = defineEmits(['expired'])

const contacts = ref([])
const favoritesOnly = ref(false)
const loading = ref(true)
const error = ref('')
const methodLabels = { phone: '电话', email: '邮箱', social: '社交账号', address: '地址' }
const favorites = computed(() => contacts.value.filter(contact => contact.favorite))
const visibleContacts = computed(() => favoritesOnly.value ? favorites.value : contacts.value)
const editing = ref(null)
const working = ref(false)
const feedback = ref('')
const upload = ref(null)

async function run(action) {
  if (working.value) return
  working.value = true
  feedback.value = ''
  try {
    await action()
  } catch (err) {
    feedback.value = err instanceof TypeError ? '网络连接失败，请重试。' : err.message
  } finally {
    working.value = false
  }
}

async function contactRequest(suffix, options) {
  const response = await fetch('/api/v1/contacts' + suffix, options)
  if (response.status === 401) emit('expired')
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const issue = body.error?.details?.[0]
    const where = issue?.row ? '第 ' + issue.row + ' 行 ' : ''
    throw new Error(where + (issue?.message || body.error?.message || '操作失败，请重试。'))
  }
  return response
}

function edit(contact) {
  feedback.value = ''
  editing.value = contact
}

function write(contact, fields) {
  return run(async () => {
    await contactRequest(contact.id ? '/' + contact.id : '', {
      method: contact.id ? 'PATCH' : 'POST',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fields),
    })
    editing.value = null
    if (!contact.id) favoritesOnly.value = false
    await loadContacts()
  })
}

function remove(contact) {
  if (!window.confirm('确定删除「' + contact.name + '」及其所有联系方式？')) return
  return run(async () => {
    await contactRequest('/' + contact.id, {method:'DELETE'})
    await loadContacts()
  })
}

function importFile(event) {
  const file = event.target.files[0]
  event.target.value = ''
  if (!file) return
  return run(async () => {
    const body = new FormData()
    body.append('file', file)
    const response = await contactRequest('/import', {method:'POST', body})
    const result = await response.json()
    feedback.value = '已导入 ' + result.imported_count + ' 位联系人。'
    favoritesOnly.value = false
    await loadContacts()
  })
}

function exportFile() {
  return run(async () => {
    const response = await contactRequest('/export')
    const url = URL.createObjectURL(await response.blob())
    const link = document.createElement('a')
    link.href = url
    link.download = 'contacts.xlsx'
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  })
}

async function loadContacts() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch('/api/v1/contacts')
    if (response.status === 401) {
      emit('expired')
      return
    }
    if (!response.ok) throw new Error()
    const { items } = await response.json()
    if (!Array.isArray(items)) throw new Error()
    contacts.value = items
  } catch {
    error.value = '无法读取联系人。请确认后端服务已启动，然后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(loadContacts)
</script>

<template>
  <main class="directory">
    <div class="workspace">
      <nav aria-label="联系人筛选">
        <button v-for="view in [{ favorite: false, label: '全部联系人', count: contacts.length }, { favorite: true, label: '我的收藏', count: favorites.length }]"
          :key="view.label" :aria-pressed="favoritesOnly === view.favorite"
          @click="favoritesOnly = view.favorite">
          {{ view.label }} <span v-if="!loading && !error">{{ view.count }}</span>
        </button>
      </nav>
      <section aria-labelledby="list-title">
        <div class="section-head">
          <h2 id="list-title">{{ favoritesOnly ? '我的收藏' : '全部联系人' }}</h2>
          <span v-if="!loading && !error">{{ visibleContacts.length }} 位联系人</span>
        </div>
        <div v-if="!editing" class="actions toolbar">
          <button class="retry" :disabled="working || loading" @click="edit({name:'',notes:'',methods:[]})">新增联系人</button>
          <button class="text-button" :disabled="working || loading" @click="upload.click()">导入 Excel</button>
          <button class="text-button" :disabled="working || loading" @click="exportFile">导出 Excel</button>
          <input ref="upload" type="file" accept=".xlsx" hidden @change="importFile">
        </div>
        <ContactEditor v-if="editing" :contact="editing" :labels="methodLabels" :busy="working"
          @cancel="editing = null; feedback = ''" @save="write(editing, $event)" />
        <p v-if="feedback" role="status">{{ feedback }}</p>
        <div v-if="loading" class="status" role="status">正在读取联系人…</div>
        <div v-else-if="error || !visibleContacts.length" class="status">
          <span class="book-mark large" aria-hidden="true"></span>
          <template v-if="error">
            <h3 role="alert">暂时无法读取联系人</h3>
            <p>请确认通讯录服务已启动，然后重试。</p>
            <button class="retry" @click="loadContacts">重新加载</button>
          </template>
          <h3 v-else>{{ favoritesOnly ? '暂无收藏联系人' : '通讯录为空' }}</h3>
        </div>
        <article v-for="contact in (!loading && !error ? visibleContacts : [])" :key="contact.id">
          <div class="identity"><span class="initial" aria-hidden="true">{{ Array.from(contact.name)[0] }}</span><h3>{{ contact.name }}</h3><small v-if="contact.favorite">★ 已收藏</small></div>
          <div>
            <dl v-if="contact.methods.length">
              <div v-for="method in contact.methods" :key="JSON.stringify([method.type, method.value])">
                <dt>{{ methodLabels[method.type] }}</dt><dd>{{ method.value }}</dd>
              </div>
            </dl>
            <p v-if="contact.notes" class="notes">{{ contact.notes }}</p>
            <div v-if="!editing" class="actions">
              <button class="text-button" :disabled="working" :aria-pressed="contact.favorite" @click="write(contact,{favorite:!contact.favorite})">{{ contact.favorite ? '取消收藏' : '收藏' }}</button>
              <button class="text-button" :disabled="working" @click="edit(contact)">编辑</button>
              <button class="text-button" :disabled="working" @click="remove(contact)">删除</button>
            </div>
          </div>
        </article>
      </section>
    </div>
  </main>
</template>

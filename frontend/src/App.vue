<script setup>
import { computed, onMounted, ref } from 'vue'
import ContactEditor from './ContactEditor.vue'
import { displayMethod, methodLabels, websiteHref } from './contactMethods.js'

const emit = defineEmits(['expired'])

const contacts = ref([])
const favoritesOnly = ref(false)
const loading = ref(true)
const error = ref('')
const methodOrder = [...Object.keys(methodLabels), 'social']
const cards = computed(() => contacts.value.map(contact => ({
  contact,
  methods: contact.methods.map(method => ({
    ...displayMethod(method),
    key: JSON.stringify([method.type, method.value]),
  }))
    .sort((a, b) => methodOrder.indexOf(a.type) - methodOrder.indexOf(b.type)),
})))
const allCount = ref(null)
const favoriteCount = ref(null)
let listRequest = 0
const workbookColumns = { name: '姓名', notes: '备注', favorite: '收藏', phones: '电话', emails: '邮箱', socials: '社交账号', addresses: '地址' }
const editing = ref(null)
const working = ref(false)
const feedback = ref('')
const upload = ref(null)
const animals = Array.from('🐼🦊🐨🐱🐶🐰🐻🐯🐹🐸🐵🐷🐮🐧🦁🐙')

function avatarFor(id) {
  // Use the permanent contact ID as a seed so reloads keep the same avatar.
  const seed = Math.imul(id ^ (id >>> 16), 0x9e3779b1) >>> 0
  return animals[Math.floor(seed / 2 ** 32 * animals.length)]
}

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
    const problem = body?.error
    if (response.status === 422 && problem?.code === 'INVALID_WORKBOOK' && Array.isArray(problem.details)) {
      const lines = problem.details.filter(issue => issue?.message).map(({ row, field, message }) => {
        const column = Object.hasOwn(workbookColumns, field) ? workbookColumns[field] + '（' + field + '）' : field
        const location = [row != null && '第 ' + row + ' 行', column].filter(Boolean).join(' · ')
        return location ? location + '：' + message : message
      })
      if (lines.length) throw new Error(lines.join('\n'))
    }
    throw new Error(problem?.details?.[0]?.message || problem?.message || '操作失败，请重试。')
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
    if (allCount.value !== null) allCount.value--
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

function switchView(favorite) {
  if (favorite === favoritesOnly.value) return
  favoritesOnly.value = favorite
  feedback.value = ''
  loadContacts()
}

async function loadContacts() {
  const current = ++listRequest
  const favorite = favoritesOnly.value
  loading.value = true
  error.value = ''
  try {
    const response = await fetch('/api/v1/contacts' + (favorite ? '?favorite=true' : ''))
    if (current !== listRequest) return
    if (response.status === 401) {
      emit('expired')
      return
    }
    if (!response.ok) throw new Error()
    const { items } = await response.json()
    if (current !== listRequest) return
    if (!Array.isArray(items)) throw new Error()
    contacts.value = items
    if (favorite) {
      favoriteCount.value = items.length
    } else {
      allCount.value = items.length
      favoriteCount.value = items.filter(contact => contact.favorite).length
    }
  } catch {
    if (current === listRequest) error.value = '无法读取联系人。请确认后端服务已启动，然后重试。'
  } finally {
    if (current === listRequest) loading.value = false
  }
}

onMounted(loadContacts)
</script>

<template>
  <main class="directory">
    <div class="workspace">
      <ContactEditor v-if="editing" :contact="editing" :labels="methodLabels" :busy="working"
        :feedback="feedback" @back="edit(null)" @save="write(editing, $event)" />
      <nav v-if="!editing" aria-label="联系人筛选">
        <button v-for="view in [{ favorite: false, label: '全部联系人', count: allCount }, { favorite: true, label: '我的收藏', count: favoriteCount }]"
          :key="view.label" :aria-pressed="favoritesOnly === view.favorite"
          @click="switchView(view.favorite)">
          {{ view.label }} <span v-if="!loading && !error && view.count !== null">{{ view.count }}</span>
        </button>
      </nav>
      <section v-if="!editing" aria-labelledby="list-title">
        <div class="section-head">
          <h2 id="list-title">{{ favoritesOnly ? '我的收藏' : '全部联系人' }}</h2>
          <span v-if="!loading && !error">{{ contacts.length }} 位联系人</span>
        </div>
        <div class="actions toolbar">
          <button class="retry" :disabled="working || loading" @click="edit({name:'',notes:'',methods:[]})">新增联系人</button>
          <button class="text-button" :disabled="working || loading" @click="upload.click()">导入 Excel</button>
          <button class="text-button" :disabled="working || loading" @click="exportFile">导出 Excel</button>
          <input ref="upload" type="file" accept=".xlsx" hidden @change="importFile">
        </div>
        <p v-if="feedback" class="operation-feedback" role="status">{{ feedback }}</p>
        <div v-if="loading" class="status" role="status">正在读取联系人…</div>
        <div v-else-if="error || !contacts.length" class="status">
          <span class="book-mark large" aria-hidden="true"></span>
          <template v-if="error">
            <h3 role="alert">暂时无法读取联系人</h3>
            <p>请确认通讯录服务已启动，然后重试。</p>
            <button class="retry" @click="loadContacts">重新加载</button>
          </template>
          <h3 v-else>{{ favoritesOnly ? '暂无收藏联系人' : '通讯录为空' }}</h3>
        </div>
        <div v-else class="contact-grid">
          <article v-for="{ contact, methods } in cards" :key="contact.id" class="contact-card" :data-palette="contact.id % 4">
            <div class="identity">
              <span class="portrait" aria-hidden="true">{{ avatarFor(contact.id) }}</span>
              <h3 :title="contact.name">{{ contact.name }}</h3>
              <small v-if="contact.favorite" aria-label="已收藏">★</small>
            </div>
            <div class="contact-info" v-if="methods.length || contact.notes">
              <dl v-if="methods.length">
                <div v-for="method in methods" :key="method.key">
                  <dt>{{ methodLabels[method.type] || '社交账号' }}</dt>
                  <dd>
                    <a v-if="method.type === 'website' && websiteHref(method.value)" :href="websiteHref(method.value)"
                      target="_blank" rel="noopener noreferrer">{{ method.value }}</a>
                    <template v-else>{{ method.value }}</template>
                  </dd>
                </div>
              </dl>
              <p v-if="contact.notes" class="notes">{{ contact.notes }}</p>
            </div>
            <div class="contact-actions">
              <button class="text-button" :disabled="working" :aria-pressed="contact.favorite" @click="write(contact,{favorite:!contact.favorite})">{{ contact.favorite ? '取消收藏' : '收藏' }}</button>
              <button class="text-button" :disabled="working" @click="edit(contact)">编辑</button>
              <button class="text-button" :disabled="working" @click="remove(contact)">删除</button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </main>
</template>

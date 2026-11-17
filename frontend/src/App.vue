<script setup>
import { language, t } from './language.js'
import { computed, onMounted, ref } from 'vue'
import ContactEditor from './ContactEditor.vue'
import CopyValue from './CopyValue.vue'
import SearchHighlight from './SearchHighlight.vue'
import { displayMethod, methodLabels, websiteHref } from './contactMethods.js'

const emit = defineEmits(['expired'])

const contacts = ref([])
const favoritesOnly = ref(false)
const search = ref('')
const searchPattern = computed(() => {
  const term = search.value.trim()
  if (!term) return null
  const literal = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return new RegExp('(' + literal + ')', 'iu')
})
const matches = computed(() => {
  const pattern = searchPattern.value
  if (!pattern) return contacts.value
  return contacts.value.filter(contact =>
    pattern.test(contact.name) || pattern.test(contact.notes) ||
    contact.methods.some(method => pattern.test(method.value)))
})
const groups = computed(() => [
  { pinned: true, title: '置顶收藏', items: matches.value.filter(contact => contact.favorite) },
  { pinned: false, title: '其他联系人', items: matches.value.filter(contact => !contact.favorite) },
].filter(group => group.items.length))
const loading = ref(true)
const error = ref('')
const methodOrder = [...Object.keys(methodLabels), 'social']
const allCount = ref(null)
const favoriteCount = ref(null)
let listRequest = 0
const workbookColumns = { name: '姓名', notes: '备注', favorite: '收藏', phones: '电话', emails: '邮箱', socials: '社交账号', addresses: '地址' }
const editing = ref(null)
const working = ref(false)
const feedback = ref('')
const workbookIssues = ref([])
const upload = ref(null)
const animals = Array.from('🐼🦊🐨🐱🐶🐰🐻🐯🐹🐸🐵🐷🐮🐧🦁🐙')

function avatarFor(id) {
  // Use the permanent contact ID as a seed so reloads keep the same avatar.
  const seed = Math.imul(id ^ (id >>> 16), 0x9e3779b1) >>> 0
  return animals[Math.floor(seed / 2 ** 32 * animals.length)]
}

function displayContact(contact) {
  return {
    ...contact,
    methods: contact.methods.map(displayMethod)
      .sort((a, b) => methodOrder.indexOf(a.type) - methodOrder.indexOf(b.type)),
  }
}

async function run(action) {
  if (working.value) return
  working.value = true
  feedback.value = ''
  workbookIssues.value = []
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
      workbookIssues.value = problem.details.filter(issue => issue?.message)
      if (workbookIssues.value.length) throw new Error(problem.message || '工作簿校验失败，未导入任何联系人。')
    }
    throw new Error(problem?.details?.[0]?.message || problem?.message || '操作失败，请重试。')
  }
  return response
}

function edit(contact) {
  feedback.value = ''
  workbookIssues.value = []
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
  const prompt = language.value === 'en' ? 'Delete “' + contact.name + '” and all their contact details?' : '确定删除「' + contact.name + '」及其所有联系方式？'
  if (!window.confirm(prompt)) return
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

function downloadWorkbook(template = false) {
  return run(async () => {
    const response = await contactRequest(template ? '/template' : '/export')
    const url = URL.createObjectURL(await response.blob())
    const link = document.createElement('a')
    link.href = url
    link.download = template ? 'contacts-template.xlsx' : 'contacts.xlsx'
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  })
}

function switchView(favorite) {
  if (favorite === favoritesOnly.value) return
  favoritesOnly.value = favorite
  feedback.value = ''
  workbookIssues.value = []
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
    contacts.value = items.map(displayContact)
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
      <nav v-if="!editing" :aria-label="t('联系人筛选')">
        <button v-for="view in [{ favorite: false, label: '全部联系人', count: allCount }, { favorite: true, label: '我的收藏', count: favoriteCount }]"
          :key="view.label" :aria-pressed="favoritesOnly === view.favorite"
          @click="switchView(view.favorite)">
          {{ t(view.label) }} <span v-if="!loading && !error && view.count !== null">{{ view.count }}</span>
        </button>
      </nav>
      <section v-if="!editing" aria-labelledby="list-title">
        <div class="section-head">
          <h2 id="list-title">{{ t(favoritesOnly ? '我的收藏' : '全部联系人') }}</h2>
          <span v-if="!loading && !error">{{ matches.length }} {{ language === 'zh' ? '位联系人' : matches.length === 1 ? 'contact' : 'contacts' }}</span>
        </div>
        <div class="search-bar" role="search">
          <input v-model="search" type="search" :aria-label="t('搜索联系人')" :placeholder="t('搜索姓名、电话、地址或备注')">
          <button v-if="search" type="button" class="text-button" @click="search = ''">{{ t('清除搜索') }}</button>
        </div>
        <div class="actions toolbar">
          <button class="retry" :disabled="working || loading" @click="edit({name:'',notes:'',methods:[]})">{{ t('新增联系人') }}</button>
          <button class="text-button" :disabled="working || loading" @click="upload.click()">{{ t('导入 Excel') }}</button>
          <button class="text-button" :disabled="working" @click="downloadWorkbook(true)">{{ t('下载 Excel 模板') }}</button>
          <button class="text-button" :disabled="working || loading" @click="downloadWorkbook()">{{ t('导出 Excel') }}</button>
          <input ref="upload" type="file" accept=".xlsx" hidden @change="importFile">
        </div>
        <p v-if="feedback" class="operation-feedback" role="status">{{ t(feedback) }}</p>
        <ul v-if="workbookIssues.length" class="workbook-errors">
          <li v-for="(issue, index) in workbookIssues" :key="index">
            <template v-if="issue.row != null">{{ language === 'en' ? 'Row ' + issue.row : '第 ' + issue.row + ' 行' }} · </template>
            <template v-if="issue.field">{{ workbookColumns[issue.field] ? t(workbookColumns[issue.field]) + ' (' + issue.field + ')' : issue.field }}: </template>
            {{ t(issue.message) }}
          </li>
        </ul>
        <div v-if="loading" class="status" role="status">{{ t('正在读取联系人…') }}</div>
        <div v-else-if="error || !matches.length" class="status">
          <span class="book-mark large" aria-hidden="true"></span>
          <template v-if="error">
            <h3 role="alert">{{ t('暂时无法读取联系人') }}</h3>
            <p>{{ t('请确认通讯录服务已启动，然后重试。') }}</p>
            <button class="retry" @click="loadContacts">{{ t('重新加载') }}</button>
          </template>
          <h3 v-else-if="searchPattern">{{ t('没有匹配的联系人') }}</h3>
          <h3 v-else>{{ t(favoritesOnly ? '暂无收藏联系人' : '通讯录为空') }}</h3>
        </div>
        <div v-else class="contact-groups">
          <section v-for="group in groups" :key="group.title" class="contact-group">
            <h3 v-if="!favoritesOnly && (group.pinned || groups.length > 1)" class="group-title">{{ t(group.title) }}</h3>
            <div class="contact-grid">
              <article v-for="contact in group.items" :key="contact.id" class="contact-card" :class="{ pinned: group.pinned }" :data-palette="contact.id % 4">
                <div class="identity">
                  <span class="portrait" aria-hidden="true">{{ avatarFor(contact.id) }}</span>
                  <h3 :title="contact.name"><SearchHighlight :text="contact.name" :pattern="searchPattern" /></h3>
                  <small v-if="contact.favorite" :aria-label="t('已收藏')">★</small>
                </div>
                <div class="contact-info" v-if="contact.methods.length || contact.notes">
                  <dl v-if="contact.methods.length">
                    <div v-for="method in contact.methods" :key="JSON.stringify([method.type, method.value])">
                      <dt>{{ t(methodLabels[method.type] || '社交账号') }}</dt>
                      <dd class="method-value">
                        <span>
                        <a v-if="method.type === 'website' && websiteHref(method.value)" :href="websiteHref(method.value)"
                          target="_blank" rel="noopener noreferrer"><SearchHighlight :text="method.value" :pattern="searchPattern" /></a>
                        <SearchHighlight v-else :text="method.value" :pattern="searchPattern" />
                        </span>
                        <CopyValue :value="method.value" :label="t(methodLabels[method.type] || '社交账号')" />
                      </dd>
                    </div>
                  </dl>
                  <p v-if="contact.notes" class="notes"><SearchHighlight :text="contact.notes" :pattern="searchPattern" /></p>
                </div>
                <div class="contact-actions">
                  <button class="text-button" :disabled="working" :aria-pressed="contact.favorite" @click="write(contact,{favorite:!contact.favorite})">{{ t(contact.favorite ? '取消收藏' : '收藏') }}</button>
                  <button class="text-button" :disabled="working" @click="edit(contact)">{{ t('编辑') }}</button>
                  <button class="text-button" :disabled="working" @click="remove(contact)">{{ t('删除') }}</button>
                </div>
              </article>
            </div>
          </section>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const contacts = ref([])
const favoritesOnly = ref(false)
const loading = ref(true)
const error = ref('')
const methodLabels = { phone: '电话', email: '邮箱', social: '社交账号', address: '地址' }
const favorites = computed(() => contacts.value.filter(contact => contact.favorite))
const visibleContacts = computed(() => favoritesOnly.value ? favorites.value : contacts.value)

async function loadContacts() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch('/api/v1/contacts')
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
    <header><span class="book-mark" aria-hidden="true"></span><h1>通讯录</h1></header>
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
        <div v-if="loading" class="status" role="status">正在读取联系人…</div>
        <div v-else-if="error || !visibleContacts.length" class="status">
          <div class="folio" aria-hidden="true"><i></i></div>
          <template v-if="error">
            <h3 role="alert">暂时无法读取联系人</h3>
            <p>请确认通讯录服务已启动，然后重试。</p>
            <button class="retry" @click="loadContacts">重新加载</button>
          </template>
          <h3 v-else>{{ favoritesOnly ? '暂无收藏联系人' : '通讯录为空' }}</h3>
        </div>
        <article v-for="contact in (!loading && !error ? visibleContacts : [])" :key="contact.id">
          <div class="identity"><h3>{{ contact.name }}</h3><small v-if="contact.favorite">★ 已收藏</small></div>
          <div>
            <dl v-if="contact.methods.length">
              <div v-for="method in contact.methods" :key="JSON.stringify([method.type, method.value])">
                <dt>{{ methodLabels[method.type] }}</dt><dd>{{ method.value }}</dd>
              </div>
            </dl>
            <p v-if="contact.notes" class="notes">{{ contact.notes }}</p>
          </div>
        </article>
      </section>
    </div>
  </main>
</template>

<style>
:root {
  --paper: #faf9f5;
  --ink: #282922;
  --muted: #64665e;
  --line: #d9d7cb;
  --accent: #983f29;
  font-family: "Microsoft YaHei", system-ui, sans-serif;
  color: var(--ink);
  background: var(--paper);
}
* { box-sizing: border-box; }
body { margin: 0; }
.directory { max-width: 1180px; margin: auto; padding: 0 clamp(18px, 5vw, 72px) 60px; }
header { display: flex; align-items: center; gap: 14px; height: 86px; border-bottom: 1px solid var(--ink); }
h1, h2, h3, p, dl, dd { margin: 0; }
h1, h2, h3 { font-family: "Songti SC", SimSun, serif; }
h1 { font-size: 26px; }
.book-mark { width: 22px; height: 26px; border: 2px solid var(--accent); border-left-width: 6px; border-radius: 2px 5px 5px 2px; }
.workspace { display: grid; grid-template-columns: 176px minmax(0, 1fr); gap: clamp(32px, 6vw, 86px); padding-top: 52px; }
nav { display: flex; flex-direction: column; align-self: start; gap: 4px; }
button { font: inherit; color: inherit; cursor: pointer; }
nav button { text-align: left; display: flex; justify-content: space-between; gap: 10px; padding: 13px 16px; background: transparent; border: 0; border-left: 3px solid transparent; }
nav button span { font-variant-numeric: tabular-nums; }
nav button:hover { background: #f0eee7; }
nav button[aria-pressed="true"] { background: #ede9df; border-color: var(--accent); font-weight: 600; }
button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.section-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; padding-bottom: 22px; border-bottom: 1px solid var(--line); }
h2 { font-size: clamp(32px, 4vw, 48px); letter-spacing: -.04em; }
.section-head span, dt, .notes, .status p { color: var(--muted); font-size: 14px; }
.status { min-height: 300px; display: grid; justify-items: center; align-content: center; gap: 12px; text-align: center; }
.folio { position: relative; width: 54px; height: 66px; background: #e7e2d5; border: 1px solid #9f998a; border-radius: 3px 7px 7px 3px; box-shadow: inset 6px 0 #cfc8b7, 3px 3px var(--paper), 4px 4px #ada795; margin-bottom: 12px; }
.folio i { position: absolute; top: -1px; right: 9px; width: 9px; height: 23px; background: var(--accent); clip-path: polygon(0 0,100% 0,100% 100%,50% 80%,0 100%); }
.retry { margin-top: 6px; padding: 9px 18px; border-radius: 4px; border: 1px solid var(--ink); background: var(--ink); color: var(--paper); }
.retry:hover { background: #494b41; }
article { display: grid; grid-template-columns: minmax(100px, 1fr) minmax(0, 2fr); gap: 20px; padding: 24px 0; border-bottom: 1px solid var(--line); overflow-wrap: anywhere; }
h3 { font-size: 21px; }
small { color: var(--accent); }
dl > div { display: grid; grid-template-columns: 5em minmax(0, 1fr); padding-bottom: 5px; }
.notes { white-space: pre-wrap; line-height: 1.6; }
@media (max-width: 680px) {
  header { height: 64px; }
  .workspace { grid-template-columns: 1fr; gap: 28px; padding-top: 18px; }
  nav { flex-direction: row; }
  nav button { flex: 1; align-items: center; }
  article { grid-template-columns: 1fr; gap: 10px; }
}
</style>
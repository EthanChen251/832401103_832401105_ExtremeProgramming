<script setup>
import { language, t } from './language.js'
import { computed, ref } from 'vue'
import { storedMethod } from './contactMethods.js'

const props = defineProps({ contact: Object, labels: Object, busy: Boolean, feedback: String })
const emit = defineEmits(['save', 'back'])
const name = ref(props.contact.name)
const notes = ref(props.contact.notes)
let nextKey = 0
const methods = ref(props.contact.methods.map(method => ({ ...method, key: nextKey++ })))
const changed = computed(() => name.value !== props.contact.name || notes.value !== props.contact.notes ||
  methods.value.length !== props.contact.methods.length || methods.value.some((method, index) => {
    const original = props.contact.methods[index]
    return method.type !== original.type || method.value !== original.value
  }))

function back() {
  if (!changed.value || window.confirm(t('放弃尚未保存的修改并返回通讯录？'))) emit('back')
}

function save() {
  emit('save', {
    name: name.value, notes: notes.value,
    methods: methods.value.map(storedMethod),
  })
}
</script>

<template>
  <form class="editor" @submit.prevent="save">
    <fieldset :disabled="busy">
      <legend>{{ t(contact.id ? '编辑联系人' : '新增联系人') }}</legend>
      <label>{{ t('姓名') }}<input v-model="name" required></label>
      <label>{{ t('备注') }}<textarea v-model="notes" rows="2"></textarea></label>
      <div v-for="(method, index) in methods" :key="method.key" class="method-row">
        <select v-model="method.type" :aria-label="language === 'en' ? 'Contact method type ' + (index + 1) : '第 ' + (index + 1) + ' 条联系方式类型'">
          <option v-if="method.type === 'social'" value="social">{{ t('社交账号（旧记录）') }}</option>
          <option v-for="(label,type) in labels" :key="type" :value="type">{{ t(label) }}</option>
        </select>
        <input v-if="method.type === 'website'" v-model.trim="method.value" type="url"
          :aria-label="t('个人网站')" placeholder="https://example.com" pattern="[Hh][Tt][Tt][Pp][Ss]?://.+"
          :title="t('请输入以 https:// 或 http:// 开头的完整网址')" required>
        <input v-else v-model="method.value" :aria-label="t(labels[method.type] || '社交账号')" pattern=".*\S.*" :title="t('请输入联系方式')" required>
        <button type="button" class="text-button" @click="methods.splice(index,1)">{{ t('移除') }}</button>
      </div>
      <button type="button" class="text-button" @click="methods.push({type:'phone', value:'', key:nextKey++})">{{ t('＋ 添加联系方式') }}</button>
      <div class="actions"><button class="retry">{{ t(busy ? '保存中…' : '保存联系人') }}</button>
        <button type="button" class="text-button" @click="back">{{ t('返回通讯录') }}</button>
        <span role="status">{{ t(feedback || (changed ? '有未保存的修改' : '')) }}</span>
      </div>
    </fieldset>
  </form>
</template>

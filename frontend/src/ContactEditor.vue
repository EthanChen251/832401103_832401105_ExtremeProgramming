<script setup>
import { ref } from 'vue'

const props = defineProps({ contact: Object, labels: Object, busy: Boolean })
const emit = defineEmits(['save', 'cancel'])
const name = ref(props.contact.name)
const notes = ref(props.contact.notes)
let nextKey = 0
const methods = ref(props.contact.methods.map(method => ({ ...method, key: nextKey++ })))

function save() {
  emit('save', {
    name: name.value, notes: notes.value,
    methods: methods.value.map(({type, value}) => ({type, value})),
  })
}
</script>

<template>
  <form class="editor" @submit.prevent="save">
    <fieldset :disabled="busy">
      <legend>{{ contact.id ? '编辑联系人' : '新增联系人' }}</legend>
      <label>姓名<input v-model="name" required></label>
      <label>备注<textarea v-model="notes" rows="2"></textarea></label>
      <div v-for="(method, index) in methods" :key="method.key" class="method-row">
        <select v-model="method.type" :aria-label="'第 ' + (index+1) + ' 条联系方式类型'">
          <option v-for="(label,type) in labels" :key="type" :value="type">{{ label }}</option>
        </select>
        <input v-model="method.value" :aria-label="labels[method.type]" required>
        <button type="button" class="text-button" @click="methods.splice(index,1)">移除</button>
      </div>
      <button type="button" class="text-button" @click="methods.push({type:'phone', value:'', key:nextKey++})">＋ 添加联系方式</button>
      <div class="actions"><button class="retry">保存联系人</button>
        <button type="button" class="text-button" @click="emit('cancel')">取消</button></div>
    </fieldset>
  </form>
</template>

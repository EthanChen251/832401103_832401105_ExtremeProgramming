<script setup>
import { onUnmounted, ref } from 'vue'
import { t } from './language.js'

const props = defineProps({ value: String, label: String })
const status = ref('')
let timer

function copyWithSelection() {
  const input = document.createElement('textarea')
  input.value = props.value
  input.readOnly = true
  input.style.cssText = 'position:fixed;top:0;left:-9999px'
  const previous = document.activeElement
  document.body.append(input)
  try {
    input.select()
    return document.execCommand('copy')
  } finally {
    input.remove()
    previous?.focus({ preventScroll: true })
  }
}

async function copy() {
  try {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(props.value)
    else if (!copyWithSelection()) throw new Error()
    status.value = '已复制'
  } catch {
    status.value = '复制失败'
  }
  clearTimeout(timer)
  timer = setTimeout(() => { status.value = '' }, 1800)
}

onUnmounted(() => clearTimeout(timer))
</script>

<template>
  <button type="button" class="copy-value" :aria-label="t('复制') + ' · ' + label + ' · ' + value" @click="copy">
    <span aria-live="polite">{{ t(status || '复制') }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ text: String, pattern: RegExp })
// The search pattern has one capture group: odd pieces are the literal matches.
const pieces = computed(() => props.pattern ? props.text.split(props.pattern) : [props.text])
</script>

<template>
  <template v-for="(piece, index) in pieces" :key="index"><mark v-if="index % 2">{{ piece }}</mark><template v-else>{{ piece }}</template></template>
</template>

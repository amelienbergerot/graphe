<template>
  <div @click="toggle">{{ label(rain) }}</div>
</template>

<script setup lang="ts">
import { label } from './ui/Panel'
import { Gauge } from './lib/water'

const { rain } = defineProps<{ rain: number }>()

function toggle() {
  const g = new Gauge()
  return g.level(rain)
}
</script>

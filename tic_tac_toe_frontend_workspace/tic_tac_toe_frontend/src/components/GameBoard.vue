<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';

const props = defineProps<{
  board: ("X"|"O"|null)[][];
  active: boolean;
  disabled: boolean;
  myPlayer: "X"|"O"|null;
  turn: "X"|"O"|null;
}>();

const emit = defineEmits<{
  (e: 'cell-click', row: number, col: number): void;
}>();

function handleCellClick(row: number, col: number) {
  if (!props.active || props.disabled || props.board[row][col]) return;
  emit('cell-click', row, col);
}
</script>

<template>
  <div class="ttt-board" :style="{opacity: disabled ? 0.6 : 1}">
    <template v-for="(row, r) in props.board" :key="r">
      <div
        v-for="(cell, c) in row"
        :key="`${r},${c}`"
        class="ttt-cell"
        :data-value="cell || ''"
        @click="handleCellClick(r, c)"
        :style="{
          cursor: (active && !disabled && !cell) ? 'pointer' : 'default',
          background: cell ? 'var(--ttt-bg)' : (active && !disabled ? '#fafbfc' : 'var(--ttt-bg)')
        }"
      >
        <span v-if="cell">{{ cell }}</span>
      </div>
    </template>
  </div>
</template>

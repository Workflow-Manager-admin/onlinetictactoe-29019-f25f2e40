<script setup lang="ts">
import type { GameStateResponse, GameHistoryEntry, Player } from '../api/tictactoe';

defineProps<{
  gameState: GameStateResponse | null;
  gameId: string;
  player: Player|null;
  history: GameHistoryEntry[];
  step: string;
}>();
defineEmits(['restart']);

const resultSummary = (entry: GameHistoryEntry) => {
  if (entry.winner) return `Winner: ${entry.winner}`;
  if (entry.draw) return 'Draw';
  return "";
};
</script>

<template>
  <aside class="ttt-sidebar">
    <section v-if="step==='playing'">
      <div style="font-weight:600;margin-bottom:1.1em;">
        <span>Your symbol:</span>
        <span :style="{color:player==='X'?'var(--ttt-x)':'var(--ttt-o)',marginLeft:'0.45em',fontSize:'1.4em'}">{{ player || '-' }}</span>
      </div>
      <div>
        <div style="font-size:1.07em;margin-bottom:0.40em;">
          <span v-if="gameState">
            <b>Status:</b> {{ gameState.status }}
          </span>
        </div>
        <div v-if="gameState && gameState.winner" style="font-size:1.13em;color:var(--ttt-secondary);margin-bottom:0.5em;">
          Winner: {{ gameState.winner }}
        </div>
        <div v-if="gameState && gameState.draw" style="color:var(--ttt-draw);margin-bottom:0.5em;">Draw!</div>
        <div style="font-size:0.95em;margin-bottom:0.8em;"><b>Game ID:</b><br><span style="word-break:break-all;">{{ gameId }}</span></div>
        <button class="ttt-btn ttt-secondary" style="width:100%;margin-bottom:1.2em" @click="$emit('restart')">New Game / Home</button>
      </div>
    </section>
    <section>
      <h3 style="margin-bottom:0.2em;font-size:1.12em;">Previous Games</h3>
      <ul class="ttt-list">
        <li v-if="!history?.length" style="color:#aaa;">No game history</li>
        <li v-for="entry in history" :key="entry.game_id">
          <span style="font-weight:500;">{{ entry.started_at.slice(2,10) }}</span>
          &mdash; <span>{{ resultSummary(entry) }}</span>
        </li>
      </ul>
    </section>
  </aside>
</template>

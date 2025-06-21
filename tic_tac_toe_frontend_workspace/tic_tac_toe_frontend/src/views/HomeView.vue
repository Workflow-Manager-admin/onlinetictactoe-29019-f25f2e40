<script setup lang="ts">
import { computed, reactive, onMounted, watch } from 'vue';
import GameBoard from '../components/GameBoard.vue';
import PlayerSidebar from '../components/PlayerSidebar.vue';
import {
  startNewGame,
  joinGame,
  getGameState,
  makeMove,
  listOpenGames,
  getGameHistory,
  type Player,
  type GameStateResponse,
  type GameHistoryEntry
} from '../api/tictactoe';

const state = reactive<{
  loading: boolean;
  gameState: GameStateResponse|null;
  gameId: string;
  player: Player|null;
  step: 'home'|'creating'|'joining'|'playing';
  error: string|null;
  playerName: string;
  openGames: string[];
  history: GameHistoryEntry[];
}>({
  loading: false,
  gameState: null,
  gameId: '',
  player: null,
  step: 'home',
  error: null,
  playerName: '',
  openGames: [],
  history: [],
});

function resetToHome() {
  state.player = null;
  state.gameId = '';
  state.gameState = null;
  state.error = null;
  state.step = 'home';
  state.playerName = '';
}

const fetchOpenGames = async () => {
  try {
    state.openGames = await listOpenGames();
  } catch {}
};

const fetchHistory = async () => {
  try {
    const res = await getGameHistory();
    state.history = res.games || [];
  } catch {}
};

async function handleStartGame() {
  state.loading = true;
  state.error = null;
  try {
    const res = await startNewGame(state.playerName);
    state.step = 'playing';
    state.gameId = res.game_id;
    state.player = res.player;
    await refreshState();
    fetchHistory();
  } catch (e) {
    state.error = (e instanceof Error) ? e.message : String(e);
  } finally {
    state.loading = false;
  }
}

async function handleJoinGame() {
  state.loading = true;
  state.error = null;
  try {
    const res = await joinGame(state.gameId, state.playerName);
    if (!res.success) {
      state.error = res.message;
      state.step = 'joining';
      return;
    }
    state.player = "O";
    state.step = 'playing';
    await refreshState();
    fetchHistory();
  } catch (e) {
    state.error = (e instanceof Error) ? e.message : String(e);
  } finally {
    state.loading = false;
  }
}

const refreshState = async () => {
  if (!state.gameId) return;
  try {
    state.gameState = await getGameState(state.gameId);
  } catch (e) {
    state.error = (e instanceof Error) ? e.message : String(e);
  }
};

// Automatically refresh board every 2.5 seconds if in play
let polling: null|ReturnType<typeof setInterval> = null;
function setPolling(active: boolean) {
  if (polling) { clearInterval(polling); polling = null; }
  if (active && state.step === 'playing') {
    polling = setInterval(refreshState, 2500);
  }
}
onMounted(() => {
  fetchOpenGames();
  fetchHistory();
});

watch(
  () => state.step,
  (step) => setPolling(step === 'playing')
);

async function handleMove(row: number, col: number) {
  if (!state.gameId || !state.player || !state.gameState?.next_turn) return;
  if (state.player !== state.gameState.next_turn) return;
  try {
    state.loading = true;
    const res = await makeMove(state.gameId, row, col, state.player);
    state.gameState = res;
    if (res.winner || res.draw) fetchHistory();
  } catch (e) {
    state.error = (e instanceof Error) ? e.message : String(e);
  } finally {
    state.loading = false;
  }
}

const isMyTurn = computed(() =>
  !!state.player && state.gameState?.next_turn === state.player
);

</script>

<template>
  <main class="ttt-container">
    <link rel="stylesheet" href="@/assets/tictactoe.css" />
    <div class="ttt-main">
      <div class="ttt-board-panel">
        <h1 style="margin-bottom:0.85rem;color:var(--ttt-primary);text-align:center;">Online Tic Tac Toe</h1>
        <div v-if="state.step === 'home'">
          <form @submit.prevent="handleStartGame" class="ttt-form-group" style="margin-bottom:2rem;">
            <label class="ttt-label" for="playerName">Enter name (optional):</label>
            <input class="ttt-input" type="text" v-model="state.playerName" id="playerName" placeholder="Your name (optional)" />
            <button class="ttt-btn" type="submit" :disabled="state.loading" style="width:100%;margin-top:1rem;">Start New Game</button>
          </form>
          <div style="margin:1rem 0 0.55rem 0;font-weight:500;">-- Or Join an Open Game --</div>
          <div>
            <button class="ttt-btn ttt-secondary" @click="fetchOpenGames" style="font-size:0.96rem;margin-bottom:0.4rem;">Refresh Open Games</button>
            <ul class="ttt-list">
              <li v-if="state.openGames.length === 0" style="color:#999;font-size:1rem;">No open games to join</li>
              <li v-for="gid in state.openGames" :key="gid">
                <span style="font-size:0.98rem;">ID: {{ gid.slice(0,7) }}...</span>
                <button class="ttt-btn ttt-accent" style="font-size:0.93rem;padding:0.37em 0.85em;margin-left:0.5em"
                        @click="state.step='joining';state.gameId=gid;">Join</button>
              </li>
            </ul>
          </div>
        </div>
        <div v-else-if="state.step === 'joining'">
          <form @submit.prevent="handleJoinGame" class="ttt-form-group" style="margin-bottom:1.2rem;">
            <label class="ttt-label" for="join-playerName">Name (optional):</label>
            <input class="ttt-input" id="join-playerName" v-model="state.playerName" type="text" placeholder="Your name (optional)" />
            <div style="margin:0.82rem 0;">
              <span style="font-size:1rem;color:#222;">Game ID:</span>
              <span style="font-size:1.07rem;font-weight:bold;color:var(--ttt-primary);margin-left:0.65em">{{ state.gameId }}</span>
            </div>
            <button type="submit" class="ttt-btn ttt-secondary" :disabled="state.loading" style="width:100%;">Join Game</button>
            <div style="margin-top:1em;"><button type="button" class="ttt-btn" @click="resetToHome">Back</button></div>
          </form>
        </div>
        <div v-else-if="state.step === 'playing' && state.gameState">
          <div class="ttt-status-bar">
            <span v-if="!state.gameState.winner && !state.gameState.draw">
              <span :style="{color:isMyTurn?'var(--ttt-accent)':'#333'}">
                {{ isMyTurn ? 'Your turn!' : 'Opponent turn' }}
              </span>
              <span style="margin-left:0.85em;font-size:0.98em;color:#555;">({{ state.gameState.status }})</span>
            </span>
            <span v-if="state.gameState.winner">
              <b style="color:var(--ttt-secondary);">Winner: {{ state.gameState.winner }}</b>
            </span>
            <span v-if="state.gameState.draw">
              <b style="color:var(--ttt-draw);">Draw!</b>
            </span>
          </div>
          <GameBoard
            :board="state.gameState.board"
            :active="!state.gameState.winner && !state.gameState.draw"
            :disabled="state.loading || !isMyTurn"
            :myPlayer="state.player"
            :turn="state.gameState.next_turn"
            @cell-click="handleMove"
          />
          <div style="margin-top:1.0rem;">
            <button class="ttt-btn" @click="resetToHome" style="width:100%;">Return to Home</button>
          </div>
        </div>
        <div v-if="state.error" style="color:#d33;margin-top:1em;text-align:center;font-weight:500;">{{ state.error }}</div>
      </div>
      <PlayerSidebar
        :gameState="state.gameState"
        :gameId="state.gameId"
        :player="state.player"
        :history="state.history"
        :step="state.step"
        @restart="resetToHome"
      />
    </div>
  </main>
</template>


//
// Tic Tac Toe API integration for FastAPI backend.
//

export type Player = "X" | "O";
export interface CreateGameResponse {
  game_id: string;
  player: Player;
}
export interface JoinGameResponse {
  success: boolean;
  player: string;
  message: string;
}
export interface GameStateResponse {
  board: Array<Array<Player|null>>;
  next_turn: Player|null;
  winner: Player|null;
  draw: boolean;
  status: string;
  game_id: string;
}
export interface GameHistoryEntry {
  game_id: string;
  started_at: string;
  finished_at: string|null;
  winner: Player|null;
  draw: boolean;
}
export interface GameHistoryResponse {
  games: GameHistoryEntry[];
}

const BASE_URL = import.meta.env.VITE_TTT_BACKEND_URL || "http://localhost:3001";

async function api<T>(
  path: string,
  opts?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "omit",
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

// PUBLIC_INTERFACE
export async function startNewGame(player_name?: string): Promise<CreateGameResponse> {
  return api("/game", {
    method: "POST",
    body: JSON.stringify(player_name ? { player_name } : {}),
  });
}

// PUBLIC_INTERFACE
export async function joinGame(game_id: string, player_name?: string): Promise<JoinGameResponse> {
  return api(`/game/${encodeURIComponent(game_id)}/join`, {
    method: "POST",
    body: JSON.stringify({ player_name }),
  });
}

// PUBLIC_INTERFACE
export async function getGameState(game_id: string): Promise<GameStateResponse> {
  return api(`/game/${encodeURIComponent(game_id)}`);
}

// PUBLIC_INTERFACE
export async function makeMove(game_id: string, row: number, col: number, player: Player): Promise<GameStateResponse> {
  return api(`/game/${encodeURIComponent(game_id)}/move`, {
    method: "POST",
    body: JSON.stringify({ row, col, player }),
  });
}

// PUBLIC_INTERFACE
export async function listOpenGames(): Promise<string[]> {
  return api("/games/open");
}

// PUBLIC_INTERFACE
export async function getGameHistory(): Promise<GameHistoryResponse> {
  return api("/history");
}

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import Optional, List, Dict, Literal
from datetime import datetime

# ----------------------------------------------------
# Data Models
# ----------------------------------------------------

# Exactly 2 blank lines above top-level class


class Player(str):
    X = "X"
    O_ = "O"  # Renamed to 'O_' to avoid ambiguous variable name E741




class CreateGameResponse(BaseModel):
    game_id: str = Field(
        ...,
        description="The ID of the newly created game session."
    )
    player: Literal["X"] = Field(
        ...,
        description="The symbol assigned to the player who started the game."
    )

class JoinGameRequest(BaseModel):
    player_name: Optional[str] = Field(
        None, description="Optional: Human-readable player name."
    )


class JoinGameResponse(BaseModel):
    success: bool = Field(
        ..., description="True if the player successfully joined the game."
    )
    player: Literal["O"] = Field(
        ..., description="The symbol assigned to the joining player."
    )
    message: str = Field(
        ..., description="Status or explanation message."
    )


class MakeMoveRequest(BaseModel):
    row: int = Field(
        ..., ge=0, le=2, description="Row index (0-2)"
    )
    col: int = Field(
        ..., ge=0, le=2, description="Column index (0-2)"
    )
    player: Player = Field(
        ..., description="Player symbol making the move ('X' or 'O')"
    )


class GameStateResponse(BaseModel):
    board: List[List[Optional[Player]]] = Field(
        ..., description="Current state of the game board."
    )
    next_turn: Optional[Player] = Field(
        None,
        description="The symbol of the player whose turn is next, or None if game over."
    )
    winner: Optional[Player] = Field(
        None, description="The symbol of the winning player, if any."
    )
    draw: bool = Field(
        ..., description="True if the game ended in a draw."
    )
    status: str = Field(
        ..., description="Text description of game status."
    )
    game_id: str = Field(
        ..., description="The ID of the game session."
    )


class GameHistoryEntry(BaseModel):
    game_id: str
    started_at: datetime
    finished_at: Optional[datetime]
    winner: Optional[Player]
    draw: bool


class GameHistoryResponse(BaseModel):
    games: List[GameHistoryEntry]


# ----------------------------------------------------
# In-Memory Game Store
# (Replace with DB in production)
# ----------------------------------------------------

class GameSession:

    def __init__(self):
        self.game_id: str = str(uuid4())
        self.board: List[List[Optional[Player]]] = [
            [None] * 3 for _ in range(3)
        ]
        # Use keys Player.X and Player.O_ to avoid ambiguous O
        self.players: Dict[Player, Optional[str]] = {
            Player.X: None,
            Player.O_: None
        }
        self.current_turn: Player = Player.X
        self.winner: Optional[Player] = None
        self.draw: bool = False
        self.moves: List[Dict] = []
        self.started_at: datetime = datetime.utcnow()
        self.finished_at: Optional[datetime] = None

    def available_slot(self) -> Optional[Player]:
        if self.players[Player.O_] is None:
            return Player.O_
        return None

    def is_open(self) -> bool:
        return self.players[Player.O_] is None and self.winner is None and not self.draw

    def add_player(self, player: Player, player_name: Optional[str]):
        if self.players[player] is None:
            self.players[player] = player_name

    def make_move(self, row: int, col: int, player: Player):
        if self.winner or self.draw:
            raise ValueError("Game is already finished.")
        if player != self.current_turn:
            raise ValueError("It's not your turn.")
        if not (0 <= row <= 2 and 0 <= col <= 2):
            raise ValueError("Row/col out of bounds.")
        if self.board[row][col] is not None:
            raise ValueError("Cell is already occupied.")

        self.board[row][col] = player
        self.moves.append(
            {"row": row, "col": col, "player": player}
        )
        self.check_game_status()
        if not (self.winner or self.draw):
            self.current_turn = Player.O_ if player == Player.X else Player.X

    def check_game_status(self):
        # Rows
        lines = [row[:] for row in self.board]
        # Columns
        lines.extend(
            [[self.board[r][c] for r in range(3)] for c in range(3)]
        )
        # Diagonals
        lines.append([self.board[i][i] for i in range(3)])
        lines.append([self.board[i][2 - i] for i in range(3)])
        for line in lines:
            if line.count(line[0]) == 3 and line[0] is not None:
                self.winner = line[0]
                self.finished_at = datetime.utcnow()
                return
        # Draw if all filled
        if all(
            cell is not None
            for row in self.board
            for cell in row
        ):
            self.draw = True
            self.finished_at = datetime.utcnow()

    def to_state_response(self) -> GameStateResponse:
        status_msg = (
            f"Player {self.winner} won!"
            if self.winner else
            ("Draw!" if self.draw else f"Next turn: {self.current_turn}")
        )
        return GameStateResponse(
            board=self.board,
            next_turn=None if (self.winner or self.draw) else self.current_turn,
            winner=self.winner,
            draw=self.draw,
            status=status_msg,
            game_id=self.game_id
        )


game_sessions: Dict[str, GameSession] = {}
completed_game_archive: List[GameSession] = []

# ----------------------------------------------------
# FastAPI App Definition
# ----------------------------------------------------

app = FastAPI(
    title="Tic Tac Toe Backend",
    description="REST API for managing tic tac toe games, session management, moves, and game history.",
    version="1.0.0",
    openapi_tags=[
        {"name": "games", "description": "Game session management"},
        {"name": "moves", "description": "Player actions"},
        {"name": "history", "description": "Previous games and results"},
    ]
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Public API Endpoints
# ----------------------------------------------------

@app.get("/", tags=["games"])
def health_check():
    """Check the health of the backend API."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.post(
    "/game",
    response_model=CreateGameResponse,
    summary="Start a new game",
    description="Create a new Tic Tac Toe game session. The creator is always assigned as 'X'.",
    tags=["games"]
)
def create_game(player_name: Optional[str] = Body(None, embed=True)):
    """
    Create a new game session.

    Args:
        player_name (str, optional): Optional player name of the creator.

    Returns:
        CreateGameResponse: Game ID and assigned symbol.
    """
    game = GameSession()
    game.add_player(Player.X, player_name)
    game_sessions[game.game_id] = game
    return CreateGameResponse(game_id=game.game_id, player=Player.X)


# PUBLIC_INTERFACE
@app.post(
    "/game/{game_id}/join",
    response_model=JoinGameResponse,
    summary="Join an existing game",
    description="Join an open Tic Tac Toe game session as Player 'O'.",
    tags=["games"]
)
def join_game(game_id: str, req: JoinGameRequest):
    """
    Join an existing game as Player O.

    Args:
        game_id (str): The session/game ID.
        req (JoinGameRequest): Player name (optional).

    Returns:
        JoinGameResponse
    """
    game = game_sessions.get(game_id)
    if not game or not game.is_open():
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "player": "",
                "message": (
                    "Game not available for joining."
                )
            },
        )
    if game.players[Player.O_] is not None:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "player": "",
                "message": (
                    "Two players already joined."
                )
            },
        )
    game.add_player(Player.O_, req.player_name)
    return JoinGameResponse(
        success=True,
        player="O",
        message="Joined as Player O"
    )



# PUBLIC_INTERFACE
@app.get(
    "/game/{game_id}",
    response_model=GameStateResponse,
    summary="Get game state",
    description="Returns the full game board, whose turn it is, winner, and status.",
    tags=["games"]
)
def get_game_state(game_id: str):
    """
    Retrieve the current state of a specific game.

    Args:
        game_id (str): The session/game ID.

    Returns:
        GameStateResponse: The game board and state.
    """
    game = game_sessions.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")
    return game.to_state_response()


# PUBLIC_INTERFACE
@app.post(
    "/game/{game_id}/move",
    response_model=GameStateResponse,
    summary="Make a move",
    description="Submit a move for the specified game and player.",
    tags=["moves"]
)
def make_move(game_id: str, req: MakeMoveRequest):
    """
    Make a move in the current game session.

    Args:
        game_id (str): The session/game ID.
        req (MakeMoveRequest): The details of the move and player.

    Returns:
        GameStateResponse: Updated board and status.
    """
    game = game_sessions.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")
    try:
        # Accept both "O" and "O_" as Player.O_
        req_player = (
            Player.O_
            if (req.player == "O" or req.player == Player.O_)
            else req.player
        )
        game.make_move(
            req.row,
            req.col,
            req_player
        )

    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    if game.winner or game.draw:
        # Archive the finished game for history
        if all(g.game_id != game.game_id for g in completed_game_archive):
            completed_game_archive.append(game)
    return game.to_state_response()


# PUBLIC_INTERFACE
@app.get(
    "/games/open",
    response_model=List[str],
    summary="List open games",
    description="List all games waiting for a second player to join.",
    tags=["games"]
)
def list_open_games():
    """Get a list of IDs for games open to join."""
    open_gids = [
        gid
        for gid, g in game_sessions.items()
        if g.is_open()
    ]
    return open_gids



# PUBLIC_INTERFACE
@app.get(
    "/history",
    response_model=GameHistoryResponse,
    summary="Get game history",
    description="List the history of completed games (winner, draw status, timestamps).",
    tags=["history"]
)
def get_game_history():
    """Get summary history of finished games."""
    games = [
        GameHistoryEntry(
            game_id=g.game_id,
            started_at=g.started_at,
            finished_at=g.finished_at,
            winner=g.winner,
            draw=g.draw
        )
        for g in completed_game_archive
    ]
    return GameHistoryResponse(games=games)



# PUBLIC_INTERFACE
@app.delete(
    "/game/{game_id}",
    response_model=dict,
    summary="Delete a game",
    description="Delete an open or completed game session from the server. For development/demo only.",
    tags=["games"]
)
def delete_game(game_id: str):
    """Delete a game session forcibly (dev/demo only)."""
    if game_id in game_sessions:
        del game_sessions[game_id]
    for idx, g in enumerate(completed_game_archive):
        if g.game_id == game_id:
            completed_game_archive.pop(idx)
            break
    return {"deleted": True}

# FastAPI auto-generates OpenAPI docs at /docs and /openapi.json

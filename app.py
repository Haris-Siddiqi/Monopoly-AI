from __future__ import annotations

from dataclasses import asdict
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from monopoly.engine import GameEngine, GameRuleError, InsufficientFunds
from monopoly.data import BOARD, PROPERTY_DATA


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

_ENGINE: Optional[GameEngine] = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.post("/api/start")
def start_game(payload: dict) -> dict:
    global _ENGINE
    players = payload.get("players")
    if not isinstance(players, list) or not (2 <= len(players) <= 4):
        raise HTTPException(status_code=400, detail="Provide 2-4 player names.")
    if any(not isinstance(name, str) or not name.strip() for name in players):
        raise HTTPException(status_code=400, detail="Player names must be non-empty strings.")
    _ENGINE = GameEngine([name.strip() for name in players])
    _ENGINE.start_turn()
    return {"ok": True}


@app.get("/api/state")
def get_state() -> dict:
    if _ENGINE is None:
        return {"started": False}
    state = _ENGINE.state
    return {
        "started": True,
        "players": [
            {
                "id": player.player_id,
                "name": player.name,
                "cash": player.cash,
                "position": player.position,
                "in_jail": player.in_jail,
                "bankrupt": player.bankrupt,
            }
            for player in state.players
        ],
        "current_player": state.current_player_index,
        "turn_phase": state.turn_state.phase,
        "pending_property_id": state.turn_state.pending_property_id,
        "last_roll": state.turn_state.last_roll,
        "event_log": state.event_log[-10:],
        "board": [asdict(space) for space in BOARD],
        "properties": {
            str(prop_id): {
                "owner_id": prop_state.owner_id,
                "houses": prop_state.houses,
                "mortgaged": prop_state.mortgaged,
                "name": PROPERTY_DATA[prop_id].name,
            }
            for prop_id, prop_state in state.properties.items()
        },
        "houses_available": state.houses_available,
        "hotels_available": state.hotels_available,
    }


def _require_engine() -> GameEngine:
    if _ENGINE is None:
        raise HTTPException(status_code=400, detail="Game not started.")
    return _ENGINE


def _wrap_action(action_name: str, action) -> dict:
    engine = _require_engine()
    try:
        action(engine)
    except (GameRuleError, InsufficientFunds) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "action": action_name}


@app.post("/api/roll")
def roll_dice() -> dict:
    return _wrap_action("roll", lambda engine: engine.roll_dice())


@app.post("/api/jail/roll")
def jail_roll() -> dict:
    return _wrap_action("jail_roll", lambda engine: engine.attempt_jail_roll())


@app.post("/api/jail/pay")
def jail_pay() -> dict:
    return _wrap_action("jail_pay", lambda engine: engine.pay_jail_fine())


@app.post("/api/buy")
def buy_property() -> dict:
    return _wrap_action("buy", lambda engine: engine.buy_property())


@app.post("/api/decline")
def decline_property() -> dict:
    return _wrap_action("decline", lambda engine: engine.decline_property())


@app.post("/api/end_turn")
def end_turn() -> dict:
    return _wrap_action("end_turn", lambda engine: engine.end_turn())

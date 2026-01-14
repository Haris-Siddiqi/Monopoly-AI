from monopoly.engine import GameEngine, TurnPhase


def test_buy_property_flow():
    engine = GameEngine(["A", "B"], seed=1)
    engine.start_turn()
    player = engine.current_player()
    player.position = 1
    engine._resolve_landing()
    assert engine.state.turn_state.phase == TurnPhase.AWAIT_BUY_DECISION
    engine.buy_property()
    assert engine.state.properties[1].owner_id == player.player_id
    assert player.cash == 1500 - 60
    assert engine.state.turn_state.phase == TurnPhase.TURN_OVER


def test_pass_go_collects_salary():
    engine = GameEngine(["A", "B"], seed=1)
    engine.start_turn()
    player = engine.current_player()
    player.position = 39
    engine._move_current_player(2, collect_go=True)
    assert player.position == 1
    assert player.cash == 1500 + 200


def test_go_to_jail_space():
    engine = GameEngine(["A", "B"], seed=2)
    engine.start_turn()
    player = engine.current_player()
    player.position = 30
    engine._resolve_landing()
    assert player.in_jail is True
    assert player.position == 10

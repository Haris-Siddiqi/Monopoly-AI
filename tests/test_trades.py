from monopoly.engine import GameEngine


def test_trade_offer_acceptance():
    engine = GameEngine(["A", "B"], seed=1)
    engine.start_turn()
    player_a = engine.state.players[0]
    player_b = engine.state.players[1]
    engine.state.properties[1].owner_id = player_a.player_id
    offer = engine.create_trade_offer(
        from_player=player_a.player_id,
        to_player=player_b.player_id,
        give_cash=0,
        give_properties=[1],
        receive_cash=100,
        receive_properties=[],
    )
    engine.accept_trade_offer(offer.offer_id, player_b.player_id)
    assert engine.state.properties[1].owner_id == player_b.player_id
    assert player_a.cash == 1500 + 100
    assert player_b.cash == 1500 - 100

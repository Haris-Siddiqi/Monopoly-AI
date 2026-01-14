import argparse

from monopoly.engine import GameEngine, InsufficientFunds, TurnPhase


def run_simulation(players, turns, seed, auto_buy):
    engine = GameEngine(players, seed=seed)
    engine.start_turn()
    for _ in range(turns):
        player = engine.current_player()
        if player.bankrupt:
            engine.end_turn()
            continue
        if engine.state.turn_state.phase == TurnPhase.AWAIT_JAIL_ACTION:
            engine.attempt_jail_roll()
        if engine.state.turn_state.phase == TurnPhase.AWAIT_ROLL:
            engine.roll_dice()
        if engine.state.turn_state.phase == TurnPhase.AWAIT_BUY_DECISION and auto_buy:
            try:
                engine.buy_property()
            except InsufficientFunds:
                engine.decline_property()
        if engine.state.turn_state.phase == TurnPhase.AWAIT_BUY_DECISION and not auto_buy:
            engine.decline_property()
        while engine.state.turn_state.phase == TurnPhase.AWAIT_AUCTION:
            auction = engine.state.turn_state.pending_auction
            if auction is None:
                break
            for bidder in list(auction.active_bidders):
                if bidder == auction.highest_bidder:
                    continue
                engine.pass_bid(bidder)
        if engine.state.turn_state.phase == TurnPhase.TURN_OVER:
            engine.end_turn()
    return engine


def main():
    parser = argparse.ArgumentParser(description="Run a Monopoly engine simulation.")
    parser.add_argument("--players", nargs="+", required=True)
    parser.add_argument("--turns", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--auto-buy", action="store_true")
    args = parser.parse_args()
    engine = run_simulation(args.players, args.turns, args.seed, args.auto_buy)
    for event in engine.state.event_log[-20:]:
        print(event)
    print("\nFinal cash:")
    for player in engine.state.players:
        print(f"{player.name}: ${player.cash}")


if __name__ == "__main__":
    main()

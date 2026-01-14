from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Card:
    description: str
    action: str
    amount: Optional[int] = None
    destination: Optional[int] = None
    per_house: Optional[int] = None
    per_hotel: Optional[int] = None
    collect_go: bool = True


def standard_chance_cards() -> List[Card]:
    return [
        Card("Advance to GO (Collect $200)", "move", destination=0),
        Card("Advance to Illinois Avenue", "move", destination=24),
        Card("Advance to St. Charles Place", "move", destination=11),
        Card("Advance to nearest Utility", "move_nearest_utility"),
        Card("Advance to nearest Railroad", "move_nearest_railroad"),
        Card("Advance to nearest Railroad", "move_nearest_railroad"),
        Card("Bank pays you dividend of $50", "collect", amount=50),
        Card("Get Out of Jail Free", "get_out_of_jail"),
        Card("Go Back 3 Spaces", "move_back", amount=3, collect_go=False),
        Card("Go to Jail. Go directly to Jail", "go_to_jail"),
        Card("Make general repairs on all your property", "repair", per_house=25, per_hotel=100),
        Card("Pay poor tax of $15", "pay", amount=15),
        Card("Take a trip to Reading Railroad", "move", destination=5),
        Card("Take a walk on the Boardwalk", "move", destination=39),
        Card("You have been elected Chairman of the Board", "pay_each", amount=50),
        Card("Your building loan matures", "collect", amount=150),
    ]


def standard_community_chest_cards() -> List[Card]:
    return [
        Card("Advance to GO (Collect $200)", "move", destination=0),
        Card("Bank error in your favor. Collect $200", "collect", amount=200),
        Card("Doctor's fees. Pay $50", "pay", amount=50),
        Card("From sale of stock you get $50", "collect", amount=50),
        Card("Get Out of Jail Free", "get_out_of_jail"),
        Card("Go to Jail. Go directly to Jail", "go_to_jail"),
        Card("Grand Opera Night. Collect $50 from every player", "collect_each", amount=50),
        Card("Income tax refund. Collect $20", "collect", amount=20),
        Card("Life insurance matures. Collect $100", "collect", amount=100),
        Card("Pay hospital fees of $100", "pay", amount=100),
        Card("Pay school fees of $150", "pay", amount=150),
        Card("Receive $25 consultancy fee", "collect", amount=25),
        Card("You are assessed for street repairs", "repair", per_house=40, per_hotel=115),
        Card("You have won second prize in a beauty contest. Collect $10", "collect", amount=10),
        Card("You inherit $100", "collect", amount=100),
        Card("Holiday fund matures. Receive $100", "collect", amount=100),
    ]

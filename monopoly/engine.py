from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import random

from . import cards
from .data import (
    BOARD,
    GO_SALARY,
    HOUSE_SELL_VALUE,
    JAIL_FINE,
    MAX_HOTELS,
    MAX_HOUSES,
    MORTGAGE_INTEREST_RATE,
    PROPERTY_DATA,
    PROPERTY_GROUPS,
    RAILROADS,
    START_CASH,
    UTILITIES,
    SpaceType,
)


class TurnPhase(str, Enum):
    AWAIT_JAIL_ACTION = "await_jail_action"
    AWAIT_ROLL = "await_roll"
    AWAIT_BUY_DECISION = "await_buy_decision"
    AWAIT_AUCTION = "await_auction"
    TURN_OVER = "turn_over"


@dataclass
class PropertyState:
    owner_id: Optional[int] = None
    houses: int = 0
    mortgaged: bool = False


@dataclass
class Player:
    player_id: int
    name: str
    cash: int = START_CASH
    position: int = 0
    in_jail: bool = False
    jail_turns: int = 0
    get_out_of_jail_cards: List[Tuple[str, cards.Card]] = field(default_factory=list)
    bankrupt: bool = False


@dataclass
class AuctionState:
    property_id: int
    highest_bid: int = 0
    highest_bidder: Optional[int] = None
    active_bidders: Set[int] = field(default_factory=set)


@dataclass
class TradeOffer:
    offer_id: int
    from_player: int
    to_player: Optional[int]
    give_cash: int
    give_properties: List[int]
    receive_cash: int
    receive_properties: List[int]
    status: str = "open"


@dataclass
class TurnState:
    phase: TurnPhase = TurnPhase.AWAIT_ROLL
    pending_property_id: Optional[int] = None
    pending_auction: Optional[AuctionState] = None
    last_roll: Optional[Tuple[int, int]] = None
    doubles_count: int = 0


@dataclass
class GameState:
    players: List[Player]
    properties: Dict[int, PropertyState]
    chance_deck: List[cards.Card]
    community_deck: List[cards.Card]
    current_player_index: int = 0
    turn_state: TurnState = field(default_factory=TurnState)
    trade_offers: Dict[int, TradeOffer] = field(default_factory=dict)
    event_log: List[str] = field(default_factory=list)
    next_offer_id: int = 1
    houses_available: int = MAX_HOUSES
    hotels_available: int = MAX_HOTELS


class GameRuleError(Exception):
    pass


class InsufficientFunds(GameRuleError):
    def __init__(self, player_id: int, amount_due: int):
        super().__init__(f"Player {player_id} has insufficient funds for ${amount_due}.")
        self.player_id = player_id
        self.amount_due = amount_due


class GameEngine:
    def __init__(self, player_names: List[str], seed: Optional[int] = None) -> None:
        if not (2 <= len(player_names) <= 4):
            raise GameRuleError("Game supports 2-4 players.")
        self.random = random.Random(seed)
        players = [Player(player_id=i, name=name) for i, name in enumerate(player_names)]
        properties = {prop_id: PropertyState() for prop_id in PROPERTY_DATA.keys()}
        chance_deck = cards.standard_chance_cards()
        community_deck = cards.standard_community_chest_cards()
        self.random.shuffle(chance_deck)
        self.random.shuffle(community_deck)
        self.state = GameState(players=players, properties=properties, chance_deck=chance_deck, community_deck=community_deck)
        self._log("Game started.")

    def _log(self, message: str) -> None:
        self.state.event_log.append(message)

    def current_player(self) -> Player:
        return self.state.players[self.state.current_player_index]

    def _advance_turn_index(self) -> None:
        total_players = len(self.state.players)
        for _ in range(total_players):
            self.state.current_player_index = (self.state.current_player_index + 1) % total_players
            if not self.current_player().bankrupt:
                return
        raise GameRuleError("No active players remain.")

    def start_turn(self) -> None:
        player = self.current_player()
        if player.bankrupt:
            self._advance_turn_index()
            player = self.current_player()
        if player.in_jail:
            self.state.turn_state = TurnState(phase=TurnPhase.AWAIT_JAIL_ACTION)
        else:
            self.state.turn_state = TurnState(phase=TurnPhase.AWAIT_ROLL)
        self._log(f"Turn started for {player.name}.")

    def roll_dice(self) -> Tuple[int, int]:
        if self.state.turn_state.phase != TurnPhase.AWAIT_ROLL:
            raise GameRuleError("Not ready to roll dice.")
        die1 = self.random.randint(1, 6)
        die2 = self.random.randint(1, 6)
        self.state.turn_state.last_roll = (die1, die2)
        self._log(f"{self.current_player().name} rolled {die1} and {die2}.")
        if die1 == die2:
            self.state.turn_state.doubles_count += 1
            if self.state.turn_state.doubles_count == 3:
                self.send_player_to_jail(self.current_player().player_id)
                self.state.turn_state.phase = TurnPhase.TURN_OVER
                return die1, die2
        self._move_current_player(die1 + die2, collect_go=True)
        self._resolve_landing()
        return die1, die2

    def attempt_jail_roll(self) -> Tuple[int, int]:
        if self.state.turn_state.phase != TurnPhase.AWAIT_JAIL_ACTION:
            raise GameRuleError("Not awaiting jail action.")
        player = self.current_player()
        die1 = self.random.randint(1, 6)
        die2 = self.random.randint(1, 6)
        self._log(f"{player.name} rolled {die1} and {die2} in jail.")
        if die1 == die2:
            player.in_jail = False
            player.jail_turns = 0
            self.state.turn_state = TurnState(phase=TurnPhase.AWAIT_ROLL)
            self._move_current_player(die1 + die2, collect_go=True)
            self._resolve_landing()
            return die1, die2
        player.jail_turns += 1
        if player.jail_turns >= 3:
            self._pay_bank(player.player_id, JAIL_FINE)
            player.in_jail = False
            player.jail_turns = 0
            self.state.turn_state = TurnState(phase=TurnPhase.AWAIT_ROLL)
            self._move_current_player(die1 + die2, collect_go=True)
            self._resolve_landing()
        return die1, die2

    def pay_jail_fine(self) -> None:
        if self.state.turn_state.phase != TurnPhase.AWAIT_JAIL_ACTION:
            raise GameRuleError("Not awaiting jail action.")
        player = self.current_player()
        self._pay_bank(player.player_id, JAIL_FINE)
        player.in_jail = False
        player.jail_turns = 0
        self.state.turn_state.phase = TurnPhase.AWAIT_ROLL

    def use_get_out_of_jail_card(self, deck_name: str) -> None:
        player = self.current_player()
        for idx, (name, card) in enumerate(player.get_out_of_jail_cards):
            if name == deck_name:
                player.get_out_of_jail_cards.pop(idx)
                if deck_name == "chance":
                    self.state.chance_deck.append(card)
                else:
                    self.state.community_deck.append(card)
                player.in_jail = False
                player.jail_turns = 0
                self.state.turn_state.phase = TurnPhase.AWAIT_ROLL
                self._log(f"{player.name} used a Get Out of Jail Free card.")
                return
        raise GameRuleError("No matching Get Out of Jail Free card.")

    def buy_property(self) -> None:
        if self.state.turn_state.phase != TurnPhase.AWAIT_BUY_DECISION:
            raise GameRuleError("No property available to buy.")
        player = self.current_player()
        prop_id = self.state.turn_state.pending_property_id
        if prop_id is None:
            raise GameRuleError("No property pending.")
        prop_data = PROPERTY_DATA[prop_id]
        self._pay_bank(player.player_id, prop_data.price)
        self.state.properties[prop_id].owner_id = player.player_id
        self.state.turn_state.pending_property_id = None
        self.state.turn_state.phase = TurnPhase.TURN_OVER
        self._log(f"{player.name} bought {prop_data.name} for ${prop_data.price}.")

    def decline_property(self) -> None:
        if self.state.turn_state.phase != TurnPhase.AWAIT_BUY_DECISION:
            raise GameRuleError("No property to decline.")
        prop_id = self.state.turn_state.pending_property_id
        if prop_id is None:
            raise GameRuleError("No property pending.")
        auction = AuctionState(property_id=prop_id)
        auction.active_bidders = {p.player_id for p in self.state.players if not p.bankrupt}
        self.state.turn_state.pending_property_id = None
        self.state.turn_state.pending_auction = auction
        self.state.turn_state.phase = TurnPhase.AWAIT_AUCTION
        self._log(f"Auction started for {PROPERTY_DATA[prop_id].name}.")

    def place_bid(self, player_id: int, amount: int) -> None:
        if self.state.turn_state.phase != TurnPhase.AWAIT_AUCTION:
            raise GameRuleError("No auction running.")
        auction = self.state.turn_state.pending_auction
        if auction is None:
            raise GameRuleError("No auction state.")
        if player_id not in auction.active_bidders:
            raise GameRuleError("Player not in auction.")
        player = self.state.players[player_id]
        if player.cash < amount:
            raise InsufficientFunds(player_id, amount)
        if amount <= auction.highest_bid:
            raise GameRuleError("Bid must exceed highest bid.")
        auction.highest_bid = amount
        auction.highest_bidder = player_id
        self._log(f"{player.name} bid ${amount}.")

    def pass_bid(self, player_id: int) -> None:
        if self.state.turn_state.phase != TurnPhase.AWAIT_AUCTION:
            raise GameRuleError("No auction running.")
        auction = self.state.turn_state.pending_auction
        if auction is None:
            raise GameRuleError("No auction state.")
        auction.active_bidders.discard(player_id)
        self._log(f"Player {player_id} passed in auction.")
        if len(auction.active_bidders) <= 1:
            self._finalize_auction(auction)

    def _finalize_auction(self, auction: AuctionState) -> None:
        if auction.highest_bidder is not None:
            winner = self.state.players[auction.highest_bidder]
            self._pay_bank(winner.player_id, auction.highest_bid)
            self.state.properties[auction.property_id].owner_id = winner.player_id
            self._log(f"{winner.name} won auction for ${auction.highest_bid}.")
        else:
            self._log("Auction ended with no bids.")
        self.state.turn_state.pending_auction = None
        self.state.turn_state.phase = TurnPhase.TURN_OVER

    def create_trade_offer(
        self,
        from_player: int,
        to_player: Optional[int],
        give_cash: int,
        give_properties: List[int],
        receive_cash: int,
        receive_properties: List[int],
    ) -> TradeOffer:
        self._validate_trade_assets(from_player, give_cash, give_properties)
        offer = TradeOffer(
            offer_id=self.state.next_offer_id,
            from_player=from_player,
            to_player=to_player,
            give_cash=give_cash,
            give_properties=give_properties,
            receive_cash=receive_cash,
            receive_properties=receive_properties,
        )
        self.state.trade_offers[offer.offer_id] = offer
        self.state.next_offer_id += 1
        self._log(f"Trade offer {offer.offer_id} created by player {from_player}.")
        return offer

    def cancel_trade_offer(self, offer_id: int, player_id: int) -> None:
        offer = self._get_offer(offer_id)
        if offer.from_player != player_id:
            raise GameRuleError("Only offer creator can cancel.")
        offer.status = "cancelled"
        self._log(f"Trade offer {offer_id} cancelled.")

    def accept_trade_offer(self, offer_id: int, accepting_player: int) -> None:
        offer = self._get_offer(offer_id)
        if offer.status != "open":
            raise GameRuleError("Offer is not open.")
        if offer.to_player is not None and offer.to_player != accepting_player:
            raise GameRuleError("Offer not addressed to this player.")
        self._validate_trade_assets(offer.from_player, offer.give_cash, offer.give_properties)
        self._validate_trade_assets(accepting_player, offer.receive_cash, offer.receive_properties)
        self._transfer_cash(offer.from_player, accepting_player, offer.give_cash)
        self._transfer_cash(accepting_player, offer.from_player, offer.receive_cash)
        self._transfer_properties(offer.from_player, accepting_player, offer.give_properties)
        self._transfer_properties(accepting_player, offer.from_player, offer.receive_properties)
        offer.status = "accepted"
        self._log(f"Trade offer {offer_id} accepted by player {accepting_player}.")

    def mortgage_property(self, player_id: int, property_id: int) -> None:
        self._require_owner(player_id, property_id)
        prop_state = self.state.properties[property_id]
        if prop_state.mortgaged:
            raise GameRuleError("Property already mortgaged.")
        if self._group_has_houses(property_id):
            raise GameRuleError("Cannot mortgage while houses exist in group.")
        mortgage_value = PROPERTY_DATA[property_id].mortgage
        prop_state.mortgaged = True
        self.state.players[player_id].cash += mortgage_value
        self._log(f"Player {player_id} mortgaged {PROPERTY_DATA[property_id].name} for ${mortgage_value}.")

    def unmortgage_property(self, player_id: int, property_id: int) -> None:
        self._require_owner(player_id, property_id)
        prop_state = self.state.properties[property_id]
        if not prop_state.mortgaged:
            raise GameRuleError("Property is not mortgaged.")
        cost = int(PROPERTY_DATA[property_id].mortgage * (1 + MORTGAGE_INTEREST_RATE))
        self._pay_bank(player_id, cost)
        prop_state.mortgaged = False
        self._log(f"Player {player_id} unmortgaged {PROPERTY_DATA[property_id].name} for ${cost}.")

    def build_house(self, player_id: int, property_id: int) -> None:
        self._require_owner(player_id, property_id)
        prop_data = PROPERTY_DATA[property_id]
        if prop_data.type != SpaceType.PROPERTY:
            raise GameRuleError("Can only build on color properties.")
        if not self._owns_group(player_id, prop_data.color):
            raise GameRuleError("Must own full color group to build.")
        if self._group_has_mortgage(prop_data.color):
            raise GameRuleError("Cannot build with mortgaged property in group.")
        prop_state = self.state.properties[property_id]
        if prop_state.houses >= 5:
            raise GameRuleError("Property already has a hotel.")
        if not self._can_build_evenly(property_id):
            raise GameRuleError("Must build evenly across the group.")
        if prop_state.houses == 4:
            if self.state.hotels_available < 1:
                raise GameRuleError("No hotels available.")
        else:
            if self.state.houses_available < 1:
                raise GameRuleError("No houses available.")
        self._pay_bank(player_id, prop_data.house_cost or 0)
        if prop_state.houses == 4:
            self.state.hotels_available -= 1
            self.state.houses_available = min(MAX_HOUSES, self.state.houses_available + 4)
            prop_state.houses = 5
        else:
            self.state.houses_available -= 1
            prop_state.houses += 1
        self._log(f"Player {player_id} built on {prop_data.name}.")

    def sell_house(self, player_id: int, property_id: int) -> None:
        self._require_owner(player_id, property_id)
        prop_data = PROPERTY_DATA[property_id]
        prop_state = self.state.properties[property_id]
        if prop_state.houses == 0:
            raise GameRuleError("No houses to sell.")
        if not self._can_sell_evenly(property_id):
            raise GameRuleError("Must sell evenly across the group.")
        if prop_state.houses == 5:
            if self.state.houses_available < 4:
                raise GameRuleError("Not enough houses available to sell a hotel.")
            prop_state.houses = 4
            self.state.hotels_available = min(MAX_HOTELS, self.state.hotels_available + 1)
            self.state.houses_available -= 4
            sale_value = int((prop_data.house_cost or 0) * 5 * HOUSE_SELL_VALUE)
        else:
            prop_state.houses -= 1
            self.state.houses_available = min(MAX_HOUSES, self.state.houses_available + 1)
            sale_value = int((prop_data.house_cost or 0) * HOUSE_SELL_VALUE)
        self.state.players[player_id].cash += sale_value
        self._log(f"Player {player_id} sold a house on {prop_data.name} for ${sale_value}.")

    def declare_bankruptcy(self, player_id: int, creditor_id: Optional[int] = None) -> None:
        player = self.state.players[player_id]
        if player.bankrupt:
            raise GameRuleError("Player already bankrupt.")
        self._liquidate_houses(player_id)
        if creditor_id is not None:
            creditor = self.state.players[creditor_id]
            creditor.cash += player.cash
            player.cash = 0
            for prop_id, prop_state in self.state.properties.items():
                if prop_state.owner_id == player_id:
                    prop_state.owner_id = creditor_id
                    self._handle_mortgage_transfer(creditor_id, prop_id)
            self._log(f"Player {player_id} bankrupt to player {creditor_id}.")
        else:
            for prop_id, prop_state in self.state.properties.items():
                if prop_state.owner_id == player_id:
                    prop_state.owner_id = None
                    prop_state.mortgaged = False
                    prop_state.houses = 0
            self._log(f"Player {player_id} bankrupt to bank.")
        player.bankrupt = True
        player.in_jail = False

    def end_turn(self) -> None:
        if self.state.turn_state.phase != TurnPhase.TURN_OVER:
            raise GameRuleError("Turn not complete.")
        if self.state.turn_state.doubles_count > 0 and not self.current_player().in_jail:
            self.state.turn_state = TurnState(phase=TurnPhase.AWAIT_ROLL)
            self._log(f"{self.current_player().name} rolls again for doubles.")
            return
        self._advance_turn_index()
        self.start_turn()

    def send_player_to_jail(self, player_id: int) -> None:
        player = self.state.players[player_id]
        player.position = 10
        player.in_jail = True
        player.jail_turns = 0
        self._log(f"{player.name} sent to jail.")

    def _move_current_player(self, steps: int, collect_go: bool) -> None:
        player = self.current_player()
        start = player.position
        new_pos = (start + steps) % len(BOARD)
        if collect_go and (start + steps) >= len(BOARD):
            player.cash += GO_SALARY
            self._log(f"{player.name} collected ${GO_SALARY} for passing GO.")
        player.position = new_pos

    def _move_player_to(self, player_id: int, destination: int, collect_go: bool) -> None:
        player = self.state.players[player_id]
        if collect_go and destination < player.position:
            player.cash += GO_SALARY
            self._log(f"{player.name} collected ${GO_SALARY} for passing GO.")
        player.position = destination

    def _resolve_landing(self) -> None:
        player = self.current_player()
        space = BOARD[player.position]
        if space.type in (SpaceType.PROPERTY, SpaceType.RAILROAD, SpaceType.UTILITY):
            prop_id = space.property_id
            if prop_id is None:
                return
            prop_state = self.state.properties[prop_id]
            if prop_state.owner_id is None:
                self.state.turn_state.phase = TurnPhase.AWAIT_BUY_DECISION
                self.state.turn_state.pending_property_id = prop_id
                return
            if prop_state.owner_id != player.player_id and not prop_state.mortgaged:
                rent = self._calculate_rent(prop_id, player.player_id)
                self._pay_player(player.player_id, prop_state.owner_id, rent)
            self.state.turn_state.phase = TurnPhase.TURN_OVER
        elif space.type == SpaceType.CHANCE:
            self._draw_card("chance")
        elif space.type == SpaceType.COMMUNITY_CHEST:
            self._draw_card("community")
        elif space.type == SpaceType.TAX:
            self._pay_bank(player.player_id, space.tax_amount or 0)
            self.state.turn_state.phase = TurnPhase.TURN_OVER
        elif space.type == SpaceType.GO_TO_JAIL:
            self.send_player_to_jail(player.player_id)
            self.state.turn_state.phase = TurnPhase.TURN_OVER
        else:
            self.state.turn_state.phase = TurnPhase.TURN_OVER

    def _draw_card(self, deck_name: str) -> None:
        deck = self.state.chance_deck if deck_name == "chance" else self.state.community_deck
        card = deck.pop(0)
        player = self.current_player()
        self._log(f"{player.name} drew card: {card.description}.")
        if card.action == "get_out_of_jail":
            player.get_out_of_jail_cards.append((deck_name, card))
            self._log(f"{player.name} kept a Get Out of Jail Free card.")
        else:
            deck.append(card)
            self._apply_card(card, player.player_id)
        if self.state.turn_state.phase != TurnPhase.AWAIT_BUY_DECISION:
            self.state.turn_state.phase = TurnPhase.TURN_OVER

    def _apply_card(self, card: cards.Card, player_id: int) -> None:
        if card.action == "move":
            self._move_player_to(player_id, card.destination or 0, collect_go=card.collect_go)
            self._resolve_landing()
        elif card.action == "move_nearest_railroad":
            destination = self._find_nearest(player_id, RAILROADS)
            self._move_player_to(player_id, destination, collect_go=True)
            self._resolve_landing_with_rent_multiplier(2)
        elif card.action == "move_nearest_utility":
            destination = self._find_nearest(player_id, UTILITIES)
            self._move_player_to(player_id, destination, collect_go=True)
            self._resolve_landing_with_utility_multiplier(10)
        elif card.action == "move_back":
            player = self.state.players[player_id]
            player.position = (player.position - (card.amount or 0)) % len(BOARD)
            self._resolve_landing()
        elif card.action == "collect":
            self.state.players[player_id].cash += card.amount or 0
        elif card.action == "pay":
            self._pay_bank(player_id, card.amount or 0)
        elif card.action == "pay_each":
            for other in self.state.players:
                if other.player_id != player_id and not other.bankrupt:
                    self._pay_player(player_id, other.player_id, card.amount or 0)
        elif card.action == "collect_each":
            total = 0
            for other in self.state.players:
                if other.player_id != player_id and not other.bankrupt:
                    self._pay_player(other.player_id, player_id, card.amount or 0)
                    total += card.amount or 0
        elif card.action == "go_to_jail":
            self.send_player_to_jail(player_id)
        elif card.action == "repair":
            house_count, hotel_count = self._count_houses_hotels(player_id)
            cost = (card.per_house or 0) * house_count + (card.per_hotel or 0) * hotel_count
            self._pay_bank(player_id, cost)

    def _resolve_landing_with_rent_multiplier(self, multiplier: int) -> None:
        player = self.current_player()
        space = BOARD[player.position]
        if space.property_id is None:
            return
        prop_state = self.state.properties[space.property_id]
        if prop_state.owner_id is not None and prop_state.owner_id != player.player_id:
            rent = self._calculate_rent(space.property_id, player.player_id)
            self._pay_player(player.player_id, prop_state.owner_id, rent * multiplier)
            self.state.turn_state.phase = TurnPhase.TURN_OVER
        elif prop_state.owner_id is None:
            self.state.turn_state.phase = TurnPhase.AWAIT_BUY_DECISION
            self.state.turn_state.pending_property_id = space.property_id

    def _resolve_landing_with_utility_multiplier(self, multiplier: int) -> None:
        player = self.current_player()
        space = BOARD[player.position]
        if space.property_id is None:
            return
        prop_state = self.state.properties[space.property_id]
        if prop_state.owner_id is not None and prop_state.owner_id != player.player_id:
            last_roll = self.state.turn_state.last_roll or (0, 0)
            dice_sum = sum(last_roll)
            self._pay_player(player.player_id, prop_state.owner_id, dice_sum * multiplier)
            self.state.turn_state.phase = TurnPhase.TURN_OVER
        elif prop_state.owner_id is None:
            self.state.turn_state.phase = TurnPhase.AWAIT_BUY_DECISION
            self.state.turn_state.pending_property_id = space.property_id

    def _calculate_rent(self, property_id: int, tenant_id: int) -> int:
        prop_data = PROPERTY_DATA[property_id]
        prop_state = self.state.properties[property_id]
        owner_id = prop_state.owner_id
        if owner_id is None or owner_id == tenant_id:
            return 0
        if prop_data.type == SpaceType.RAILROAD:
            count = self._count_owned(owner_id, RAILROADS)
            return prop_data.rents[count - 1]
        if prop_data.type == SpaceType.UTILITY:
            count = self._count_owned(owner_id, UTILITIES)
            multiplier = 10 if count == 2 else 4
            dice_sum = sum(self.state.turn_state.last_roll or (0, 0))
            return dice_sum * multiplier
        rent_index = prop_state.houses
        rent = prop_data.rents[rent_index]
        if prop_state.houses == 0 and self._owns_group(owner_id, prop_data.color):
            rent *= 2
        return rent

    def _pay_bank(self, player_id: int, amount: int) -> None:
        if amount <= 0:
            return
        player = self.state.players[player_id]
        if player.cash < amount:
            raise InsufficientFunds(player_id, amount)
        player.cash -= amount

    def _pay_player(self, from_player: int, to_player: int, amount: int) -> None:
        if amount <= 0:
            return
        payer = self.state.players[from_player]
        if payer.cash < amount:
            raise InsufficientFunds(from_player, amount)
        payer.cash -= amount
        self.state.players[to_player].cash += amount

    def _transfer_cash(self, from_player: int, to_player: int, amount: int) -> None:
        if amount <= 0:
            return
        payer = self.state.players[from_player]
        if payer.cash < amount:
            raise InsufficientFunds(from_player, amount)
        payer.cash -= amount
        self.state.players[to_player].cash += amount

    def _transfer_properties(self, from_player: int, to_player: int, property_ids: List[int]) -> None:
        for prop_id in property_ids:
            self._require_owner(from_player, prop_id)
            self.state.properties[prop_id].owner_id = to_player
            self._handle_mortgage_transfer(to_player, prop_id)

    def _handle_mortgage_transfer(self, new_owner_id: int, property_id: int) -> None:
        prop_state = self.state.properties[property_id]
        if prop_state.mortgaged:
            interest = int(PROPERTY_DATA[property_id].mortgage * MORTGAGE_INTEREST_RATE)
            self._pay_bank(new_owner_id, interest)

    def _validate_trade_assets(self, player_id: int, cash: int, properties: List[int]) -> None:
        player = self.state.players[player_id]
        if player.cash < cash:
            raise InsufficientFunds(player_id, cash)
        for prop_id in properties:
            self._require_owner(player_id, prop_id)

    def _require_owner(self, player_id: int, property_id: int) -> None:
        if self.state.properties[property_id].owner_id != player_id:
            raise GameRuleError("Player does not own the property.")

    def _owns_group(self, player_id: int, color: Optional[str]) -> bool:
        if color is None:
            return False
        return all(self.state.properties[prop_id].owner_id == player_id for prop_id in PROPERTY_GROUPS[color])

    def _group_has_houses(self, property_id: int) -> bool:
        color = PROPERTY_DATA[property_id].color
        if color is None:
            return False
        return any(self.state.properties[prop_id].houses > 0 for prop_id in PROPERTY_GROUPS[color])

    def _group_has_mortgage(self, color: Optional[str]) -> bool:
        if color is None:
            return False
        return any(self.state.properties[prop_id].mortgaged for prop_id in PROPERTY_GROUPS[color])

    def _can_build_evenly(self, property_id: int) -> bool:
        color = PROPERTY_DATA[property_id].color
        if color is None:
            return False
        houses = [self.state.properties[prop].houses for prop in PROPERTY_GROUPS[color]]
        target = self.state.properties[property_id].houses
        return target <= min(houses)

    def _can_sell_evenly(self, property_id: int) -> bool:
        color = PROPERTY_DATA[property_id].color
        if color is None:
            return False
        houses = [self.state.properties[prop].houses for prop in PROPERTY_GROUPS[color]]
        target = self.state.properties[property_id].houses
        return target >= max(houses)

    def _count_owned(self, player_id: int, prop_ids: List[int]) -> int:
        return sum(1 for prop_id in prop_ids if self.state.properties[prop_id].owner_id == player_id and not self.state.properties[prop_id].mortgaged)

    def _find_nearest(self, player_id: int, targets: List[int]) -> int:
        player = self.state.players[player_id]
        position = player.position
        distances = sorted(((target - position) % len(BOARD), target) for target in targets)
        return distances[0][1]

    def _count_houses_hotels(self, player_id: int) -> Tuple[int, int]:
        houses = 0
        hotels = 0
        for prop_id, prop_state in self.state.properties.items():
            if prop_state.owner_id == player_id:
                if prop_state.houses == 5:
                    hotels += 1
                else:
                    houses += prop_state.houses
        return houses, hotels

    def _liquidate_houses(self, player_id: int) -> None:
        for prop_id, prop_state in self.state.properties.items():
            if prop_state.owner_id == player_id and prop_state.houses > 0:
                prop_data = PROPERTY_DATA[prop_id]
                if prop_state.houses == 5:
                    sale_value = int((prop_data.house_cost or 0) * 5 * HOUSE_SELL_VALUE)
                    self.state.hotels_available = min(MAX_HOTELS, self.state.hotels_available + 1)
                    self.state.houses_available = min(MAX_HOUSES, self.state.houses_available + 4)
                    self.state.players[player_id].cash += sale_value
                else:
                    sale_value = int((prop_data.house_cost or 0) * HOUSE_SELL_VALUE)
                    self.state.houses_available = min(MAX_HOUSES, self.state.houses_available + prop_state.houses)
                    self.state.players[player_id].cash += sale_value * prop_state.houses
                prop_state.houses = 0

    def _get_offer(self, offer_id: int) -> TradeOffer:
        if offer_id not in self.state.trade_offers:
            raise GameRuleError("Offer not found.")
        return self.state.trade_offers[offer_id]

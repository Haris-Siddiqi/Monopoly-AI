from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class SpaceType(str, Enum):
    GO = "go"
    PROPERTY = "property"
    RAILROAD = "railroad"
    UTILITY = "utility"
    CHANCE = "chance"
    COMMUNITY_CHEST = "community_chest"
    TAX = "tax"
    JAIL = "jail"
    FREE_PARKING = "free_parking"
    GO_TO_JAIL = "go_to_jail"


@dataclass(frozen=True)
class Space:
    name: str
    type: SpaceType
    property_id: Optional[int] = None
    tax_amount: Optional[int] = None


@dataclass(frozen=True)
class PropertyData:
    name: str
    color: Optional[str]
    price: int
    rents: List[int]
    house_cost: Optional[int]
    mortgage: int
    type: SpaceType


BOARD: List[Space] = [
    Space("GO", SpaceType.GO),
    Space("Mediterranean Avenue", SpaceType.PROPERTY, property_id=1),
    Space("Community Chest", SpaceType.COMMUNITY_CHEST),
    Space("Baltic Avenue", SpaceType.PROPERTY, property_id=3),
    Space("Income Tax", SpaceType.TAX, tax_amount=200),
    Space("Reading Railroad", SpaceType.RAILROAD, property_id=5),
    Space("Oriental Avenue", SpaceType.PROPERTY, property_id=6),
    Space("Chance", SpaceType.CHANCE),
    Space("Vermont Avenue", SpaceType.PROPERTY, property_id=8),
    Space("Connecticut Avenue", SpaceType.PROPERTY, property_id=9),
    Space("Jail / Just Visiting", SpaceType.JAIL),
    Space("St. Charles Place", SpaceType.PROPERTY, property_id=11),
    Space("Electric Company", SpaceType.UTILITY, property_id=12),
    Space("States Avenue", SpaceType.PROPERTY, property_id=13),
    Space("Virginia Avenue", SpaceType.PROPERTY, property_id=14),
    Space("Pennsylvania Railroad", SpaceType.RAILROAD, property_id=15),
    Space("St. James Place", SpaceType.PROPERTY, property_id=16),
    Space("Community Chest", SpaceType.COMMUNITY_CHEST),
    Space("Tennessee Avenue", SpaceType.PROPERTY, property_id=18),
    Space("New York Avenue", SpaceType.PROPERTY, property_id=19),
    Space("Free Parking", SpaceType.FREE_PARKING),
    Space("Kentucky Avenue", SpaceType.PROPERTY, property_id=21),
    Space("Chance", SpaceType.CHANCE),
    Space("Indiana Avenue", SpaceType.PROPERTY, property_id=23),
    Space("Illinois Avenue", SpaceType.PROPERTY, property_id=24),
    Space("B. & O. Railroad", SpaceType.RAILROAD, property_id=25),
    Space("Atlantic Avenue", SpaceType.PROPERTY, property_id=26),
    Space("Ventnor Avenue", SpaceType.PROPERTY, property_id=27),
    Space("Water Works", SpaceType.UTILITY, property_id=28),
    Space("Marvin Gardens", SpaceType.PROPERTY, property_id=29),
    Space("Go To Jail", SpaceType.GO_TO_JAIL),
    Space("Pacific Avenue", SpaceType.PROPERTY, property_id=31),
    Space("North Carolina Avenue", SpaceType.PROPERTY, property_id=32),
    Space("Community Chest", SpaceType.COMMUNITY_CHEST),
    Space("Pennsylvania Avenue", SpaceType.PROPERTY, property_id=34),
    Space("Short Line", SpaceType.RAILROAD, property_id=35),
    Space("Chance", SpaceType.CHANCE),
    Space("Park Place", SpaceType.PROPERTY, property_id=37),
    Space("Luxury Tax", SpaceType.TAX, tax_amount=100),
    Space("Boardwalk", SpaceType.PROPERTY, property_id=39),
]


PROPERTY_DATA: Dict[int, PropertyData] = {
    1: PropertyData("Mediterranean Avenue", "brown", 60, [2, 10, 30, 90, 160, 250], 50, 30, SpaceType.PROPERTY),
    3: PropertyData("Baltic Avenue", "brown", 60, [4, 20, 60, 180, 320, 450], 50, 30, SpaceType.PROPERTY),
    5: PropertyData("Reading Railroad", None, 200, [25, 50, 100, 200], None, 100, SpaceType.RAILROAD),
    6: PropertyData("Oriental Avenue", "light_blue", 100, [6, 30, 90, 270, 400, 550], 50, 50, SpaceType.PROPERTY),
    8: PropertyData("Vermont Avenue", "light_blue", 100, [6, 30, 90, 270, 400, 550], 50, 50, SpaceType.PROPERTY),
    9: PropertyData("Connecticut Avenue", "light_blue", 120, [8, 40, 100, 300, 450, 600], 50, 60, SpaceType.PROPERTY),
    11: PropertyData("St. Charles Place", "pink", 140, [10, 50, 150, 450, 625, 750], 100, 70, SpaceType.PROPERTY),
    12: PropertyData("Electric Company", None, 150, [4, 10], None, 75, SpaceType.UTILITY),
    13: PropertyData("States Avenue", "pink", 140, [10, 50, 150, 450, 625, 750], 100, 70, SpaceType.PROPERTY),
    14: PropertyData("Virginia Avenue", "pink", 160, [12, 60, 180, 500, 700, 900], 100, 80, SpaceType.PROPERTY),
    15: PropertyData("Pennsylvania Railroad", None, 200, [25, 50, 100, 200], None, 100, SpaceType.RAILROAD),
    16: PropertyData("St. James Place", "orange", 180, [14, 70, 200, 550, 750, 950], 100, 90, SpaceType.PROPERTY),
    18: PropertyData("Tennessee Avenue", "orange", 180, [14, 70, 200, 550, 750, 950], 100, 90, SpaceType.PROPERTY),
    19: PropertyData("New York Avenue", "orange", 200, [16, 80, 220, 600, 800, 1000], 100, 100, SpaceType.PROPERTY),
    21: PropertyData("Kentucky Avenue", "red", 220, [18, 90, 250, 700, 875, 1050], 150, 110, SpaceType.PROPERTY),
    23: PropertyData("Indiana Avenue", "red", 220, [18, 90, 250, 700, 875, 1050], 150, 110, SpaceType.PROPERTY),
    24: PropertyData("Illinois Avenue", "red", 240, [20, 100, 300, 750, 925, 1100], 150, 120, SpaceType.PROPERTY),
    25: PropertyData("B. & O. Railroad", None, 200, [25, 50, 100, 200], None, 100, SpaceType.RAILROAD),
    26: PropertyData("Atlantic Avenue", "yellow", 260, [22, 110, 330, 800, 975, 1150], 150, 130, SpaceType.PROPERTY),
    27: PropertyData("Ventnor Avenue", "yellow", 260, [22, 110, 330, 800, 975, 1150], 150, 130, SpaceType.PROPERTY),
    28: PropertyData("Water Works", None, 150, [4, 10], None, 75, SpaceType.UTILITY),
    29: PropertyData("Marvin Gardens", "yellow", 280, [24, 120, 360, 850, 1025, 1200], 150, 140, SpaceType.PROPERTY),
    31: PropertyData("Pacific Avenue", "green", 300, [26, 130, 390, 900, 1100, 1275], 200, 150, SpaceType.PROPERTY),
    32: PropertyData("North Carolina Avenue", "green", 300, [26, 130, 390, 900, 1100, 1275], 200, 150, SpaceType.PROPERTY),
    34: PropertyData("Pennsylvania Avenue", "green", 320, [28, 150, 450, 1000, 1200, 1400], 200, 160, SpaceType.PROPERTY),
    35: PropertyData("Short Line", None, 200, [25, 50, 100, 200], None, 100, SpaceType.RAILROAD),
    37: PropertyData("Park Place", "dark_blue", 350, [35, 175, 500, 1100, 1300, 1500], 200, 175, SpaceType.PROPERTY),
    39: PropertyData("Boardwalk", "dark_blue", 400, [50, 200, 600, 1400, 1700, 2000], 200, 200, SpaceType.PROPERTY),
}


PROPERTY_GROUPS: Dict[str, List[int]] = {
    "brown": [1, 3],
    "light_blue": [6, 8, 9],
    "pink": [11, 13, 14],
    "orange": [16, 18, 19],
    "red": [21, 23, 24],
    "yellow": [26, 27, 29],
    "green": [31, 32, 34],
    "dark_blue": [37, 39],
}


RAILROADS = [5, 15, 25, 35]
UTILITIES = [12, 28]


START_CASH = 1500
GO_SALARY = 200
JAIL_FINE = 50
HOUSE_SELL_VALUE = 0.5
MORTGAGE_INTEREST_RATE = 0.1
MAX_HOUSES = 32
MAX_HOTELS = 12

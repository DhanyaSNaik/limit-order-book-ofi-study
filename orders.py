from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


@dataclass
class Order:
    order_id: str
    side: Side
    order_type: OrderType
    quantity: int
    price: Optional[float] = None
    timestamp: int = 0 
    # informational only — FIFO priority is determined by insertion order into the book's deque, not by this field

    remaining: Optional[int] = None

    def __post_init__(self):
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders require a price")

        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")

        if self.order_type == OrderType.MARKET:
            self.price = None

        self.remaining = self.quantity


@dataclass
class Trade:
    buy_order_id: str
    sell_order_id: str
    price: float
    quantity: int


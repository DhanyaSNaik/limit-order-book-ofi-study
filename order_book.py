from collections import deque
from orders import Side, Order


class OrderBook:
    def __init__(self):
        self.bids = {}
        self.asks = {}
        self.order_map = {}
        self._ledger_qty = {} 

    def add_order(self, order: Order):
        if order.order_id in self.order_map:
            raise ValueError(f"Duplicate order_id: {order.order_id}")

        levels = self.bids if order.side == Side.BUY else self.asks

        if order.price not in levels:
            levels[order.price] = deque()

        levels[order.price].append(order)
        self.order_map[order.order_id] = order

        key = (order.side, order.price)
        self._ledger_qty[key] = self._ledger_qty.get(key, 0) + order.remaining

    def remove_order(self, order_id):
        order = self.order_map.get(order_id)

        if order is None:
            return False

        levels = self.bids if order.side == Side.BUY else self.asks
        queue = levels[order.price]

        queue.remove(order)

        key = (order.side, order.price)
        self._ledger_qty[key] = self._ledger_qty.get(key, 0) - order.remaining

        if not queue:
            del levels[order.price]

        del self.order_map[order_id]

        return True
        
    def reduce_order(self, order_id, quantity):
        order = self.order_map.get(order_id)
        if order is None:
            return

        order.remaining -= quantity

        key = (order.side, order.price)
        self._ledger_qty[key] = self._ledger_qty.get(key, 0) - quantity

    def best_bid(self):
        if not self.bids:
            return None

        return max(self.bids.keys())

    def best_ask(self):
        if not self.asks:
            return None

        return min(self.asks.keys())

    def spread(self):
        bid = self.best_bid()
        ask = self.best_ask()

        if bid is None or ask is None:
            return None

        return ask - bid

    def midprice(self):
        bid = self.best_bid()
        ask = self.best_ask()

        if bid is None or ask is None:
            return None

        return (bid + ask) / 2

    def total_quantity_at_price(self, side, price):
        levels = self.bids if side == Side.BUY else self.asks

        if price not in levels:
            return 0

        return sum(order.remaining for order in levels[price])

    def ledger_quantity_at_price(self, side, price):
        return self._ledger_qty.get((side, price), 0)

    def all_orders(self):
        return list(self.order_map.values())
        

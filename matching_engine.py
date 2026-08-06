from orders import Side, OrderType, Trade
from order_book import OrderBook


class MatchingEngine:

    def __init__(self):
        self.book = OrderBook()

    def submit_order(self, incoming):
        if incoming.order_id in self.book.order_map:
            raise ValueError(f"Duplicate order_id: {incoming.order_id}")

        trades = []
        while incoming.remaining > 0:

            if incoming.side == Side.BUY:
                best_price = self.book.best_ask()

                if best_price is None:
                    break

                if (
                    incoming.order_type == OrderType.LIMIT
                    and incoming.price < best_price
                ):
                    break

                resting_queue = self.book.asks[best_price]

            else:
                best_price = self.book.best_bid()

                if best_price is None:
                    break

                if (
                    incoming.order_type == OrderType.LIMIT
                    and incoming.price > best_price
                ):
                    break

                resting_queue = self.book.bids[best_price]


            resting = resting_queue[0]

            quantity = min(
                incoming.remaining,
                resting.remaining
            )

            incoming.remaining -= quantity
            self.book.reduce_order(resting.order_id, quantity)

            if incoming.side == Side.BUY:
                buy_id = incoming.order_id
                sell_id = resting.order_id
            else:
                buy_id = resting.order_id
                sell_id = incoming.order_id

            trades.append(
                Trade(
                    buy_order_id=buy_id,
                    sell_order_id=sell_id,
                    price=resting.price,
                    quantity=quantity,
                )
            )

            if resting.remaining == 0:
                self.book.remove_order(resting.order_id)

        if (
            incoming.remaining > 0
            and incoming.order_type == OrderType.LIMIT
        ):
            self.book.add_order(incoming)

        return trades


    def cancel_order(self, order_id):
        return self.book.remove_order(order_id)
        

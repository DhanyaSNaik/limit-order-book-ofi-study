import random

from matching_engine import MatchingEngine
from orders import Order, Side, OrderType

def limit(order_id, side, price, qty, ts=0):
    return Order(
        order_id=order_id,
        side=side,
        order_type=OrderType.LIMIT,
        price=price,
        quantity=qty,
        timestamp=ts,
    )


def market(order_id, side, qty):
    return Order(
        order_id=order_id,
        side=side,
        order_type=OrderType.MARKET,
        quantity=qty,
    )


def test_limit_order_fully_filled():
    engine = MatchingEngine()

    engine.submit_order(
        limit("sell1", Side.SELL, 101, 10)
    )

    trades = engine.submit_order(
        limit("buy1", Side.BUY, 101, 10)
    )

    assert len(trades) == 1
    assert trades[0].quantity == 10
    assert engine.book.best_ask() is None


def test_partial_fill_against_two_orders():
    engine = MatchingEngine()

    engine.submit_order(
        limit("sell1", Side.SELL, 100, 5)
    )

    engine.submit_order(
        limit("sell2", Side.SELL, 100, 7)
    )

    trades = engine.submit_order(
        limit("buy1", Side.BUY, 100, 10)
    )

    assert len(trades) == 2
    assert trades[0].quantity == 5
    assert trades[1].quantity == 5

    assert engine.book.asks[100][0].remaining == 2


def test_fifo_priority():
    engine = MatchingEngine()

    engine.submit_order(
        limit("sell1", Side.SELL, 100, 5, ts=1)
    )

    engine.submit_order(
        limit("sell2", Side.SELL, 100, 5, ts=2)
    )

    trades = engine.submit_order(
        limit("buy1", Side.BUY, 100, 5)
    )

    assert trades[0].sell_order_id == "sell1"


def test_cancelled_order_cannot_fill():
    engine = MatchingEngine()

    engine.submit_order(
        limit("sell1", Side.SELL, 100, 5)
    )

    assert engine.cancel_order("sell1")

    trades = engine.submit_order(
        limit("buy1", Side.BUY, 100, 5)
    )

    assert trades == []


def test_market_order_matches_best_price():
    engine = MatchingEngine()

    engine.submit_order(
        limit("sell1", Side.SELL, 105, 5)
    )

    engine.submit_order(
        limit("sell2", Side.SELL, 100, 5)
    )

    trades = engine.submit_order(
        market("buy1", Side.BUY, 5)
    )

    assert trades[0].price == 100


def test_crosses_multiple_price_levels():
    engine = MatchingEngine()

    engine.submit_order(
        limit("sell1", Side.SELL, 100, 3)
    )

    engine.submit_order(
        limit("sell2", Side.SELL, 101, 4)
    )

    trades = engine.submit_order(
        limit("buy1", Side.BUY, 101, 10)
    )

    assert len(trades) == 2
    assert trades[0].price == 100
    assert trades[1].price == 101
    assert engine.book.best_ask() is None


def assert_book_invariants(engine):
    book = engine.book

    if book.bids and book.asks:
        assert book.best_bid() < book.best_ask()

    ids = [
        order.order_id
        for order in book.all_orders()
    ]

    assert len(ids) == len(set(ids))

    for price in book.bids:
        assert (
            book.total_quantity_at_price(Side.BUY, price)
            ==
            book.ledger_quantity_at_price(Side.BUY, price)
        )

    for price in book.asks:
        assert (
            book.total_quantity_at_price(Side.SELL, price)
            ==
            book.ledger_quantity_at_price(Side.SELL, price)
        )


def test_randomized_property():
    for seed in range(1000):
        random.seed(seed)

        engine = MatchingEngine()

        for i in range(100):
            active_ids = [
                order.order_id
                for order in engine.book.all_orders()
            ]

            action = random.choice(
                ["submit", "cancel"]
            )

            if action == "submit":
                if active_ids and random.random() < 0.1:
                    order_id = random.choice(active_ids)
                else:
                    order_id = f"{seed}-{i}"

                side = random.choice(
                    [Side.BUY, Side.SELL]
                )

                order = limit(
                    order_id,
                    side,
                    random.randint(95, 105),
                    random.randint(1, 10),
                )

                try:
                    engine.submit_order(order)
                except ValueError:
                    pass

            elif active_ids:
                cancel_id = random.choice(active_ids)
                engine.cancel_order(cancel_id)

            assert_book_invariants(engine)

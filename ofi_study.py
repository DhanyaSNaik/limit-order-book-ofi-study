import random
from dataclasses import dataclass

import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from matching_engine import MatchingEngine
from orders import Order, Side, OrderType


@dataclass
class Snapshot:
    tick: int
    midprice: float
    bid_depth: int
    ask_depth: int


def make_limit_order(order_id, side, price, quantity):
    return Order(
        order_id=order_id,
        side=side,
        order_type=OrderType.LIMIT,
        price=price,
        quantity=quantity,
    )


def total_bid_depth(engine):
    return sum(
        order.remaining
        for orders in engine.book.bids.values()
        for order in orders
    )


def total_ask_depth(engine):
    return sum(
        order.remaining
        for orders in engine.book.asks.values()
        for order in orders
    )


def current_midprice(engine, fallback):
    mid = engine.book.midprice()

    if mid is None:
        return fallback

    return mid


def generate_order_params(n_orders=5000, seed=42, market_order_prob=0.15):
    random.seed(seed)
    pressure = 0
    for i in range(n_orders):
        pressure += random.choice([-1, 0, 0, 0, 1])
        if pressure > 2:
            buy_bias = 0.6
        elif pressure < -2:
            buy_bias = 0.4
        else:
            buy_bias = 0.5

        side = (
            Side.BUY
            if random.random() < buy_bias
            else Side.SELL
        )
        distance = random.randint(0, 3)
        quantity = random.randint(1, 10)
        is_market = random.random() < market_order_prob

        yield i, side, distance, quantity, is_market

def run_simulation(n_orders=5000, starting_price=100.0, seed=42):
    engine = MatchingEngine()
    snapshots = []
    mid = starting_price
    reference_price = starting_price
    trades_executed = 0

    for i, side, distance, quantity, is_market in generate_order_params(n_orders, seed):
        if is_market:
            order = Order(
                order_id=f"synthetic-{i}",
                side=side,
                order_type=OrderType.MARKET,
                quantity=quantity,
            )
        else:
            if side == Side.BUY:
                order_price = round(reference_price - distance * 0.5, 2)
            else:
                order_price = round(reference_price + distance * 0.5, 2)
            order = make_limit_order(f"synthetic-{i}", side, order_price, quantity)

        trades = engine.submit_order(order)
        trades_executed += len(trades)

        mid = current_midprice(engine, mid)
        reference_price = mid 

        snapshots.append(
            Snapshot(
                tick=i,
                midprice=mid,
                bid_depth=total_bid_depth(engine),
                ask_depth=total_ask_depth(engine),
            )
        )

    print(f"Trades executed: {trades_executed}")
    return pd.DataFrame(snapshots)


def add_ofi_targets(df):

    df["bid_change"] = (
        df["bid_depth"].diff()
    )

    df["ask_change"] = (
        df["ask_depth"].diff()
    )

    df["ofi"] = (
        df["bid_change"]
        -
        df["ask_change"]
    )

    for horizon in [5, 20]:

        df[f"future_move_{horizon}"] = (
            df["midprice"]
            .shift(-horizon)
            -
            df["midprice"]
        )

    return df.dropna()


def evaluate(df, horizon):

    X = df[["ofi"]]
    y = df[f"future_move_{horizon}"]

    split = int(len(df) * 0.7)

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    model = LinearRegression()

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_test
    )

    r2 = r2_score(
        y_test,
        predictions,
    )

    nonzero_mask = y_test.values != 0
    sign_accuracy = (
        np.sign(predictions[nonzero_mask])
        ==
        np.sign(y_test.values[nonzero_mask])
    ).mean()

    return {
        "horizon": horizon,
        "coefficient": model.coef_[0],
        "r2": r2,
        "sign_accuracy": sign_accuracy,
        "nonzero_test_rows": int(nonzero_mask.sum()),
        "total_test_rows": len(y_test),
    }


if __name__ == "__main__":

    df = run_simulation()

    df = add_ofi_targets(df)

    print("Rows analyzed:", len(df))

    for horizon in [5, 20]:

        result = evaluate(
            df,
            horizon,
        )

        print()
        print(result)

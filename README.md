# Limit Order Book Matching Engine & Order Flow Imbalance Study

## Overview

This project combines two related components into a single workflow. First, I built a Python limit order book and matching engine implementing strict price-time priority, supporting limit and market orders, cancellations, partial fills, and core book queries. I then used that engine as a controlled synthetic market to investigate whether a simple Order Flow Imbalance (OFI) measure predicts short-term midprice movements. The emphasis is on correct engineering and honest experimental methodology rather than demonstrating a profitable trading strategy.

## Project Structure

```text
orders.py
order_book.py
matching_engine.py
test_matching_engine.py
ofi_study.py
```

## Running the Project

Install the required packages:

```bash
pip install numpy pandas scikit-learn pytest
```

Run the matching engine tests:

```bash
pytest test_matching_engine.py
```

Run the OFI study:

```bash
python ofi_study.py
```

## Test Results

The matching engine passed all required tests:

* Limit order resting and full fill
* Partial fills across multiple resting orders
* FIFO (price-time priority)
* Order cancellation
* Market order execution
* Matching across multiple price levels
* Randomized property test (1,000 event sequences)

**Result:** 7/7 tests passed.

## OFI Study

Synthetic order flow was generated using a simple momentum/noise process with a mix of resting limit orders and occasional market orders. Orders were processed through the matching engine to produce synthetic book evolution.

For each snapshot:

* OFI = change in total resting bid depth − change in total resting ask depth
* Targets:

  * 5-tick forward midprice change
  * 20-tick forward midprice change

A linear regression was trained on the first 70% of observations and evaluated on the remaining 30% without shuffling.

All results are deterministic and reproducible: the synthetic order generator uses a fixed random seed (**42**).

### Experimental Results

* Trades executed: **1,816**
* Rows analyzed: **4,979**

|  Horizon | Coefficient | Test R² | Sign Accuracy |
| -------: | ----------: | ------: | ------------: |
|  5 ticks |    0.000210 | -0.0179 |        50.42% |
| 20 ticks |    0.000601 | -0.0468 |        50.49% |

Sign accuracy is computed **only over test rows where the forward midprice change is nonzero**. Flat-price rows are excluded because they have no directional sign to predict. For this run, sign accuracy was evaluated on **718 of 1,494** test observations at the 5-tick horizon and **1,131 of 1,494** observations at the 20-tick horizon.

### Interpretation

In this synthetic environment, the simplified OFI measure did **not** demonstrate meaningful predictive power for future midprice movements. Although the fitted regression coefficients were positive, out-of-sample performance was poor (negative R²), and directional accuracy remained approximately 50%, indicating little to no predictive signal.

This is an expected and valid outcome for a simple synthetic market and is reported without post-hoc tuning.

## Notes and Limitations

* OFI is approximated as the **change in total resting bid depth minus the change in total resting ask depth**. This is a simplified implementation rather than the full event-level OFI definition commonly used in market microstructure research.
* Synthetic order flow includes both resting limit orders and a smaller proportion of market orders so that the matching engine produces executions and evolving prices.
* When one side of the book becomes empty, the reference price and recorded midprice remain at the last observed value until both sides of the book are available again.
* Results are based entirely on **synthetic data** and should **not** be interpreted as evidence of a real-market trading signal.

## Future Work

* IOC/FOK order types
* Order replacement/modification
* C++ rewrite of the matching engine for performance
* Replace synthetic flow with real limit order book data (e.g. LOBSTER)
* Walk-forward validation instead of a single train/test split
* Latency benchmarking

# Tech Sector Equity Analysis
### Internship Assignment — May 2026

---

## What this project is about

This project analyses three large-cap US technology stocks — **Microsoft (MSFT)**, **Alphabet (GOOGL)**, and **Nvidia (NVDA)** — using real monthly price data from January 2022 to December 2024.

The goal is to identify interesting patterns in the data and build a simple, testable trading idea based on those patterns.

**The trading idea:** MSFT and GOOGL normally move together. When they stop moving together (measured by rolling correlation), it often means a temporary narrative divergence — and a pair trade opportunity to profit when they re-converge.

---

## Key findings

| Finding | What the data showed |
|---|---|
| 2022 synchronised crash | All three fell together despite different businesses. NVDA fell 65% even as its order book was accelerating. |
| Correlation sign reversal | MSFT/GOOGL correlation peaked at 0.98 (Dec 2022) then collapsed to −0.79 (Mar 2024) as AI narratives split them apart. |
| NVDA volatility premium | NVDA's annualised vol hit 73.9% — and stayed elevated even during its bull run, unlike MSFT and GOOGL which compressed to under 10%. |

---

## Repo structure

```
├── README.md               — this file
├── requirements.txt        — Python libraries needed
├── TechEquityAnalysis.docx — full written submission
│
├── data/
│   └── data.csv            — real monthly adjusted closing prices (Yahoo Finance)
│
├── code/
│   ├── data_analysis.py    — computes indexed prices, volatility, correlation + saves charts
│   └── backtest.py         — runs the pair trade backtest and prints results
│
└── charts/
    ├── chart1_indexed_prices.png
    ├── chart2_rolling_volatility.png
    └── chart3_rolling_correlation.png
```

---

## How to run

**Step 1 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2 — Run the data analysis (generates all 3 charts)**
```bash
python code/data_analysis.py
```

**Step 3 — Run the backtest**
```bash
python code/backtest.py
```

You can change the trade parameters at the top of `backtest.py`:

```python
ENTRY_THRESH     = 0.60   # Enter when correlation drops below this
EXIT_THRESH      = 0.70   # Exit when correlation recovers above this
STOP_LOSS_PTS    = 15.0   # Stop-loss threshold in index points
TIME_STOP_MONTHS = 9      # Maximum months to hold the trade
```

---

## Data source

All prices are **monthly adjusted closing prices** sourced from **Yahoo Finance**.  
"Adjusted" means the data is corrected for stock splits and dividends — NVDA's 10-for-1 split (June 2024) is already factored in, so the full series is comparable.

All calculations (log returns, rolling volatility, rolling correlation) are done in plain Python — no black-box libraries — so every number is fully reproducible.

---

## Limitations

- Only 36 months of data = only one trade signal. A proper backtest needs 10 years of data.
- 3-month volatility window is sensitive to outliers — a 6-month window would be more stable.
- Backtest does not include borrow costs, transaction fees, or market impact.
- The 0.60 entry threshold was chosen by observing the data (look-ahead bias). Walk-forward testing on unseen data is required before trusting the strategy.

---

## AI usage

Claude (Anthropic) was used as an assistant throughout. All AI-assisted sections are clearly labelled in the written submission. Data collection, calculations, stock selection, and core observations are original work.

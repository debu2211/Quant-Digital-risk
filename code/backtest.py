"""
backtest.py
-----------
Runs a simple pair trade backtest on MSFT vs GOOGL using real monthly data.

Strategy:
  - Signal : Rolling 6-month correlation between MSFT and GOOGL drops below ENTRY_THRESH
  - Trade  : Long the prior-3-month outperformer, Short the underperformer (equal notional)
  - Exit   : Correlation recovers above EXIT_THRESH  OR  time stop (TIME_STOP_MONTHS)
  - Risk   : Stop-loss if spread widens STOP_LOSS_PTS points against the position

How to run:
    python code/backtest.py

Requirements:
    pip install pandas matplotlib
"""

import math
import csv
import os

# ------------------------------------------------------------------
# Parameters — change these to test different settings
# ------------------------------------------------------------------

ENTRY_THRESH     = 0.60   # Enter when correlation drops below this
EXIT_THRESH      = 0.70   # Exit when correlation recovers above this
STOP_LOSS_PTS    = 15.0   # Stop-loss: exit if spread moves this many index points against us
TIME_STOP_MONTHS = 9      # Exit after this many months regardless

# ------------------------------------------------------------------
# Load data
# ------------------------------------------------------------------

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'data.csv')

dates, msft_raw, googl_raw = [], [], []

with open(DATA_PATH, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dates.append(row['Date'])
        msft_raw.append(float(row['MSFT']))
        googl_raw.append(float(row['GOOGL']))

n = len(dates)

# ------------------------------------------------------------------
# Step 1: Index prices to 100
# ------------------------------------------------------------------

base_m = msft_raw[0]
base_g = googl_raw[0]
msft_idx  = [round(v / base_m * 100, 2) for v in msft_raw]
googl_idx = [round(v / base_g * 100, 2) for v in googl_raw]

# Spread = MSFT indexed - GOOGL indexed
# Positive spread = MSFT outperforming
spread = [round(msft_idx[i] - googl_idx[i], 2) for i in range(n)]

# ------------------------------------------------------------------
# Step 2: Compute log returns
# ------------------------------------------------------------------

def log_returns(series):
    return [math.log(series[i] / series[i-1]) for i in range(1, len(series))]

rm = log_returns(msft_raw)
rg = log_returns(googl_raw)

# ------------------------------------------------------------------
# Step 3: Rolling 6-month correlation
# ------------------------------------------------------------------

CORR_WINDOW = 6

def rolling_corr(a, b, window):
    result = [None] * window   # first `window` months have no correlation yet
    for i in range(window - 1, len(a)):
        sa = a[i - window + 1 : i + 1]
        sb = b[i - window + 1 : i + 1]
        ma = sum(sa) / window
        mb = sum(sb) / window
        num = sum((sa[j] - ma) * (sb[j] - mb) for j in range(window))
        da  = math.sqrt(sum((x - ma) ** 2 for x in sa))
        db  = math.sqrt(sum((x - mb) ** 2 for x in sb))
        result.append(round(num / (da * db) if da * db > 0 else 0, 3))
    return result

# corr[i] corresponds to price index i (shifted by 1 because returns start at index 1)
# returns have n-1 elements; corr_returns[i] aligns with price index i+1
corr_returns = rolling_corr(rm, rg, CORR_WINDOW)
# Align correlation to price indices: corr_price[i] = correlation as of month i
corr_price = [None] + corr_returns  # index 0 has no corr; corr_returns[0] aligns to price[1]

# ------------------------------------------------------------------
# Step 4: Run the backtest
# ------------------------------------------------------------------

in_trade       = False
entry_idx      = -1
entry_spread   = 0.0
direction      = 1    # +1 = long MSFT / short GOOGL, -1 = opposite
trades         = []

statuses = ['—'] * n

for i in range(n):
    c = corr_price[i]
    if c is None:
        statuses[i] = 'No data yet'
        continue

    if not in_trade:
        # Check if correlation has dropped below entry threshold
        prev_c = corr_price[i-1] if i > 0 and corr_price[i-1] is not None else 1.0
        if c < ENTRY_THRESH and prev_c >= ENTRY_THRESH:
            # Determine direction: which stock outperformed over prior 3 months?
            lookback = 3
            start = max(0, i - lookback)
            msft_ret_3m  = msft_idx[i]  / msft_idx[start]  - 1
            googl_ret_3m = googl_idx[i] / googl_idx[start] - 1
            direction = 1 if msft_ret_3m > googl_ret_3m else -1

            in_trade     = True
            entry_idx    = i
            entry_spread = spread[i] * direction
            statuses[i]  = 'ENTRY'
            print(f"  ENTRY  @ {dates[i]}  |  corr={c:.3f}  |  "
                  f"{'Long MSFT / Short GOOGL' if direction==1 else 'Long GOOGL / Short MSFT'}"
                  f"  |  spread={spread[i]:.1f}")
        else:
            statuses[i] = 'Watching'

    else:
        months_held   = i - entry_idx
        current_pnl   = (spread[i] * direction) - entry_spread
        exit_reason   = None

        if c > EXIT_THRESH:
            exit_reason = 'Correlation recovered'
        elif current_pnl < -STOP_LOSS_PTS:
            exit_reason = 'Stop-loss hit'
        elif months_held >= TIME_STOP_MONTHS:
            exit_reason = 'Time stop'

        if exit_reason:
            trades.append({
                'entry_date':  dates[entry_idx],
                'exit_date':   dates[i],
                'direction':   'Long MSFT / Short GOOGL' if direction == 1 else 'Long GOOGL / Short MSFT',
                'months_held': months_held,
                'pnl_pts':     round(current_pnl, 2),
                'exit_reason': exit_reason,
            })
            print(f"  EXIT   @ {dates[i]}  |  corr={c:.3f}  |  "
                  f"P&L={current_pnl:+.2f} pts  |  held={months_held}mo  |  reason={exit_reason}")
            statuses[i] = f'EXIT ({exit_reason})'
            in_trade = False
        else:
            statuses[i] = f'Holding ({months_held}mo)'

# Handle open trade at end of data
if in_trade:
    i = n - 1
    current_pnl = (spread[i] * direction) - entry_spread
    trades.append({
        'entry_date':  dates[entry_idx],
        'exit_date':   dates[i] + ' (open)',
        'direction':   'Long MSFT / Short GOOGL' if direction == 1 else 'Long GOOGL / Short MSFT',
        'months_held': i - entry_idx,
        'pnl_pts':     round(current_pnl, 2),
        'exit_reason': 'Still open at end of data',
    })
    print(f"  OPEN   @ {dates[i]}  |  P&L={current_pnl:+.2f} pts  |  Still open")

# ------------------------------------------------------------------
# Step 5: Print results summary
# ------------------------------------------------------------------

print("\n" + "="*60)
print("BACKTEST RESULTS SUMMARY")
print("="*60)
print(f"Parameters: Entry<{ENTRY_THRESH} | Exit>{EXIT_THRESH} | "
      f"Stop={STOP_LOSS_PTS}pts | TimeStop={TIME_STOP_MONTHS}mo")
print(f"Period    : {dates[0]} to {dates[-1]}")
print(f"Total trades triggered : {len(trades)}")

if trades:
    profitable = [t for t in trades if t['pnl_pts'] > 0]
    hit_rate   = len(profitable) / len(trades) * 100
    avg_pnl    = sum(t['pnl_pts'] for t in trades) / len(trades)
    total_pnl  = sum(t['pnl_pts'] for t in trades)
    avg_hold   = sum(t['months_held'] for t in trades) / len(trades)

    print(f"Hit rate               : {hit_rate:.0f}%  ({len(profitable)}/{len(trades)} profitable)")
    print(f"Average P&L per trade  : {avg_pnl:+.2f} spread points")
    print(f"Total P&L              : {total_pnl:+.2f} spread points")
    print(f"Average holding period : {avg_hold:.1f} months")

    print("\nTrade-by-trade breakdown:")
    print(f"  {'Entry':<10} {'Exit':<18} {'Direction':<30} {'Held':>5} {'P&L':>8}  Reason")
    print("  " + "-"*85)
    for t in trades:
        print(f"  {t['entry_date']:<10} {t['exit_date']:<18} {t['direction']:<30} "
              f"{t['months_held']:>4}mo {t['pnl_pts']:>+7.2f}  {t['exit_reason']}")

    print("\nNote:")
    print("  P&L is in indexed spread points (MSFT index - GOOGL index).")
    print("  Positive = profit for the long/short position as entered.")
    print("  This does NOT include borrow costs, transaction fees, or slippage.")
    print("  With only 36 months of data one signal is expected — run on 10 years for robust results.")

else:
    print("No trades triggered with these parameters.")
    print("Try lowering the entry threshold (e.g. ENTRY_THRESH = 0.80)")

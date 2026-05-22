"""
data_analysis.py
-----------------
Loads raw monthly price data for MSFT, GOOGL, and NVDA and computes:
  1. Indexed prices (base = 100 at Jan 2022)
  2. Rolling 3-month annualised volatility
  3. Rolling 6-month correlation between MSFT and GOOGL

Saves three charts to the charts/ folder.

How to run:
    python code/data_analysis.py

Requirements:
    pip install pandas matplotlib
"""

import math
import csv
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ------------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------------

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'data.csv')
CHARTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'charts')
os.makedirs(CHARTS_PATH, exist_ok=True)

dates, msft_raw, googl_raw, nvda_raw = [], [], [], []

with open(DATA_PATH, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dates.append(row['Date'])
        msft_raw.append(float(row['MSFT']))
        googl_raw.append(float(row['GOOGL']))
        nvda_raw.append(float(row['NVDA']))

n = len(dates)
labels = []
for d in dates:
    y, m = d.split('-')
    month_names = ['','Jan','Feb','Mar','Apr','May','Jun',
                   'Jul','Aug','Sep','Oct','Nov','Dec']
    labels.append(f"{month_names[int(m)]} '{y[2:]}")

print(f"Loaded {n} monthly observations from {dates[0]} to {dates[-1]}")

# ------------------------------------------------------------------
# 2. Index prices to 100
# ------------------------------------------------------------------

def index_series(series):
    base = series[0]
    return [round(v / base * 100, 2) for v in series]

msft_idx  = index_series(msft_raw)
googl_idx = index_series(googl_raw)
nvda_idx  = index_series(nvda_raw)

# ------------------------------------------------------------------
# 3. Log returns
# ------------------------------------------------------------------

def log_returns(series):
    return [math.log(series[i] / series[i-1]) for i in range(1, len(series))]

rm = log_returns(msft_raw)
rg = log_returns(googl_raw)
rn = log_returns(nvda_raw)

# ------------------------------------------------------------------
# 4. Rolling 3-month annualised volatility
# ------------------------------------------------------------------

def rolling_vol(rets, window=3):
    """Annualised volatility from rolling window of log returns."""
    result = []
    for i in range(window - 1, len(rets)):
        sl = rets[i - window + 1 : i + 1]
        mean = sum(sl) / window
        variance = sum((x - mean) ** 2 for x in sl) / window
        result.append(round(math.sqrt(variance * 12) * 100, 2))
    return result

vol_msft  = rolling_vol(rm)
vol_googl = rolling_vol(rg)
vol_nvda  = rolling_vol(rn)
vol_labels = labels[3:]   # first vol needs 3 returns = starts at index 3

print(f"\nVolatility computed: {len(vol_msft)} data points")
print(f"  MSFT  — max: {max(vol_msft):.1f}%  min: {min(vol_msft):.1f}%")
print(f"  GOOGL — max: {max(vol_googl):.1f}%  min: {min(vol_googl):.1f}%")
print(f"  NVDA  — max: {max(vol_nvda):.1f}%  min: {min(vol_nvda):.1f}%")

# ------------------------------------------------------------------
# 5. Rolling 6-month correlation (MSFT vs GOOGL)
# ------------------------------------------------------------------

def rolling_corr(a, b, window=6):
    """Pearson correlation of two return series over a rolling window."""
    result = []
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

corr       = rolling_corr(rm, rg)
corr_labels = labels[6:]   # 6 returns needs 7 price points → label index 6

print(f"\nCorrelation computed: {len(corr)} data points")
print(f"  Max: {max(corr):.3f}  Min: {min(corr):.3f}")

# ------------------------------------------------------------------
# 6. Chart styling helpers
# ------------------------------------------------------------------

COLORS = {
    'msft':  '#185FA5',
    'googl': '#993C1D',
    'nvda':  '#0F6E56',
    'corr':  '#534AB7',
    'grid':  '#E5E5E5',
    'text':  '#444441',
}

def style_ax(ax):
    ax.set_facecolor('white')
    ax.grid(True, color=COLORS['grid'], linewidth=0.5, linestyle='-')
    ax.tick_params(colors=COLORS['text'], labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(COLORS['grid'])
    ax.yaxis.label.set_color(COLORS['text'])
    ax.xaxis.label.set_color(COLORS['text'])

def set_x_ticks(ax, lbl_list, max_ticks=12):
    step = max(1, len(lbl_list) // max_ticks)
    ax.set_xticks(range(0, len(lbl_list), step))
    ax.set_xticklabels(lbl_list[::step], rotation=45, ha='right', fontsize=8)

# ------------------------------------------------------------------
# 7. Chart 1 — Indexed price performance
# ------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 4))
fig.patch.set_facecolor('white')

x = range(n)
ax.plot(x, msft_idx,  color=COLORS['msft'],  linewidth=2,   label='MSFT')
ax.plot(x, googl_idx, color=COLORS['googl'], linewidth=2,   label='GOOGL', linestyle='--')
ax.plot(x, nvda_idx,  color=COLORS['nvda'],  linewidth=2,   label='NVDA',  linestyle=':')
ax.axhline(100, color=COLORS['grid'], linewidth=1, linestyle='-')

style_ax(ax)
set_x_ticks(ax, labels)
ax.set_ylabel('Indexed price (Jan 2022 = 100)', fontsize=9)
ax.set_title('Chart 1 — Indexed price performance: MSFT, GOOGL, NVDA (Jan 2022 – Dec 2024)',
             fontsize=10, color=COLORS['text'], pad=12)
ax.legend(fontsize=9, framealpha=0.6)

# Annotate final values
for series, name, color in [(msft_idx, 'MSFT', COLORS['msft']),
                              (googl_idx, 'GOOGL', COLORS['googl']),
                              (nvda_idx, 'NVDA', COLORS['nvda'])]:
    ax.annotate(f"{series[-1]:.0f}", xy=(n-1, series[-1]),
                xytext=(4, 0), textcoords='offset points',
                fontsize=8, color=color, va='center')

plt.tight_layout()
out1 = os.path.join(CHARTS_PATH, 'chart1_indexed_prices.png')
plt.savefig(out1, dpi=150, bbox_inches='tight')
plt.close()
print(f"\nSaved: {out1}")

# ------------------------------------------------------------------
# 8. Chart 2 — Rolling 3-month volatility
# ------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 4))
fig.patch.set_facecolor('white')

xv = range(len(vol_labels))
ax.plot(xv, vol_msft,  color=COLORS['msft'],  linewidth=2, label='MSFT vol')
ax.plot(xv, vol_googl, color=COLORS['googl'], linewidth=2, label='GOOGL vol', linestyle='--')
ax.plot(xv, vol_nvda,  color=COLORS['nvda'],  linewidth=2, label='NVDA vol',  linestyle=':')

style_ax(ax)
set_x_ticks(ax, vol_labels)
ax.set_ylabel('Annualised volatility (%)', fontsize=9)
ax.set_title('Chart 2 — Rolling 3-month annualised volatility (Jan 2022 – Dec 2024)',
             fontsize=10, color=COLORS['text'], pad=12)
ax.legend(fontsize=9, framealpha=0.6)

plt.tight_layout()
out2 = os.path.join(CHARTS_PATH, 'chart2_rolling_volatility.png')
plt.savefig(out2, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {out2}")

# ------------------------------------------------------------------
# 9. Chart 3 — Rolling 6-month correlation
# ------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 4))
fig.patch.set_facecolor('white')

xc = range(len(corr_labels))
ax.plot(xc, corr, color=COLORS['corr'], linewidth=2, label='MSFT / GOOGL correlation')
ax.axhline(0,    color=COLORS['grid'], linewidth=1)
ax.axhline(0.60, color=COLORS['msft'],  linewidth=1, linestyle='--', alpha=0.7)
ax.axhline(0.70, color=COLORS['nvda'],  linewidth=1, linestyle='--', alpha=0.7)

ax.annotate('Entry threshold (0.60)', xy=(0, 0.60), xytext=(1, 0.63),
            fontsize=7.5, color=COLORS['msft'])
ax.annotate('Exit threshold (0.70)',  xy=(0, 0.70), xytext=(1, 0.73),
            fontsize=7.5, color=COLORS['nvda'])

style_ax(ax)
set_x_ticks(ax, corr_labels, max_ticks=10)
ax.set_ylim(-1.1, 1.1)
ax.set_ylabel('Pearson correlation', fontsize=9)
ax.set_title('Chart 3 — Rolling 6-month correlation: MSFT vs GOOGL (Jul 2022 – Dec 2024)',
             fontsize=10, color=COLORS['text'], pad=12)
ax.legend(fontsize=9, framealpha=0.6)

plt.tight_layout()
out3 = os.path.join(CHARTS_PATH, 'chart3_rolling_correlation.png')
plt.savefig(out3, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {out3}")

print("\nAll charts saved successfully.")

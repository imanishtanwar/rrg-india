import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Aditya Classes Bikaner – ETF RRG Dashboard",
    layout="centered"
)

# =====================================================
# CONSTANTS
# =====================================================
PERIOD = "1y"
BENCHMARK = "NIFTYBEES.NS"
ETFS_PER_PAGE = 5
ROLL = 14
TAIL = 10

ETF_LIST = [
    "BANKIETF", "CPSEETF", "ENERGY", "EVIETF", "FINIETF",
    "GOLDBEES", "GROWWRAIL", "ITBEES", "MAFANG", "MASPTOP50",
    "METAL", "MIDCAPETF", "MODEFENCE", "MON100", "PHARMABEES",
    "PSUBNKIETF", "PVTBANIETF", "SILVER", "SMALLCAP"
]

def ns(symbol):
    return f"{symbol}.NS"

# =====================================================
# SESSION STATE – PAGINATION
# =====================================================
if "page" not in st.session_state:
    st.session_state.page = 0

# =====================================================
# HEADER
# =====================================================
st.markdown("## Aditya Classes, Bikaner")
st.markdown("**ETF Relative Rotation Graph (RRG)**")
st.markdown("Benchmark: **NIFTYBEES**")
st.markdown("---")

# =====================================================
# PAGINATION
# =====================================================
total_pages = (len(ETF_LIST) - 1) // ETFS_PER_PAGE + 1

c1, _, c3 = st.columns([1, 2, 1])

with c1:
    if st.button("⬅ Previous") and st.session_state.page > 0:
        st.session_state.page -= 1

with c3:
    if st.button("Next ➡") and st.session_state.page < total_pages - 1:
        st.session_state.page += 1

start = st.session_state.page * ETFS_PER_PAGE
end = start + ETFS_PER_PAGE
visible_etfs = ETF_LIST[start:end]

st.caption(f"Showing ETFs {start+1}–{min(end,len(ETF_LIST))} of {len(ETF_LIST)}")

# =====================================================
# DATA DOWNLOAD (ALL ETFs for GLOBAL SCALE)
# =====================================================
benchmark = yf.download(BENCHMARK, period=PERIOD, progress=False)["Close"]

prices = pd.DataFrame(index=benchmark.index)
prices["Benchmark"] = benchmark

for etf in ETF_LIST:
    df = yf.download(ns(etf), period=PERIOD, progress=False)
    if not df.empty:
        prices[etf] = df["Close"]

prices.dropna(inplace=True)

# =====================================================
# RRG CALCULATIONS
# =====================================================
rs = prices[ETF_LIST].div(prices["Benchmark"], axis=0)
rs_ratio = 100 * rs / rs.rolling(ROLL).mean()
rs_momentum = 100 * rs_ratio / rs_ratio.rolling(ROLL).mean()

# =====================================================
# GLOBAL AXIS LIMITS (KEY FIX)
# =====================================================
x_all = rs_ratio.iloc[-1]
y_all = rs_momentum.iloc[-1]

xmin, xmax = x_all.min() * 0.97, x_all.max() * 1.03
ymin, ymax = y_all.min() * 0.97, y_all.max() * 1.03

# =====================================================
# RRG PLOT (LOG SCALE – NO SQUEEZE)
# =====================================================
fig, ax = plt.subplots(figsize=(9, 9))

ax.set_xscale("log")
ax.set_yscale("log")

ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

# Quadrants
ax.axvline(100, color="black", lw=1)
ax.axhline(100, color="black", lw=1)

ax.text(xmax*0.995, ymax*0.995, "LEADING", ha="right", va="top", weight="bold")
ax.text(xmax*0.995, ymin*1.005, "WEAKENING", ha="right", va="bottom", weight="bold")
ax.text(xmin*1.005, ymin*1.005, "LAGGING", ha="left", va="bottom", weight="bold")
ax.text(xmin*1.005, ymax*0.995, "IMPROVING", ha="left", va="top", weight="bold")

# Plot only visible ETFs
for etf in visible_etfs:
    x = rs_ratio[etf].iloc[-TAIL:]
    y = rs_momentum[etf].iloc[-TAIL:]

    ax.plot(x, y, marker="o", lw=1.3)
    ax.scatter(x.iloc[-1], y.iloc[-1], s=140, edgecolor="black", zorder=3)
    ax.text(x.iloc[-1]*1.002, y.iloc[-1]*1.002, etf, fontsize=9, weight="bold")

ax.set_xlabel("RS-Ratio (log)")
ax.set_ylabel("RS-Momentum (log)")
ax.set_title("Relative Rotation Graph (1Y, Weekly)")
ax.grid(True, which="both", alpha=0.4)

st.pyplot(fig)

# =====================================================
# MASTER QUADRANT TABLE + TREND ARROWS
# =====================================================
rows = []

for etf in ETF_LIST:
    rs_now = rs_ratio[etf].iloc[-1]
    mom_now = rs_momentum[etf].iloc[-1]

    rs_prev = rs_ratio[etf].iloc[-2]
    mom_prev = rs_momentum[etf].iloc[-2]

    if rs_now >= 100 and mom_now >= 100:
        quad = "Leading"
    elif rs_now >= 100 and mom_now < 100:
        quad = "Weakening"
    elif rs_now < 100 and mom_now < 100:
        quad = "Lagging"
    else:
        quad = "Improving"

    if rs_now > rs_prev and mom_now > mom_prev:
        trend = "↗"
    elif rs_now < rs_prev and mom_now < mom_prev:
        trend = "↘"
    else:
        trend = "→"

    rows.append([etf, quad, trend, round(rs_now,2), round(mom_now,2)])

master_df = pd.DataFrame(
    rows,
    columns=["ETF", "Quadrant", "Trend", "RS-Ratio", "RS-Momentum"]
).sort_values(["Quadrant","ETF"])

st.subheader("Master ETF Quadrant Table (All ETFs)")
st.dataframe(master_df, use_container_width=True, hide_index=True)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    "<center>© 2026 Aditya Classes, Bikaner | ETF RRG Dashboard</center>",
    unsafe_allow_html=True
)

import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

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
st.image("aditya_classes_logo.png", width=120)
st.markdown("## Aditya Classes, Bikaner")
st.markdown("**ETF Relative Rotation Graph (RRG)**")
st.markdown("Benchmark: **NIFTYBEES**")
st.markdown("---")

# =====================================================
# PAGINATION CONTROLS
# =====================================================
total_pages = (len(ETF_LIST) - 1) // ETFS_PER_PAGE + 1

c1, c2, c3 = st.columns([1, 2, 1])

with c1:
    if st.button("⬅ Previous") and st.session_state.page > 0:
        st.session_state.page -= 1

with c3:
    if st.button("Next ➡") and st.session_state.page < total_pages - 1:
        st.session_state.page += 1

start = st.session_state.page * ETFS_PER_PAGE
end = start + ETFS_PER_PAGE
visible_etfs = ETF_LIST[start:end]

st.caption(
    f"Showing ETFs {start + 1}–{min(end, len(ETF_LIST))} "
    f"of {len(ETF_LIST)}"
)

# =====================================================
# DATA DOWNLOAD
# =====================================================
benchmark_df = yf.download(BENCHMARK, period=PERIOD, progress=False)
benchmark_df.dropna(inplace=True)

prices = pd.DataFrame()
prices["Benchmark"] = benchmark_df["Close"]

for etf in visible_etfs:
    df = yf.download(ns(etf), period=PERIOD, progress=False)
    if not df.empty and "Close" in df.columns:
        prices[etf] = df["Close"]

prices.dropna(inplace=True)

if prices.shape[1] < 2:
    st.error("Not enough ETF data available. Please refresh.")
    st.stop()

# =====================================================
# RRG CALCULATIONS
# =====================================================
rs = prices[visible_etfs].div(prices["Benchmark"], axis=0)
rs_ratio = 100 * rs / rs.rolling(14).mean()
rs_momentum = 100 * rs_ratio / rs_ratio.rolling(14).mean()

tail_length = 10

# =====================================================
# RRG PLOT (NO SQUEEZE / DYNAMIC SCALE)
# =====================================================
fig, ax = plt.subplots(figsize=(9, 9))

x_last = rs_ratio[visible_etfs].iloc[-1]
y_last = rs_momentum[visible_etfs].iloc[-1]

x_min, x_max = x_last.min(), x_last.max()
y_min, y_max = y_last.min(), y_last.max()

pad_x = (x_max - x_min) * 0.4
pad_y = (y_max - y_min) * 0.4

xmin = min(x_min - pad_x, 98)
xmax = max(x_max + pad_x, 102)
ymin = min(y_min - pad_y, 98)
ymax = max(y_max + pad_y, 102)

ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

# Quadrant shading
ax.axvspan(100, xmax, ymin=(100 - ymin)/(ymax - ymin), ymax=1, alpha=0.15, color="#C8E6C9")
ax.axvspan(100, xmax, ymin=0, ymax=(100 - ymin)/(ymax - ymin), alpha=0.15, color="#FFE0B2")
ax.axvspan(xmin, 100, ymin=0, ymax=(100 - ymin)/(ymax - ymin), alpha=0.15, color="#FFCDD2")
ax.axvspan(xmin, 100, ymin=(100 - ymin)/(ymax - ymin), ymax=1, alpha=0.15, color="#BBDEFB")

ax.axvline(100, color="black", linewidth=1)
ax.axhline(100, color="black", linewidth=1)

ax.text(xmax - 0.4, ymax - 0.4, "LEADING", ha="right", va="top", weight="bold")
ax.text(xmax - 0.4, ymin + 0.4, "WEAKENING", ha="right", va="bottom", weight="bold")
ax.text(xmin + 0.4, ymin + 0.4, "LAGGING", ha="left", va="bottom", weight="bold")
ax.text(xmin + 0.4, ymax - 0.4, "IMPROVING", ha="left", va="top", weight="bold")

for etf in visible_etfs:
    x = rs_ratio[etf].iloc[-tail_length:]
    y = rs_momentum[etf].iloc[-tail_length:]

    ax.plot(x, y, marker="o", linewidth=1.2)
    ax.scatter(x.iloc[-1], y.iloc[-1], s=160, edgecolor="black", zorder=3)
    ax.text(x.iloc[-1] + 0.2, y.iloc[-1] + 0.2, etf, fontsize=9, weight="bold")

ax.set_xlabel("RS-Ratio")
ax.set_ylabel("RS-Momentum")
ax.set_title("Relative Rotation Graph (1Y, Weekly)")
ax.grid(True)
ax.set_aspect("equal", adjustable="box")

st.pyplot(fig)

# =====================================================
# CONSOLIDATED QUADRANT TABLE
# =====================================================
quadrants = {
    "Leading": [],
    "Weakening": [],
    "Lagging": [],
    "Improving": []
}

for etf in visible_etfs:
    rs_val = x_last[etf]
    mom_val = y_last[etf]

    if rs_val >= 100 and mom_val >= 100:
        quadrants["Leading"].append(etf)
    elif rs_val >= 100 and mom_val < 100:
        quadrants["Weakening"].append(etf)
    elif rs_val < 100 and mom_val < 100:
        quadrants["Lagging"].append(etf)
    else:
        quadrants["Improving"].append(etf)

max_len = max(len(v) for v in quadrants.values())

quadrant_df = pd.DataFrame({
    k: v + [""] * (max_len - len(v))
    for k, v in quadrants.items()
})

st.subheader("ETF Quadrant Classification (Latest Week)")
st.dataframe(quadrant_df, use_container_width=True, hide_index=True)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    "<center>© 2026 Aditya Classes, Bikaner | ETF RRG Dashboard</center>",
    unsafe_allow_html=True
)

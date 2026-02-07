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
ROLL = 14
TAIL = 5

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
# PAGINATION CONTROLS
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
# DATA DOWNLOAD (ALL ETFs)
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
# RRG PLOT (FIXED SCALE 90–110)
# =====================================================
fig, ax = plt.subplots(figsize=(9, 9))

ax.set_xlim(90, 110)
ax.set_ylim(90, 110)

# Quadrant shading
ax.axvspan(100, 110, 0.5, 1.0, color="#C8E6C9", alpha=0.2)   # Leading
ax.axvspan(100, 110, 0.0, 0.5, color="#FFE0B2", alpha=0.2)   # Weakening
ax.axvspan(90, 100, 0.0, 0.5, color="#FFCDD2", alpha=0.2)    # Lagging
ax.axvspan(90, 100, 0.5, 1.0, color="#BBDEFB", alpha=0.2)    # Improving

ax.axvline(100, color="black", lw=1)
ax.axhline(100, color="black", lw=1)

ax.text(109, 109, "LEADING", ha="right", va="top", weight="bold")
ax.text(109, 91, "WEAKENING", ha="right", va="bottom", weight="bold")
ax.text(91, 91, "LAGGING", ha="left", va="bottom", weight="bold")
ax.text(91, 109, "IMPROVING", ha="left", va="top", weight="bold")

# Plot visible ETFs
for etf in visible_etfs:
    x = rs_ratio[etf].iloc[-TAIL:]
    y = rs_momentum[etf].iloc[-TAIL:]

    ax.plot(x, y, marker="o", lw=1.3)
    ax.scatter(x.iloc[-1], y.iloc[-1], s=140, edgecolor="black", zorder=3)
    ax.text(x.iloc[-1] + 0.2, y.iloc[-1] + 0.2, etf, fontsize=9, weight="bold")

ax.set_xlabel("RS-Ratio")
ax.set_ylabel("RS-Momentum")
ax.set_title("Relative Rotation Graph (1Y, Weekly)")
ax.grid(True)

st.pyplot(fig)

# =====================================================
# MASTER QUADRANT TABLE (ONLY ETF NAMES)
# =====================================================
quadrants = {
    "Leading": [],
    "Weakening": [],
    "Lagging": [],
    "Improving": []
}

for etf in ETF_LIST:
    rs_val = rs_ratio[etf].iloc[-1]
    mom_val = rs_momentum[etf].iloc[-1]

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

st.subheader("ETF Quadrant Classification (All ETFs)")
st.dataframe(quadrant_df, use_container_width=True, hide_index=True)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    "<center>© 2026 Aditya Classes, Bikaner | ETF RRG Dashboard</center>",
    unsafe_allow_html=True
)


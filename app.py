import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="Aditya Classes Bikaner – ETF RRG Dashboard",
    layout="centered"
)

PERIOD = "1y"
BENCHMARK = "NIFTYBEES.NS"
ETFS_PER_PAGE = 5   # change to 10 later if needed

ETF_LIST = [
    "BANKIETF", "CPSEETF", "ENERGY", "EVIETF", "FINIETF",
    "GOLDBEES", "GROWWRAIL", "ITBEES", "MAFANG", "MASPTOP50",
    "METAL", "MIDCAPETF", "MODEFENCE", "MON100", "PHARMABEES",
    "PSUBNKIETF", "PVTBANIETF", "SILVER", "SMALLCAP"
]

def ns(symbol):
    return f"{symbol}.NS"

# =====================================================
# SESSION STATE (PAGINATION)
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
# RRG PLOT
# =====================================================
fig, ax = plt.subplots(figsize=(8, 8))

# Quadrant shading
ax.axvspan(100, 110, ymin=0.5, ymax=1.0, alpha=0.15, color="#C8E6C9")
ax.axvspan(100, 110, ymin=0.0, ymax=0.5, alpha=0.15, color="#FFE0B2")
ax.axvspan(90, 100, ymin=0.0, ymax=0.5, alpha=0.15, color="#FFCDD2")
ax.axvspan(90, 100, ymin=0.5, ymax=1.0, alpha=0.15, color="#BBDEFB")

ax.text(102, 102, "LEADING", weight="bold", fontsize=10)
ax.text(102, 98, "WEAKENING", weight="bold", fontsize=10)
ax.text(96, 98, "LAGGING", weight="bold", fontsize=10)
ax.text(96, 102, "IMPROVING", weight="bold", fontsize=10)

# ---- Label overlap control ----
label_offsets = {}

def smart_offset(x, y):
    key = (round(x, 1), round(y, 1))
    offset = label_offsets.get(key, 0)
    label_offsets[key] = offset + 0.6
    return offset

# ---- Plot ETFs ----
for etf in visible_etfs:
    x = rs_ratio[etf].iloc[-tail_length:]
    y = rs_momentum[etf].iloc[-tail_length:]

    ax.plot(x, y, marker="o", linewidth=1.2, alpha=0.9)
    ax.scatter(x.iloc[-1], y.iloc[-1], s=160, edgecolor="black")

    offset = smart_offset(x.iloc[-1], y.iloc[-1])
    ax.text(
        x.iloc[-1] + 0.3,
        y.iloc[-1] + 0.3 + offset,
        etf,
        fontsize=9,
        weight="bold"
    )

# ---- Dynamic axis padding (anti-squeeze) ----
x_last = rs_ratio[visible_etfs].iloc[-1]
y_last = rs_momentum[visible_etfs].iloc[-1]

pad_x = (x_last.max() - x_last.min()) * 0.25
pad_y = (y_last.max() - y_last.min()) * 0.25

ax.set_xlim(x_last.min() - pad_x, x_last.max() + pad_x)
ax.set_ylim(y_last.min() - pad_y, y_last.max() + pad_y)

ax.set_xlabel("RS-Ratio")
ax.set_ylabel("RS-Momentum")
ax.set_title("Relative Rotation Graph (1Y, Weekly)")
ax.grid(True)

st.pyplot(fig)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    "<center>© 2026 Aditya Classes, Bikaner | ETF RRG Dashboard</center>",
    unsafe_allow_html=True
)

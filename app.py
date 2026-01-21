import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# SAFE DEFAULTS
# -----------------------------
quadrant_counts = {
    "Leading": 0,
    "Improving": 0,
    "Weakening": 0,
    "Lagging": 0
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def get_quadrant(rs_ratio, rs_momentum):
    if rs_ratio >= 100 and rs_momentum >= 100:
        return "Leading"
    elif rs_ratio >= 100 and rs_momentum < 100:
        return "Weakening"
    elif rs_ratio < 100 and rs_momentum < 100:
        return "Lagging"
    else:
        return "Improving"


def daily_entry_signal(df):
    close = df["Close"].copy()

    if len(close) < 21:
        return "NO"

    sma20 = close.rolling(20).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    price_now = close.iloc[-1].item()
    sma_now = sma20.iloc[-1].item()
    rsi_now = rsi.iloc[-1].item()
    rsi_prev = rsi.iloc[-2].item()

    return "YES" if (price_now > sma_now and rsi_now > 55 and rsi_now > rsi_prev) else "NO"


# -----------------------------
# COLOR SETTINGS
# -----------------------------
quadrant_colors = {
    "Leading": "#E6F4EA",
    "Weakening": "#FFF4E5",
    "Lagging": "#FDECEA",
    "Improving": "#E8F0FE"
}

sector_colors = {
    "Bank": "#1f77b4",
    "IT": "#ff7f0e",
    "FMCG": "#2ca02c",
    "Auto": "#d62728",
    "Pharma": "#9467bd",
    "Metal": "#8c564b",
    "Energy": "#e377c2"
}

# -----------------------------
# UI HEADER
# -----------------------------
st.set_page_config(
    page_title="Aditya Classes Bikaner – Market RRG Dashboard",
    page_icon="aditya_classes_logo.png",
    layout="centered"
)

# -----------------------------
# SUBTLE BRAND BACKGROUND (OPTIONAL)
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #fffdf8;  /* very light warm tone */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.image(
    "aditya_classes_logo.png",
    width=120
)

st.markdown(
    "<h2 style='margin-top:0'>Aditya Classes, Bikaner</h2>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='color:gray'>Market Relative Rotation Graph (RRG) Dashboard</p>",
    unsafe_allow_html=True
)

st.markdown("---")

st.markdown(
    """
    **Benchmark:** NIFTY 50 (via NIFTYBEES ETF)
    This Relative Rotation Graph (RRG) shows how major Indian sectors rotate
    between **Leading, Weakening, Lagging, and Improving** phases.
    """
)

benchmark_name = None
benchmark_symbol = None
benchmark_df = None

# -----------------------------
# BENCHMARK WITH FALLBACKS
# -----------------------------
benchmark_candidates = [
    ("NIFTY 50 (ETF)", "NIFTYBEES.NS"),
    ("NIFTY 50 (Index)", "^NSEI"),
    ("Bank Nifty (ETF)", "BANKBEES.NS"),
]

for name, symbol in benchmark_candidates:
    df = yf.download(symbol, period=period, progress=False)
    if not df.empty and "Close" in df.columns:
        benchmark_name = name
        benchmark_symbol = symbol
        benchmark_df = df
        break

if benchmark_df is None:
    st.error(
        "Benchmark data could not be loaded from Yahoo Finance.\n\n"
        "This is a temporary Yahoo Finance cloud issue.\n"
        "Please refresh the app after a few seconds."
    )
    st.stop()


sectors = {
    "Bank": "^NSEBANK",
    "IT": "^CNXIT",
    "FMCG": "^CNXFMCG",
    "Auto": "^CNXAUTO",
    "Pharma": "^CNXPHARMA",
    "Metal": "^CNXMETAL",
    "Energy": "^CNXENERGY"
}

# -----------------------------
# SIDEBAR CONTROLS
# -----------------------------
st.sidebar.image(
    "aditya_classes_logo.png",
    width=100
)

st.sidebar.header("RRG Controls")

rrg_timeframe = st.sidebar.selectbox(
    "RRG Timeframe",
    ["Daily", "Weekly", "Monthly"],
    index=1
)

period = st.sidebar.selectbox(
    "Data Period",
    ["1y", "2y", "3y"],
    index=1
)

mode = st.sidebar.radio(
    "Analysis Mode",
    ["Swing", "Positional"],
    index=1
)

tail_length = 5 if mode == "Swing" else 10
st.sidebar.caption(f"Tail Length auto-set to {tail_length}")

st.sidebar.markdown("---")
st.sidebar.subheader("Daily Entry Logic")
st.sidebar.markdown(
    """
    **YES when:**
    - Price > 20 DMA  
    - RSI(14) > 55  
    - RSI rising  

    *(Daily Entry applies only in Weekly RRG)*
    """
)

# -----------------------------
# SAFE DATA DOWNLOAD (FINAL)
# -----------------------------
prices = pd.DataFrame()

# ---- Benchmark (MANDATORY) ----
bench_df = yf.download(benchmark, period=period, progress=False)

if bench_df.empty or "Close" not in bench_df.columns:
    st.error("Benchmark data (NIFTY 50) could not be loaded. Please refresh the app.")
    st.stop()

prices["Benchmark"] = bench_df["Close"]

# ---- Sector data ----
for name, ticker in sectors.items():
    df = yf.download(ticker, period=period, progress=False)

    if df.empty or "Close" not in df.columns:
        continue  # skip failed sector download

    prices[name] = df["Close"]

# ---- Final cleanup ----
prices.dropna(inplace=True)

# -----------------------------
# APPLY TIMEFRAME
# -----------------------------
if rrg_timeframe == "Weekly":
    prices = prices.resample("W-FRI").last()
elif rrg_timeframe == "Monthly":
    prices = prices.resample("M").last()

prices.dropna(inplace=True)

# -----------------------------
# RRG CALCULATIONS
# -----------------------------
rs = prices[sectors.keys()].div(prices["Benchmark"], axis=0)
rs_ratio = 100 * rs / rs.rolling(14).mean()
rs_momentum = 100 * rs_ratio / rs_ratio.rolling(14).mean()

# -----------------------------
# DAILY DATA (FOR WEEKLY MODE)
# -----------------------------
daily_prices = {}
for name, ticker in sectors.items():
    df = yf.download(ticker, period="6mo", progress=False)
    df.dropna(inplace=True)
    daily_prices[name] = df

# -----------------------------
# RANKING TABLE
# -----------------------------
latest_data = []

for sector in sectors.keys():
    r = rs_ratio[sector].iloc[-1]
    m = rs_momentum[sector].iloc[-1]
    q = get_quadrant(r, m)

    if rrg_timeframe == "Weekly" and q in ["Leading", "Improving"]:
        daily_signal = daily_entry_signal(daily_prices[sector])
    elif rrg_timeframe == "Weekly":
        daily_signal = "—"
    else:
        daily_signal = "N/A"

    latest_data.append({
        "Sector": sector,
        "RS-Ratio": round(r, 2),
        "RS-Momentum": round(m, 2),
        "Quadrant": q,
        "Daily Entry": daily_signal
    })

ranking_df = pd.DataFrame(latest_data)

quadrant_order = {
    "Leading": 0,
    "Improving": 1,
    "Weakening": 2,
    "Lagging": 3
}

ranking_df["Order"] = ranking_df["Quadrant"].map(quadrant_order)
ranking_df = ranking_df.sort_values(["Order", "RS-Ratio"], ascending=[True, False]).drop(columns="Order")

quadrant_counts = (
    ranking_df["Quadrant"]
    .value_counts()
    .reindex(["Leading", "Improving", "Weakening", "Lagging"], fill_value=0)
)

# -----------------------------
# RRG PLOT
# -----------------------------
fig, ax = plt.subplots(figsize=(8, 8))

# -----------------------------
# QUADRANT BACKGROUND SHADING
# -----------------------------
ax.axvspan(100, 110, ymin=0.5, ymax=1.0, alpha=0.15, color="#C8E6C9")  # Leading
ax.axvspan(100, 110, ymin=0.0, ymax=0.5, alpha=0.15, color="#FFE0B2")  # Weakening
ax.axvspan(90, 100, ymin=0.0, ymax=0.5, alpha=0.15, color="#FFCDD2")  # Lagging
ax.axvspan(90, 100, ymin=0.5, ymax=1.0, alpha=0.15, color="#BBDEFB")  # Improving


ax.text(102, 102, "LEADING", fontsize=10, weight="bold")
ax.text(102, 98, "WEAKENING", fontsize=10, weight="bold")
ax.text(96, 98, "LAGGING", fontsize=10, weight="bold")
ax.text(96, 102, "IMPROVING", fontsize=10, weight="bold")

for sector in sectors.keys():
    x = rs_ratio[sector].iloc[-tail_length:]
    y = rs_momentum[sector].iloc[-tail_length:]

    color = sector_colors.get(sector, "#000000")

    ax.plot(x, y, marker="o", linewidth=1, color=color, alpha=0.9)
    ax.scatter(x.iloc[-1], y.iloc[-1], s=180, color=color, edgecolor="black")

    ax.text(x.iloc[-1] + 0.3, y.iloc[-1] + 0.3, sector, fontsize=9, weight="bold")

ax.set_xlabel("RS-Ratio")
ax.set_ylabel("RS-Momentum")
ax.set_title(f"Relative Rotation Graph – {rrg_timeframe}")
ax.grid(True)

st.pyplot(fig)

# -----------------------------
# SNAPSHOT + TABLE
# -----------------------------
st.subheader("Market Rotation Snapshot")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Leading", quadrant_counts["Leading"])
c2.metric("Improving", quadrant_counts["Improving"])
c3.metric("Weakening", quadrant_counts["Weakening"])
c4.metric("Lagging", quadrant_counts["Lagging"])

st.subheader(f"Sector Rotation Ranking ({rrg_timeframe})")

def highlight_row(row):
    bg = quadrant_colors.get(row["Quadrant"], "#FFFFFF")
    style = f"background-color: {bg}; color: black"
    if row["Daily Entry"] == "YES":
        style += "; font-weight: bold; border-left: 6px solid #2E7D32"
    return [style] * len(row)

st.dataframe(
    ranking_df.style.apply(highlight_row, axis=1),
    width="stretch"
)

st.markdown("---")
st.markdown(
    "<center>© 2026 Aditya Classes, Bikaner | Market Analytics Dashboard</center>",
    unsafe_allow_html=True
)

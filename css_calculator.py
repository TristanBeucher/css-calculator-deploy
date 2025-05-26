import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --- Load dataset ---
df = pd.read_csv(
    "data/unified_energy_dataset.csv", parse_dates=["Datetime"], low_memory=False
)
df.set_index("Datetime", inplace=True)

# --- Sidebar Controls ---
st.sidebar.markdown(
    "<h2 style='margin-top: -40px;'>⚙️ Parameters</h2>", unsafe_allow_html=True
)

country = st.sidebar.selectbox("Select Power Market (Country)", options=["FR", "BE"])
gas_index = st.sidebar.selectbox(
    "Select Gas Index",
    options=["PEG", "TTF", "THE", "CEGH VTP", "CZ VTP", "ETF", "NBP", "PVB", "ZTP"],
)
efficiency = (
    st.sidebar.slider("Efficiency (%)", min_value=30, max_value=65, value=50) / 100
)
emission_factor_th = st.sidebar.slider(
    "Emission Factor (tCO₂/MWh_th)", min_value=0.050, max_value=0.250, value=0.090
)
variable_cost = st.sidebar.number_input("Variable Cost (€/MWh)", value=2.0)

# --- Date selection ---
dates = df.index.date
min_date = max(min(dates), pd.to_datetime("2025-04-01").date())
max_date = max(dates)

start_date, end_date = st.sidebar.date_input(
    "Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date
)

# --- Filter dataframe by date ---
mask = (df.index.date >= start_date) & (df.index.date <= end_date)
df_filtered = df[mask].copy()
df_filtered.index = pd.to_datetime(df_filtered.index)


# --- Calculate Clean Spark Spread (CSS) ---
df_filtered["CSS"] = (
    df_filtered[country]
    - df_filtered[gas_index] / efficiency
    - df_filtered["EUA Prices"] * (emission_factor_th / efficiency)
    - variable_cost
)

# --- Main View ---
st.markdown(
    "<h1 style='margin-top: -60px;'>⚡ Clean Spark Spread Dashboard</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    """Visualize the Clean Spark Spread based on power, gas, and CO₂ prices, with user-defined plant parameters."""
)

css_series = df_filtered["CSS"]
time_index = df_filtered.index

fig = go.Figure()

# Clean Spark Spread line
fig.add_trace(
    go.Scatter(
        x=df_filtered.index,
        y=df_filtered["CSS"],
        mode="lines",
        name="Clean Spark Spread",
        line=dict(color="black"),
    )
)

# Green area (CSS > 0)
fig.add_trace(
    go.Bar(
        x=df_filtered.index,
        y=df_filtered["CSS"].clip(lower=0),  # Keep only positive values
        marker_color="rgba(0, 200, 0, 0.2)",
        name="Positive CSS",
        hoverinfo="skip",
    )
)

# Red area (CSS < 0)
fig.add_trace(
    go.Bar(
        x=df_filtered.index,
        y=df_filtered["CSS"].clip(upper=0),  # Keep only negative values
        marker_color="rgba(255, 0, 0, 0.2)",
        name="Negative CSS",
        hoverinfo="skip",
    )
)

# Layout adjustments
fig.update_layout(
    barmode="overlay",
    yaxis_title="€/MWh",
    showlegend=False,
    height=400,
    margin=dict(l=20, r=20, t=30, b=20),
)

st.plotly_chart(fig, use_container_width=True)

# Filter between 08:00 and 20:00 (inclusive)
peak_css = df_filtered.between_time("08:00", "20:00")["CSS"]

# Centered metrics using HTML and flexbox
avg_css = round(df_filtered["CSS"].mean(), 2)
peak_css = round(df_filtered.between_time("08:00", "20:00")["CSS"].mean(), 2)

st.markdown(
    f"""
<div style='display: flex; justify-content: center; gap: 50px; margin-top: -10px; margin-bottom: 20px;'>
    <div>
        <h4 style='text-align: center;'>Average CSS (€/MWh)</h4>
        <p style='font-size: 32px; font-weight: bold; text-align: center;'>{avg_css}</p>
    </div>
    <div>
        <h4 style='text-align: center;'>Average Peak CSS (€/MWh)</h4>
        <p style='font-size: 32px; font-weight: bold; text-align: center;'>{peak_css}</p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# --- Optional: Display data table ---
with st.expander("🔍 View Raw Data"):
    st.dataframe(df_filtered[[country, gas_index, "EUA Prices", "CSS"]])

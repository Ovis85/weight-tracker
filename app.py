import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

SHEET_ID = "16i8iuwieWRI7nIu4JpZjnvg9PEWCMOPPCWgAawr7wpY"
SHEET_NAME = "Weight track"
CREDENTIALS_FILE = "/Users/brianly/Documents/Projects_2026/Weight_trackers/resoruce/trackers-494815-b3b138998176.json"
GOAL_WEIGHT = 64.0
WEEKLY_LOSS_RATE = 0.25  # kg per week


@st.cache_data(ttl=300)
def load_data():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    else:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    df = pd.DataFrame(sheet.get_all_records())

    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    for col in ["Weight", "7da", "7ma", "3ma"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.sort_values("Date").reset_index(drop=True)


st.set_page_config(page_title="Weight Tracker", layout="wide")
st.title("Weight Tracker")

if st.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

latest = df.dropna(subset=["Weight"]).iloc[-1]
current_weight = latest["Weight"]
start_weight = df.dropna(subset=["Weight"]).iloc[0]["Weight"]
remaining = current_weight - GOAL_WEIGHT
weeks_to_goal = remaining / WEEKLY_LOSS_RATE
last_date = latest["Date"]
projected_date = last_date + timedelta(weeks=weeks_to_goal)
progress = max(0.0, min(1.0, (start_weight - current_weight) / (start_weight - GOAL_WEIGHT)))

# --- Metrics ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Current", f"{current_weight:.1f} kg")
c2.metric("Goal", f"{GOAL_WEIGHT} kg")
c3.metric("To go", f"{remaining:.1f} kg")
c4.metric("Est. goal date", projected_date.strftime("%d %b %Y"))

st.progress(progress, text=f"{progress * 100:.1f}% of the way there")

# --- Chart ---
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"], y=df["Weight"],
    mode="lines+markers",
    name="Weight",
    line=dict(color="#2196F3", width=2),
    marker=dict(size=4),
))
fig.add_trace(go.Scatter(
    x=df["Date"], y=df["7ma"],
    mode="lines",
    name="7-Day MA",
    line=dict(color="#FF9800", width=2),
))
fig.add_trace(go.Scatter(
    x=df["Date"], y=df["3ma"],
    mode="lines",
    name="3-Day MA",
    line=dict(color="#4CAF50", width=2),
))

sundays = df.dropna(subset=["7da"])
fig.add_trace(go.Scatter(
    x=sundays["Date"], y=sundays["7da"],
    mode="markers",
    name="Weekly Avg",
    marker=dict(size=9, color="#E91E63", symbol="diamond"),
))

# Goal line
fig.add_hline(
    y=GOAL_WEIGHT,
    line_dash="dash",
    line_color="red",
    annotation_text=f"Goal: {GOAL_WEIGHT} kg",
)

# Projection
fig.add_trace(go.Scatter(
    x=[last_date, projected_date],
    y=[current_weight, GOAL_WEIGHT],
    mode="lines",
    name="Projection",
    line=dict(color="red", width=1, dash="dot"),
))

chart_start = df.dropna(subset=["Weight"])["Date"].min()
chart_end = projected_date

fig.update_layout(
    xaxis=dict(range=[chart_start, chart_end]),
    xaxis_title="Date",
    yaxis_title="Weight (kg)",
    hovermode="x unified",
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

st.plotly_chart(fig, use_container_width=True)

# --- Weekly averages chart ---
st.subheader("Weekly Averages (7da)")
sundays_only = df.dropna(subset=["7da"])
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=sundays_only["Date"],
    y=sundays_only["7da"],
    name="Weekly Avg",
    marker_color="#00897B",
))
fig2.add_hline(
    y=GOAL_WEIGHT,
    line_dash="dash",
    line_color="red",
    annotation_text=f"Goal: {GOAL_WEIGHT} kg",
)
fig2.update_layout(
    xaxis=dict(range=[chart_start, chart_end]),
    xaxis_title="Week ending",
    yaxis_title="Weight (kg)",
    hovermode="x unified",
    height=350,
    yaxis=dict(range=[min(sundays_only["7da"].min() - 1, GOAL_WEIGHT - 1), sundays_only["7da"].max() + 1]),
)
st.plotly_chart(fig2, use_container_width=True)

# --- Recent entries ---
st.subheader("Recent Entries")
recent = df.dropna(subset=["Weight"]).tail(14).sort_values("Date", ascending=False).copy()
recent["Date"] = recent["Date"].dt.strftime("%d/%m/%Y")
st.markdown(recent.to_html(index=False), unsafe_allow_html=True)

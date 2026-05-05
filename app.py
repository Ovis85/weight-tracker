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


def get_creds(readonly=True):
    if readonly:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
    else:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)


@st.cache_data(ttl=300)
def load_data():
    client = gspread.authorize(get_creds(readonly=True))
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    df = pd.DataFrame(sheet.get_all_records())

    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    for col in ["Weight", "7da", "7ma", "3ma"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.sort_values("Date").reset_index(drop=True)


def log_weight(date, weight):
    client = gspread.authorize(get_creds(readonly=False))
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    date_str = date.strftime("%d/%m/%Y")
    cell = sheet.find(date_str)
    if cell:
        sheet.update_cell(cell.row, 3, weight)
        return True
    return False


ANALYSIS_MARKDOWN = """*Last updated: 5 May 2026*

## Headlines
- **Down 2.60 kg overall** (70.40 → 67.80) over 76 days at **0.24 kg/week** — right on your 0.25 target.
- **Last 30 days: -1.45 kg.** Pace has *accelerated* — nearly double the 0.18 kg/week running average.
- **Last 7 days: -0.65 kg.** Your best week of the cut. The "first uptick" worry from last week was noise.

## Trend Analysis
- **Daily**: still ~0.5 kg weekly oscillation — Mon/Wed lightest, Fri/Sat heaviest. Pattern unchanged.
- **Weekly (7-day avgs)**: 70.35 → 70.18 → 69.98 → 69.55 → 69.27 → 68.94 → 68.89 → 68.05 → **68.09** → trending toward ~67.85 next Sunday.
  The Apr 26 → May 3 jump (+0.04) was effectively flat, not a reversal. The 7-day rolling MA has dropped from 68.26 (May 1) to **67.87** today — a 0.39 kg drop in 4 days.
- **Overall**: clean linear descent. Last 60 days: -2.05 kg. Last 30 days: -1.45 kg. Most recent stretch is the steepest of the cut.

## Interesting Facts
1. **Yesterday (Mon May 4) was a new all-time low: 67.55 kg.** The previous floor (67.65 on Apr 22) held for almost 2 weeks before being broken.
2. **Mondays are your high-signal day.** Avg daily change on Mondays across the cut: **-0.20 kg** — by far your biggest drop day. Tuesday adds another -0.09. By Wednesday you're at the week's true reading.
3. **Weekend damage has shrunk.** Sat+Sun combined averaged +0.21 kg early in the cut; the last two weekends netted -0.10 and -0.45. Whatever you changed in late April is working.
4. **You're now 3.80 kg from start, 3.80 kg into a 6.40 kg cut — exactly 41% to goal.** At current 30-day pace (1.45 kg/month) you hit 64.0 in **~11 weeks** (mid-July). At the original 0.25/week pace it's 15 weeks.
5. **The Sydney trip cost you nothing.** You logged 68.25 on return (Apr 20) and you're 0.45 kg below that 15 days later. Travel is not your bottleneck.

## Actionable Takeaways
- **Hold the line — don't celebrate-eat.** A 0.65 kg week feels like license to relax; that's exactly when people give back two weeks of progress in one weekend.
- **Watch Sunday May 10's 7da.** A reading ≤67.90 confirms you've moved into a new range. ≤67.70 would be a meaningful step-down.
- **Lock the weekend behaviors.** The last two weekends were unusually clean — figure out what was different (food consistency? earlier dinners? lower alcohol?) and keep doing it.
- **Re-check body comp around 66.5 kg**, not at the goal. If muscle mass is holding, the 64 kg target stays valid; if you're shedding lean tissue, you may want to slow the rate or recalculate the target.
- **Sub-goal: 67.0 by May 19.** That's 0.80 kg in 2 weeks — slightly above your average pace but well inside the last 7 days' rate.

## Watch For
- **Mon/Tue rebounds above 68.0.** With 7ma at 67.87, any Mon or Tue reading >68.0 means the trend has stalled. Last 4 Mondays: 68.25, 68.45, 67.55 — the May 4 reading is the new benchmark.
- **A 7da increase ≥0.20 kg.** One flat Sunday is fine; a real rise is the signal to look at calories/sleep/training, not the day-to-day noise.
- **Friday spikes >0.40 kg.** Pattern from late April held — Thu→Fri averages +0.07 but spikes flag a high-sodium or high-carb Thursday worth noting.
"""


st.set_page_config(page_title="Weight Tracker", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* ---------- Hide Streamlit chrome ---------- */
header[data-testid="stHeader"] {display: none;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stToolbar"] {display: none;}

/* ---------- Page ---------- */
.stApp {
    background: linear-gradient(180deg, #F7F5F0 0%, #FAFAF9 100%);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", system-ui, sans-serif;
    color: #2A2A2A !important;
}

/* Force dark text everywhere */
.stApp, .stApp p, .stApp span, .stApp div, .stApp li, .stApp strong, .stApp em {
    color: #2A2A2A;
}
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown strong {
    color: #2A2A2A !important;
}
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 4rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 720px;
}

/* ---------- Title ---------- */
h1 {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #1A1A1A !important;
    margin-bottom: 1rem !important;
    padding: 0 !important;
}

/* ---------- Refresh button ---------- */
button[kind="secondary"] {
    background: white !important;
    border: 1px solid #E5E5E0 !important;
    border-radius: 12px !important;
    color: #555 !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 0.4rem 0.9rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    transition: all 0.15s ease;
}
button[kind="secondary"]:hover {
    border-color: #C0C0B8 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

/* ---------- Today's banner ---------- */
[data-testid="stAlert"] {
    background: white !important;
    border: 1px solid #ECEAE3 !important;
    border-left: 4px solid #00897B !important;
    border-radius: 14px !important;
    padding: 1rem 1.1rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-top: 0.5rem !important;
}
[data-testid="stAlert"] p {
    color: #2A2A2A !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
}

/* ---------- Metric cards ---------- */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #ECEAE3;
    border-radius: 16px;
    padding: 1.1rem 1.2rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
[data-testid="stMetricLabel"] {
    color: #888 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetricValue"] {
    color: #1A1A1A !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

/* ---------- Progress bar ---------- */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #00897B 0%, #4CAF50 100%) !important;
    border-radius: 999px !important;
}
.stProgress > div > div {
    background: #ECEAE3 !important;
    border-radius: 999px !important;
    height: 8px !important;
}

/* ---------- Tabs ---------- */
[data-baseweb="tab-list"] {
    gap: 4px !important;
    background: #ECEAE3 !important;
    padding: 4px !important;
    border-radius: 12px !important;
    margin-bottom: 1.5rem !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: #666 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.5rem 1rem !important;
    flex: 1 !important;
    justify-content: center !important;
    transition: all 0.15s ease;
}
[data-baseweb="tab"][aria-selected="true"] {
    background: white !important;
    color: #1A1A1A !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
    display: none !important;
}

/* ---------- Subheaders ---------- */
h2, h3 {
    color: #1A1A1A !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
}

/* ---------- Plotly chart container ---------- */
.js-plotly-plot {
    background: white !important;
    border: 1px solid #ECEAE3 !important;
    border-radius: 16px !important;
    padding: 0.5rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
/* Force chart text colors */
.js-plotly-plot text, .js-plotly-plot .legendtext, .js-plotly-plot .xtick text, .js-plotly-plot .ytick text {
    fill: #555 !important;
}
.js-plotly-plot .annotation-text {
    fill: #E76F51 !important;
}

/* ---------- Recent entries table ---------- */
table {
    width: 100%;
    background: white;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #ECEAE3;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    border-collapse: separate !important;
    border-spacing: 0;
    font-size: 0.85rem;
}
table th {
    background: #F7F5F0 !important;
    color: #666 !important;
    font-weight: 600 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.7rem 0.6rem !important;
    text-align: left;
    border: none !important;
}
table td {
    padding: 0.6rem !important;
    border: none !important;
    border-top: 1px solid #F0EEE8 !important;
    color: #2A2A2A;
}

/* ---------- AI Analysis tab content ---------- */
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 0.5rem;
}

/* AI tab markdown styling — give it some breathing room */
.stTabs [data-baseweb="tab-panel"] h2 {
    font-size: 1.1rem !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.6rem !important;
    color: #00897B !important;
}
.stTabs [data-baseweb="tab-panel"] ul, .stTabs [data-baseweb="tab-panel"] ol {
    padding-left: 1.2rem;
}
.stTabs [data-baseweb="tab-panel"] li {
    margin-bottom: 0.4rem;
    line-height: 1.55;
}

/* ---------- Mobile tweaks ---------- */
@media (max-width: 600px) {
    h1 { font-size: 1.5rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
    .block-container { padding-left: 0.75rem !important; padding-right: 0.75rem !important; }
}
</style>
""", unsafe_allow_html=True)

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

# --- Daily insight ---
actual_for_insight = df.dropna(subset=["Weight"]).copy()
actual_for_insight["change"] = actual_for_insight["Weight"].diff()
today_day = latest["Day"]
prev = actual_for_insight.iloc[-2] if len(actual_for_insight) >= 2 else None
delta = current_weight - prev["Weight"] if prev is not None else 0

insights = {
    "Mon": "Mondays avg −0.19 kg — your biggest weekly drop. Real progress shows here.",
    "Tue": "Tuesdays keep the Monday flush going (avg −0.12 kg). Trend day.",
    "Wed": "Wednesday is your true weight day — avg lightest of the week. Trust this number.",
    "Thu": "Thursdays trend down lightly (avg −0.07 kg). Still your 'real' zone.",
    "Fri": "Fridays start creeping up (avg +0.07 kg). Don't panic — it's water, not fat.",
    "Sat": "Saturdays are your peak gain day (avg +0.13 kg). Ignore the scale today.",
    "Sun": "Sundays are statistically your heaviest day. Wait for Wednesday for the truth.",
}

st.info(f"**Today ({today_day} {last_date.strftime('%d %b')}): {current_weight:.2f} kg ({delta:+.2f} kg)** — {insights.get(today_day, '')}")

tab_overview, tab_ai = st.tabs(["Overview", "AI Analysis"])

with tab_overview:
    c1, c2 = st.columns(2)
    c1.metric("Current", f"{current_weight:.1f} kg")
    c2.metric("Goal", f"{GOAL_WEIGHT} kg")
    c3, c4 = st.columns(2)
    c3.metric("To go", f"{remaining:.1f} kg")
    c4.metric("Est. goal date", projected_date.strftime("%d %b %Y"))

    st.progress(progress, text=f"{progress * 100:.1f}% of the way there")

    actual = df.dropna(subset=["Weight"])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=actual["Date"], y=actual["Weight"],
        mode="lines+markers",
        name="Weight",
        line=dict(color="#CBC2B0", width=1),
        marker=dict(size=3, color="#A89E89"),
        opacity=0.6,
    ))
    fig.add_trace(go.Scatter(
        x=actual["Date"], y=actual["3ma"],
        mode="lines",
        name="3-Day Avg",
        line=dict(color="#EA580C", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=actual["Date"], y=actual["7ma"],
        mode="lines",
        name="7-Day Avg",
        line=dict(color="#0F766E", width=3.5),
    ))

    sundays = actual.dropna(subset=["7da"])
    fig.add_trace(go.Scatter(
        x=sundays["Date"], y=sundays["7da"],
        mode="markers",
        name="Weekly Avg",
        marker=dict(size=11, color="#1E293B", symbol="diamond", line=dict(width=2, color="white")),
    ))

    fig.add_hline(
        y=GOAL_WEIGHT,
        line_dash="dash",
        line_color="#DC2626",
        line_width=1.5,
        annotation_text=f"Goal: {GOAL_WEIGHT} kg",
        annotation_font=dict(color="#DC2626", size=11, family="-apple-system, system-ui"),
        annotation_position="top right",
    )

    fig.add_trace(go.Scatter(
        x=[last_date, projected_date],
        y=[current_weight, GOAL_WEIGHT],
        mode="lines",
        name="Projection",
        line=dict(color="#DC2626", width=1.5, dash="dot"),
        opacity=0.5,
    ))

    chart_start = actual["Date"].min()
    chart_end = projected_date

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="-apple-system, BlinkMacSystemFont, system-ui, sans-serif", color="#555"),
        xaxis=dict(
            range=[chart_start, chart_end],
            tickangle=-45,
            tickfont=dict(size=10, color="#888"),
            fixedrange=True,
            gridcolor="#F0EEE8",
            linecolor="#ECEAE3",
            showline=False,
            zeroline=False,
        ),
        yaxis=dict(
            tickfont=dict(size=10, color="#888"),
            fixedrange=True,
            gridcolor="#F0EEE8",
            linecolor="#ECEAE3",
            showline=False,
            zeroline=False,
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="system-ui", bordercolor="#ECEAE3"),
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#666"),
            bgcolor="rgba(255,255,255,0)",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False})

    st.subheader("Recent Entries")
    recent = actual.tail(14).sort_values("Date", ascending=False).copy()
    recent["Date"] = recent["Date"].dt.strftime("%d/%m/%Y")
    st.markdown(recent.to_html(index=False), unsafe_allow_html=True)

with tab_ai:
    st.markdown(ANALYSIS_MARKDOWN)

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import numpy as np
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
    if "Waist" in df.columns:
        df["Waist"] = pd.to_numeric(df["Waist"], errors="coerce")

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
last_date = latest["Date"]
progress = max(0.0, min(1.0, (start_weight - current_weight) / (start_weight - GOAL_WEIGHT)))


def project_goal_date(actual_df, goal, days_window=30):
    """Linear regression on the last `days_window` days; project to goal weight."""
    cutoff = actual_df["Date"].iloc[-1] - timedelta(days=days_window)
    recent = actual_df[actual_df["Date"] >= cutoff]
    if len(recent) < 7:
        return None, None
    x = (recent["Date"] - recent["Date"].iloc[0]).dt.days.values.astype(float)
    y = recent["Weight"].values.astype(float)
    slope, intercept = np.polyfit(x, y, 1)
    if slope >= -0.001:
        return None, slope
    last_x = x[-1]
    current_fit = intercept + slope * last_x
    days_to_goal = (goal - current_fit) / slope
    return recent["Date"].iloc[-1] + timedelta(days=days_to_goal), slope


actual_full = df.dropna(subset=["Weight"]).reset_index(drop=True)
projected_date, recent_slope = project_goal_date(actual_full, GOAL_WEIGHT)
recent_pace_per_wk = -recent_slope * 7 if recent_slope is not None else None

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
    if projected_date is not None:
        pace_label = f"@ {recent_pace_per_wk:.2f} kg/wk (last 30d)"
        c4.metric("Est. goal date", projected_date.strftime("%d %b %Y"), pace_label, delta_color="off")
    else:
        c4.metric("Est. goal date", "Stalled", "no recent loss", delta_color="off")

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

    if projected_date is not None:
        fig.add_trace(go.Scatter(
            x=[last_date, projected_date],
            y=[current_weight, GOAL_WEIGHT],
            mode="lines",
            name="Projection",
            line=dict(color="#DC2626", width=1.5, dash="dot"),
            opacity=0.5,
        ))

    chart_start = actual["Date"].min()
    chart_end = projected_date if projected_date is not None else last_date + timedelta(days=30)

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

    # ---------- On Track? ----------
    st.subheader("On Track?")

    SLOW_BAND = 0.15
    FAST_BAND = 0.40

    def classify_pace(loss_per_wk):
        """Return (status, color) for a positive loss-per-week value."""
        if loss_per_wk <= 0:
            return "Gained", "#DC2626"
        if loss_per_wk < SLOW_BAND:
            return "Too slow", "#D97706"
        if loss_per_wk > FAST_BAND:
            return "Too fast", "#EA580C"
        return "On target", "#15803D"

    days_in = (last_date - actual["Date"].iloc[0]).days
    expected_loss = (days_in / 7) * WEEKLY_LOSS_RATE
    actual_loss = start_weight - current_weight
    overall_loss_per_wk = actual_loss / (days_in / 7) if days_in > 0 else 0
    diff_vs_plan = actual_loss - expected_loss

    ov_verdict, ov_color = classify_pace(overall_loss_per_wk)
    if ov_verdict == "Too fast":
        ov_verdict = "Too fast — muscle-loss risk"

    diff_color = "#15803D" if diff_vs_plan >= 0 else "#D97706"
    diff_label = "ahead of plan" if diff_vs_plan >= 0 else "behind plan"

    st.markdown(
        f"""<div style='background:white; border:1px solid #ECEAE3; border-left:4px solid {ov_color};
                      border-radius:14px; padding:1rem 1.2rem; margin-bottom:1rem;
                      box-shadow:0 2px 8px rgba(0,0,0,0.03)'>
            <div style='color:#888; font-size:0.78rem; font-weight:500; text-transform:uppercase; letter-spacing:0.05em'>Overall pace</div>
            <div style='color:{ov_color}; font-size:1.4rem; font-weight:700; margin:0.2rem 0'>{ov_verdict}</div>
            <div style='color:#555; font-size:0.92rem; line-height:1.55'>
                <strong>{overall_loss_per_wk:.2f} kg/wk</strong> over {days_in} days vs target <strong>{WEEKLY_LOSS_RATE} kg/wk</strong>.
                Lost <strong>{actual_loss:.2f} kg</strong>; plan said <strong>{expected_loss:.2f} kg</strong> by now —
                <span style='color:{diff_color}; font-weight:600'>{abs(diff_vs_plan):.2f} kg {diff_label}</span>.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Per-window pace cards, all framed vs the 0.25 kg/wk target.
    def window_loss_per_wk(days):
        cutoff = last_date - timedelta(days=days)
        sub = actual[actual["Date"] <= cutoff]
        if sub.empty:
            return None
        return (sub.iloc[-1]["Weight"] - current_weight) / (days / 7)

    pace_windows = [
        ("Last 7 days", window_loss_per_wk(7)),
        ("Last 30 days", window_loss_per_wk(30)),
        ("Overall", overall_loss_per_wk),
    ]

    pace_cards_html = "<div style='display:grid; grid-template-columns:repeat(3, 1fr); gap:0.6rem; margin-bottom:1rem'>"
    for label, lpw in pace_windows:
        if lpw is None:
            pace_cards_html += (
                f"<div style='background:white; border:1px solid #ECEAE3; border-radius:14px; "
                f"padding:0.8rem 0.9rem; box-shadow:0 2px 8px rgba(0,0,0,0.03)'>"
                f"<div style='color:#888; font-size:0.7rem; font-weight:500; text-transform:uppercase; letter-spacing:0.05em'>{label}</div>"
                f"<div style='color:#1A1A1A; font-size:1.15rem; font-weight:700; margin-top:0.2rem'>—</div>"
                f"</div>"
            )
            continue
        status, color = classify_pace(lpw)
        diff_to_target = lpw - WEEKLY_LOSS_RATE
        diff_text = f"{diff_to_target:+.2f} vs target"
        pace_cards_html += (
            f"<div style='background:white; border:1px solid #ECEAE3; border-radius:14px; "
            f"padding:0.8rem 0.9rem; box-shadow:0 2px 8px rgba(0,0,0,0.03)'>"
            f"<div style='color:#888; font-size:0.7rem; font-weight:500; text-transform:uppercase; letter-spacing:0.05em'>{label}</div>"
            f"<div style='color:#1A1A1A; font-size:1.15rem; font-weight:700; margin-top:0.2rem'>−{lpw:.2f} kg/wk</div>"
            f"<div style='color:{color}; font-size:0.78rem; font-weight:600; margin-top:0.15rem'>{status}</div>"
            f"<div style='color:#999; font-size:0.72rem; margin-top:0.1rem'>{diff_text}</div>"
            f"</div>"
        )
    pace_cards_html += "</div>"
    st.markdown(pace_cards_html, unsafe_allow_html=True)

    # 2-week rolling weekly bars (smoothed to absorb single-Sunday noise).
    sundays_df = actual.dropna(subset=["7da"]).sort_values("Date").reset_index(drop=True)
    if len(sundays_df) >= 3:
        wk_dates, wk_deltas, wk_colors = [], [], []
        for i in range(2, len(sundays_df)):
            delta = (sundays_df.iloc[i]["7da"] - sundays_df.iloc[i - 2]["7da"]) / 2
            loss = -delta
            _, color = classify_pace(loss)
            wk_dates.append(sundays_df.iloc[i]["Date"])
            wk_deltas.append(delta)
            wk_colors.append(color)

        wk_fig = go.Figure()
        wk_fig.add_hrect(y0=-FAST_BAND, y1=-SLOW_BAND, fillcolor="#15803D", opacity=0.08, line_width=0)
        wk_fig.add_hline(
            y=-WEEKLY_LOSS_RATE,
            line_dash="dash", line_color="#0F766E", line_width=1.5,
            annotation_text=f"Target −{WEEKLY_LOSS_RATE} kg/wk",
            annotation_font=dict(color="#0F766E", size=10),
            annotation_position="top right",
        )
        wk_fig.add_hline(y=0, line_color="#CBC2B0", line_width=1)
        wk_fig.add_trace(go.Bar(
            x=wk_dates, y=wk_deltas,
            marker=dict(color=wk_colors),
            text=[f"{d:+.2f}" for d in wk_deltas],
            textposition="outside",
            textfont=dict(size=10, color="#444"),
            hovertemplate="Week ending %{x|%d %b}<br>2-wk avg Δ %{y:+.2f} kg<extra></extra>",
        ))
        wk_fig.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="-apple-system, system-ui, sans-serif", color="#555"),
            xaxis=dict(tickangle=-45, tickfont=dict(size=10, color="#888"),
                       fixedrange=True, gridcolor="#F0EEE8", showline=False, zeroline=False),
            yaxis=dict(tickfont=dict(size=10, color="#888"),
                       title=dict(text="2-wk rolling Δ (kg)", font=dict(size=11, color="#666")),
                       fixedrange=True, gridcolor="#F0EEE8", showline=False, zeroline=False),
            height=300,
            margin=dict(l=10, r=10, t=20, b=10),
            showlegend=False,
            bargap=0.35,
        )
        st.plotly_chart(wk_fig, use_container_width=True,
                        config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False})

        st.markdown(
            f"""<div style='color:#666; font-size:0.85rem; margin-top:-0.5rem; line-height:1.5'>
            Each bar = 2-week rolling pace at that Sunday (smoothed to absorb single-week noise).
            Green band = on-target (−{SLOW_BAND} to −{FAST_BAND} kg/wk).
            </div>""",
            unsafe_allow_html=True,
        )

    # ---------- Waist ----------
    st.subheader("Waist")

    if "Waist" not in df.columns:
        st.markdown(
            """<div style='color:#888; font-size:0.92rem; padding:0.9rem 1rem;
                          background:white; border:1px solid #ECEAE3;
                          border-radius:12px; line-height:1.5'>
            No <code>Waist</code> column in the sheet yet — add it as a header in column G,
            then log Sunday measurements. Chart will appear automatically.
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        waist_data = df.dropna(subset=["Waist"]).sort_values("Date").reset_index(drop=True)
        if waist_data.empty:
            st.markdown(
                """<div style='color:#888; font-size:0.92rem; padding:0.9rem 1rem;
                              background:white; border:1px solid #ECEAE3;
                              border-radius:12px; line-height:1.5'>
                No measurements yet — log your first reading on Sunday morning
                (fasted, at navel, relaxed exhale).
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            latest_waist = waist_data.iloc[-1]["Waist"]
            first_waist = waist_data.iloc[0]["Waist"]
            delta_waist = latest_waist - first_waist
            wc1, wc2 = st.columns(2)
            wc1.metric("Current", f"{latest_waist:.1f} cm")
            wc2.metric("Δ since start",
                       f"{delta_waist:+.1f} cm" if len(waist_data) >= 2 else "—")

            if len(waist_data) >= 2:
                wfig = go.Figure()
                wfig.add_trace(go.Scatter(
                    x=waist_data["Date"], y=waist_data["Waist"],
                    mode="lines+markers",
                    name="Waist",
                    line=dict(color="#0F766E", width=2.5),
                    marker=dict(size=8, color="#0F766E"),
                ))
                wfig.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    font=dict(family="-apple-system, system-ui, sans-serif", color="#555"),
                    xaxis=dict(tickangle=-45, tickfont=dict(size=10, color="#888"),
                               fixedrange=True, gridcolor="#F0EEE8", showline=False, zeroline=False),
                    yaxis=dict(tickfont=dict(size=10, color="#888"),
                               title=dict(text="cm", font=dict(size=11, color="#666")),
                               fixedrange=True, gridcolor="#F0EEE8", showline=False, zeroline=False),
                    height=280,
                    margin=dict(l=10, r=10, t=20, b=10),
                    showlegend=False,
                )
                st.plotly_chart(wfig, use_container_width=True,
                                config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False})
            else:
                st.markdown(
                    "<div style='color:#888; font-size:0.85rem; margin-top:0.4rem'>"
                    "First reading logged — trend chart appears from your second measurement.</div>",
                    unsafe_allow_html=True,
                )

    # ---------- By Day of Week ----------
    st.subheader("By Day of Week")

    dow_df = actual.copy()
    dow_df["change"] = dow_df["Weight"].diff()
    dow_df["dow"] = dow_df["Date"].dt.day_name().str[:3]

    overall_dow = dow_df.groupby("dow")["change"].mean()

    sundays = dow_df[dow_df["dow"] == "Sun"]["Date"]
    if not sundays.empty:
        last_sun = sundays.max()
        recent_start = last_sun - timedelta(days=13)
        recent_dow_df = dow_df[(dow_df["Date"] >= recent_start) & (dow_df["Date"] <= last_sun)]
        recent_dow = recent_dow_df.groupby("dow")["change"].mean()
        recent_label = f"Last 2 wks (to {last_sun.strftime('%d %b')})"
    else:
        recent_dow = pd.Series(dtype=float)
        recent_label = "Last 2 wks"

    def fmt_change(v):
        return "—" if pd.isna(v) else f"{v:+.2f} kg"

    def change_color(v):
        if pd.isna(v):
            return "#888"
        return "#0F766E" if v < 0 else "#B45309"

    dow_rows = ""
    for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        a = overall_dow.get(d, float("nan"))
        r = recent_dow.get(d, float("nan"))
        dow_rows += (
            f"<tr><td>{d}</td>"
            f"<td style='text-align:right; color:{change_color(a)}; font-weight:600'>{fmt_change(a)}</td>"
            f"<td style='text-align:right; color:{change_color(r)}; font-weight:600'>{fmt_change(r)}</td></tr>"
        )

    st.markdown(
        f"""<table>
        <thead><tr><th>Day</th>
        <th style='text-align:right'>All-time avg</th>
        <th style='text-align:right'>{recent_label}</th></tr></thead>
        <tbody>{dow_rows}</tbody>
        </table>""",
        unsafe_allow_html=True,
    )

    # ---------- Weekend Damage ----------
    st.subheader("Weekend Damage")

    weekends_list = []
    for sun_date in dow_df[dow_df["dow"] == "Sun"]["Date"]:
        sat_date = sun_date - timedelta(days=1)
        sat_row = dow_df[dow_df["Date"] == sat_date]
        sun_row = dow_df[dow_df["Date"] == sun_date]
        sat_chg = sat_row["change"].iloc[0] if not sat_row.empty and not pd.isna(sat_row["change"].iloc[0]) else 0
        sun_chg = sun_row["change"].iloc[0] if not sun_row.empty and not pd.isna(sun_row["change"].iloc[0]) else 0
        weekends_list.append((sat_date, sun_date, sat_chg + sun_chg))

    if weekends_list:
        avg_weekend = sum(w[2] for w in weekends_list) / len(weekends_list)
        recent_weekends = weekends_list[-4:]

        wk_rows = ""
        for sat, sun, net in recent_weekends:
            label = f"{sat.strftime('%d %b')} – {sun.strftime('%d %b')}"
            wk_rows += (
                f"<tr><td>{label}</td>"
                f"<td style='text-align:right; color:{change_color(net)}; font-weight:600'>{net:+.2f} kg</td></tr>"
            )

        st.markdown(
            f"""<table>
            <thead><tr><th>Weekend</th><th style='text-align:right'>Sat + Sun net</th></tr></thead>
            <tbody>{wk_rows}</tbody>
            </table>
            <div style='margin-top:0.7rem; color:#666; font-size:0.85rem'>
            Average across all weekends:
            <span style='color:{change_color(avg_weekend)}; font-weight:600'>{avg_weekend:+.2f} kg</span>
            </div>""",
            unsafe_allow_html=True,
        )

with tab_ai:
    st.markdown(ANALYSIS_MARKDOWN)

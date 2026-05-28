"""
core/charts.py
All Plotly chart builders.
Each function receives a DataFrame and returns a plotly Figure.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Consistent colour palette matching Ahmedabad Metro branding
COLOR_2W   = "#6366F1"   # indigo  — two-wheelers
COLOR_4W   = "#F59E0B"   # amber   — four-wheelers
COLOR_REV  = "#10B981"   # emerald — revenue
BG         = "rgba(0,0,0,0)"


def _base_layout(fig, title=""):
    fig.update_layout(
        title=title,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family="sans-serif", size=13),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", zeroline=False)
    return fig


# ── 1. Capacity donut ─────────────────────────────────────────────────────────

def capacity_donut(occupied: int, free: int, label: str) -> go.Figure:
    fig = go.Figure(go.Pie(
        values=[occupied, free],
        labels=["Occupied", "Free"],
        hole=0.65,
        marker_colors=["#EF4444", "#10B981"],
        textinfo="none",
        hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        annotations=[dict(
            text=f"<b>{occupied}/{occupied+free}</b><br><span style='font-size:11px'>{label}</span>",
            x=0.5, y=0.5, font_size=15, showarrow=False,
        )],
        height=180,
    )
    return fig


# ── 2. Hourly traffic bar chart ───────────────────────────────────────────────

def hourly_traffic(df: pd.DataFrame) -> go.Figure:
    if df.empty or "hour" not in df.columns:
        return go.Figure()
    counts = df.groupby(["hour", "vehicle_type"]).size().reset_index(name="count")
    fig = px.bar(
        counts, x="hour", y="count", color="vehicle_type",
        color_discrete_map={"2W": COLOR_2W, "4W": COLOR_4W},
        labels={"hour": "Hour of Day", "count": "Vehicles", "vehicle_type": "Type"},
        barmode="stack",
    )
    return _base_layout(fig, "Hourly Traffic")


# ── 3. Daily revenue line chart ───────────────────────────────────────────────

def daily_revenue_trend(df: pd.DataFrame) -> go.Figure:
    if df.empty or "date" not in df.columns:
        return go.Figure()
    daily = df.groupby("date")["fee"].sum().reset_index()
    daily.columns = ["date", "revenue"]
    fig = px.line(
        daily, x="date", y="revenue",
        markers=True,
        color_discrete_sequence=[COLOR_REV],
        labels={"date": "Date", "revenue": "Revenue (₹)"},
    )
    fig.update_traces(line_width=2.5, marker_size=7)
    return _base_layout(fig, "Daily Revenue Trend")


# ── 4. Vehicle type split pie ─────────────────────────────────────────────────

def vehicle_type_split(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    counts = df["vehicle_type"].value_counts().reset_index()
    counts.columns = ["type", "count"]
    counts["label"] = counts["type"].map({"2W": "Two-Wheeler", "4W": "Four-Wheeler"})
    fig = px.pie(
        counts, names="label", values="count",
        color="label",
        color_discrete_map={"Two-Wheeler": COLOR_2W, "Four-Wheeler": COLOR_4W},
        hole=0.4,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    return _base_layout(fig, "Vehicle Mix")


# ── 5. Revenue by vehicle type bar ───────────────────────────────────────────

def revenue_by_type(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    rev = df.groupby("vehicle_type")["fee"].sum().reset_index()
    rev["label"] = rev["vehicle_type"].map({"2W": "Two-Wheeler", "4W": "Four-Wheeler"})
    fig = px.bar(
        rev, x="label", y="fee",
        color="label",
        color_discrete_map={"Two-Wheeler": COLOR_2W, "Four-Wheeler": COLOR_4W},
        labels={"fee": "Revenue (₹)", "label": ""},
        text="fee",
    )
    fig.update_traces(texttemplate="₹%{text:.0f}", textposition="outside")
    return _base_layout(fig, "Revenue by Vehicle Type")


# ── 6. Duration histogram ─────────────────────────────────────────────────────

def duration_histogram(df: pd.DataFrame) -> go.Figure:
    if df.empty or "duration_hrs" not in df.columns:
        return go.Figure()
    fig = px.histogram(
        df, x="duration_hrs", nbins=20,
        color="vehicle_type",
        color_discrete_map={"2W": COLOR_2W, "4W": COLOR_4W},
        labels={"duration_hrs": "Duration (hours)", "count": "Vehicles"},
        barmode="overlay", opacity=0.75,
    )
    return _base_layout(fig, "Parking Duration Distribution")


# ── 7. Slot grid heatmap ──────────────────────────────────────────────────────

def slot_heatmap(slot_data: list) -> go.Figure:
    """Takes list of dicts from lot.all_slots_as_list()"""
    if not slot_data:
        return go.Figure()
    df = pd.DataFrame(slot_data)
    df["occupied"] = df["Status"].str.contains("Occupied").astype(int)
    df["col"] = [i % 5 for i in range(len(df))]
    df["row"] = [i // 5 for i in range(len(df))]
    fig = go.Figure(go.Heatmap(
        z=df["occupied"],
        x=df["col"],
        y=df["row"],
        text=df["Slot ID"],
        texttemplate="%{text}",
        colorscale=[[0, "#10B981"], [1, "#EF4444"]],
        showscale=False,
        hovertemplate="Slot: %{text}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        height=200,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig

"""
FOUNDATIONX - Geotechnical Engineering Analysis & Foundation Design (CE 402 | IIT Mandi).
Modules: Home | P1 Soil Profile | P2 Parameter Tools | P3 Bearing Capacity | P4 Stress Increase | P5 Settlement | Sources.
NO site values are hard-coded: all data are typed in, uploaded as JSON, or loaded from examples/*.json.
All calculations live in geotech.py, where every equation carries a source comment.
SI units throughout: kN, kPa, m, mm.
"""
import glob
import json
import math
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

import geotech as gt

st.set_page_config(
    page_title="FOUNDATIONX · CE 402 | IIT Mandi",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

KINDS = ["fill", "sand", "gravel", "clay"]
COLS = [
    "Name", "Type", "Top (m)", "Bottom (m)", "γ moist (kN/m³)", "γ sat (kN/m³)",
    "c′ (kPa)", "φ′ (°)", "cu (kPa)", "SPT N (blows/0.3 m)", "qc/N (kPa per blow)",
    "E user (kPa)", "Cc (–)", "Cr (–)", "e0 top (–)", "e0 bottom (–)",
    "cv (m²/yr)", "OCR (–)", "σ′p add (kPa)",
]
GENERIC = [
    ["Sand", "sand", 0.0, 3.0, 17.0, 19.0, 0.0, 32.0, 0.0, 12.0, 400.0, None, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    ["Clay", "clay", 3.0, 8.0, 18.0, 18.0, 0.0, 0.0, 40.0, None, 400.0, None, 0.25, 0.04, 0.90, 0.85, 3.0, 1.0, 0.0],
    ["Gravel", "gravel", 8.0, 20.0, 20.0, 21.0, 0.0, 38.0, 0.0, 50.0, 800.0, None, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
]
SPT_COLS = ["Depth (m)", "N (blows/0.3 m)", "Saturated fine/silty sand? (dilatancy)"]
DS_COLS = ["σn (kPa)", "τf (kPa)"]

NAV_PAGES = [
    ("Home", "🏠", "Platform Overview"),
    ("P1 Soil Profile", "🧱", "P1 · Soil Profile"),
    ("P2 Parameter Tools", "📐", "P2 · Parameter Tools"),
    ("P3 Bearing Capacity", "🏗️", "P3 · Bearing Capacity"),
    ("P4 Stress Increase", "📉", "P4 · Stress Increase"),
    ("P5 Settlement", "📏", "P5 · Settlement Analysis"),
    ("Sources", "📚", "References & Sources"),
]


# ------------------------------------------------------------------ styling & layout helpers
def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --fx-bg: #0B1120;
            --fx-surface: #111827;
            --fx-card: #162033;
            --fx-border: #26334D;
            --fx-accent: #38BDF8;
            --fx-accent-2: #60A5FA;
            --fx-text: #F1F5F9;
            --fx-muted: #94A3B8;
        }
        .stApp {
            background-color: var(--fx-bg);
            color: var(--fx-text);
        }
        section[data-testid="stSidebar"] {
            background-color: var(--fx-surface);
            border-right: 1px solid var(--fx-border);
        }
        section[data-testid="stSidebar"] * {
            color: var(--fx-text);
        }
        header[data-testid="stHeader"] {
            background-color: rgba(11, 17, 32, 0.92);
        }
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stSidebarCollapseButton"] svg,
        [data-testid="stSidebarCollapseButton"] span,
        [data-testid="collapsedControl"],
        [data-testid="collapsedControl"] button,
        [data-testid="collapsedControl"] svg,
        button[kind="header"],
        [data-testid="stHeader"] button,
        [data-testid="stHeader"] svg {
            color: #F8FAFC !important;
            fill: #F8FAFC !important;
        }
        .stButton > button,
        .stDownloadButton > button {
            background-color: #1E293B !important;
            color: #F8FAFC !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background-color: #26354D !important;
            border-color: #38BDF8 !important;
            color: #FFFFFF !important;
        }
        .stButton > button[kind="primary"] {
            background-color: #0284C7 !important;
            border-color: #38BDF8 !important;
            color: #FFFFFF !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #0369A1 !important;
            color: #FFFFFF !important;
        }
        .stButton > button p,
        .stDownloadButton > button p,
        .stButton > button span,
        .stDownloadButton > button span {
            color: #F8FAFC !important;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] {
            background-color: #162033 !important;
            border-color: #334155 !important;
            color: #F8FAFC !important;
        }
        input, textarea, [data-baseweb="select"] span {
            color: #F8FAFC !important;
        }
        [data-testid="stFileUploader"] section {
            background-color: #162033 !important;
            border: 1px dashed #334155 !important;
            color: #E2E8F0 !important;
        }
        [data-testid="stExpander"] {
            background-color: #162033 !important;
            border: 1px solid #26334D !important;
            border-radius: 8px !important;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary * {
            color: #F1F5F9 !important;
        }
        .block-container {
            padding-top: 3.6rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }
        h1, h2, h3, h4, p, label, .stMarkdown, .stCaption {
            color: var(--fx-text);
        }
        .fx-mod-hdr {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: flex-end;
            gap: 0.75rem;
            padding-bottom: 0.85rem;
            margin-bottom: 1.15rem;
            border-bottom: 1px solid var(--fx-border);
        }
        .fx-mod-code {
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            color: var(--fx-accent);
            text-transform: uppercase;
        }
        .fx-mod-main-title {
            font-size: 1.65rem;
            font-weight: 800;
            color: #F8FAFC;
            margin: 0.1rem 0 0.2rem 0;
        }
        .fx-mod-sub {
            font-size: 0.9rem;
            color: var(--fx-muted);
            margin: 0;
        }
        .fx-meta-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .fx-chip {
            background: var(--fx-card);
            border: 1px solid var(--fx-border);
            border-radius: 6px;
            padding: 0.32rem 0.65rem;
            font-size: 0.78rem;
            color: #CBD5E1;
            font-variant-numeric: tabular-nums;
        }
        .fx-chip strong {
            color: #F8FAFC;
        }
        .fx-sec {
            font-size: 0.98rem;
            font-weight: 700;
            color: #E2E8F0;
            border-bottom: 1px solid var(--fx-border);
            padding-bottom: 0.35rem;
            margin: 1.25rem 0 0.8rem 0;
        }
        .fx-hero {
            background: linear-gradient(135deg, #0F172A 0%, #172554 100%);
            color: #F8FAFC;
            border-radius: 10px;
            padding: 1.8rem 2rem;
            border: 1px solid #2A3F66;
            margin-bottom: 1.35rem;
        }
        .fx-course-pill {
            display: inline-block;
            background: rgba(56, 189, 248, 0.14);
            color: #7DD3FC;
            border: 1px solid rgba(56, 189, 248, 0.35);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            padding: 0.24rem 0.68rem;
            border-radius: 6px;
            margin-bottom: 0.65rem;
        }
        .fx-hero h1 {
            color: #FFFFFF !important;
            font-size: 2.05rem;
            font-weight: 800;
            margin: 0 0 0.25rem 0;
            letter-spacing: 0.04em;
        }
        .fx-hero .fx-sub {
            color: #BAE6FD;
            font-size: 1.05rem;
            font-weight: 500;
            margin: 0 0 0.7rem 0;
        }
        .fx-hero .fx-desc {
            color: #CBD5E1;
            font-size: 0.92rem;
            line-height: 1.55;
            max-width: 840px;
            margin: 0;
        }
        .fx-card {
            background: var(--fx-card);
            border: 1px solid var(--fx-border);
            border-radius: 8px;
            padding: 1.15rem 1.2rem;
            margin-bottom: 0.65rem;
        }
        .fx-mod-tag {
            font-size: 0.73rem;
            font-weight: 700;
            color: var(--fx-accent);
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .fx-mod-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: #F8FAFC;
            margin: 0.22rem 0 0.42rem 0;
        }
        .fx-mod-desc {
            font-size: 0.87rem;
            color: var(--fx-muted);
            line-height: 1.48;
            margin: 0;
        }
        .fx-mcard {
            background: var(--fx-card);
            border: 1px solid var(--fx-border);
            border-left: 4px solid var(--fx-accent);
            border-radius: 8px;
            padding: 0.82rem 1rem;
            font-variant-numeric: tabular-nums;
        }
        .fx-mcard-lbl {
            font-size: 0.73rem;
            font-weight: 700;
            color: var(--fx-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .fx-mcard-val {
            font-size: 1.28rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-top: 0.14rem;
        }
        .fx-mcard-sub {
            font-size: 0.78rem;
            color: var(--fx-muted);
            margin-top: 0.12rem;
        }
        .fx-pipe {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.45rem;
            background: var(--fx-surface);
            border: 1px solid var(--fx-border);
            border-radius: 8px;
            padding: 0.7rem 0.9rem;
            margin: 0.5rem 0 1rem 0;
            font-variant-numeric: tabular-nums;
        }
        .fx-pipe-node {
            background: var(--fx-card);
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 0.42rem 0.65rem;
            font-size: 0.8rem;
        }
        .fx-pipe-node small {
            display: block;
            color: var(--fx-muted);
            font-size: 0.7rem;
        }
        .fx-pipe-arrow {
            color: var(--fx-accent);
            font-weight: 700;
            font-size: 0.95rem;
        }
        .fx-eq-box {
            background: var(--fx-surface);
            border: 1px solid var(--fx-border);
            border-left: 3px solid var(--fx-accent);
            border-radius: 6px;
            padding: 0.75rem 1rem;
            font-size: 0.88rem;
            color: #E2E8F0;
            margin-top: 0.65rem;
            font-variant-numeric: tabular-nums;
        }
        .fx-banner-ok {
            background: rgba(21, 128, 61, 0.22);
            color: #86EFAC;
            border: 1px solid rgba(74, 222, 128, 0.45);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-weight: 600;
            margin: 0.65rem 0 1rem 0;
            font-variant-numeric: tabular-nums;
        }
        .fx-banner-warn {
            background: rgba(180, 83, 9, 0.22);
            color: #FCD34D;
            border: 1px solid rgba(251, 191, 36, 0.45);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-weight: 600;
            margin: 0.65rem 0 1rem 0;
            font-variant-numeric: tabular-nums;
        }
        .fx-banner-err {
            background: rgba(185, 28, 28, 0.25);
            color: #FCA5A5;
            border: 1px solid rgba(248, 113, 113, 0.45);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-weight: 600;
            margin: 0.65rem 0 1rem 0;
            font-variant-numeric: tabular-nums;
        }
        [data-testid="stMetricValue"] {
            font-variant-numeric: tabular-nums;
            color: #F8FAFC;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mod_header(code: str, title: str, subtitle: str, chips: list[tuple[str, str]] | None = None):
    chips_html = ""
    if chips:
        items = "".join(f'<div class="fx-chip">{k}: <strong>{v}</strong></div>' for k, v in chips)
        chips_html = f'<div class="fx-meta-strip">{items}</div>'
    st.markdown(
        f"""
        <div class="fx-mod-hdr">
            <div>
                <div class="fx-mod-code">{code} · CE 402 | IIT MANDI</div>
                <div class="fx-mod-main-title">{title}</div>
                <p class="fx-mod-sub">{subtitle}</p>
            </div>
            {chips_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sec_title(text: str):
    st.markdown(f'<div class="fx-sec">{text}</div>', unsafe_allow_html=True)


def mcard(label: str, value: str, sub: str = "", border_color: str = "#38BDF8"):
    sub_html = f'<div class="fx-mcard-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="fx-mcard" style="border-left-color: {border_color};">
            <div class="fx-mcard-lbl">{label}</div>
            <div class="fx-mcard-val">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plotly(fig: go.Figure, x_title: str, y_title: str, height: int = 480, reverse_y: bool = False) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="#111827",
        plot_bgcolor="#162033",
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=12, color="#E2E8F0"),
        margin=dict(l=65, r=28, t=54, b=55),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(17, 24, 39, 0.88)",
            bordercolor="#26334D",
            borderwidth=1,
            font=dict(color="#E2E8F0"),
        ),
        hovermode="closest",
    )
    fig.update_xaxes(
        title_text=x_title,
        showgrid=True,
        gridcolor="#26334D",
        zeroline=True,
        zerolinecolor="#475569",
        linecolor="#334155",
        tickfont=dict(color="#CBD5E1"),
        title_font=dict(color="#F1F5F9"),
    )
    fig.update_yaxes(
        title_text=y_title,
        showgrid=True,
        gridcolor="#26334D",
        zeroline=True,
        zerolinecolor="#475569",
        linecolor="#334155",
        tickfont=dict(color="#CBD5E1"),
        title_font=dict(color="#F1F5F9"),
        autorange="reversed" if reverse_y else True,
    )
    return fig


def fig_footing_plan(shape: str, B: float, L: float, eB: float, eL: float, Be: float, Le: float) -> go.Figure:
    """Schematic footing plan showing gross footprint, eccentricity offset, and effective area."""
    fig = go.Figure()
    if shape == "Circular":
        R = B / 2.0
        theta = np.linspace(0, 2 * np.pi, 180)
        fig.add_trace(
            go.Scatter(
                x=R * np.cos(theta),
                y=R * np.sin(theta),
                mode="lines",
                fill="toself",
                fillcolor="rgba(56, 189, 248, 0.12)",
                line=dict(color="#38BDF8", width=2.2),
                name=f"Gross Circle (D = {B:.2f} m)",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[0.0, eB],
                y=[0.0, eL],
                mode="markers+lines",
                marker=dict(size=[8, 11], color=["#94A3B8", "#F59E0B"]),
                line=dict(color="#F59E0B", width=2, dash="dot"),
                name=f"Load Offset (eB={eB:.2f} m, eL={eL:.2f} m)",
            )
        )
        lim = max(R * 1.25, 1.0)
        fig.update_xaxes(range=[-lim, lim], scaleanchor="y", scaleratio=1)
        fig.update_yaxes(range=[-lim, lim])
    else:
        w_gross = B if shape == "Strip" else B
        l_gross = min(B * 2.5, 6.0) if shape == "Strip" else L
        fig.add_shape(
            type="rect",
            x0=-w_gross / 2,
            x1=w_gross / 2,
            y0=-l_gross / 2,
            y1=l_gross / 2,
            line=dict(color="#60A5FA", width=2),
            fillcolor="rgba(56, 189, 248, 0.10)",
        )
        # Effective rectangle centered at (eB, eL)
        w_eff = Be
        l_eff = min(Le, l_gross) if shape == "Strip" else Le
        fig.add_shape(
            type="rect",
            x0=eB - w_eff / 2,
            x1=eB + w_eff / 2,
            y0=eL - l_eff / 2,
            y1=eL + l_eff / 2,
            line=dict(color="#34D399", width=2, dash="dash"),
            fillcolor="rgba(52, 211, 153, 0.18)",
        )
        fig.add_trace(
            go.Scatter(
                x=[0.0],
                y=[0.0],
                mode="markers",
                marker=dict(size=8, color="#94A3B8"),
                name="Footing Centroid (0, 0)",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[eB],
                y=[eL],
                mode="markers",
                marker=dict(size=11, color="#F59E0B"),
                name=f"Load Eccentricity (eB={eB:.2f} m, eL={eL:.2f} m)",
            )
        )
        span_x = max(w_gross * 0.7, 1.0)
        span_y = max(l_gross * 0.7, 1.0)
        fig.update_xaxes(range=[-span_x, span_x], scaleanchor="y", scaleratio=1)
        fig.update_yaxes(range=[-span_y, span_y])

    style_plotly(fig, "Along Width / X (m)", "Along Length / Y (m)", height=360)
    fig.update_layout(title=dict(text="Footing Plan, Eccentricity & Effective Zone", font=dict(size=13)))
    return fig


# ------------------------------------------------------------------ state helpers
def init_state():
    ss = st.session_state
    ss.setdefault("nav_page", "Home")
    ss.setdefault("ver", 0)
    ss.setdefault("layers", pd.DataFrame(GENERIC, columns=COLS))
    ss.setdefault("wt_meas", 2.0)
    ss.setdefault("wt_des", 1.0)
    ss.setdefault("spt", pd.DataFrame([[1.5, 10, False], [3.0, 14, False]], columns=SPT_COLS))
    ss.setdefault("ds", pd.DataFrame([[50.0, 40.0], [100.0, 72.0], [150.0, 105.0]], columns=DS_COLS))


def load_json(d):
    ss = st.session_state
    ss["layers"] = pd.DataFrame(d["layers"]).reindex(columns=COLS)
    ss["wt_meas"] = float(d["wt_measured"])
    ss["wt_des"] = float(d["wt_design"])
    if "spt" in d:
        ss["spt"] = pd.DataFrame(d["spt"]).reindex(columns=SPT_COLS)
    if "direct_shear" in d:
        ss["ds"] = pd.DataFrame(d["direct_shear"]).reindex(columns=DS_COLS)
    ss["ver"] += 1


def nz(v, default=0.0):
    return default if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)


def validate(df, wm, wd):
    errs = []
    if df.empty:
        return ["Enter at least one layer."]
    d = df.reset_index(drop=True)
    for i, r in d.iterrows():
        if r["Type"] not in KINDS:
            errs.append(f"Layer {i+1}: type must be one of {KINDS}.")
        if nz(r["Bottom (m)"]) <= nz(r["Top (m)"]):
            errs.append(f"Layer {i+1}: bottom must be deeper than top.")
        if nz(r["γ sat (kN/m³)"]) < nz(r["γ moist (kN/m³)"]) - 1e-9:
            errs.append(f"Layer {i+1}: saturated unit weight is below moist unit weight (check units).")
        if i > 0 and abs(nz(r["Top (m)"]) - nz(d.loc[i - 1, "Bottom (m)"])) > 1e-6:
            errs.append(f"Layer {i+1}: top does not equal the bottom of layer {i} (gap or overlap).")
    if abs(nz(d.loc[0, "Top (m)"])) > 1e-6:
        errs.append("First layer must start at 0 m.")
    if wm < 0 or wd < 0:
        errs.append("Water-table depths must be ≥ 0 m.")
    return errs


def to_profile(df, wm, wd):
    L = []
    for _, r in df.reset_index(drop=True).iterrows():
        N = r["SPT N (blows/0.3 m)"]
        E = r["E user (kPa)"]
        L.append(
            gt.Layer(
                top=nz(r["Top (m)"]),
                bot=nz(r["Bottom (m)"]),
                name=str(r["Name"]),
                kind=r["Type"],
                gamma=nz(r["γ moist (kN/m³)"]),
                gamma_sat=nz(r["γ sat (kN/m³)"]),
                c=nz(r["c′ (kPa)"]),
                phi=nz(r["φ′ (°)"]),
                cu=nz(r["cu (kPa)"]),
                N=None if pd.isna(N) else float(N),
                Cc=nz(r["Cc (–)"]),
                Cr=nz(r["Cr (–)"]),
                e0_top=nz(r["e0 top (–)"]),
                e0_bot=nz(r["e0 bottom (–)"]),
                cv=nz(r["cv (m²/yr)"]),
                ocr=nz(r["OCR (–)"], 1.0),
                sp_add=nz(r["σ′p add (kPa)"]),
                E=None if pd.isna(E) else float(E),
                qc_factor=nz(r["qc/N (kPa per blow)"], 400.0),
            )
        )
    return gt.Profile(layers=L, wt_measured=wm, wt_design=wd)


def fig_profile_plotly(p: gt.Profile) -> go.Figure:
    colors = {
        "fill": "#5C4D3C",
        "sand": "#786228",
        "gravel": "#475569",
        "clay": "#2D5A4C",
    }
    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.42, 0.58],
        shared_yaxes=True,
        horizontal_spacing=0.08,
        subplot_titles=("Stratigraphy & Water Tables", "Vertical Stress Profile (Design WT)"),
    )

    for L in p.layers:
        fc = colors.get(L.kind, "#334155")
        thick = L.bot - L.top
        fig.add_shape(
            type="rect",
            x0=0,
            x1=1,
            y0=L.top,
            y1=L.bot,
            fillcolor=fc,
            line=dict(color="#94A3B8", width=1.2),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=[0.5],
                y=[(L.top + L.bot) / 2],
                mode="text",
                text=[f"<b>{L.name}</b> ({L.kind})<br>{L.top:g}–{L.bot:g} m (h={thick:g} m)"],
                textfont=dict(size=11, color="#F8FAFC"),
                hovertemplate=(
                    f"<b>{L.name}</b> ({L.kind})<br>"
                    f"Depth: {L.top:g} – {L.bot:g} m (thickness {thick:g} m)<br>"
                    f"γ moist: {L.gamma:g} kN/m³ | γ sat: {L.gamma_sat:g} kN/m³<extra></extra>"
                ),
                showlegend=False,
            ),
            row=1,
            col=1,
        )

    fig.add_hline(
        y=p.wt_measured,
        line=dict(color="#38BDF8", width=2.2, dash="dash"),
        annotation_text=f"Measured GWT: {p.wt_measured:g} m",
        annotation_position="top right",
        annotation_font=dict(color="#7DD3FC"),
        row=1,
        col=1,
    )
    fig.add_hline(
        y=p.wt_design,
        line=dict(color="#F87171", width=2.4, dash="solid"),
        annotation_text=f"Design GWT: {p.wt_design:g} m",
        annotation_position="bottom right",
        annotation_font=dict(color="#FCA5A5"),
        row=1,
        col=1,
    )

    zmax = p.layers[-1].bot
    zs = np.linspace(0, zmax, 220)
    st_, se_ = zip(*[gt.sigma_v_total_eff(p, float(z)) for z in zs])
    u_ = [s - t for s, t in zip(st_, se_)]

    fig.add_trace(
        go.Scatter(
            x=list(st_),
            y=zs,
            mode="lines",
            name="Total stress σv (kPa)",
            line=dict(color="#F8FAFC", width=2.3),
            hovertemplate="z = %{y:.2f} m<br>σv = %{x:.1f} kPa<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=u_,
            y=zs,
            mode="lines",
            name="Pore pressure u (kPa)",
            line=dict(color="#38BDF8", width=2.1, dash="dot"),
            hovertemplate="z = %{y:.2f} m<br>u = %{x:.1f} kPa<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=list(se_),
            y=zs,
            mode="lines",
            name="Effective stress σ′v (kPa)",
            line=dict(color="#34D399", width=2.6),
            hovertemplate="z = %{y:.2f} m<br>σ′v = %{x:.1f} kPa<extra></extra>",
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        template="plotly_dark",
        height=540,
        paper_bgcolor="#111827",
        plot_bgcolor="#162033",
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=12, color="#E2E8F0"),
        margin=dict(l=65, r=28, t=65, b=55),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=0,
            bgcolor="rgba(17, 24, 39, 0.88)",
            bordercolor="#26334D",
            borderwidth=1,
        ),
    )
    fig.update_xaxes(range=[0, 1], showticklabels=False, showgrid=False, title_text="Stratum", row=1, col=1)
    fig.update_xaxes(title_text="Stress (kPa)", showgrid=True, gridcolor="#26334D", row=1, col=2)
    fig.update_yaxes(
        title_text="Depth below ground level, z (m)",
        autorange="reversed",
        showgrid=True,
        gridcolor="#26334D",
        row=1,
        col=1,
    )
    fig.update_yaxes(autorange="reversed", showgrid=True, gridcolor="#26334D", row=1, col=2)
    return fig


def layer_options(p):
    return {f"{L.name} ({L.top:g}–{L.bot:g} m)": L for L in p.layers}


# ------------------------------------------------------------------ app init & nav
init_state()
inject_styles()
ss = st.session_state

with st.sidebar:
    st.markdown(
        """
        <div style="padding:0.25rem 0 0.75rem 0;border-bottom:1px solid #26334D;margin-bottom:0.75rem;">
            <div style="font-size:1.28rem;font-weight:800;color:#F8FAFC;letter-spacing:0.04em;">
                FOUNDATIONX
            </div>
            <div style="font-size:0.8rem;color:#94A3B8;margin-top:0.12rem;">
                Geotechnical Engineering Analysis &amp; Foundation Design
            </div>
            <div style="margin-top:0.42rem;font-size:0.74rem;font-weight:700;color:#38BDF8;">
                CE 402 | IIT Mandi
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for page_key, icon, label in NAV_PAGES:
        is_sel = ss["nav_page"] == page_key
        if st.button(
            f"{icon}  {label}",
            key=f"nav_{page_key}",
            use_container_width=True,
            type="primary" if is_sel else "secondary",
        ):
            ss["nav_page"] = page_key
            st.rerun()
    st.markdown("---")
    st.caption("SI units throughout (kN, kPa, m, mm, °). All equations in `geotech.py`.")

page = ss["nav_page"]

# ------------------------------------------------------------------ HOME
if page == "Home":
    st.markdown(
        """
        <div class="fx-hero">
            <div class="fx-course-pill">CE 402 | IIT MANDI</div>
            <h1>FOUNDATIONX</h1>
            <div class="fx-sub">Geotechnical Engineering Analysis &amp; Foundation Design</div>
            <p class="fx-desc">
                Integrated engineering analysis suite for subsurface stratigraphy, SPT &amp; direct shear parameter
                evaluation, shallow foundation bearing capacity (IS 6403:1981), subsurface stress distribution,
                and settlement &amp; consolidation analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        mcard("Engineering Modules", "5", "P1 – P5 Analysis Suite", "#38BDF8")
    with k2:
        mcard("Unit System", "SI", "kN · kPa · m · mm · °", "#60A5FA")
    with k3:
        mcard("Profile Exchange", "JSON", "Upload, Presets & Export", "#34D399")
    with k4:
        mcard("Course Suite", "CE 402", "IIT Mandi Foundation Design", "#A78BFA")

    sec_title("Engineering Modules")
    cards_meta = [
        ("P1 Soil Profile", "MODULE 01", "🧱", "Soil Profile",
         "Configure soil layers, unit weights, strength/stiffness/consolidation inputs, measured vs. design water tables, stratigraphy plots, and vertical stresses."),
        ("P2 Parameter Tools", "MODULE 02", "📐", "Parameter Tools",
         "Compute IS 2131 SPT overburden and dilatancy corrections with step-by-step tables and least-squares direct shear regression for c′, φ′, and R²."),
        ("P3 Bearing Capacity", "MODULE 03", "🏗️", "Bearing Capacity",
         "Evaluate shallow footing bearing capacity under general, local, or blended shear with shape, depth, inclination, GWT (W′), and eccentricity effects."),
        ("P4 Stress Increase", "MODULE 04", "📉", "Stress Increase",
         "Calculate vertical stress increments (Δσz) with depth via Boussinesq and 2:1 methods, including centre, corner, and custom-point comparisons."),
        ("P5 Settlement", "MODULE 05", "📏", "Settlement Analysis",
         "Estimate granular settlement (Schmertmann et al., 1978) and 1-D consolidation settlement (NC/OC clays) with sublayer tables and time–settlement curves."),
    ]

    r1 = st.columns(3)
    for i in range(3):
        route, tag, ico, title, desc = cards_meta[i]
        with r1[i]:
            st.markdown(
                f"""
                <div class="fx-card" style="min-height:165px;">
                    <div class="fx-mod-tag">{tag}</div>
                    <div class="fx-mod-title">{ico} {title}</div>
                    <p class="fx-mod-desc">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Open {title}", key=f"go_{route}", use_container_width=True):
                ss["nav_page"] = route
                st.rerun()

    r2 = st.columns(3)
    for i in range(3, 5):
        route, tag, ico, title, desc = cards_meta[i]
        with r2[i - 3]:
            st.markdown(
                f"""
                <div class="fx-card" style="min-height:165px;">
                    <div class="fx-mod-tag">{tag}</div>
                    <div class="fx-mod-title">{ico} {title}</div>
                    <p class="fx-mod-desc">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Open {title}", key=f"go_{route}", use_container_width=True):
                ss["nav_page"] = route
                st.rerun()

# ------------------------------------------------------------------ P1 · SOIL PROFILE WORKSPACE
elif page == "P1 Soil Profile":
    mod_header(
        "P1",
        "Soil Profile & Subsurface Investigation Workspace",
        "Stratigraphy definition, measured vs. design water tables, and vertical stress distribution (SI units: m, kN/m³, kPa).",
        chips=[
            ("Layers", str(len(ss["layers"]))),
            ("Measured GWT", f"{ss['wt_meas']:g} m"),
            ("Design GWT", f"{ss['wt_des']:g} m"),
        ],
    )

    # Top workspace: Left = Investigation source & GWT; Right = Layer editor
    w_left, w_right = st.columns([1.05, 1.95], gap="large")
    ex = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples", "*.json")))

    with w_left:
        sec_title("1. Investigation & Import/Export")
        pick = st.selectbox("Bundled borehole profile", ["—"] + [os.path.basename(e) for e in ex])
        if st.button("Load selected example", use_container_width=True) and pick != "—":
            load_json(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples", pick))))
            st.rerun()

        up = st.file_uploader("Upload profile JSON", type="json")
        if up is not None and st.button("Load uploaded JSON", use_container_width=True):
            load_json(json.load(up))
            st.rerun()

        sec_title("2. Groundwater Conditions")
        ss["wt_meas"] = st.number_input(
            "Measured water table (m bgl)", 0.0, 100.0, float(ss["wt_meas"]), 0.1,
            help="Level observed at the time of investigation; used for SPT corrections.",
        )
        ss["wt_des"] = st.number_input(
            "Design water table (m bgl)", 0.0, 100.0, float(ss["wt_des"]), 0.1,
            help="Conservative seasonal groundwater level for bearing capacity and settlement.",
        )

    with w_right:
        sec_title("3. Soil Layer Editor")
        st.caption(
            "Edit, add, or remove strata (depths in m bgl, unit weights kN/m³, shear/consolidation parameters in SI units). "
            "Leave unused fields blank; σ′p = OCR·σ′v0 + σ′p add."
        )
        edited = st.data_editor(
            ss["layers"],
            num_rows="dynamic",
            width="stretch",
            key=f"layers_{ss['ver']}",
            column_config={"Type": st.column_config.SelectboxColumn("Type", options=KINDS, required=True)},
        )
        ss["layers"] = edited

    errs = validate(edited, ss["wt_meas"], ss["wt_des"])
    if errs:
        for e in errs:
            st.markdown(f'<div class="fx-banner-err">{e}</div>', unsafe_allow_html=True)
        st.stop()

    prof = to_profile(edited, ss["wt_meas"], ss["wt_des"])

    # Main visual centerpiece: large stratigraphy & stress diagram
    sec_title("4. Subsurface Stratigraphy & Vertical Stress Diagram")
    st.plotly_chart(fig_profile_plotly(prof), use_container_width=True)

    # Stress summary table + JSON download action bar
    sec_title("5. Vertical Stress Summary & Profile Export")
    pts = sorted({0.0, *[L.bot for L in prof.layers], prof.wt_design})
    rows = []
    for z in pts:
        s, se = gt.sigma_v_total_eff(prof, z)
        rows.append({"Depth (m)": z, "σv total (kPa)": round(s, 1), "u (kPa)": round(s - se, 1), "σ′v (kPa)": round(se, 1)})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    act_l, act_r = st.columns([1.2, 2.8])
    with act_l:
        st.download_button(
            "Download Profile (.json)",
            json.dumps(
                {
                    "wt_measured": ss["wt_meas"],
                    "wt_design": ss["wt_des"],
                    "layers": json.loads(edited.to_json(orient="records")),
                    "spt": json.loads(ss["spt"].to_json(orient="records")),
                    "direct_shear": json.loads(ss["ds"].to_json(orient="records")),
                },
                indent=1,
            ),
            "profile.json",
            use_container_width=True,
        )
    with act_r:
        st.caption("Capillary rise above the water table is ignored: moist unit weight is used above it, saturated below.")

# ------------------------------------------------------------------ P2 · LABORATORY ANALYSIS WORKSPACE
elif page == "P2 Parameter Tools":
    prof = to_profile(ss["layers"], ss["wt_meas"], ss["wt_des"])
    mod_header(
        "P2",
        "Parameter Tools — Laboratory & Field Analysis",
        "Stage-wise IS 2131 SPT corrections and Mohr–Coulomb direct shear regression.",
        chips=[("SPT Rows", str(len(ss["spt"].dropna(how="all")))), ("Shear Points", str(len(ss["ds"].dropna())))],
    )

    # ---- TASK A: SPT CORRECTIONS ----
    sec_title("A. SPT Corrections (IS 2131)")
    s1_l, s1_r = st.columns([1.8, 1.2], gap="large")
    with s1_l:
        st.markdown("**Stage 1A · SPT Test Observations**")
        ss["spt"] = st.data_editor(ss["spt"], num_rows="dynamic", width="stretch", key=f"spt_{ss['ver']}")
    with s1_r:
        st.markdown("**Stage 1B · Correction Controls**")
        wtc = st.radio(
            "Water table for overburden stress",
            ["Measured (stress state during the test)", "Design"],
            horizontal=True,
            help="The correction describes the stress when the test was done, so the measured level is the default.",
        )
        cap = st.number_input("Cap on CN (–)", 1.0, 3.0, 2.0, 0.1, help="Limits the overburden factor at very low stress.")
        wt_used = prof.wt_measured if wtc.startswith("Measured") else prof.wt_design
        if st.button("Auto-flag saturated fine/silty sand from profile", use_container_width=True):
            d = ss["spt"].copy()
            d[SPT_COLS[2]] = [(z >= wt_used) and prof.layer_at(z).kind == "sand" for z in d[SPT_COLS[0]]]
            ss["spt"] = d
            ss["ver"] += 1
            st.rerun()

    out = []
    for _, r in ss["spt"].dropna(subset=[SPT_COLS[0], SPT_COLS[1]]).iterrows():
        _, sv = gt.sigma_v_total_eff(prof, float(r[SPT_COLS[0]]), wt_used)
        c = gt.spt_corrections(float(r[SPT_COLS[1]]), sv, bool(r[SPT_COLS[2]]), cn_cap=cap)
        out.append(
            {
                "Depth (m)": r[SPT_COLS[0]],
                "Layer": prof.layer_at(float(r[SPT_COLS[0]])).name,
                "N (field)": c["N"],
                "σ′v (kPa)": round(c["sigma_v_eff"], 1),
                "CN = 0.77 log10(1920/σ′v) (–)": round(c["CN"], 3),
                "N′ = CN·N": round(c["N_overburden"], 1),
                "N′ > 15 and saturated fine sand?": c["dilatancy_applied"],
                "N″ = 15 + 0.5(N′−15)": round(c["N_design"], 1),
            }
        )

    if out:
        first_o = out[0]
        st.markdown("**Stage 2 · Correction Sequence (Representative Row 1)**")
        st.markdown(
            f"""
            <div class="fx-pipe">
                <div class="fx-pipe-node"><small>Measured N</small><strong>{first_o['N (field)']:g}</strong></div>
                <div class="fx-pipe-arrow">→</div>
                <div class="fx-pipe-node"><small>σ′v (at {first_o['Depth (m)']:g} m)</small><strong>{first_o['σ′v (kPa)']:.1f} kPa</strong></div>
                <div class="fx-pipe-arrow">→</div>
                <div class="fx-pipe-node"><small>Overburden CN</small><strong>{first_o['CN = 0.77 log10(1920/σ′v) (–)']:.3f}</strong></div>
                <div class="fx-pipe-arrow">→</div>
                <div class="fx-pipe-node"><small>Corrected N′</small><strong>{first_o['N′ = CN·N']:.1f}</strong></div>
                <div class="fx-pipe-arrow">→</div>
                <div class="fx-pipe-node"><small>Dilatancy N′ &gt; 15?</small><strong>{'Yes' if first_o['N′ > 15 and saturated fine sand?'] else 'No'}</strong></div>
                <div class="fx-pipe-arrow">→</div>
                <div class="fx-pipe-node" style="border-color:#38BDF8;"><small>Final N″</small><strong>{first_o['N″ = 15 + 0.5(N′−15)']:.1f}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("**Stage 3 · Corrected SPT Results Table**")
        st.dataframe(pd.DataFrame(out), width="stretch", hide_index=True)

        with st.expander("Cross-check of φ′ from N′ (Wolff 1989; use only as a sanity check)"):
            for o in out:
                st.write(f"z = {o['Depth (m)']} m: φ′ ≈ {gt.phi_from_N(o['N′ = CN·N']):.1f}°")

    st.caption(
        "Step 1: σ′v at the test depth. Step 2: overburden factor CN and N′ = CN·N (closed form of the "
        "IS 2131 chart: Peck, Hanson & Thornburn, quoted in Das; check against the chart in your copy). "
        "Step 3: dilatancy N″ = 15 + 0.5(N′ − 15) only if N′ > 15 in saturated fine or silty sand "
        "(Terzaghi & Peck, IS 2131). Gravelly or coarse sand: untick the flag."
    )

    # ---- TASK B: DIRECT SHEAR ANALYSIS ----
    sec_title("B. Direct Shear Failure Envelope & Parameter Fitting")
    ds_left, ds_right = st.columns([1.05, 1.95], gap="large")
    with ds_left:
        st.markdown("**Test Observations (σn, τf)**")
        ss["ds"] = st.data_editor(ss["ds"], num_rows="dynamic", width="stretch", key=f"ds_{ss['ver']}")
        st.caption(
            "Enter normal stress σn and peak shear stress τf in kPa. A small c′ from a soaked or remoulded "
            "test is often set to zero in design; judge whether suction or sampling effects apply."
        )

    dsd = ss["ds"].dropna()
    with ds_right:
        if len(dsd) >= 2 and dsd[DS_COLS[0]].nunique() >= 2:
            sn, tau = list(dsd[DS_COLS[0]]), list(dsd[DS_COLS[1]])
            c, phi, r2 = gt.fit_cphi(sn, tau)
            sxx = sum(x * x for x in sn)
            phi0 = math.degrees(math.atan(sum(x * y for x, y in zip(sn, tau)) / sxx))

            xs = np.linspace(0, max(sn) * 1.1, 50)
            fig_ds = go.Figure()
            fig_ds.add_trace(
                go.Scatter(
                    x=sn,
                    y=tau,
                    mode="markers",
                    name="Observed Data (σn, τf)",
                    marker=dict(size=10, color="#38BDF8", line=dict(color="#F8FAFC", width=1)),
                    hovertemplate="σn = %{x:.2f} kPa<br>τf = %{y:.2f} kPa<extra></extra>",
                )
            )
            fig_ds.add_trace(
                go.Scatter(
                    x=xs,
                    y=c + xs * math.tan(math.radians(phi)),
                    mode="lines",
                    name=f"Fitted Envelope (c′={c:.2f} kPa, φ′={phi:.2f}°)",
                    line=dict(color="#F59E0B", width=2.5),
                    hovertemplate="σn = %{x:.2f} kPa<br>τ_fit = %{y:.2f} kPa<extra></extra>",
                )
            )
            style_plotly(fig_ds, "Normal Stress, σn (kPa)", "Shear Stress, τf (kPa)", height=450)
            st.plotly_chart(fig_ds, use_container_width=True)

            m1, m2, m3 = st.columns(3)
            with m1:
                mcard("Effective Cohesion c′", f"{c:.2f} kPa", "Least-squares intercept", "#38BDF8")
            with m2:
                mcard("Friction Angle φ′", f"{phi:.2f}°", f"Through-origin (c′=0): {phi0:.2f}°", "#60A5FA")
            with m3:
                mcard("Coefficient of Determination R²", f"{r2:.4f}", "Goodness of linear fit", "#34D399")

            sign_op = "+" if math.tan(math.radians(phi)) >= 0 else "−"
            st.markdown(
                f'<div class="fx-eq-box"><strong>Fitted Mohr–Coulomb Envelope:</strong> '
                f'τf = {c:.2f} {sign_op} {abs(math.tan(math.radians(phi))):.4f} · σn &nbsp;(φ′ = {phi:.2f}°, R² = {r2:.4f})</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="fx-banner-warn">Enter at least two different normal stresses.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ P3 · FOUNDATION DESIGN DASHBOARD
elif page == "P3 Bearing Capacity":
    prof = to_profile(ss["layers"], ss["wt_meas"], ss["wt_des"])
    lay = prof.layer_at(st.session_state.get("p3_df_val", 1.5))

    mod_header(
        "P3",
        "Shallow Foundation Bearing Capacity Dashboard",
        "IS 6403:1981 general & local shear capacity with shape, depth, inclination, W′, and eccentricity.",
        chips=[("Design GWT", f"{prof.wt_design:g} m"), ("Strata", str(len(prof.layers)))],
    )

    # Grouped design input area
    sec_title("1. Design Inputs — Geometry, Strength & Loading")
    in_g, in_s, in_l = st.columns(3, gap="medium")
    with in_g:
        st.markdown("**Footing Geometry**")
        shape_ui = st.selectbox("Footing shape", ["Square", "Rectangular", "Strip", "Circular"])
        shape = {"Square": "square", "Rectangular": "rect", "Strip": "strip", "Circular": "circle"}[shape_ui]
        B = st.number_input("Width B, or diameter for circular (m)", 0.1, 100.0, 2.0, 0.05)
        Lf = st.number_input("Length L (m)", 0.1, 500.0, 3.0, 0.05, disabled=shape != "rect") if shape == "rect" else B
        Df = st.number_input("Founding depth Df (m)", 0.0, 50.0, 1.5, 0.1, key="p3_df_val")
        lay = prof.layer_at(Df)

    with in_s:
        st.markdown("**Soil Properties & Factor of Safety**")
        src = st.radio(
            "Strength source",
            ["Drained from profile layer at founding depth (c′, φ′)", "Undrained from profile layer (c = cu, φ = 0)", "Manual"],
        )
        if src.startswith("Drained"):
            c_in, phi_in = lay.c, lay.phi
        elif src.startswith("Undrained"):
            c_in, phi_in = lay.cu, 0.0
        else:
            c_in = st.number_input("c (kPa)", 0.0, 1000.0, 0.0, 1.0)
            phi_in = st.number_input("φ (°)", 0.0, 50.0, 30.0, 0.5)
        st.caption(f"Founding stratum: **{lay.name}** · c = {c_in:g} kPa · φ = {phi_in:g}° · Design GWT = {prof.wt_design:g} m")
        FoS = st.number_input("Factor of safety (–)", 1.0, 10.0, 3.0, 0.1)

    with in_l:
        st.markdown("**Loading, Eccentricity & Failure Mechanism**")
        alpha = st.number_input("Load inclination α from vertical (°)", 0.0, 60.0, 0.0, 1.0)
        ex_ = st.number_input("Eccentricity e_B along B (m)", 0.0, 10.0, 0.0, 0.01)
        ey_ = st.number_input("Eccentricity e_L along L (m)", 0.0, 10.0, 0.0, 0.01, disabled=shape != "rect") if shape == "rect" else 0.0
        mode = st.radio("Shear failure mode", ["General", "Local", "Blend by SPT N″"], horizontal=True)
        if mode.startswith("Blend"):
            Nd = st.number_input("Design N″ at founding level (blows/0.3 m)", 0.0, 100.0, 15.0, 1.0)
            lo = st.number_input("N″ at or below which failure is fully local", 0.0, 50.0, 10.0, 1.0)
            hi = st.number_input("N″ at or above which failure is fully general", 1.0, 100.0, 30.0, 1.0)
            w = gt.local_general_weight(Nd, lo, hi)
            st.caption(f"Local-shear weight w = {w:.2f}")
        else:
            w = 1.0 if mode == "Local" else 0.0

    if shape == "strip":
        Lf = 1e6
    kw = dict(profile=prof, B=B, L=Lf, shape=shape, Df=Df, c=c_in, phi=phi_in, alpha=alpha, FoS=FoS, ex=ex_, ey=ey_)
    if shape == "circle" and ex_ > 0:
        st.markdown(
            '<div class="fx-banner-warn">Eccentric circular footing: B′ = D − 2e is used as an approximation; IS 6403 gives no circular rule.</div>',
            unsafe_allow_html=True,
        )

    G = gt.bearing_capacity(**kw, local_shear=False)
    Lc = gt.bearing_capacity(**kw, local_shear=True)
    qns = (1 - w) * G["qns"] + w * Lc["qns"]
    qnu_design = (1 - w) * G["qnu"] + w * Lc["qnu"]
    qgross_design = (1 - w) * G["qs_gross"] + w * Lc["qs_gross"]
    eff_area = (G["B_eff"] * (G["L_eff"] if shape != "strip" else 1.0)) if shape != "circle" else math.pi / 4 * G["B_eff"] ** 2

    # Results dashboard + footing geometry preview
    sec_title("2. Bearing Capacity Dashboard & Footing Geometry")
    dash_l, dash_r = st.columns([1.85, 1.15], gap="large")
    with dash_l:
        r1, r2, r3 = st.columns(3)
        with r1:
            mcard("Net Ultimate q_nu", f"{qnu_design:.1f} kPa", f"Mode: {mode}", "#38BDF8")
        with r2:
            mcard("Net Safe q_ns", f"{qns:.1f} kPa", f"FoS = {FoS:g}", "#34D399")
        with r3:
            mcard("Gross Safe q_s", f"{qgross_design:.1f} kPa", f"q_ns + q ({G['q_overburden']:.1f} kPa)", "#60A5FA")

        st.markdown("<div style='height:0.55rem'></div>", unsafe_allow_html=True)
        r4, r5 = st.columns(2)
        with r4:
            area_str = f"{eff_area:.2f} m²" if shape != "strip" else f"{G['B_eff']:.2f} m (strip)"
            mcard("Effective Dimensions", f"{G['B_eff']:.2f} × {G['L_eff'] if shape != 'strip' else float('inf'):.2f} m", f"Effective area: {area_str}", "#A78BFA")
        with r5:
            mcard("Depth & GWT Factor W′", f"Df = {Df:.2f} m · W′ = {G['W']:.2f}", f"Avg γ below base: {G['gamma_used']:.2f} kN/m³", "#F59E0B")

        st.markdown(f'<div class="fx-banner-ok">Design net safe bearing capacity ({mode.lower()}): {qns:.1f} kPa</div>', unsafe_allow_html=True)

        P = st.number_input("Applied column / strip load P (kN; kN/m for strip)", 0.0, 1e7, 0.0, 50.0)
        if P > 0:
            qa = P / eff_area
            util = qa / qns
            b_cls = "fx-banner-ok" if qa <= qns else "fx-banner-err"
            verdict = "SAFE (qa ≤ q_ns)" if qa <= qns else "EXCEEDS q_ns"
            st.markdown(
                f'<div class="{b_cls}">Applied pressure = {qa:.1f} kPa · Utilisation = {util:.2f} → {verdict}</div>',
                unsafe_allow_html=True,
            )
            if shape != "strip" and st.button("Find smallest B that carries P"):
                ratio = Lf / B
                for Bt in np.arange(0.5, 30, 0.05):
                    kk = dict(kw, B=Bt, L=Bt * ratio if shape == "rect" else Bt)
                    qq = (1 - w) * gt.bearing_capacity(**kk)["qns"] + w * gt.bearing_capacity(**kk, local_shear=True)["qns"]
                    Gx = gt.bearing_capacity(**kk)
                    ar = Gx["B_eff"] * Gx["L_eff"] if shape != "circle" else math.pi / 4 * Gx["B_eff"] ** 2
                    if P / ar <= qq:
                        st.markdown(
                            f'<div class="fx-banner-ok">Minimum B = {Bt:.2f} m (L = {kk["L"]:.2f} m), q_ns = {qq:.1f} kPa, applied {P/ar:.1f} kPa</div>',
                            unsafe_allow_html=True,
                        )
                        break
                else:
                    st.markdown('<div class="fx-banner-err">No size up to 30 m is adequate.</div>', unsafe_allow_html=True)

    with dash_r:
        st.plotly_chart(
            fig_footing_plan(shape, B, Lf if shape != "strip" else B * 2.0, ex_, ey_, G["B_eff"], G["L_eff"]),
            use_container_width=True,
        )

    # General vs. Local shear comparison & structured calculation breakdown
    sec_title("3. General vs. Local Shear Comparison & Calculation Breakdown")
    comp_df = pd.DataFrame(
        {
            "Parameter / Term": [
                "Effective width B′ (m)", "Effective length L′ (m)", "c used (kPa)", "φ used (°)",
                "Nc (–)", "Nq (–)", "Nγ (–)",
                "sc (–)", "sq (–)", "sγ (–)",
                "dc (–)", "dq (–)", "dγ (–)",
                "ic (–)", "iq (–)", "iγ (–)",
                "W′ (–)", "γ in term 3 (kN/m³)", "Overburden q (kPa)",
                "Term 1: c Nc sc dc ic (kPa)", "Term 2: q(Nq−1) sq dq iq (kPa)", "Term 3: 0.5 B′ γ Nγ sγ dγ iγ W′ (kPa)",
                "Net ultimate q_nu (kPa)", f"Net safe q_ns (FoS={FoS:g}) (kPa)", "Gross safe q_s (kPa)",
            ],
            "General Shear": [
                G["B_eff"], G["L_eff"] if shape != "strip" else float("inf"), G["c_used"], G["phi_used"],
                G["Nc"], G["Nq"], G["Ng"],
                G["sc"], G["sq"], G["sg"],
                G["dc"], G["dq"], G["dg"],
                G["ic"], G["iq"], G["ig"],
                G["W"], G["gamma_used"], G["q_overburden"],
                G["term_c"], G["term_q"], G["term_g"],
                G["qnu"], G["qns"], G["qs_gross"],
            ],
            "Local Shear": [
                Lc["B_eff"], Lc["L_eff"] if shape != "strip" else float("inf"), Lc["c_used"], Lc["phi_used"],
                Lc["Nc"], Lc["Nq"], Lc["Ng"],
                Lc["sc"], Lc["sq"], Lc["sg"],
                Lc["dc"], Lc["dq"], Lc["dg"],
                Lc["ic"], Lc["iq"], Lc["ig"],
                Lc["W"], Lc["gamma_used"], Lc["q_overburden"],
                Lc["term_c"], Lc["term_q"], Lc["term_g"],
                Lc["qnu"], Lc["qns"], Lc["qs_gross"],
            ],
        }
    ).round(3)
    st.dataframe(comp_df, width="stretch", hide_index=True, height=560)

    with st.expander("Grouped IS 6403 Factor & Capacity Summary"):
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Bearing, Shape, Depth & Inclination Factors (General)**")
            st.write(f"• Bearing factors: Nc = {G['Nc']:.3f}, Nq = {G['Nq']:.3f}, Nγ = {G['Ng']:.3f}")
            st.write(f"• Shape factors: sc = {G['sc']:.3f}, sq = {G['sq']:.3f}, sγ = {G['sg']:.3f}")
            st.write(f"• Depth factors: dc = {G['dc']:.3f}, dq = {G['dq']:.3f}, dγ = {G['dg']:.3f}")
            st.write(f"• Inclination factors: ic = {G['ic']:.3f}, iq = {G['iq']:.3f}, iγ = {G['ig']:.3f}")
        with g2:
            st.markdown("**Groundwater, Eccentricity & Design Capacities**")
            st.write(f"• Groundwater: W′ = {G['W']:.3f}, q = {G['q_overburden']:.2f} kPa, γ_avg = {G['gamma_used']:.2f} kN/m³")
            st.write(f"• Effective dimensions: B′ = {G['B_eff']:.3f} m, L′ = {G['L_eff'] if shape != 'strip' else float('inf'):.3f} m")
            st.write(f"• Selected/blended net ultimate q_nu = {qnu_design:.2f} kPa")
            st.write(f"• Selected/blended net safe q_ns = {qns:.2f} kPa · Gross safe q_s = {qgross_design:.2f} kPa")

    st.caption(
        "q_nu is the NET ultimate capacity: q(Nq−1) already removes the overburden q. With W′ the third term uses the "
        "bulk/saturated unit weight, not the buoyant one, otherwise the water table is counted twice."
    )

# ------------------------------------------------------------------ P4 · STRESS ANALYSIS WORKSPACE
elif page == "P4 Stress Increase":
    mod_header(
        "P4",
        "Subsurface Stress Increase Workspace",
        "Boussinesq / Newmark corner superposition and 2:1 stress spread across depth.",
    )

    sec_title("1. Footing Load, Geometry & Depth Grid")
    b1, b2, b3 = st.columns(3)
    with b1:
        q4 = st.number_input("Uniform net pressure q (kPa)", 0.1, 5000.0, 150.0, 5.0)
        B4 = st.number_input("Width B (m)", 0.1, 200.0, 2.0, 0.1, key="B4")
        L4 = st.number_input("Length L (m)", 0.1, 500.0, 3.0, 0.1, key="L4")
    with b2:
        zmax = st.number_input("Maximum depth below base (m)", 0.5, 200.0, 10.0, 0.5)
        dz = st.number_input("Depth step Δz (m)", 0.05, 5.0, 0.5, 0.05)
    with b3:
        px = st.number_input("Extra point x along B from centre (m)", -100.0, 100.0, 0.0, 0.5)
        py = st.number_input("Extra point y along L from centre (m)", -100.0, 100.0, 0.0, 0.5)

    zs = np.arange(dz, zmax + 1e-9, dz)
    pt_col = f"Δσz at ({px:g},{py:g}) m (kPa)"
    tab = pd.DataFrame(
        {
            "z (m)": zs,
            "Δσz centre (kPa)": [gt.dsig_center(q4, B4, L4, float(z)) for z in zs],
            "Δσz corner (kPa)": [gt.dsig_corner(q4, B4, L4, float(z)) for z in zs],
            "Δσz 2:1 (kPa)": [gt.dsig_2to1(q4, B4, L4, float(z)) for z in zs],
            pt_col: [gt.dsig_rect_point(q4, -B4 / 2, B4 / 2, -L4 / 2, L4 / 2, px, py, float(z)) for z in zs],
            "I corner (–)": [gt.I_corner(B4 / float(z), L4 / float(z)) for z in zs],
        }
    )

    sec_title("2. Stress Increase vs. Depth Visualization")
    palette = ["#38BDF8", "#34D399", "#F59E0B", "#C084FC"]
    fig4 = go.Figure()
    for idx, k in enumerate(tab.columns[1:5]):
        fig4.add_trace(
            go.Scatter(
                x=tab[k],
                y=tab["z (m)"],
                mode="lines",
                name=k,
                line=dict(color=palette[idx % len(palette)], width=2.4),
                hovertemplate=f"<b>{k}</b><br>z = %{{y:.2f}} m<br>Δσz = %{{x:.2f}} kPa<extra></extra>",
            )
        )
    style_plotly(fig4, "Vertical Stress Increase, Δσz (kPa)", "Depth Below Footing Base, z (m)", height=520, reverse_y=True)
    st.plotly_chart(fig4, use_container_width=True)

    sec_title("3. Method Comparison Table")
    st.dataframe(tab.round(3), width="stretch", hide_index=True)

    sec_title("4. Engineering Notes")
    st.markdown(
        """
        <div class="fx-eq-box">
            • <strong>Attenuation with depth:</strong> Vertical stress increment Δσz decays with depth z as the load spreads over a wider subsurface zone.<br>
            • <strong>Boussinesq vs. 2:1 spread:</strong> Boussinesq integrates elastic half-space stress distribution (centre = 4 × corner of a B/2 × L/2 rectangle; arbitrary points via signed corner superposition), whereas the 2:1 method approximates spread at a constant 2V:1 slope [Δσz = qBL/((B+z)(L+z))].<br>
            • <strong>Centre vs. corner:</strong> Stress directly beneath the footing centre exceeds that beneath a corner at shallow-to-moderate depths and converges as z becomes large relative to B and L.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------ P5 · SETTLEMENT ANALYSIS DASHBOARD
elif page == "P5 Settlement":
    prof = to_profile(ss["layers"], ss["wt_meas"], ss["wt_des"])
    mod_header(
        "P5",
        "Settlement & Consolidation Analysis Dashboard",
        "Schmertmann granular settlement, NC/OC clay sublayer consolidation, and time–settlement response.",
        chips=[("Design GWT", f"{prof.wt_design:g} m"), ("Clay Strata", str(sum(1 for L in prof.layers if L.kind == "clay")))],
    )

    sec_title("1. Foundation, Loading & Consolidation Inputs")
    d1, d2, d3 = st.columns(3)
    with d1:
        B5 = st.number_input("Footing width B (m)", 0.1, 200.0, 2.0, 0.1, key="B5")
        L5 = st.number_input("Footing length L (m)", 0.1, 500.0, 2.0, 0.1, key="L5")
        Df5 = st.number_input("Founding depth Df (m)", 0.0, 50.0, 1.5, 0.1, key="Df5")
    with d2:
        q5 = st.number_input(
            "Net pressure Δp at founding level (kPa)", 0.1, 5000.0, 100.0, 5.0,
            help="Gross pressure minus the overburden removed (net pressure).",
        )
        yrs = st.number_input("Time for creep factor C2 (years)", 0.1, 100.0, 5.0, 0.5)
        sub = st.number_input("Clay sublayer thickness (m, ≤ 0.5)", 0.05, 0.5, 0.5, 0.05)
    with d3:
        where = st.selectbox("Stress under the footing for clay layers", ["Centre (Boussinesq)", "Corner (Boussinesq)", "2:1 method"])
        nc = st.checkbox("Treat all clay as normally consolidated (ignore OCR)", value=False)

    Bs, Ls = min(B5, L5), max(B5, L5)
    ss_ = gt.schmertmann(prof, Bs, Ls, Df5, q5, years=yrs)
    fn = {
        "Centre (Boussinesq)": lambda z: gt.dsig_center(q5, B5, L5, z - Df5),
        "Corner (Boussinesq)": lambda z: gt.dsig_corner(q5, B5, L5, z - Df5),
        "2:1 method": lambda z: gt.dsig_2to1(q5, B5, L5, z - Df5),
    }[where]
    cs = gt.consolidation(prof, fn, sub=sub, force_nc=nc)
    tot = ss_["S_mm"] + cs["S_mm"]

    # Granular settlement section: metrics + Iz graph side-by-side, slice table below
    sec_title("2. Granular Settlement — Schmertmann et al. (1978)")
    g_left, g_right = st.columns([1.25, 1.75], gap="large")
    with g_left:
        gm1, gm2 = st.columns(2)
        with gm1:
            mcard("Granular Settlement", f"{ss_['S_mm']:.1f} mm", "Schmertmann Eq. 1", "#38BDF8")
        with gm2:
            mcard("z_peak / z_max", f"{ss_['z_peak']:.2f} / {ss_['z_max']:.2f} m", "Influence depths below base", "#A78BFA")
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        gm3, gm4, gm5 = st.columns(3)
        with gm3:
            mcard("C1 Factor", f"{ss_['C1']:.3f}", "≥ 0.5", "#60A5FA")
        with gm4:
            mcard("C2 Factor", f"{ss_['C2']:.3f}", f"t = {yrs:g} yr", "#34D399")
        with gm5:
            mcard("Peak Izp", f"{ss_['Izp']:.3f}", "At z_peak", "#F59E0B")

    rs = pd.DataFrame(ss_["rows"])
    with g_right:
        if not rs.empty:
            fig_iz = go.Figure()
            fig_iz.add_trace(
                go.Scatter(
                    x=rs["Iz"],
                    y=rs["z"],
                    mode="lines",
                    name="Strain Influence Factor Iz",
                    line=dict(color="#38BDF8", width=2.5),
                    hovertemplate="Depth z = %{y:.2f} m<br>Iz = %{x:.4f}<extra></extra>",
                )
            )
            style_plotly(fig_iz, "Strain Influence Factor, Iz (–)", "Depth Below Footing Base, z (m)", height=420, reverse_y=True)
            st.plotly_chart(fig_iz, use_container_width=True)
        else:
            st.info("No granular slices within influence depth.")

    if not rs.empty:
        with st.expander("Granular Slice Calculation Table (Δz = 0.1 m)"):
            st.dataframe(
                rs.rename(columns={"z": "z (m)", "E": "Es (kPa)", "strain_term": "Iz Δz/Es (1/kPa)"}),
                width="stretch",
                hide_index=True,
            )

    st.caption(
        "S = C1 C2 Δp Σ(Iz/Es)Δz; C1 = 1 − 0.5σ′v0/Δp ≥ 0.5; C2 = 1 + 0.2 log10(t/0.1); Es = 2.5qc (square) to 3.5qc (L/B ≥ 10); "
        "qc = (qc/N)·N from the profile unless an Es is entered. Clay slices are skipped here and handled below."
    )

    # Clay consolidation section
    sec_title("3. Clay Consolidation Settlement (1-D Sublayers)")
    mcard("Consolidation Settlement (All Clay Sublayers)", f"{cs['S_mm']:.1f} mm", f"Stress method: {where} · Design GWT", "#60A5FA")
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    if cs["rows"]:
        cr = pd.DataFrame(cs["rows"]).rename(
            columns={
                "layer": "Layer",
                "z": "z mid (m)",
                "h": "h (m)",
                "e0": "e0 (–)",
                "s0": "σ′v0 (kPa)",
                "sp": "σ′p (kPa)",
                "ds": "Δσ (kPa)",
                "state": "State",
                "S_mm": "S (mm)",
            }
        )
        st.dataframe(cr.round(3), width="stretch", hide_index=True)
        st.caption(
            "NC: S = Cc h/(1+e0) log10((σ′v0+Δσ)/σ′v0). OC with σ′v0+Δσ ≤ σ′p: Cr in place of Cc. "
            "OC with σ′v0+Δσ > σ′p: Cr h/(1+e0) log10(σ′p/σ′v0) + Cc h/(1+e0) log10((σ′v0+Δσ)/σ′p). Water table: design."
        )
    else:
        st.info("No clay layer in the profile.")

    # Time-settlement analysis section
    sec_title("4. Time–Settlement Analysis")
    clays = [L for L in prof.layers if L.kind == "clay"]
    if clays:
        lo = layer_options(prof)
        names = [k for k, v in lo.items() if v.kind == "clay"]
        sel = st.selectbox("Selected clay layer", names)
        Ls_ = lo[sel]
        e1, e2, e3 = st.columns(3)
        with e1:
            drain = st.selectbox("Drainage boundary", ["Double (top and bottom)", "Single (top only)", "Single (bottom only)"])
        with e2:
            cv = st.number_input("Coefficient of consolidation cv (m²/year)", 0.001, 1000.0, float(Ls_.cv) if Ls_.cv > 0 else 1.0, 0.1)
        with e3:
            H = st.number_input("Layer thickness H (m)", 0.1, 100.0, float(Ls_.bot - Ls_.top), 0.1)

        Hdr = H / 2 if drain.startswith("Double") else H
        Sc = sum(r["S_mm"] for r in cs["rows"] if r["layer"] == Ls_.name)
        ts = np.logspace(-2, 2, 80)
        curve = gt.time_settlement(Sc, cv, H, drain.startswith("Double"), list(ts))
        t50 = 0.197 * Hdr ** 2 / cv
        t90 = 0.848 * Hdr ** 2 / cv

        tm1, tm2, tm3, tm4 = st.columns(4)
        with tm1:
            mcard("Drainage Path H_dr", f"{Hdr:g} m", drain.split(" (")[0], "#38BDF8")
        with tm2:
            mcard("Selected Layer S_c", f"{Sc:.1f} mm", Ls_.name, "#34D399")
        with tm3:
            mcard("t50 (50% Consol.)", f"{t50:.2f} yr", "Tv = 0.197", "#60A5FA")
        with tm4:
            mcard("t90 (90% Consol.)", f"{t90:.2f} yr", "Tv = 0.848", "#F59E0B")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        fig_t = go.Figure()
        fig_t.add_trace(
            go.Scatter(
                x=ts,
                y=[ss_["S_mm"] + c[2] for c in curve],
                mode="lines",
                name="Granular + Consolidation (mm)",
                line=dict(color="#38BDF8", width=2.5),
                hovertemplate="t = %{x:.2f} yr<br>Total S(t) = %{y:.1f} mm<extra></extra>",
            )
        )
        fig_t.add_trace(
            go.Scatter(
                x=ts,
                y=[c[2] for c in curve],
                mode="lines",
                name="Consolidation of Selected Clay Layer (mm)",
                line=dict(color="#34D399", width=2.2, dash="dash"),
                hovertemplate="t = %{x:.2f} yr<br>Clay S_c(t) = %{y:.1f} mm<extra></extra>",
            )
        )
        style_plotly(fig_t, "Time, t (years)", "Settlement, S (mm)", height=500, reverse_y=True)
        fig_t.update_xaxes(type="log")
        st.plotly_chart(fig_t, use_container_width=True)

        st.caption(
            "Tv = cv t / H_dr²; Tv = (π/4)U² for U < 0.6, else Tv = −0.933 log10(1−U) − 0.085. "
            "The granular settlement is taken as immediate."
        )
    else:
        st.info("Add a clay layer in P1 to get a time–settlement curve.")

    # Overall settlement summary
    sec_title("5. Overall Settlement Summary")
    s_sum1, s_sum2, s_sum3 = st.columns(3)
    with s_sum1:
        mcard("Granular Settlement", f"{ss_['S_mm']:.1f} mm", "Schmertmann method", "#38BDF8")
    with s_sum2:
        mcard("Consolidation Settlement", f"{cs['S_mm']:.1f} mm", "1-D clay sublayers", "#60A5FA")
    with s_sum3:
        mcard("Total Settlement", f"{tot:.1f} mm", "End of primary consolidation", "#34D399")

    st.markdown(
        f'<div class="fx-banner-ok">Total settlement at the end of consolidation = {ss_["S_mm"]:.1f} + {cs["S_mm"]:.1f} = {tot:.1f} mm</div>',
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------ SOURCES
elif page == "Sources":
    mod_header(
        "REF",
        "Equation Sources & References",
        "Primary Indian Standards, textbooks, and course references for CE 402 (IIT Mandi).",
    )
    st.table(
        pd.DataFrame(
            [
                ["Vertical stress, pore pressure", "σv = Σγh, u = γw(z − zw), σ′ = σ − u", "Terzaghi, Peck & Mesri (1996), Ch. 1"],
                ["SPT overburden correction", "CN = 0.77 log10(1920/σ′v), N′ = CN·N", "IS 2131:1981 cl. 5.2.1 / Fig. 2 (chart); closed form Peck et al. (1974) in Das"],
                ["SPT dilatancy correction", "N″ = 15 + 0.5(N′ − 15) for N′ > 15, saturated fine sand", "IS 2131:1981; Terzaghi & Peck (1948)"],
                ["c′, φ′ from direct shear", "τ = c′ + σn tanφ′, least squares", "Mohr–Coulomb; Das, Principles of Foundation Engineering"],
                ["Bearing capacity factors", "Nq = e^(π tanφ) tan²(45+φ/2); Nc = (Nq−1)cotφ; Nγ = 2(Nq+1)tanφ", "IS 6403:1981 cl. 5.1.2 and Table 1"],
                ["Net ultimate capacity", "q_nu = c Nc sc dc ic + q(Nq−1) sq dq iq + 0.5Bγ Nγ sγ dγ iγ W′", "IS 6403:1981 cl. 5.1.2"],
                ["Shape factors", "Square 1.3 / 1.2 / 0.8; rectangular 1+0.2B/L, 1+0.2B/L, 1−0.4B/L; circle 1.3 / 1.2 / 0.6", "IS 6403:1981 Table 2"],
                ["Depth factors", "dc = 1 + 0.2(Df/B)√Nφ; dq = dγ = 1 + 0.1(Df/B)√Nφ for φ > 10°", "IS 6403:1981 cl. 5.1.2.2"],
                ["Inclination factors", "ic = iq = (1 − α/90)²; iγ = (1 − α/φ)²", "IS 6403:1981 cl. 5.1.2.3"],
                ["Water-table factor", "W′ = 0.5 (zw ≤ Df) … 1.0 (zw ≥ Df + B), linear between", "IS 6403:1981 cl. 5.1.2.2"],
                ["Local shear", "c* = (2/3)c, tanφ* = (2/3)tanφ", "Terzaghi (1943); IS 6403:1981 cl. 5.1.2.1"],
                ["Eccentric load", "B′ = B − 2e_B, L′ = L − 2e_L", "IS 6403:1981; Meyerhof (1953)"],
                ["Stress under a corner", "Δσz = q I(m,n); I from Newmark (1935) closed form", "Das, Principles of Foundation Engineering, Boussinesq/Newmark"],
                ["Stress at any point", "Signed sum of corner contributions (superposition)", "Newmark (1935)"],
                ["2:1 method", "Δσz = qBL/((B+z)(L+z))", "Das, approximate stress distribution"],
                ["Granular settlement", "S = C1 C2 Δp Σ(Iz/Es)Δz; C1, C2, Izp, Es", "Schmertmann, Hartman & Brown (1978), J. Geotech. Eng. Div. ASCE 104(GT8)"],
                ["Clay consolidation", "NC / OC settlement with Cc, Cr, σ′p", "Terzaghi (1925); Das; Terzaghi, Peck & Mesri (1996)"],
                ["Time–settlement", "Tv = cv t/Hdr², U–Tv relations", "Terzaghi 1-D consolidation; Das"],
            ],
            columns=["Item", "Equation", "Source"],
        )
    )
    st.caption("Some code-table values were checked against secondary sources only; verify them against your copy of the standard before submission.")

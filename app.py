"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         SIMULASI SISTEM PIKET IT DEL - DASHBOARD ANALITIK PROFESIONAL       ║
║         Discrete Event Simulation (SimPy) | Modern Dark Dashboard            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Cara menjalankan:
    pip install streamlit simpy plotly pandas numpy
    streamlit run simulasi_piket_itdel.py
"""

# ============================================================
# IMPORTS
# ============================================================
import streamlit as st
import simpy
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64

# ============================================================
# PAGE CONFIG (must be first Streamlit call)
# ============================================================
st.set_page_config(
    page_title="Simulasi Piket IT Del",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# FORMAT HELPERS  (digunakan di seluruh output)
# ============================================================
def format_time_human(seconds: float, show_seconds: bool = True) -> str:
    """
    Konversi detik ke format human-readable.
    Contoh: 3723 → '1 jam 2 mnt 3 dtk'  |  183 → '3 mnt 3 dtk'  |  45 → '45 dtk'
    show_seconds=False → '1 jam 2 mnt' / '3 mnt'
    """
    if seconds is None or (isinstance(seconds, float) and np.isnan(seconds)):
        return "–"
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    parts = []
    if h > 0:
        parts.append(f"{h} jam")
    if m > 0:
        parts.append(f"{m} mnt")
    if show_seconds and (s > 0 or (h == 0 and m == 0)):
        parts.append(f"{s} dtk")
    return " ".join(parts) if parts else "0 dtk"


def format_time_hms(seconds: float) -> str:
    """Format digital: 01:23:45"""
    if seconds is None:
        return "00:00:00"
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def fmt(seconds: float) -> str:
    """Alias pendek — dipakai di tooltip & teks inline."""
    return format_time_human(seconds)


# ============================================================
# CUSTOM CSS – DARK MODERN THEME
# ============================================================
st.markdown("""
<style>
    /* ── Base ── */
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .main .block-container { padding: 1.5rem 2rem; max-width: 1600px; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    [data-testid="stSidebar"] .stMarkdown h3 { color: #58a6ff; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }

    /* ── KPI Cards ── */
    .kpi-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2333 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }
    .kpi-card:hover { transform: translateY(-2px); border-color: #58a6ff; }
    .kpi-value { font-size: 2rem; font-weight: 700; margin: 0.3rem 0; }
    .kpi-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #8b949e; }
    .kpi-delta { font-size: 0.8rem; margin-top: 0.3rem; }
    .accent-blue  { color: #58a6ff; }
    .accent-green { color: #3fb950; }
    .accent-orange{ color: #f0883e; }
    .accent-red   { color: #f85149; }
    .accent-purple{ color: #bc8cff; }

    /* ── Section Headers ── */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e6edf3;
        border-bottom: 2px solid #21262d;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }
    .section-subheader { font-size: 0.85rem; color: #8b949e; margin-bottom: 1rem; }

    /* ── Insight Box ── */
    .insight-box {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }
    .insight-title { font-weight: 600; color: #58a6ff; margin-bottom: 0.3rem; font-size: 0.9rem; }
    .insight-text { color: #c9d1d9; font-size: 0.85rem; line-height: 1.6; }

    /* ── Warning / Bottleneck ── */
    .bottleneck-box {
        background: linear-gradient(135deg, #1a0a0a 0%, #2d1515 100%);
        border: 1px solid #f85149;
        border-left: 4px solid #f85149;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }
    .bottleneck-title { font-weight: 600; color: #f85149; margin-bottom: 0.3rem; font-size: 0.9rem; }

    /* ── Progress bar ── */
    .prog-bar-wrap { background: #21262d; border-radius: 6px; overflow: hidden; height: 8px; margin-top: 4px; }
    .prog-bar-fill { height: 8px; border-radius: 6px; transition: width 0.4s ease; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { background-color: #161b22; border-radius: 8px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { color: #8b949e; }
    .stTabs [aria-selected="true"] { background-color: #21262d !important; color: #58a6ff !important; border-radius: 6px; }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%);
        color: white; border: none; border-radius: 8px;
        font-weight: 600; padding: 0.5rem 1.5rem;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }

    /* ── Metric overrides ── */
    [data-testid="metric-container"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 0.8rem; }

    /* ── Stage stat cards (Bottleneck tab) ── */
    .stage-card {
        background: #161b22; border: 1px solid #30363d; border-radius: 10px;
        padding: 1rem; text-align: center; margin-bottom: 0.5rem;
    }
    .stage-card.bottleneck-stage { border-color: #f85149; background: #1a0e0e; }
    .stage-card .sc-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; color: #8b949e; }
    .stage-card .sc-value { font-size: 1.4rem; font-weight: 700; margin: 0.2rem 0; }
    .stage-card .sc-sub   { font-size: 0.75rem; color: #8b949e; }

    /* ── Severity badge ── */
    .severity-critical { background:#3d0f0f; color:#f85149; border:1px solid #f85149; border-radius:6px; padding:2px 10px; font-size:0.75rem; font-weight:700; }
    .severity-high     { background:#3d2a0a; color:#f0883e; border:1px solid #f0883e; border-radius:6px; padding:2px 10px; font-size:0.75rem; font-weight:700; }
    .severity-medium   { background:#1e2a0a; color:#ffa657; border:1px solid #ffa657; border-radius:6px; padding:2px 10px; font-size:0.75rem; font-weight:700; }
    .severity-low      { background:#0a2a1a; color:#3fb950; border:1px solid #3fb950; border-radius:6px; padding:2px 10px; font-size:0.75rem; font-weight:700; }

    /* ── Summary banner ── */
    .summary-banner {
        background: linear-gradient(135deg, #0d1b35 0%, #0f2340 100%);
        border: 1px solid #1f3a6e; border-radius: 12px;
        padding: 1.2rem 1.5rem; margin: 1rem 0;
        font-size: 0.9rem; color: #c9d1d9; line-height: 1.8;
    }
    .summary-banner b { color: #58a6ff; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA MODELS
# ============================================================
@dataclass
class SimConfig:
    """Konfigurasi simulasi sistem piket."""
    # Struktur
    num_meja: int = 60
    mahasiswa_per_meja: int = 3

    # Petugas per tahap (total harus 7 secara default)
    petugas_lauk: int = 2
    petugas_angkut: int = 2
    petugas_nasi: int = 3

    # Distribusi waktu (detik)
    lauk_min: float = 30.0
    lauk_max: float = 60.0
    angkut_min: float = 20.0
    angkut_max: float = 60.0
    nasi_min: float = 30.0
    nasi_max: float = 60.0

    # Kapasitas angkut
    angkut_min_ompreng: int = 4
    angkut_max_ompreng: int = 7

    # Seed
    random_seed: int = 42

    @property
    def total_ompreng(self) -> int:
        return self.num_meja * self.mahasiswa_per_meja

    @property
    def total_petugas(self) -> int:
        return self.petugas_lauk + self.petugas_angkut + self.petugas_nasi


@dataclass
class TableRecord:
    """Rekaman data satu meja."""
    meja_id: int
    start_lauk: float = 0.0
    end_lauk: float = 0.0
    start_angkut: float = 0.0
    end_angkut: float = 0.0
    start_nasi: float = 0.0
    end_nasi: float = 0.0
    wait_before_lauk: float = 0.0
    wait_before_angkut: float = 0.0
    wait_before_nasi: float = 0.0

    @property
    def total_time(self) -> float:
        return self.end_nasi

    @property
    def lauk_duration(self) -> float:
        return self.end_lauk - self.start_lauk

    @property
    def angkut_duration(self) -> float:
        return self.end_angkut - self.start_angkut

    @property
    def nasi_duration(self) -> float:
        return self.end_nasi - self.start_nasi


@dataclass
class SimResult:
    """Hasil simulasi lengkap."""
    config: SimConfig
    tables: List[TableRecord] = field(default_factory=list)
    stage_busy_time: Dict[str, float] = field(default_factory=dict)
    total_sim_time: float = 0.0

    @property
    def df_tables(self) -> pd.DataFrame:
        rows = []
        for t in self.tables:
            rows.append({
                "Meja": t.meja_id + 1,
                "Mulai Lauk (s)": t.start_lauk,
                "Selesai Lauk (s)": t.end_lauk,
                "Mulai Angkut (s)": t.start_angkut,
                "Selesai Angkut (s)": t.end_angkut,
                "Mulai Nasi (s)": t.start_nasi,
                "Selesai Nasi (s)": t.end_nasi,
                "Durasi Lauk (s)": t.lauk_duration,
                "Durasi Angkut (s)": t.angkut_duration,
                "Durasi Nasi (s)": t.nasi_duration,
                "Total Waktu (s)": t.total_time,
                "Tunggu Lauk (s)": t.wait_before_lauk,
                "Tunggu Angkut (s)": t.wait_before_angkut,
                "Tunggu Nasi (s)": t.wait_before_nasi,
            })
        return pd.DataFrame(rows)


# ============================================================
# SIMULATION MODEL (SimPy DES)
# ============================================================
class PiketSimulation:
    """Discrete Event Simulation sistem piket IT Del menggunakan SimPy."""

    def __init__(self, config: SimConfig):
        self.config = config
        self.env = simpy.Environment()
        self.rng = random.Random(config.random_seed)

        # Resources
        self.res_lauk   = simpy.Resource(self.env, capacity=config.petugas_lauk)
        self.res_angkut = simpy.Resource(self.env, capacity=config.petugas_angkut)
        self.res_nasi   = simpy.Resource(self.env, capacity=config.petugas_nasi)

        self.tables: List[TableRecord] = []
        self._busy: Dict[str, float] = {"lauk": 0.0, "angkut": 0.0, "nasi": 0.0}

    def _t_lauk(self) -> float:
        return self.rng.uniform(self.config.lauk_min, self.config.lauk_max)

    def _t_angkut(self) -> float:
        batch = self.rng.randint(self.config.angkut_min_ompreng, self.config.angkut_max_ompreng)
        per_trip = self.rng.uniform(self.config.angkut_min, self.config.angkut_max)
        # Total angkut time ≈ ceil(ompreng/batch) * per_trip
        trips = max(1, int(np.ceil(self.config.mahasiswa_per_meja / batch)))
        return trips * per_trip

    def _t_nasi(self) -> float:
        return self.rng.uniform(self.config.nasi_min, self.config.nasi_max)

    def _meja_process(self, meja_id: int):
        rec = TableRecord(meja_id=meja_id)

        # ── Tahap 1: Lauk ────────────────────────────────────
        arrive_lauk = self.env.now
        with self.res_lauk.request() as req:
            yield req
            rec.wait_before_lauk = self.env.now - arrive_lauk
            rec.start_lauk = self.env.now
            dur = self._t_lauk() * self.config.mahasiswa_per_meja
            yield self.env.timeout(dur)
            rec.end_lauk = self.env.now
            self._busy["lauk"] += dur

        # ── Tahap 2: Angkut ──────────────────────────────────
        arrive_angkut = self.env.now
        with self.res_angkut.request() as req:
            yield req
            rec.wait_before_angkut = self.env.now - arrive_angkut
            rec.start_angkut = self.env.now
            dur = self._t_angkut()
            yield self.env.timeout(dur)
            rec.end_angkut = self.env.now
            self._busy["angkut"] += dur

        # ── Tahap 3: Nasi ────────────────────────────────────
        arrive_nasi = self.env.now
        with self.res_nasi.request() as req:
            yield req
            rec.wait_before_nasi = self.env.now - arrive_nasi
            rec.start_nasi = self.env.now
            dur = self._t_nasi() * self.config.mahasiswa_per_meja
            yield self.env.timeout(dur)
            rec.end_nasi = self.env.now
            self._busy["nasi"] += dur

        self.tables.append(rec)

    def _generator(self):
        for i in range(self.config.num_meja):
            self.env.process(self._meja_process(i))
            yield self.env.timeout(0)  # semua mulai bersamaan (dibatasi resource)

    def run(self) -> SimResult:
        self.env.process(self._generator())
        self.env.run()

        result = SimResult(
            config=self.config,
            tables=sorted(self.tables, key=lambda x: x.meja_id),
            stage_busy_time=self._busy.copy(),
            total_sim_time=self.env.now,
        )
        return result


# ============================================================
# ANALYSIS MODULE
# ============================================================
def compute_utilization(result: SimResult) -> Dict[str, float]:
    """Hitung utilisasi tiap tahap (0–100%)."""
    T = result.total_sim_time
    cfg = result.config
    utils = {}
    for stage, cap in [("lauk", cfg.petugas_lauk),
                       ("angkut", cfg.petugas_angkut),
                       ("nasi", cfg.petugas_nasi)]:
        util = (result.stage_busy_time[stage] / (T * cap)) * 100 if T > 0 else 0
        utils[stage] = min(util, 100.0)
    return utils


def detect_bottleneck(result: SimResult) -> Tuple[str, str, Dict[str, float]]:
    utils = compute_utilization(result)
    df = result.df_tables
    avg_wait = {
        "lauk": df["Tunggu Lauk (s)"].mean(),
        "angkut": df["Tunggu Angkut (s)"].mean(),
        "nasi": df["Tunggu Nasi (s)"].mean(),
    }
    # Bottleneck = highest wait time
    bottleneck = max(avg_wait, key=avg_wait.get)
    labels = {"lauk": "Proses Lauk", "angkut": "Proses Angkut", "nasi": "Proses Nasi"}
    return labels[bottleneck], bottleneck, avg_wait


def compute_throughput(result: SimResult) -> float:
    """Meja per menit."""
    T_minutes = result.total_sim_time / 60
    return result.config.num_meja / T_minutes if T_minutes > 0 else 0


def bottleneck_severity(util_pct: float, avg_wait_s: float) -> Tuple[str, str]:
    """
    Kembalikan (label, css_class) berdasarkan utilisasi dan rata-rata tunggu.
    """
    if util_pct >= 90 or avg_wait_s >= 120:
        return "CRITICAL 🔴", "severity-critical"
    elif util_pct >= 75 or avg_wait_s >= 60:
        return "HIGH 🟠", "severity-high"
    elif util_pct >= 55 or avg_wait_s >= 20:
        return "MEDIUM 🟡", "severity-medium"
    else:
        return "LOW 🟢", "severity-low"


def sensitivity_analysis(base_config: SimConfig, bottleneck_stage: str) -> List[Dict]:
    """Simulasikan efek penambahan petugas pada bottleneck."""
    rows = []
    for extra in range(0, 4):
        cfg_copy = SimConfig(
            num_meja=base_config.num_meja,
            mahasiswa_per_meja=base_config.mahasiswa_per_meja,
            petugas_lauk=base_config.petugas_lauk + (extra if bottleneck_stage == "lauk" else 0),
            petugas_angkut=base_config.petugas_angkut + (extra if bottleneck_stage == "angkut" else 0),
            petugas_nasi=base_config.petugas_nasi + (extra if bottleneck_stage == "nasi" else 0),
            lauk_min=base_config.lauk_min, lauk_max=base_config.lauk_max,
            angkut_min=base_config.angkut_min, angkut_max=base_config.angkut_max,
            nasi_min=base_config.nasi_min, nasi_max=base_config.nasi_max,
            angkut_min_ompreng=base_config.angkut_min_ompreng,
            angkut_max_ompreng=base_config.angkut_max_ompreng,
            random_seed=base_config.random_seed,
        )
        sim = PiketSimulation(cfg_copy)
        res = sim.run()
        rows.append({
            "Extra Petugas": extra,
            "Total Petugas Tahap": (cfg_copy.petugas_lauk if bottleneck_stage=="lauk"
                                    else cfg_copy.petugas_angkut if bottleneck_stage=="angkut"
                                    else cfg_copy.petugas_nasi),
            "Total Waktu (s)": res.total_sim_time,
            "Total Waktu (menit)": res.total_sim_time / 60,
            "Total Waktu (Human)": fmt(res.total_sim_time),
        })
    return rows


# ============================================================
# VISUALISATION MODULE
# ============================================================
PLOT_THEME = dict(
    paper_bgcolor="#0e1117",
    plot_bgcolor="#161b22",
    font_color="#c9d1d9",
    font_family="Inter, sans-serif",
    font_size=11,
    colorway=["#58a6ff", "#3fb950", "#f0883e", "#bc8cff", "#f85149", "#ffa657"],
    margin=dict(l=40, r=20, t=40, b=40),
)

GRID_STYLE = dict(gridcolor="#21262d", zerolinecolor="#30363d")


def _apply_theme(fig) -> go.Figure:
    fig.update_layout(**PLOT_THEME)
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE)
    return fig


def chart_gantt(result: SimResult) -> go.Figure:
    """Gantt chart: proses tiap meja."""
    df = result.df_tables
    n = min(30, len(df))  # tampilkan 30 meja pertama agar readable
    colors = {"Lauk": "#58a6ff", "Angkut": "#f0883e", "Nasi": "#3fb950"}

    fig = go.Figure()
    stages = [
        ("Lauk",   "Mulai Lauk (s)",   "Selesai Lauk (s)"),
        ("Angkut", "Mulai Angkut (s)", "Selesai Angkut (s)"),
        ("Nasi",   "Mulai Nasi (s)",   "Selesai Nasi (s)"),
    ]
    for stage, col_start, col_end in stages:
        for _, row in df.head(n).iterrows():
            dur = row[col_end] - row[col_start]
            fig.add_trace(go.Bar(
                x=[dur],
                y=[f"Meja {int(row['Meja'])}"],
                base=[row[col_start]],
                orientation='h',
                marker_color=colors[stage],
                name=stage,
                showlegend=(int(row['Meja']) == 1),
                legendgroup=stage,
                hovertemplate=(
                    f"<b>{stage}</b> — Meja {int(row['Meja'])}<br>"
                    f"Mulai : {fmt(row[col_start])}<br>"
                    f"Selesai: {fmt(row[col_end])}<br>"
                    f"Durasi : <b>{fmt(dur)}</b><extra></extra>"
                ),
            ))

    fig.update_layout(
        title="Gantt Chart – Proses per Meja (30 Meja Pertama)",
        barmode='overlay',
        height=600,
        xaxis_title="Waktu sejak mulai (detik) — hover untuk format jam:menit:detik",
        yaxis_title="Meja",
        legend_title="Tahap",
        **PLOT_THEME,
    )
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE, autorange="reversed")
    return fig


def chart_completion_progress(result: SimResult) -> go.Figure:
    """Line chart: progress penyelesaian meja terhadap waktu."""
    df = result.df_tables.sort_values("Selesai Nasi (s)").copy()
    df["Meja Selesai Kumulatif"] = range(1, len(df) + 1)
    # human-readable label column for tooltip
    df["_waktu_fmt"] = df["Selesai Nasi (s)"].apply(fmt)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Selesai Nasi (s)"],
        y=df["Meja Selesai Kumulatif"],
        mode='lines+markers',
        line=dict(color="#58a6ff", width=2),
        marker=dict(size=4, color="#58a6ff"),
        fill='tozeroy',
        fillcolor='rgba(88,166,255,0.08)',
        name="Meja Selesai",
        customdata=df[["_waktu_fmt"]],
        hovertemplate="Waktu: <b>%{customdata[0]}</b><br>Meja Selesai: <b>%{y}</b><extra></extra>",
    ))

    # Target line
    fig.add_hline(y=result.config.num_meja, line_dash="dash",
                  line_color="#f0883e", annotation_text="Target semua meja")

    fig.update_layout(
        title="Progress Penyelesaian Meja terhadap Waktu",
        xaxis_title="Waktu sejak mulai (detik) — hover untuk format jam:menit:detik",
        yaxis_title="Jumlah Meja Selesai",
        height=350,
        **PLOT_THEME,
    )
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE)
    return fig


def chart_bottleneck(result: SimResult) -> go.Figure:
    """Bar chart bottleneck: rata-rata waktu tunggu per tahap."""
    df = result.df_tables
    stages = ["Lauk", "Angkut", "Nasi"]
    waits  = [df["Tunggu Lauk (s)"].mean(), df["Tunggu Angkut (s)"].mean(), df["Tunggu Nasi (s)"].mean()]
    max_idx = waits.index(max(waits))
    colors  = ["#f85149" if i == max_idx else "#2d4a6e" for i in range(3)]
    labels_fmt = [fmt(w) for w in waits]

    fig = go.Figure(go.Bar(
        x=stages, y=waits,
        marker_color=colors,
        text=labels_fmt,
        textposition="outside",
        customdata=[[fmt(w), fmt(df[f"Tunggu {s} (s)"].max())]
                    for s, w in zip(stages, waits)],
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Rata-rata tunggu: <b>%{customdata[0]}</b><br>"
            "Maks tunggu: %{customdata[1]}<extra></extra>"
        ),
    ))
    fig.update_layout(
        title="Bottleneck Detection – Rata-rata Waktu Tunggu per Tahap",
        yaxis_title="Waktu Tunggu Rata-rata (detik) — label menampilkan format jam:menit:detik",
        height=350,
        **PLOT_THEME,
    )
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE)
    return fig


def chart_utilization(result: SimResult) -> go.Figure:
    """Gauge charts untuk utilisasi tiap tahap."""
    utils = compute_utilization(result)
    stages = [("lauk", "Lauk"), ("angkut", "Angkut"), ("nasi", "Nasi")]

    fig = make_subplots(rows=1, cols=3, specs=[[{"type": "indicator"}]*3])
    colors_gauge = {"lauk": "#58a6ff", "angkut": "#f0883e", "nasi": "#3fb950"}

    for col, (key, label) in enumerate(stages, 1):
        val = utils[key]
        bar_color = "#f85149" if val > 85 else colors_gauge[key]
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=val,
            title={"text": f"Utilisasi {label}", "font": {"size": 13, "color": "#c9d1d9"}},
            number={"suffix": "%", "font": {"size": 22, "color": "#e6edf3"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#8b949e"},
                "bar": {"color": bar_color},
                "bgcolor": "#21262d",
                "bordercolor": "#30363d",
                "steps": [
                    {"range": [0, 60], "color": "#161b22"},
                    {"range": [60, 85], "color": "#1c2a1c"},
                    {"range": [85, 100], "color": "#2d1515"},
                ],
                "threshold": {"line": {"color": "#f85149", "width": 2}, "value": 85},
            },
        ), row=1, col=col)

    fig.update_layout(
        height=260,
        paper_bgcolor="#0e1117",
        font_color="#c9d1d9",
        margin=dict(l=20, r=20, t=30, b=10),
    )
    return fig


def chart_duration_distribution(result: SimResult) -> go.Figure:
    """Box plot distribusi durasi proses per tahap."""
    df = result.df_tables
    fig = go.Figure()
    stage_data = [
        ("Lauk",   df["Durasi Lauk (s)"],   "#58a6ff"),
        ("Angkut", df["Durasi Angkut (s)"], "#f0883e"),
        ("Nasi",   df["Durasi Nasi (s)"],   "#3fb950"),
    ]
    for name, data, color in stage_data:
        fig.add_trace(go.Box(
            y=data, name=name,
            marker_color=color,
            boxmean='sd',
            hovertemplate=f"<b>{name}</b><br>Durasi: <b>%{{customdata}}</b><extra></extra>",
            customdata=[fmt(v) for v in data],
        ))

    fig.update_layout(
        title="Distribusi Durasi Proses per Tahap",
        yaxis_title="Durasi (detik) — hover untuk format jam:menit:detik",
        height=350,
        **PLOT_THEME,
    )
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE)
    return fig


def chart_cumulative_completion(result: SimResult) -> go.Figure:
    """Cumulative completion curve dengan shaded area."""
    df = result.df_tables.sort_values("Selesai Nasi (s)").copy()
    pct = (df["Meja"].rank() / len(df) * 100).values
    df["_pct"] = pct
    df["_waktu_fmt"] = df["Selesai Nasi (s)"].apply(fmt)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Selesai Nasi (s)"],
        y=pct,
        mode='lines',
        line=dict(color="#bc8cff", width=3),
        fill='tozeroy',
        fillcolor='rgba(188,140,255,0.1)',
        name="% Selesai",
        customdata=df[["_waktu_fmt", "Meja"]],
        hovertemplate=(
            "Waktu: <b>%{customdata[0]}</b><br>"
            "Selesai: <b>%{y:.1f}%</b> (Meja ke-%{customdata[1]})<extra></extra>"
        ),
    ))
    for pct_mark in [25, 50, 75, 100]:
        fig.add_hline(y=pct_mark, line_dash="dot", line_color="#30363d",
                      annotation_text=f"{pct_mark}%", annotation_font_color="#8b949e")

    fig.update_layout(
        title="Cumulative Completion Curve",
        xaxis_title="Waktu sejak mulai (detik) — hover untuk format jam:menit:detik",
        yaxis_title="Persentase Meja Selesai (%)",
        height=350,
        **PLOT_THEME,
    )
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE, range=[0, 105])
    return fig


def chart_sensitivity(sens_data: List[Dict]) -> go.Figure:
    """Mini sensitivity analysis: waktu vs jumlah petugas bottleneck."""
    df = pd.DataFrame(sens_data)
    df["Waktu (Human)"] = df["Total Waktu (s)"].apply(fmt)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"+{r['Extra Petugas']} petugas" for _, r in df.iterrows()],
        y=df["Total Waktu (s)"],
        marker_color=["#58a6ff" if i == 0 else "#3fb950" for i in range(len(df))],
        text=df["Waktu (Human)"],
        textposition="outside",
        customdata=df[["Waktu (Human)", "Total Petugas Tahap"]],
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Total waktu: <b>%{customdata[0]}</b><br>"
            "Petugas di tahap: %{customdata[1]}<extra></extra>"
        ),
    ))

    fig.update_layout(
        title="Sensitivity Analysis – Efek Penambahan Petugas di Bottleneck",
        xaxis_title="Penambahan Petugas pada Tahap Bottleneck",
        yaxis_title="Total Waktu Selesai (detik) — label menampilkan format jam:menit:detik",
        height=350,
        **PLOT_THEME,
    )
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE)
    return fig


# ============================================================
# INSIGHT GENERATOR
# ============================================================
def generate_insights(result: SimResult, sens_data: List[Dict]) -> List[Dict]:
    cfg = result.config
    df = result.df_tables
    utils = compute_utilization(result)
    bottleneck_label, bottleneck_key, avg_wait = detect_bottleneck(result)
    T_s   = result.total_sim_time
    T_min = T_s / 60
    throughput_per_min  = compute_throughput(result)
    throughput_per_hour = throughput_per_min * 60
    avg_total = df["Total Waktu (s)"].mean()
    avg_util  = np.mean(list(utils.values()))

    # Bottleneck severity
    bn_util = utils[bottleneck_key]
    bn_wait = avg_wait[bottleneck_key]
    sev_label, _ = bottleneck_severity(bn_util, bn_wait)

    # Waktu nyata (mulai pukul 07:00)
    start_time = datetime(2024, 1, 1, 7, 0)
    end_time   = start_time + timedelta(seconds=T_s)

    # Kondisi sistem
    if avg_util > 85:
        kondisi      = "🔴 OVERLOAD"
        kondisi_desc = ("Sistem sangat sibuk — utilisasi rata-rata <b>{:.1f}%</b>. "
                        "Risiko keterlambatan tinggi. Segera tambah petugas pada tahap bottleneck.").format(avg_util)
    elif avg_util > 60:
        kondisi      = "🟡 OPTIMAL"
        kondisi_desc = ("Sistem berjalan efisien dengan utilisasi rata-rata <b>{:.1f}%</b>. "
                        "Kapasitas dan beban seimbang.").format(avg_util)
    else:
        kondisi      = "🟢 UNDERUTILIZED"
        kondisi_desc = ("Utilisasi rata-rata hanya <b>{:.1f}%</b>. "
                        "Ada kapasitas berlebih — pertimbangkan pengurangan petugas atau penambahan meja.").format(avg_util)

    # Efek penambahan petugas
    base_t  = sens_data[0]["Total Waktu (s)"]
    plus1_t = sens_data[1]["Total Waktu (s)"] if len(sens_data) > 1 else base_t
    delta_s   = base_t - plus1_t
    delta_pct = (delta_s / base_t * 100) if base_t > 0 else 0

    insights = [
        {
            "icon": "⏱️",
            "title": "Total Waktu Penyelesaian",
            "text": (
                f"Seluruh <b>{cfg.num_meja} meja</b> ({cfg.total_ompreng} ompreng) selesai dalam "
                f"<b>{fmt(T_s)}</b> ({format_time_hms(T_s)}). "
                f"Dimulai pukul 07:00 → selesai pukul <b>{end_time.strftime('%H:%M:%S')}</b>. "
                f"Rata-rata per meja: <b>{fmt(avg_total)}</b>."
            ),
            "type": "info",
        },
        {
            "icon": "🚨",
            "title": f"Bottleneck: {bottleneck_label} — Severity {sev_label}",
            "text": (
                f"Tahap <b>{bottleneck_label}</b> adalah titik kemacetan utama. "
                f"Rata-rata waktu tunggu: <b>{fmt(bn_wait)}</b> per meja. "
                f"Utilisasi tahap ini: <b>{bn_util:.1f}%</b>. "
                f"Petugas saat ini: <b>{getattr(cfg, 'petugas_'+bottleneck_key)}</b> orang."
            ),
            "type": "bottleneck",
        },
        {
            "icon": "👥",
            "title": "Efek Penambahan Petugas di Bottleneck",
            "text": (
                f"Tambah 1 petugas di <b>{bottleneck_label}</b>: "
                f"waktu total turun dari <b>{fmt(base_t)}</b> → <b>{fmt(plus1_t)}</b> "
                f"(hemat <b>{fmt(delta_s)}</b> / <b>{delta_pct:.1f}%</b> lebih cepat)."
            ),
            "type": "info",
        },
        {
            "icon": "📊",
            "title": f"Kondisi Sistem: {kondisi}",
            "text": kondisi_desc,
            "type": "warning" if avg_util > 85 else "info",
        },
        {
            "icon": "⚡",
            "title": "Throughput & Utilisasi Detail",
            "text": (
                f"Throughput: <b>{throughput_per_min:.2f} meja/menit</b> "
                f"(<b>{throughput_per_hour:.1f} meja/jam</b>). "
                f"Utilisasi — Lauk: <b>{utils['lauk']:.1f}%</b> · "
                f"Angkut: <b>{utils['angkut']:.1f}%</b> · "
                f"Nasi: <b>{utils['nasi']:.1f}%</b>. "
                f"Rata-rata tunggu — Lauk: <b>{fmt(avg_wait['lauk'])}</b> · "
                f"Angkut: <b>{fmt(avg_wait['angkut'])}</b> · "
                f"Nasi: <b>{fmt(avg_wait['nasi'])}</b>."
            ),
            "type": "info",
        },
        {
            "icon": "💡",
            "title": "Rekomendasi Sistem",
            "text": (
                f"① Prioritaskan penguatan tahap <b>{bottleneck_label}</b> "
                f"(saat ini {getattr(cfg, 'petugas_'+bottleneck_key)} petugas — tambah minimal 1). "
                f"② Total {cfg.total_petugas} petugas untuk {cfg.num_meja} meja "
                f"({'efisien' if 50 < avg_util <= 85 else 'perlu penyesuaian'}). "
                f"③ Jika ingin selesai lebih awal, targetkan utilisasi di bawah 80% pada semua tahap. "
                f"④ Pertimbangkan parallelisasi batch angkut untuk mempercepat tahap Angkut."
            ),
            "type": "info",
        },
    ]
    return insights


# ============================================================
# UI HELPERS
# ============================================================
def kpi_card(label: str, value: str, sub: str = "", accent: str = "accent-blue") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {accent}">{value}</div>
        <div class="kpi-delta">{sub}</div>
    </div>
    """


def insight_html(ins: Dict) -> str:
    box_class = "bottleneck-box" if ins["type"] == "bottleneck" else "insight-box"
    title_class = "bottleneck-title" if ins["type"] == "bottleneck" else "insight-title"
    return f"""
    <div class="{box_class}">
        <div class="{title_class}">{ins['icon']} {ins['title']}</div>
        <div class="insight-text">{ins['text']}</div>
    </div>
    """


def df_to_csv_download(df: pd.DataFrame, filename: str) -> str:
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="color:#58a6ff;text-decoration:none;">⬇️ Download {filename}</a>'


def seconds_to_hms(s: float) -> str:
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}" if h > 0 else f"{m:02d}:{sec:02d}"


# ============================================================
# SIDEBAR
# ============================================================
def build_sidebar() -> Tuple[SimConfig, bool, bool]:
    with st.sidebar:
        st.markdown("## 🍱 Piket IT Del")
        st.markdown("---")

        st.markdown("### 🏗️ Struktur")
        num_meja   = st.slider("Jumlah Meja",   20, 120, 60, 5, key="num_meja")
        mhs_per_meja = st.slider("Mahasiswa per Meja", 1, 6, 3, key="mhs_per_meja")

        st.markdown("### 👷 Petugas per Tahap")
        total_petugas = 0  # Placeholder, akan diupdate setelah input
        col1, col2, col3 = st.columns(3)
        with col1:
            p_lauk   = st.number_input("Lauk",   1, 10, 2, key="p_lauk")
        with col2:
            p_angkut = st.number_input("Angkut", 1, 10, 2, key="p_angkut")
        with col3:
            p_nasi   = st.number_input("Nasi",   1, 10, 3, key="p_nasi")
        total_petugas = int(p_lauk) + int(p_angkut) + int(p_nasi)
        st.caption(f"Total: **{total_petugas} petugas**")

        st.markdown("### ⏱️ Distribusi Waktu (detik)")
        with st.expander("Proses Lauk", expanded=False):
            lauk_min = st.slider("Min", 5, 120, 30, key="lmin")
            lauk_max = st.slider("Max", 5, 120, 60, key="lmax")
        with st.expander("Proses Angkut", expanded=False):
            angkut_min = st.slider("Min", 5, 120, 20, key="amin")
            angkut_max = st.slider("Max", 5, 120, 60, key="amax")
            a_min_ompg = st.slider("Min ompreng/angkut", 1, 10, 4, key="a_min_ompg")
            a_max_ompg = st.slider("Max ompreng/angkut", 1, 10, 7, key="a_max_ompg")
        with st.expander("Proses Nasi", expanded=False):
            nasi_min = st.slider("Min", 5, 120, 30, key="nmin")
            nasi_max = st.slider("Max", 5, 120, 60, key="nmax")

        seed = st.number_input("🎲 Random Seed", 0, 9999, 42, key="seed")

        st.markdown("---")
        run_btn     = st.button("▶ Run Simulation", use_container_width=True)
        compare_btn = st.button("⚖️ Compare Scenario", use_container_width=True, help="Bandingkan konfigurasi saat ini vs default (7 petugas merata)")

    cfg = SimConfig(
        num_meja=num_meja,
        mahasiswa_per_meja=mhs_per_meja,
        petugas_lauk=int(p_lauk),
        petugas_angkut=int(p_angkut),
        petugas_nasi=int(p_nasi),
        lauk_min=lauk_min, lauk_max=lauk_max,
        angkut_min=angkut_min, angkut_max=angkut_max,
        nasi_min=nasi_min, nasi_max=nasi_max,
        angkut_min_ompreng=a_min_ompg,
        angkut_max_ompreng=a_max_ompg,
        random_seed=int(seed),
    )
    return cfg, run_btn, compare_btn


# ============================================================
# EMPTY STATE RENDERERS  (tampil sebelum simulasi dijalankan)
# ============================================================
def render_kpi_empty(cfg: SimConfig):
    """KPI cards kosong dengan nilai placeholder."""
    col1, col2, col3, col4, col5 = st.columns(5)
    kpis = [
        (col1, "SELESAI PUKUL",      "—:—:—",  "Belum dijalankan",   "accent-blue"),
        (col2, "TOTAL OMPRENG",      str(cfg.total_ompreng),
                                     f"{cfg.num_meja} meja × {cfg.mahasiswa_per_meja}", "accent-purple"),
        (col3, "BOTTLENECK TAHAP",   "—",       "Belum diketahui",    "accent-red"),
        (col4, "UTILISASI RATA-RATA","—%",      "L:—% · A:—% · N:—%","accent-orange"),
        (col5, "THROUGHPUT",         "—/mnt",   "— meja/jam",         "accent-green"),
    ]
    for col, label, value, sub, accent in kpis:
        with col:
            st.markdown(kpi_card(label, value, sub, accent), unsafe_allow_html=True)

    st.markdown(
        '<div class="summary-banner">'
        '⏳ <b>Menunggu Simulasi:</b> &nbsp;'
        'Atur parameter di sidebar kiri, lalu tekan <b>▶ Run Simulation</b> untuk memulai.'
        '</div>',
        unsafe_allow_html=True,
    )


def _empty_fig(title: str, height: int = 350) -> go.Figure:
    """Buat figure kosong dengan pesan placeholder."""
    fig = go.Figure()
    fig.update_layout(
        title=title,
        height=height,
        annotations=[dict(
            text="⏳ Tekan <b>▶ Run Simulation</b> untuk menampilkan grafik",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14, color="#8b949e"),
        )],
        **PLOT_THEME,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def render_charts_empty():
    """Tampilkan semua chart section dalam kondisi kosong."""
    st.markdown('<div class="section-header">📊 Visualisasi Simulasi</div>', unsafe_allow_html=True)

    # Gauge placeholder (3 gauge kosong)
    fig_gauge = make_subplots(rows=1, cols=3, specs=[[{"type": "indicator"}]*3])
    for col, label in enumerate(["Lauk", "Angkut", "Nasi"], 1):
        fig_gauge.add_trace(go.Indicator(
            mode="gauge+number",
            value=0,
            title={"text": f"Utilisasi {label}", "font": {"size": 13, "color": "#8b949e"}},
            number={"suffix": "%", "font": {"size": 22, "color": "#30363d"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#30363d"},
                "bar": {"color": "#21262d"},
                "bgcolor": "#161b22",
                "bordercolor": "#21262d",
            },
        ), row=1, col=col)
    fig_gauge.update_layout(
        height=260, paper_bgcolor="#0e1117", font_color="#30363d",
        margin=dict(l=20, r=20, t=30, b=10),
    )
    st.plotly_chart(fig_gauge, use_container_width=True, key="util_gauge_empty")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 Gantt", "📈 Progress", "🚨 Bottleneck",
        "📊 Distribusi", "📉 Cumulative", "🔬 Sensitivity", "📋 Data Tabel",
    ])
    with tab1:
        st.plotly_chart(_empty_fig("Gantt Chart – Proses per Meja", 600),
                        use_container_width=True, key="gantt_empty")
    with tab2:
        st.plotly_chart(_empty_fig("Progress Penyelesaian Meja terhadap Waktu"),
                        use_container_width=True, key="progress_empty")
    with tab3:
        st.plotly_chart(_empty_fig("Bottleneck Detection – Rata-rata Waktu Tunggu per Tahap"),
                        use_container_width=True, key="bottleneck_chart_empty")
        bcols = st.columns(3)
        for i, stage in enumerate(["Lauk", "Angkut", "Nasi"]):
            with bcols[i]:
                st.markdown(
                    f'<div class="stage-card"><div class="sc-label">{stage}</div>'
                    f'<div class="sc-value" style="color:#30363d">—</div>'
                    f'<div class="sc-sub">avg tunggu · utilisasi —%</div></div>',
                    unsafe_allow_html=True,
                )
    with tab4:
        st.plotly_chart(_empty_fig("Distribusi Durasi Proses per Tahap"),
                        use_container_width=True, key="dist_empty")
    with tab5:
        st.plotly_chart(_empty_fig("Cumulative Completion Curve"),
                        use_container_width=True, key="cumulative_empty")
    with tab6:
        st.plotly_chart(_empty_fig("Sensitivity Analysis – Efek Penambahan Petugas"),
                        use_container_width=True, key="sensitivity_empty")
    with tab7:
        st.dataframe(pd.DataFrame({
            "Meja": ["—"]*3,
            "Durasi Lauk": ["—"]*3,
            "Durasi Angkut": ["—"]*3,
            "Durasi Nasi": ["—"]*3,
            "Total Waktu": ["—"]*3,
            "Tunggu Lauk": ["—"]*3,
            "Tunggu Angkut": ["—"]*3,
            "Tunggu Nasi": ["—"]*3,
        }), use_container_width=True, hide_index=True)
        st.caption("⏳ Data akan muncul setelah simulasi dijalankan.")


def render_insights_empty():
    """Tampilkan insight section dalam kondisi kosong."""
    st.markdown('<div class="section-header">🧠 Analisis & Insight Otomatis</div>', unsafe_allow_html=True)
    placeholders = [
        ("⏱️", "Total Waktu Penyelesaian",          "Hasil akan muncul setelah simulasi dijalankan."),
        ("🚨", "Bottleneck Detection",               "Tahap bottleneck akan teridentifikasi otomatis."),
        ("👥", "Efek Penambahan Petugas",            "Analisis sensitivity akan dihitung."),
        ("📊", "Kondisi Sistem",                     "Status overload / optimal / underutilized akan ditampilkan."),
        ("⚡", "Throughput & Utilisasi Detail",      "Metrik throughput dan utilisasi per tahap akan dihitung."),
        ("💡", "Rekomendasi Sistem",                 "Rekomendasi berbasis data akan dibuat secara otomatis."),
    ]
    cols = st.columns(2)
    for i, (icon, title, text) in enumerate(placeholders):
        with cols[i % 2]:
            st.markdown(
                f'<div class="insight-box" style="opacity:0.4;">'
                f'<div class="insight-title">{icon} {title}</div>'
                f'<div class="insight-text">{text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ============================================================
# MAIN DASHBOARD
# ============================================================
def render_header():
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem 0;">
        <h1 style="font-size:2rem; font-weight:800; color:#e6edf3; margin:0;">
            🍱 Simulasi Sistem Piket IT Del
        </h1>
        <p style="color:#8b949e; font-size:0.9rem; margin-top:0.3rem;">
            Discrete Event Simulation (SimPy) · Dashboard Analitik Profesional
        </p>
    </div>
    <hr style="border:none; border-top:1px solid #21262d; margin:0.5rem 0 1.5rem 0;">
    """, unsafe_allow_html=True)


def render_kpi(result: SimResult):
    utils     = compute_utilization(result)
    avg_util  = np.mean(list(utils.values()))
    bottleneck_label, bottleneck_key, avg_wait = detect_bottleneck(result)
    bn_util   = utils[bottleneck_key]
    bn_wait   = avg_wait[bottleneck_key]
    sev_label, sev_class = bottleneck_severity(bn_util, bn_wait)

    T_s   = result.total_sim_time
    throughput_per_min  = compute_throughput(result)
    throughput_per_hour = throughput_per_min * 60

    start_time = datetime(2024, 1, 1, 7, 0)
    end_time   = start_time + timedelta(seconds=T_s)

    col1, col2, col3, col4, col5 = st.columns(5)
    kpis = [
        (col1, "SELESAI PUKUL",
         end_time.strftime("%H:%M:%S"),
         fmt(T_s),
         "accent-blue"),
        (col2, "TOTAL OMPRENG",
         str(result.config.total_ompreng),
         f"{result.config.num_meja} meja × {result.config.mahasiswa_per_meja}",
         "accent-purple"),
        (col3, "BOTTLENECK TAHAP",
         bottleneck_label,
         f"Tunggu avg {fmt(bn_wait)}",
         "accent-red"),
        (col4, "UTILISASI RATA-RATA",
         f"{avg_util:.1f}%",
         f"L:{utils['lauk']:.0f}% · A:{utils['angkut']:.0f}% · N:{utils['nasi']:.0f}%",
         "accent-orange"),
        (col5, "THROUGHPUT",
         f"{throughput_per_min:.2f}/mnt",
         f"{throughput_per_hour:.1f} meja/jam",
         "accent-green"),
    ]
    for col, label, value, sub, accent in kpis:
        with col:
            st.markdown(kpi_card(label, value, sub, accent), unsafe_allow_html=True)

    # Natural language system summary
    cond_emoji = "🔴" if avg_util > 85 else ("🟡" if avg_util > 60 else "🟢")
    st.markdown(
        f'<div class="summary-banner">'
        f'{cond_emoji} <b>Ringkasan Sistem:</b> &nbsp;'
        f'{result.config.num_meja} meja · {result.config.total_ompreng} ompreng · '
        f'{result.config.total_petugas} petugas (Lauk:{result.config.petugas_lauk} · '
        f'Angkut:{result.config.petugas_angkut} · Nasi:{result.config.petugas_nasi}) &nbsp;|&nbsp; '
        f'Selesai dalam <b>{fmt(T_s)}</b> &nbsp;|&nbsp; '
        f'Bottleneck: <b>{bottleneck_label}</b> '
        f'<span class="{sev_class}">{sev_label}</span> &nbsp;|&nbsp; '
        f'Utilisasi rata-rata <b>{avg_util:.1f}%</b> &nbsp;|&nbsp; '
        f'Throughput <b>{throughput_per_hour:.1f} meja/jam</b>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_charts(result: SimResult, sens_data: List[Dict]):
    st.markdown('<div class="section-header">📊 Visualisasi Simulasi</div>', unsafe_allow_html=True)

    # Gauge utilisasi (selalu tampil)
    st.plotly_chart(chart_utilization(result), use_container_width=True, key="util_gauge")

    # Tabs untuk chart utama
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 Gantt",
        "📈 Progress",
        "🚨 Bottleneck",
        "📊 Distribusi",
        "📉 Cumulative",
        "🔬 Sensitivity",
        "📋 Data Tabel",
    ])

    with tab1:
        st.plotly_chart(chart_gantt(result), use_container_width=True, key="gantt")
        st.caption("Menampilkan 30 meja pertama. Warna biru = Lauk, oranye = Angkut, hijau = Nasi.")

    with tab2:
        st.plotly_chart(chart_completion_progress(result), use_container_width=True, key="progress")

    with tab3:
        st.plotly_chart(chart_bottleneck(result), use_container_width=True, key="bottleneck_chart")
        df = result.df_tables
        utils = compute_utilization(result)
        _, bottleneck_key, avg_wait = detect_bottleneck(result)
        bcols = st.columns(3)
        stage_meta = [
            ("Lauk",   "Tunggu Lauk (s)",   "lauk"),
            ("Angkut", "Tunggu Angkut (s)", "angkut"),
            ("Nasi",   "Tunggu Nasi (s)",   "nasi"),
        ]
        for i, (stage, wait_col, key) in enumerate(stage_meta):
            is_bn = (key == bottleneck_key)
            sev_lbl, sev_cls = bottleneck_severity(utils[key], avg_wait[key])
            with bcols[i]:
                card_class = "stage-card bottleneck-stage" if is_bn else "stage-card"
                st.markdown(
                    f'<div class="{card_class}">'
                    f'<div class="sc-label">{stage} {"🔴 BOTTLENECK" if is_bn else ""}</div>'
                    f'<div class="sc-value accent-{"red" if is_bn else "blue"}">'
                    f'{fmt(df[wait_col].mean())}</div>'
                    f'<div class="sc-sub">avg tunggu · max {fmt(df[wait_col].max())}</div>'
                    f'<div class="sc-sub">utilisasi <b>{utils[key]:.1f}%</b> · '
                    f'<span class="{sev_cls}">{sev_lbl}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    with tab4:
        st.plotly_chart(chart_duration_distribution(result), use_container_width=True, key="dist")

    with tab5:
        st.plotly_chart(chart_cumulative_completion(result), use_container_width=True, key="cumulative")

    with tab6:
        st.plotly_chart(chart_sensitivity(sens_data), use_container_width=True, key="sensitivity")
        df_sens = pd.DataFrame(sens_data)
        # Show readable table
        df_sens_display = df_sens[["Extra Petugas", "Total Petugas Tahap", "Total Waktu (Human)", "Total Waktu (menit)"]].copy()
        df_sens_display.columns = ["Extra Petugas", "Petugas di Tahap", "Total Waktu", "Total Waktu (menit)"]
        st.dataframe(
            df_sens_display.style.background_gradient(subset=["Total Waktu (menit)"], cmap="RdYlGn_r"),
            use_container_width=True, hide_index=True,
        )

    with tab7:
        df_raw = result.df_tables.copy()
        # Add human-readable columns for key time columns
        df_display = df_raw[["Meja", "Durasi Lauk (s)", "Durasi Angkut (s)", "Durasi Nasi (s)",
                              "Total Waktu (s)", "Tunggu Lauk (s)", "Tunggu Angkut (s)", "Tunggu Nasi (s)"]].copy()
        df_display.insert(2, "Durasi Lauk", df_display["Durasi Lauk (s)"].apply(fmt))
        df_display.insert(4, "Durasi Angkut", df_display["Durasi Angkut (s)"].apply(fmt))
        df_display.insert(6, "Durasi Nasi", df_display["Durasi Nasi (s)"].apply(fmt))
        df_display.insert(8, "Total Waktu", df_display["Total Waktu (s)"].apply(fmt))
        df_display.insert(10, "Tunggu Lauk", df_display["Tunggu Lauk (s)"].apply(fmt))
        df_display.insert(12, "Tunggu Angkut", df_display["Tunggu Angkut (s)"].apply(fmt))
        df_display.insert(14, "Tunggu Nasi", df_display["Tunggu Nasi (s)"].apply(fmt))
        # Drop raw seconds columns for clean view
        cols_drop = ["Durasi Lauk (s)", "Durasi Angkut (s)", "Durasi Nasi (s)",
                     "Total Waktu (s)", "Tunggu Lauk (s)", "Tunggu Angkut (s)", "Tunggu Nasi (s)"]
        df_clean = df_display.drop(columns=cols_drop)
        st.dataframe(df_clean, use_container_width=True, hide_index=True)
        st.caption("💡 Klik header kolom untuk sort · Tabel menampilkan format waktu human-readable")
        st.markdown(df_to_csv_download(df_raw, "hasil_simulasi_piket.csv"), unsafe_allow_html=True)


def render_insights(result: SimResult, sens_data: List[Dict]):
    st.markdown('<div class="section-header">🧠 Analisis & Insight Otomatis</div>', unsafe_allow_html=True)
    insights = generate_insights(result, sens_data)
    cols = st.columns(2)
    for i, ins in enumerate(insights):
        with cols[i % 2]:
            st.markdown(insight_html(ins), unsafe_allow_html=True)


def render_compare(result1: SimResult, result2: SimResult):
    """Tampilkan perbandingan dua skenario."""
    st.markdown('<div class="section-header">⚖️ Perbandingan Skenario</div>', unsafe_allow_html=True)

    utils1 = compute_utilization(result1)
    utils2 = compute_utilization(result2)
    tp1 = compute_throughput(result1)
    tp2 = compute_throughput(result2)

    compare_data = {
        "Metrik": [
            "Total Waktu Selesai", "Total Waktu (detik)",
            "Utilisasi Lauk (%)", "Utilisasi Angkut (%)", "Utilisasi Nasi (%)",
            "Throughput (meja/jam)", "Total Petugas",
        ],
        "Skenario Kustom": [
            fmt(result1.total_sim_time), f"{result1.total_sim_time:.0f}",
            f"{utils1['lauk']:.1f}", f"{utils1['angkut']:.1f}", f"{utils1['nasi']:.1f}",
            f"{tp1*60:.1f}",
            str(result1.config.total_petugas),
        ],
        "Skenario Default (2-2-3)": [
            fmt(result2.total_sim_time), f"{result2.total_sim_time:.0f}",
            f"{utils2['lauk']:.1f}", f"{utils2['angkut']:.1f}", f"{utils2['nasi']:.1f}",
            f"{tp2*60:.1f}",
            str(result2.config.total_petugas),
        ],
    }
    st.dataframe(pd.DataFrame(compare_data), use_container_width=True, hide_index=True)

    # Bar comparison
    fig = go.Figure()
    for name, res, color in [("Kustom", result1, "#58a6ff"), ("Default", result2, "#f0883e")]:
        utils = compute_utilization(res)
        fig.add_trace(go.Bar(
            name=name,
            x=["Lauk", "Angkut", "Nasi"],
            y=[utils["lauk"], utils["angkut"], utils["nasi"]],
            marker_color=color,
        ))
    fig.update_layout(
        title="Perbandingan Utilisasi per Tahap",
        barmode='group',
        yaxis_title="Utilisasi (%)",
        height=300,
        **PLOT_THEME,
    )
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE)
    st.plotly_chart(fig, use_container_width=True, key="compare_chart")


# ============================================================
# MAIN
# ============================================================
def main():
    render_header()

    cfg, run_btn, compare_btn = build_sidebar()

    if run_btn:
        with st.spinner("⏳ Menjalankan simulasi DES..."):
            sim = PiketSimulation(cfg)
            result = sim.run()
            _, bottleneck_key, _ = detect_bottleneck(result)
            sens_data = sensitivity_analysis(cfg, bottleneck_key)

        st.session_state["result"]    = result
        st.session_state["sens_data"] = sens_data
        st.session_state["cfg"]       = cfg
        st.success(
            f"✅ Simulasi selesai — {cfg.num_meja} meja · "
            f"{cfg.total_ompreng} ompreng · {cfg.total_petugas} petugas · "
            f"Durasi: {fmt(result.total_sim_time)}"
        )

    # Selalu render semua komponen UI — kosong jika belum run, terisi jika sudah
    if "result" in st.session_state:
        result    = st.session_state["result"]
        sens_data = st.session_state["sens_data"]

        render_kpi(result)
        st.markdown("<br>", unsafe_allow_html=True)
        render_charts(result, sens_data)
        render_insights(result, sens_data)

        if compare_btn:
            with st.spinner("⏳ Menjalankan skenario pembanding..."):
                cfg_default = SimConfig(
                    num_meja=cfg.num_meja,
                    mahasiswa_per_meja=cfg.mahasiswa_per_meja,
                    petugas_lauk=2, petugas_angkut=2, petugas_nasi=3,
                    random_seed=cfg.random_seed,
                )
                sim2 = PiketSimulation(cfg_default)
                result2 = sim2.run()
            render_compare(result, result2)

    else:
        # Belum ada hasil — tampilkan semua komponen dalam kondisi kosong
        render_kpi_empty(cfg)
        st.markdown("<br>", unsafe_allow_html=True)
        render_charts_empty()
        render_insights_empty()


if __name__ == "__main__":
    main()
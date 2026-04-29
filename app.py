import streamlit as st
import pandas as pd
import os, time
from datetime import datetime

st.set_page_config(
    page_title="Strickland AG 2026 — Election Night Command",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

from engine_core import load_benchmark, run_engine, ALERT_COLORS, ALERT_PRIORITY
from ingestor import get_results, get_empty_template


# Password — reads from Streamlit secrets first, then env var, then placeholder
# Local:  set in .streamlit/secrets.toml
# Cloud:  set in Streamlit Community Cloud → App settings → Secrets
def _get_password():
    try:
        return st.secrets['APP_PASSWORD']
    except Exception:
        return os.environ.get('APP_PASSWORD', 'ChangeMeBeforeLaunch')

APP_PASSWORD = _get_password()


# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Dark base */
  .stApp { background:#0D1117; color:#F0F6FF; }
  section[data-testid="stSidebar"] { background:#0B1F3A; border-right:1px solid #C9A84C33; }
  section[data-testid="stSidebar"] * { color:#F0F6FF !important; }

  /* Header */
  .cmd-header {
    background: linear-gradient(135deg,#0B1F3A 0%,#132847 100%);
    border-bottom: 2px solid #C9A84C;
    padding: 18px 28px; border-radius: 8px; margin-bottom: 20px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .cmd-title { font-size:1.5rem; font-weight:700; color:#C9A84C; letter-spacing:2px; margin:0; }
  .cmd-sub   { font-size:0.85rem; color:#94A3B8; margin:0; }
  .cmd-ts    { font-size:0.8rem; color:#C9A84C; text-align:right; }

  /* Metric cards */
  .metric-card {
    background:#161B22; border:1px solid #30363D;
    border-radius:10px; padding:18px 20px; text-align:center; height:100%;
  }
  .metric-label { font-size:0.72rem; color:#94A3B8; letter-spacing:1.5px;
                  text-transform:uppercase; margin-bottom:6px; }
  .metric-value { font-size:2.4rem; font-weight:800; line-height:1; margin:0; }
  .metric-sub   { font-size:0.78rem; color:#94A3B8; margin-top:4px; }
  .positive { color:#10B981; }
  .negative { color:#DC2626; }
  .neutral  { color:#C9A84C; }
  .white    { color:#F0F6FF; }

  /* County cards */
  .county-grid { display:flex; flex-wrap:wrap; gap:12px; margin:16px 0; }
  .county-card {
    background:#161B22; border-radius:10px; padding:14px 16px;
    min-width:180px; flex:1; border-left:4px solid;
  }
  .county-card-name  { font-size:0.82rem; color:#94A3B8; font-weight:600;
                       text-transform:uppercase; letter-spacing:0.8px; margin-bottom:4px; }
  .county-card-alert { font-size:0.72rem; font-weight:700; letter-spacing:1px; margin-bottom:8px; }
  .county-card-main  { font-size:1.5rem; font-weight:800; line-height:1; }
  .county-card-model { font-size:0.78rem; color:#94A3B8; }
  .county-card-dev   { font-size:0.85rem; font-weight:600; }
  .county-card-cush  { font-size:0.78rem; color:#94A3B8; }

  /* Alert table rows */
  .alert-row {
    background:#161B22; border-radius:6px; padding:8px 14px;
    margin-bottom:6px; display:flex; align-items:center; gap:12px;
  }
  .alert-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
  .alert-text { font-size:0.85rem; color:#F0F6FF; }
  .alert-county { font-weight:600; }
  .alert-detail { color:#94A3B8; font-size:0.78rem; }

  /* Source badge */
  .source-badge {
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:0.72rem; font-weight:700; letter-spacing:0.8px;
  }
  .source-live    { background:#10B98133; color:#10B981; border:1px solid #10B981; }
  .source-manual  { background:#F59E0B33; color:#F59E0B; border:1px solid #F59E0B; }
  .source-sample  { background:#6B728033; color:#94A3B8; border:1px solid #6B7280; }
  .source-nodata  { background:#DC262633; color:#DC2626; border:1px solid #DC2626; }

  /* Section headings */
  .section-head {
    font-size:0.72rem; color:#C9A84C; letter-spacing:2px;
    text-transform:uppercase; font-weight:700;
    border-bottom:1px solid #C9A84C44; padding-bottom:6px; margin:20px 0 12px;
  }

  /* Login */
  .login-wrap { display:flex; justify-content:center; align-items:center;
                min-height:70vh; flex-direction:column; }
  .login-icon { font-size:3rem; text-align:center; }
  .login-title { color:#C9A84C; letter-spacing:3px; font-size:1.6rem;
                 font-weight:800; text-align:center; margin:10px 0 4px; }
  .login-sub { color:#94A3B8; text-align:center; margin-bottom:30px; font-size:0.9rem; }

  /* Streamlit overrides */
  div[data-testid="stMetric"] { background:#161B22; border-radius:10px; padding:12px; }
  .stButton>button { background:#C9A84C; color:#0B1F3A; font-weight:700;
                     border:none; border-radius:6px; }
  .stButton>button:hover { background:#F0C040; color:#0B1F3A; }
  .stDownloadButton>button { background:#0B1F3A; color:#C9A84C;
                              border:1px solid #C9A84C; border-radius:6px; }
  div[data-testid="stDataFrame"] { background:#161B22; border-radius:10px; }
  /* ── Mobile responsive ───────────────────────────────────────── */
  @media (max-width: 768px) {
    .cmd-header { flex-direction:column; gap:8px; padding:14px 16px; }
    .cmd-title  { font-size:1.1rem; letter-spacing:1px; }
    .cmd-ts     { text-align:left; }
    .metric-value { font-size:1.8rem; }
    .county-grid  { flex-direction:column; gap:8px; }
    .county-card  { min-width:unset; flex:unset; }
    .county-card-main { font-size:1.2rem; }
  }
</style>
""", unsafe_allow_html=True)


# ── Password Gate ─────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get('authenticated'):
        return True
    st.markdown("""
    <div class="login-wrap">
      <div class="login-icon">⚡</div>
      <div class="login-title">ELECTION NIGHT COMMAND</div>
      <div class="login-sub">Strickland AG 2026 — Restricted Access</div>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.5, 1, 1.5])
    with c2:
        pwd = st.text_input("Password", type="password", label_visibility="collapsed",
                            placeholder="Enter password")
        if st.button("Enter Command Center", use_container_width=True):
            if pwd == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False


# ── Helpers ────────────────────────────────────────────────────────────────────
def color_for(alert):
    return ALERT_COLORS.get(alert, '#6B7280')

def sign(n):
    return f"+{n:,}" if n >= 0 else f"{n:,}"

def county_card_html(row):
    alert  = row['ALERT']
    c      = color_for(alert)
    has    = pd.notna(row['Actual %'])
    act    = f"{row['Actual %']:.2f}%" if has else "—"
    dev_ok = pd.notna(row['Dev pts'])
    csh_ok = pd.notna(row['Cushion'])
    dev    = f"{sign(int(round(float(row['Dev pts'])*10)/10))} pts" if dev_ok else "—"
    cush   = sign(int(row['Cushion'])) if csh_ok else "—"
    dev_c  = '#10B981' if (float(row['Dev pts']) if dev_ok else 0) >= 0 else '#DC2626'
    cush_c = '#10B981' if (int(row['Cushion']) if csh_ok else 0) >= 0 else '#DC2626'
    name   = row['County'].replace(' County','')
    prec   = row['Precincts']
    return f"""
<div class="county-card" style="border-left-color:{c}">
  <div class="county-card-name">{name}</div>
  <div class="county-card-alert" style="color:{c}">{alert}</div>
  <div class="county-card-main" style="color:{'#F0F6FF' if has else '#4B5563'}">{act}</div>
  <div class="county-card-model">Model: {row['Model %']:.2f}%</div>
  <div class="county-card-dev" style="color:{dev_c}">Dev: {dev}</div>
  <div class="county-card-cush" style="color:{cush_c}">Cushion: {cush} | Prec: {prec}</div>
</div>"""


def alert_row_html(row):
    c      = color_for(row['ALERT'])
    dev    = f"{sign(row['Dev pts'])} pts" if pd.notna(row['Dev pts']) else ""
    cush   = sign(int(row['Cushion'])) if pd.notna(row['Cushion']) else ""
    return f"""
<div class="alert-row">
  <div class="alert-dot" style="background:{c}"></div>
  <div class="alert-text">
    <span class="alert-county">{row['County']}</span>
    &nbsp;·&nbsp;
    <span style="color:{c};font-weight:700">{row['ALERT']}</span>
    &nbsp;·&nbsp;
    <span class="alert-detail">
      Actual {row['Actual %']:.1f}% vs Model {row['Model %']:.1f}%
      &nbsp;|&nbsp; Dev {dev} &nbsp;|&nbsp; Cushion {cush}
    </span>
  </div>
</div>"""

def source_badge(source):
    cls = {'SOS Live Feed':'source-live','Manual Upload':'source-manual',
           'Sample Data (Demo)':'source-sample'}.get(source,'source-nodata')
    return f'<span class="source-badge {cls}">{source}</span>'

def style_table(df):
    def row_color(row):
        c = color_for(row['ALERT'])
        return [f'color:{c}; font-weight:700'] + [''] * (len(row)-1)
    return df.style.apply(row_color, axis=1)


# ── Main App ──────────────────────────────────────────────────────────────────
def main():
    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### ⚡ COMMAND CENTER")
        st.markdown("---")

        # Auto-refresh
        auto_on = st.toggle("🔄 Auto-Refresh", value=True)
        if auto_on:
            interval_min = st.slider("Interval (minutes)", min_value=2, max_value=10,
                                     value=5, step=1, key="interval_slider")
            if HAS_AUTOREFRESH:
                st_autorefresh(interval=interval_min * 60_000, key="autorefresh")
            else:
                st.caption("Install streamlit-autorefresh for live polling.")
        if st.button("⚡ Refresh Now", use_container_width=True):
            st.rerun()

        st.markdown("---")
        st.markdown("**📁 Manual Upload**")
        st.caption("Upload a results CSV to override all other sources.")
        uploaded = st.file_uploader("", type=['csv'], label_visibility="collapsed",
                                    key="upload")

        st.markdown("---")
        st.markdown("**⬇️ Downloads**")
        col_a, col_b = st.columns(2)

        st.markdown("---")
        if st.button("🔒 Logout"):
            st.session_state.authenticated = False
            st.rerun()

    # ── Load data ──
    bench_df = load_benchmark()
    results_df, source = get_results(uploaded_file=uploaded if uploaded else None)
    cmd_df, summary = run_engine(bench_df, results_df)

    # ── Download buttons (need data first) ──
    with st.sidebar:
        csv_bytes = cmd_df.drop(columns=['is_key'], errors='ignore')\
                          .to_csv(index=False).encode('utf-8')
        st.download_button("📊 Command View CSV", data=csv_bytes,
                           file_name=f"command_{datetime.now().strftime('%H%M')}.csv",
                           mime='text/csv', use_container_width=True)
        tmpl = get_empty_template()
        st.download_button("📋 Results Template", data=tmpl.to_csv(index=False).encode(),
                           file_name="results_template.csv", mime='text/csv',
                           use_container_width=True)

    # ── Header ──
    rptd = summary['n_reported']; total = summary['n_total']
    st.markdown(f"""
    <div class="cmd-header">
      <div>
        <div class="cmd-title">⚡ STRICKLAND AG 2026 &nbsp;|&nbsp; ELECTION NIGHT COMMAND</div>
        <div class="cmd-sub">May 19, 2026 Republican Primary — Attorney General</div>
      </div>
      <div class="cmd-ts">
        {source_badge(source)}<br>
        Updated: {summary['timestamp']}<br>
        {rptd}/{total} counties reporting
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Top metrics ──
    str_v      = summary['str_actual']
    cow_v      = summary['cow_actual']
    str_pct    = summary['str_pct']
    cow_pct    = summary['cow_pct']
    vote_margin= summary['vote_margin']
    pt_margin  = summary['pt_margin']
    rptd_c     = summary['n_reported']
    total_c    = summary['n_total']
    total_v    = summary['total_votes']
    pct_rep    = rptd_c/total_c*100 if total_c > 0 else 0

    # Margin card content
    if total_v == 0:
        margin_label = "MARGIN"
        margin_value = "—"
        margin_sub   = "No votes reported yet"
        margin_css   = "neutral"
    elif vote_margin > 0:
        margin_label = "STRICKLAND LEADS"
        margin_value = f"+{vote_margin:,}"
        margin_sub   = f"+{pt_margin:.1f} pts &nbsp;|&nbsp; {str_pct:.1f}% vs {cow_pct:.1f}%"
        margin_css   = "positive"
    elif vote_margin < 0:
        margin_label = "COWSERT LEADS"
        margin_value = f"{vote_margin:,}"
        margin_sub   = f"{pt_margin:.1f} pts &nbsp;|&nbsp; {str_pct:.1f}% vs {cow_pct:.1f}%"
        margin_css   = "negative"
    else:
        margin_label = "TIED"
        margin_value = "0"
        margin_sub   = f"{str_pct:.1f}% vs {cow_pct:.1f}%"
        margin_css   = "neutral"

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, sub, css in [
        (c1, "STRICKLAND", f"{str_v:,}", f"{str_pct:.1f}% of votes in", "positive" if str_pct >= 50 else "negative"),
        (c2, "COWSERT",    f"{cow_v:,}", f"{cow_pct:.1f}% of votes in", "negative" if str_pct >= 50 else "positive"),
        (c3, margin_label, margin_value, margin_sub, margin_css),
        (c4, "COUNTIES REPORTING", f"{rptd_c}/{total_c}",
             f"{pct_rep:.0f}% of state &nbsp;|&nbsp; {total_v:,} votes in", "neutral"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value {css}">{value}</div>
              <div class="metric-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)


    # ── Key county cards ──
    st.markdown('<div class="section-head">KEY COUNTIES</div>', unsafe_allow_html=True)
    key_rows = cmd_df[cmd_df['is_key']].copy()
    key_rows = key_rows.sort_values('ALERT', key=lambda x: x.map(lambda v: ALERT_PRIORITY.get(v,9)))

    cards_html = '<div class="county-grid">'
    for _, row in key_rows.iterrows():
        cards_html += county_card_html(row)
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

    # ── Alert log ──
    fired = cmd_df[cmd_df['ALERT'].isin(['BEHIND','WATCH','AHEAD','BREAKOUT']) &
                   cmd_df['Actual %'].notna()]

    if fired.empty:
        st.markdown('<div class="section-head">ALERTS</div>', unsafe_allow_html=True)
        st.markdown('<div class="alert-row"><div class="alert-text" style="color:#6B7280">'
                    '✓ No alerts — all reporting counties within expected bands.</div></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-head">ALERTS ({len(fired)})</div>',
                    unsafe_allow_html=True)
        alert_html = ''
        for priority_label in ['BEHIND','WATCH','BREAKOUT','AHEAD']:
            for _, row in fired[fired['ALERT']==priority_label].iterrows():
                alert_html += alert_row_html(row)
        st.markdown(alert_html, unsafe_allow_html=True)

    # ── Full county table ──
    st.markdown('<div class="section-head">ALL 159 COUNTIES</div>', unsafe_allow_html=True)

    search = st.text_input("", placeholder="Search counties…",
                           label_visibility="collapsed", key="search")
    display_df = cmd_df.drop(columns=['is_key'], errors='ignore').copy()
    if search:
        display_df = display_df[display_df['County'].str.contains(search, case=False)]

    # Rename for display
    display_df = display_df.rename(columns={
        'Actual %':'Act%', 'Model %':'Mdl%', 'Dev pts':'Dev',
        'Str Votes':'Str V', 'Cow Votes':'Cow V', 'Total Rptd':'Total',
        'Str Exp Mid':'Exp Mid', 'Turnout Mid':'Turn Mid',
    })

    # Mobile/compact view toggle
    compact = st.checkbox(
        "Compact View (mobile-friendly — shows key columns only)",
        value=False, key="compact_view"
    )

    if compact:
        show_cols = ['County', 'ALERT', 'Act%', 'Dev', 'Cushion', 'Precincts']
    else:
        show_cols = ['County','ALERT','Act%','Mdl%','Dev','Cushion',
                     'Str V','Cow V','Total','% Exp Rptd','Precincts','Floor %','Ceiling %',
                     'Volatility','Adjustment']
    show_cols = [c for c in show_cols if c in display_df.columns]
    tbl = display_df[show_cols].copy()

    def color_win_loss(row):
        act = row.get('Act%', None)
        if act is None or (isinstance(act, float) and pd.isna(act)):
            return ['background-color:#1a1f27; color:#6B7280'] * len(row)
        if act > 50:
            return ['background-color:#0d2b1a; color:#F0F6FF'] * len(row)  # green
        else:
            return ['background-color:#2b0d0d; color:#F0F6FF'] * len(row)  # red

    styled = tbl.style.apply(color_win_loss, axis=1).format({
        'Act%':      '{:.2f}',
        'Mdl%':      '{:.2f}',
        'Dev':       '{:.2f}',
        'Floor %':   '{:.2f}',
        'Ceiling %': '{:.2f}',
        '% Exp Rptd':'{:.2f}',
        'Cushion':   '{:,.0f}',
        'Str V':     '{:,.0f}',
        'Cow V':     '{:,.0f}',
        'Total':     '{:,.0f}',
    }, na_rep='—')
    st.dataframe(
        styled,
        use_container_width=True,
        height=540,
        hide_index=True,
    )

    st.caption(f"Engine v1.0 · Model v2.6 · {summary['timestamp']} · "
               f"Source: {source} · {rptd}/{total} counties")


# ── Entry ─────────────────────────────────────────────────────────────────────
if not check_password():
    st.stop()
main()

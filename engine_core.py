"""Election Night Engine Core — importable by app.py"""
import pandas as pd
import os
from datetime import datetime

ALERT_PRIORITY = {'BEHIND':0,'WATCH':1,'BREAKOUT':2,'AHEAD':3,'ON MODEL':4,'PENDING':5}
ALERT_COLORS   = {
    'BEHIND':  '#DC2626', 'WATCH':   '#F59E0B', 'ON MODEL':'#10B981',
    'AHEAD':   '#34D399', 'BREAKOUT':'#A78BFA', 'PENDING': '#4B5563',
}
KEY_COUNT = 12   # Show top N counties by expected turnout as "key" counties

def _safe_int(val, default=0):
    """Convert a value to int safely, handling NaN, None, and empty strings."""
    try:
        if pd.isna(val):
            return default
    except (TypeError, ValueError):
        pass
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default

def find_benchmark():
    candidates = [
        os.path.join(os.path.dirname(__file__), 'County_Benchmark_Model.csv'),
        os.path.join(os.path.dirname(__file__), '..', 'data', 'County_Benchmark_Model.csv'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError("County_Benchmark_Model.csv not found.")

def load_benchmark():
    df = pd.read_csv(find_benchmark())
    return df[df['County'] != 'STATEWIDE AGGREGATE'].copy()

def get_alert(actual_pct, floor, ceiling, breakout, has_votes):
    if not has_votes:         return 'PENDING'
    if actual_pct >= breakout: return 'BREAKOUT'
    if actual_pct > ceiling:   return 'AHEAD'
    if actual_pct >= floor:    return 'ON MODEL'
    if actual_pct >= floor-5:  return 'WATCH'
    return 'BEHIND'

def run_engine(bench_df, results_df):
    # Compute key counties dynamically — top KEY_COUNT by expected turnout
    top_by_turnout = bench_df.nlargest(KEY_COUNT, 'Expected Total Mid [PRIMARY]')['County'].tolist()
    res = {}
    if results_df is not None and not results_df.empty:
        res = results_df.set_index('County').to_dict('index')

    rows = []
    sw_str=0; sw_cow=0; sw_total=0; sw_exp_rem=0; n_rep=0; n_pend=0

    for _, b in bench_df.iterrows():
        county = b['County']
        r      = res.get(county, {})
        str_v  = _safe_int(r.get('Strickland Votes', 0))
        cow_v  = _safe_int(r.get('Cowsert Votes', 0))
        tot_r  = str_v + cow_v   # derive total from candidate votes
        prec_r = _safe_int(r.get('Precincts Reporting', 0))
        prec_t = max(_safe_int(r.get('Precincts Participating', 1), 1), 1)

        has     = tot_r > 0
        act_pct = str_v/tot_r*100 if has else 0.0
        dev     = act_pct - float(b['Strickland % Adjusted']) if has else None
        cushion = str_v - (float(b['Strickland % Adjusted'])/100*tot_r) if has else None
        pct_exp = tot_r/int(b['Expected Total Mid [PRIMARY]'])*100 if has and int(b['Expected Total Mid [PRIMARY]'])>0 else 0
        alert   = get_alert(act_pct, float(b['Floor %']), float(b['Ceiling %']), float(b['Breakout %']), has)

        if has:
            sw_str+=str_v; sw_cow+=cow_v; sw_total+=tot_r; n_rep+=1
        else:
            sw_exp_rem += int(b['Expected Strickland Votes Mid [PRIMARY]']); n_pend+=1

        rows.append({
            'County':         county,
            'ALERT':          alert,
            'Actual %':       round(act_pct, 2) if has else None,
            'Model %':        round(float(b['Strickland % Adjusted']), 2),
            'Dev pts':        round(dev, 2) if dev is not None else None,
            'Cushion':        int(round(cushion)) if cushion is not None else None,
            'Str Votes':      str_v if has else None,
            'Cow Votes':      cow_v if has else None,
            'Total Rptd':     tot_r if has else None,
            '% Exp Rptd':     round(pct_exp, 2),
            'Precincts':      f"{prec_r}/{prec_t}",
            'Floor %':        round(float(b['Floor %']), 2),
            'Ceiling %':      round(float(b['Ceiling %']), 2),
            'Str Exp Mid':    int(b['Expected Strickland Votes Mid [PRIMARY]']),
            'Turnout Mid':    int(b['Expected Total Mid [PRIMARY]']),
            'Volatility':     b['Turnout Volatility'],
            'Adjustment':     b['Candidate Adjustment'],
            'Divergence':     round(float(b['SoS-Gov Divergence pts']), 2),
            'is_key':         county in top_by_turnout,
        })

    sw_pct     = sw_str/sw_total*100 if sw_total>0 else 0.0
    sw_cow_pct = sw_cow/sw_total*100 if sw_total>0 else 0.0
    vote_margin = sw_str - sw_cow

    summary = {
        'n_reported':    n_rep,
        'n_total':       n_rep+n_pend,
        'total_votes':   sw_total,
        'str_actual':    sw_str,
        'cow_actual':    sw_cow,
        'str_pct':       round(sw_pct,2),
        'cow_pct':       round(sw_cow_pct,2),
        'vote_margin':   vote_margin,
        'pt_margin':     round(sw_pct - sw_cow_pct, 2),
        'cushion':       int(round(sw_str - sw_total*0.50)) if sw_total>0 else 0,
        'proj_str':      sw_str + sw_exp_rem,
        'timestamp':     datetime.now().strftime('%H:%M:%S'),
    }

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values('ALERT', key=lambda x: x.map(lambda v: ALERT_PRIORITY.get(v,9)))
    return df, summary

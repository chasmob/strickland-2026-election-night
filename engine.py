"""
Election Night Command Engine — v1.0
Strickland vs. Cowsert AG Primary — May 19, 2026

Inputs:
  County_Benchmark_Model.csv  — 159-county model baseline
  results_live.csv            — Live county results (updated by ingestor or manually)

Output:
  Election_Night_Command_View.csv — Full county command view
  (console summary printed on every run)

Run: python engine.py
     python engine.py --watch   (reruns every 60 seconds)
"""

import csv, time, sys, os
from datetime import datetime

BENCHMARK = r'd:\2026 May 19 Primary\data\County_Benchmark_Model.csv'
RESULTS   = r'd:\2026 May 19 Primary\election_night\results_live.csv'
OUTPUT    = r'd:\2026 May 19 Primary\election_night\Election_Night_Command_View.csv'

WATCH_MODE    = '--watch' in sys.argv
POLL_INTERVAL = 60  # seconds

# ── Alert thresholds ───────────────────────────────────────────────────────────
# AHEAD:    actual % > ceiling %
# ON MODEL: floor % <= actual % <= ceiling %
# WATCH:    actual % between (floor - 5) and floor
# BEHIND:   actual % < (floor - 5)
# (Only applies to counties with votes in)

def load_benchmark():
    bench = {}
    with open(BENCHMARK, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['County'] == 'STATEWIDE AGGREGATE':
                continue
            bench[row['County']] = {
                'adj_pct':     float(row['Strickland % Adjusted']),
                'pure_pct':    float(row['Strickland % Pure Historical']),
                'floor_pct':   float(row['Floor %']),
                'ceiling_pct': float(row['Ceiling %']),
                'breakout_pct':float(row['Breakout %']),
                'exp_mid':     int(row['Expected Total Mid [PRIMARY]']),
                'exp_low':     int(row['Expected Total Low']),
                'exp_high':    int(row['Expected Total High']),
                'str_mid':     int(row['Expected Strickland Votes Mid [PRIMARY]']),
                'str_low':     int(row['Expected Strickland Votes Low']),
                'str_high':    int(row['Expected Strickland Votes High']),
                'sen_1_2m':    int(row['Sensitivity 1.2M Strickland']),
                'sen_1_6m':    int(row['Sensitivity 1.6M Strickland']),
                'adj_note':    row['Candidate Adjustment'],
                'volatility':  row['Turnout Volatility'],
                'divergence':  float(row['SoS-Gov Divergence pts']),
            }
    return bench

def load_results():
    results = {}
    with open(RESULTS, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            results[row['County']] = {
                'str_votes':   int(row['Strickland_Votes']),
                'cow_votes':   int(row['Cowsert_Votes']),
                'total_rep':   int(row['Total_Votes_Reported']),
                'prec_rep':    int(row['Precincts_Reporting']),
                'prec_total':  int(row['Precincts_Total']),
            }
    return results

def get_alert(actual_pct, floor, ceiling, breakout, has_votes):
    if not has_votes:
        return 'PENDING'
    if actual_pct >= breakout:
        return 'BREAKOUT'
    if actual_pct > ceiling:
        return 'AHEAD'
    if actual_pct >= floor:
        return 'ON MODEL'
    if actual_pct >= floor - 5:
        return 'WATCH'
    return 'BEHIND'

ALERT_PRIORITY = {'BEHIND': 0, 'WATCH': 1, 'BREAKOUT': 2,
                  'AHEAD': 3, 'ON MODEL': 4, 'PENDING': 5}

def run_engine():
    bench   = load_benchmark()
    results = load_results()
    now     = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    command_rows = []

    # Statewide accumulators
    sw_str_actual      = 0
    sw_cow_actual      = 0
    sw_total_actual    = 0
    sw_str_exp_mid     = 0
    sw_str_exp_rep     = 0   # expected Strickland in already-reporting counties (at mid turnout)
    sw_exp_remaining   = 0   # expected Strickland in not-yet-reporting counties

    reported_counties  = 0
    pending_counties   = 0

    for county, b in bench.items():
        r = results.get(county, {'str_votes':0,'cow_votes':0,'total_rep':0,'prec_rep':0,'prec_total':1})

        str_v   = r['str_votes']
        cow_v   = r['cow_votes']
        total_r = r['total_rep']
        prec_r  = r['prec_rep']
        prec_t  = r['prec_total'] if r['prec_total'] > 0 else 1

        has_votes    = total_r > 0
        prec_pct     = prec_r / prec_t * 100 if prec_t > 0 else 0
        actual_pct   = str_v / total_r * 100 if total_r > 0 else 0
        cow_actual   = cow_v / total_r * 100 if total_r > 0 else 0

        # Pct of expected turnout reported (using mid as denominator)
        pct_exp_rep  = total_r / b['exp_mid'] * 100 if b['exp_mid'] > 0 else 0

        # Cushion: among votes already cast, how many ahead/behind model?
        # = actual Strickland votes - (model adj% * total reported votes)
        cushion_rep = str_v - (b['adj_pct'] / 100 * total_r) if has_votes else 0

        # Deviation from model (percentage points)
        deviation = actual_pct - b['adj_pct'] if has_votes else 0

        # Alert
        alert = get_alert(actual_pct, b['floor_pct'], b['ceiling_pct'], b['breakout_pct'], has_votes)

        # Statewide accumulators
        sw_str_exp_mid  += b['str_mid']
        if has_votes:
            sw_str_actual   += str_v
            sw_cow_actual   += cow_v
            sw_total_actual += total_r
            sw_str_exp_rep  += b['str_mid']
            reported_counties += 1
        else:
            sw_exp_remaining += b['str_mid']
            pending_counties += 1

        command_rows.append({
            'County':                    county,
            'Precincts':                 f"{prec_r}/{prec_t} ({prec_pct:.0f}%)",
            'Pct Expected Rptd':         round(pct_exp_rep, 1),
            'Actual Str %':              round(actual_pct, 1) if has_votes else '',
            'Model Adj %':               b['adj_pct'],
            'Deviation pts':             round(deviation, 1) if has_votes else '',
            'Floor %':                   b['floor_pct'],
            'Ceiling %':                 b['ceiling_pct'],
            'Str Actual Votes':          str_v if has_votes else '',
            'Cow Actual Votes':          cow_v if has_votes else '',
            'Total Reported':            total_r if has_votes else '',
            'Cushion Votes':             round(cushion_rep) if has_votes else '',
            'Str Expected Mid':          b['str_mid'],
            'Str Expected Low':          b['str_low'],
            'Str Expected High':         b['str_high'],
            'Model Turnout Mid':         b['exp_mid'],
            'Volatility':                b['volatility'],
            'SoS-Gov Divergence':        b['divergence'],
            'Adjustment':                b['adj_note'],
            'ALERT':                     alert,
            'As Of':                     now if has_votes else '',
        })

    # ── Statewide projection ───────────────────────────────────────────────────
    sw_str_pct_actual = sw_str_actual / sw_total_actual * 100 if sw_total_actual > 0 else 0
    sw_cushion        = sw_str_actual - (sw_str_exp_mid / sw_exp_remaining * sw_total_actual) \
                        if (sw_exp_remaining > 0 and sw_total_actual > 0) \
                        else sw_str_actual - (sw_str_pct_actual / 100 * sw_total_actual)

    # Simple projection: actual votes in + model-expected votes for remaining counties
    sw_projected_str  = sw_str_actual + sw_exp_remaining
    sw_projected_cow  = (sw_total_actual - sw_str_actual) + (sw_str_exp_mid - sw_str_actual - (sw_str_exp_mid - sw_exp_remaining - sw_str_actual) if sw_exp_remaining > 0 else 0)
    # Cleaner:
    sw_projected_total = sw_str_exp_mid  # proxy for total projected
    sw_proj_str_pct   = sw_projected_str / (sw_projected_str + (sw_projected_total - sw_str_actual)) * 100 \
                        if (sw_projected_str + (sw_projected_total - sw_str_actual)) > 0 else 0

    # ── Write output CSV ──────────────────────────────────────────────────────
    command_rows.sort(key=lambda x: ALERT_PRIORITY.get(x['ALERT'], 9))

    fieldnames = list(command_rows[0].keys())
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(command_rows)

    # ── Console Summary ────────────────────────────────────────────────────────
    print()
    print('=' * 65)
    print(f'  ELECTION NIGHT COMMAND — {now}')
    print('=' * 65)
    print(f'  Counties reporting:    {reported_counties} of {reported_counties + pending_counties}')
    print(f'  Votes in (actual):     {sw_str_actual + sw_cow_actual:,}')
    print()
    print(f'  STRICKLAND — LIVE')
    print(f'    Actual votes:        {sw_str_actual:,}')
    print(f'    Actual %:            {sw_str_pct_actual:.1f}%')
    print(f'    Model baseline:      50.0%')
    print(f'    Running cushion:     {sw_str_actual - (sw_total_actual * 0.50):+,.0f} votes vs 50% anchor')
    print()
    print(f'  PROJECTED FINISH (model for unreported counties)')
    print(f'    Strickland remaining: ~{sw_exp_remaining:,} expected votes from {pending_counties} counties')
    print(f'    Projected Strickland total: ~{sw_str_actual + sw_exp_remaining:,}')
    print()

    # Alert counts
    alert_counts = {}
    for row in command_rows:
        a = row['ALERT']
        alert_counts[a] = alert_counts.get(a, 0) + 1

    print('  ALERT SUMMARY')
    for label in ['BEHIND', 'WATCH', 'ON MODEL', 'AHEAD', 'BREAKOUT', 'PENDING']:
        count = alert_counts.get(label, 0)
        if count:
            print(f'    {label:<12}: {count} counties')

    print()
    print('  KEY COUNTY STATUS')
    key = ['Henry County', 'Cobb County', 'Gwinnett County', 'Walton County',
           'Oconee County', 'Hall County', 'Lowndes County', 'Fulton County']
    for row in command_rows:
        if row['County'] in key:
            if row['ALERT'] != 'PENDING':
                dev = f"{row['Deviation pts']:+.1f}pts" if row['Deviation pts'] != '' else '---'
                print(f'    {row["County"]:<22} {row["ALERT"]:<10} '
                      f'Actual {row["Actual Str %"]}%  Model {row["Model Adj %"]}%  '
                      f'Dev {dev}  Cushion {row["Cushion Votes"]:+,.0f}')
            else:
                print(f'    {row["County"]:<22} PENDING')

    print()
    print(f'  Output: {OUTPUT}')
    print('=' * 65)

if WATCH_MODE:
    print('Watch mode — refreshing every', POLL_INTERVAL, 'seconds. Ctrl+C to stop.')
    while True:
        run_engine()
        time.sleep(POLL_INTERVAL)
else:
    run_engine()

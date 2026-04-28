"""
mock_election_night.py
Simulates a 2022-style election night by releasing county results
in waves, writing to results_live.csv so the dashboard picks them up.

Usage:  python mock_election_night.py
        Press ENTER between waves, or 'q' to quit.
"""

import csv, os, time, sys

FULL_CSV  = r'd:\2026 May 19 Primary\election_night\mock_2022_full.csv'
LIVE_CSV  = r'd:\2026 May 19 Primary\election_night\results_live.csv'
LOCK_FILE = r'd:\2026 May 19 Primary\election_night\mock_active.flag'

# ── Load all 158 counties sorted by volume (largest last, so they hit late) ──
def load_all():
    with open(FULL_CSV, newline='') as f:
        return list(csv.DictReader(f))

# ── Define election-night reporting waves (realistic order) ──────────────────
# Small rural counties report first; big metros come in last.
def build_waves(counties):
    """
    Sort counties by total_votes ascending (small first).
    Wave structure:
      Wave 1 (7:30pm):  first 30  — small rural counties
      Wave 2 (8:00pm):  next  30  — medium rural counties
      Wave 3 (8:30pm):  next  30  — small suburban counties
      Wave 4 (9:00pm):  next  30  — medium suburban counties
      Wave 5 (9:30pm):  last  38  — major metros (Cobb, Gwinnett, Fulton…)
    """
    sorted_c = sorted(counties, key=lambda x: int(x['total_votes']))
    waves = [
        sorted_c[0:30],
        sorted_c[30:60],
        sorted_c[60:90],
        sorted_c[90:120],
        sorted_c[120:],
    ]
    wave_labels = [
        "Wave 1 — 7:30 PM  |  30 small rural counties",
        "Wave 2 — 8:00 PM  |  30 medium rural counties",
        "Wave 3 — 8:30 PM  |  30 small suburban counties",
        "Wave 4 — 9:00 PM  |  30 medium suburban counties",
        "Wave 5 — 9:30 PM  |  Final 38 — major metros",
    ]
    return list(zip(wave_labels, waves))

def write_live(reported):
    """Write current reported counties to results_live.csv."""
    fields = ['County','Strickland Votes','Cowsert Votes',
              'Precincts Reporting','Precincts Participating']
    with open(LIVE_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in reported:
            w.writerow({k: r[k] for k in fields})

def summarize(reported):
    if not reported:
        return "  No counties reporting yet."
    raff = sum(int(r['Strickland Votes']) for r in reported)
    hice = sum(int(r['Cowsert Votes']) for r in reported)
    tot  = raff + hice
    pct  = raff/tot*100 if tot else 0
    lines = [
        f"  Counties reporting: {len(reported)}/158",
        f"  Raffensperger (Strickland proxy): {raff:,}  ({pct:.1f}%)",
        f"  Hice (Cowsert proxy):             {hice:,}  ({100-pct:.1f}%)",
        f"  Margin: {'+' if raff>hice else ''}{raff-hice:,} votes",
    ]
    return '\n'.join(lines)

def main():
    if not os.path.exists(FULL_CSV):
        print("ERROR: Run build_2022_mock.py first to generate mock_2022_full.csv")
        sys.exit(1)

    counties = load_all()
    waves    = build_waves(counties)

    print("=" * 60)
    print("  STRICKLAND 2026 — MOCK ELECTION NIGHT SIMULATOR")
    print("  Data: 2022 SOS race (Raffensperger/Hice proxy)")
    print("=" * 60)
    print()
    print("  Dashboard reads results_live.csv on each refresh.")
    print("  Set dashboard interval to 30s for fastest demo.")
    print("  Press ENTER to release next wave | 'q' to quit | 'r' to reset")
    print()

    # Create flag file so ingestor knows to use live CSV
    open(LOCK_FILE, 'w').close()

    reported = []
    write_live(reported)  # start clean

    for wave_idx, (label, wave_counties) in enumerate(waves):
        print(f"\n{'─'*60}")
        print(f"  READY: {label}")
        print(f"  Counties in this wave: {len(wave_counties)}")
        # Show a few notable counties
        notable = sorted(wave_counties, key=lambda x: -int(x['total_votes']))[:5]
        for c in notable:
            raff = int(c['Strickland Votes']); hice = int(c['Cowsert Votes'])
            tot  = raff + hice
            print(f"    {c['County']:<25} Raff {raff:>7,}  ({raff/tot*100:.1f}%)")
        print()
        inp = input("  Press ENTER to release → ").strip().lower()
        if inp == 'q':
            break
        if inp == 'r':
            reported = []
            write_live(reported)
            print("  RESET — starting over.")
            continue

        reported.extend(wave_counties)
        write_live(reported)

        print(f"\n  ✓ Released {len(wave_counties)} counties")
        print(summarize(reported))
        print(f"\n  ← Refresh the dashboard now (or wait for auto-refresh)")

    print("\n" + "="*60)
    print("  Simulation complete.")
    print(summarize(reported))

    # Leave results_live.csv in place so dashboard keeps showing final state
    # Remove flag file
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    print("\n  results_live.csv remains for dashboard display.")
    print("  Delete it manually to return to sample-data mode.")

if __name__ == '__main__':
    main()

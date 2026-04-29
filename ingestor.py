"""
ingestor.py — Georgia SOS Enhanced Voting results feed
Fetches live JSON from results.sos.ga.gov/cdn/results/Georgia/export-*.json
Falls back to manual CSV upload, then sample data.

ENDPOINT NOTES (confirmed via browser inspection 2026-04-28):
  Georgia SOS migrated from Clarity to Enhanced Voting platform.
  URL pattern: https://results.sos.ga.gov/cdn/results/Georgia/export-{election_id}.json
  
  Confirmed 2026 elections:
    Feb 17 Runoff:  export-Feb1726StateSenateDistrict18.json
    Mar 10 Special: export-March102026SpecialElection.json
  
  Predicted May 19 Primary (update if SOS uses different ID):
    export-51926GeneralPrimary.json
  
  HOW TO CONFIRM ON ELECTION NIGHT (if predicted URL fails):
    1. Open results.sos.ga.gov in Chrome
    2. Click Download Reports (top right)
    3. Scroll to "Media Export" link → copy URL
    4. Update LIVE_ENDPOINT below and redeploy (2 min)
"""

import requests
import pandas as pd
import io
import os
from datetime import datetime

# ── Live endpoint ─────────────────────────────────────────────────────────────
LIVE_ENDPOINT = (
    "https://results.sos.ga.gov/cdn/results/Georgia/"
    "export-51926GeneralPrimary.json"
)

# Candidate name fragments to match (case-insensitive)
# These match whatever the SOS uses on the ballot
STRICKLAND_KEYWORDS = ["strickland"]
COWSERT_KEYWORDS    = ["cowsert"]

# AG race ID in the JSON — update if SOS uses a different ID
# Common patterns: "AG", "SAG", "AttorneyGeneral", check localResults[*].ballotItems[*].id
AG_RACE_KEYWORDS = ["attorney general", "ag"]


def _parse_sos_json(data: dict) -> pd.DataFrame | None:
    """
    Parse the Enhanced Voting JSON export into a county-level results DataFrame.
    Returns columns: County, Strickland Votes, Cowsert Votes,
                     Precincts Reporting, Precincts Participating
    """
    local_results = data.get("localResults", [])
    if not local_results:
        return None

    rows = []
    for county_block in local_results:
        county_name = county_block.get("name", "")
        if not county_name.endswith(" County"):
            county_name = county_name + " County"

        # Find the AG race ballot item
        ag_item = None
        for item in county_block.get("ballotItems", []):
            item_name = item.get("name", "").lower()
            item_id   = item.get("id", "").lower()
            if any(k in item_name or k in item_id for k in AG_RACE_KEYWORDS):
                ag_item = item
                break

        if ag_item is None:
            continue  # county doesn't have the AG race (special election only covers part of state)

        prec_participating = ag_item.get("precinctsParticipating") or 0
        prec_reporting     = ag_item.get("precinctsReporting")     or 0

        str_votes = 0
        cow_votes = 0
        for option in ag_item.get("ballotOptions", []):
            name_lower = option.get("name", "").lower()
            votes      = option.get("voteCount") or 0
            if any(k in name_lower for k in STRICKLAND_KEYWORDS):
                str_votes += votes
            elif any(k in name_lower for k in COWSERT_KEYWORDS):
                cow_votes += votes

        if str_votes == 0 and cow_votes == 0 and prec_reporting == 0:
            continue  # county hasn't started reporting

        rows.append({
            "County":                 county_name,
            "Strickland Votes":       str_votes,
            "Cowsert Votes":          cow_votes,
            "Precincts Reporting":    prec_reporting,
            "Precincts Participating": prec_participating,
        })

    if not rows:
        return None
    return pd.DataFrame(rows)


def _fetch_live() -> tuple[pd.DataFrame | None, str]:
    """Hit the SOS CDN endpoint and parse results."""
    try:
        r = requests.get(LIVE_ENDPOINT, timeout=15)
        r.raise_for_status()
        data = r.json()
        df = _parse_sos_json(data)
        if df is not None and not df.empty:
            return df, "SOS Live Feed"
    except Exception as e:
        pass
    return None, ""


def _load_csv(path_or_file) -> tuple[pd.DataFrame | None, str]:
    """Load a results CSV — accepts a file path string or an uploaded file object."""
    try:
        if hasattr(path_or_file, "read"):
            content = path_or_file.read()
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_csv(path_or_file)

        required = {"County", "Strickland Votes", "Cowsert Votes"}
        if not required.issubset(df.columns):
            return None, ""
        # Drop rows where County or vote columns are blank/NaN (e.g. Excel partial rows)
        df = df.dropna(subset=list(required))
        df = df[df['County'].str.strip() != '']
        if df.empty:
            return None, ""
        return df, "Manual Upload"
    except Exception:
        return None, ""


def _sample_data() -> pd.DataFrame:
    """Generate plausible-looking sample data for ~10% of counties (demo mode)."""
    import random, csv
    # Find benchmark to get county names
    candidates = [
        os.path.join(os.path.dirname(__file__), "County_Benchmark_Model.csv"),
        os.path.join(os.path.dirname(__file__), "..", "data", "County_Benchmark_Model.csv"),
    ]
    counties = []
    for path in candidates:
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row["County"] != "STATEWIDE AGGREGATE":
                        counties.append((
                            row["County"],
                            int(row["Expected Total Mid [PRIMARY]"]),
                            float(row["Strickland % Adjusted"]),
                            int(row.get("Precincts Total", 20)),
                        ))
            break

    random.seed(42)
    rows = []
    # Report the top 16 counties (by expected turnout) as an early sample
    counties_sorted = sorted(counties, key=lambda x: -x[1])
    for county, mid_turnout, adj_pct, prec_total in counties_sorted[:16]:
        noise       = random.gauss(0, 1.5)
        str_pct     = (adj_pct + noise) / 100
        str_pct     = max(0.25, min(0.75, str_pct))
        total_votes = int(mid_turnout * random.uniform(0.90, 1.10))
        str_votes   = int(total_votes * str_pct)
        cow_votes   = total_votes - str_votes
        prec_rep    = int(prec_total * random.uniform(0.35, 0.65))
        rows.append({
            "County":                  county,
            "Strickland Votes":        str_votes,
            "Cowsert Votes":           cow_votes,
            "Precincts Reporting":     prec_rep,
            "Precincts Participating": prec_total,
        })
    return pd.DataFrame(rows)


def get_results(uploaded_file=None) -> tuple[pd.DataFrame | None, str]:
    """
    Main entry point called by app.py.
    Priority: Manual Upload → SOS Live Feed → Local results_live.csv → Sample Data
    Returns (results_df | None, source_label)
    """
    # 1. Manual upload (highest priority — operator override)
    if uploaded_file is not None:
        df, src = _load_csv(uploaded_file)
        if df is not None:
            return df, "Manual Upload"

    # 2. Live SOS feed
    df, src = _fetch_live()
    if df is not None:
        return df, src

    # 3. Local results_live.csv (mock simulator or pre-loaded results)
    local_csv = os.path.join(os.path.dirname(__file__), 'results_live.csv')
    if os.path.exists(local_csv):
        df, src = _load_csv(local_csv)
        if df is not None and not df.empty:
            return df, "Local File (results_live.csv)"

    # 4. Sample data (demo / pre-election)
    return _sample_data(), "Sample Data (Demo)"


def get_empty_template() -> pd.DataFrame:
    """Returns an empty CSV template the operator can fill in manually."""
    return pd.DataFrame(columns=[
        "County", "Strickland Votes", "Cowsert Votes",
        "Precincts Reporting", "Precincts Participating",
    ])

from engine_core import load_benchmark, run_engine
from ingestor import get_results

b = load_benchmark()
r, s = get_results()
df, summ = run_engine(b, r)

print("Engine OK")
print(f"Counties loaded: {len(df)}")
print(f"Data source:     {s}")
print(f"Strickland %:    {summ['str_pct']}%")
print(f"Cushion:         {summ['cushion']:,}")
print(f"Reporting:       {summ['n_reported']}/{summ['n_total']}")
print(f"Alert counts:")
for alert in ['BEHIND','WATCH','AHEAD','BREAKOUT','ON MODEL','PENDING']:
    count = (df['ALERT'] == alert).sum()
    if count:
        print(f"  {alert:<12}: {count}")
print("\nKey counties:")
for _, row in df[df['is_key']].iterrows():
    act = f"{row['Actual %']:.1f}%" if row['Actual %'] is not None else "PENDING"
    print(f"  {row['County']:<22} {row['ALERT']:<10} {act}")

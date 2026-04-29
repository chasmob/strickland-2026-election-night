# Election Night SOP — Strickland 2026 AG Primary
## May 19, 2026 | Standard Operating Procedure — v2.6
### Last Updated: April 29, 2026

---

## CREDENTIALS & ACCESS

| Item | Value |
|---|---|
| **Dashboard URL** | `https://strickland-ag.streamlit.app` |
| **Viewer Password** (share freely) | `Strickland2026` |
| **Operator Password** (you only) | `ink@!A5tp9` |
| **Google Broadcast Sheet** | See link in sidebar under 📡 Broadcast Channel |
| **SOS Results Portal** | `https://results.sos.ga.gov` |
| **GitHub Repo** | `https://github.com/chasmob/strickland-2026-election-night` |
| **Streamlit Account** | `chasmob@gmail.com` |

---

## HOW THE SYSTEM WORKS — READ THIS FIRST

There are two types of users:

**You (Operator)** — Log in with `ink@!A5tp9`. You see a gold ⚡ OPERATOR MODE badge.
You have access to: Manual Upload, Broadcast Sheet link, SOS endpoint override, Refresh controls.

**Everyone Else (Viewers)** — Log in with `Strickland2026`. They see a gray 👁 VIEW ONLY badge.
They can: Watch the dashboard, download the Model Brief. They cannot upload or change anything.

### Data Priority (what the system shows, in order):
1. **SOS Live Feed** — Automatic. Works for everyone the moment SOS posts results.
2. **Broadcast Sheet** — You type results into Google Sheets → all viewers auto-update within 5 min.
3. **Manual Upload** — Only you see it. Use for previewing data before broadcasting.
4. **Sample Data (Demo)** — What everyone sees before real results exist.

---

## PART 1 — WHAT TO DO RIGHT NOW (April 29 – May 18)

### This Week

- [ ] **Share the dashboard URL and viewer password** with everyone who needs access. Send them: `strickland-ag.streamlit.app` / Password: `Strickland2026`. Do this now so they can bookmark it.
- [ ] **Add secrets to Streamlit Cloud** (if not already done):
  - Go to share.streamlit.io → your app → ⋮ → Settings → Secrets
  - Paste exactly:
    ```toml
    APP_PASSWORD      = "Strickland2026"
    OPERATOR_PASSWORD = "ink@!A5tp9"
    GSHEET_URL        = "https://docs.google.com/spreadsheets/d/14m4bAy6X2uGmDgUZhD5obn3glQ_RoJbArQVtLCAfsXk/export?format=csv&gid=608499832"
    GSHEET_EDIT_URL   = "https://docs.google.com/spreadsheets/d/14m4bAy6X2uGmDgUZhD5obn3glQ_RoJbArQVtLCAfsXk/edit?gid=608499832#gid=608499832"
    ```
  - Click Save → wait 90 seconds for redeploy
- [ ] **Log in with your operator password** to confirm ⚡ OPERATOR MODE appears and the 📡 Broadcast Channel link is visible.
- [ ] **Test the dashboard on your phone.** Open `strickland-ag.streamlit.app`, log in with viewer password, verify it loads. Enable Compact View for phone use.
- [ ] **Save these credentials offline** (notes app, printed card): Dashboard URL, both passwords, GitHub login, Streamlit login.

### May 14–18 (Final Week Before Election)

- [ ] **Visit results.sos.ga.gov** and confirm it loads. They sometimes do maintenance the week before.
- [ ] **Check for a Media Export or Developer section** on the SOS site. If you find a JSON export URL, copy it — it's the correct SOS endpoint. Paste it into your notes.
- [ ] **Run the full dress rehearsal** (see Part 5 below).
- [ ] **Verify the cloud dashboard still shows Sample Data (Demo)** and no error screen.
- [ ] **Designate a backup operator** — one other person who knows the operator password and the manual upload process.

---

## PART 2 — MAY 19 TIMELINE (Election Night SOP)

### 6:00 PM — System Wake-Up

1. Log in with your **operator password** (`ink@!A5tp9`) at `strickland-ag.streamlit.app`.
2. Confirm the gold ⚡ **OPERATOR MODE** badge appears in the sidebar.
3. Confirm the dashboard shows **"Sample Data (Demo)"** — this means it's running normally.
4. Open a second browser tab to `results.sos.ga.gov` — keep this open all night.
5. Open a third browser tab to the **Google Broadcast Sheet** (click 📊 Open Broadcast Sheet in your sidebar).
6. Set sidebar refresh interval to **2 minutes** for faster initial detection of SOS data.

---

### 6:30 PM — SOS Endpoint Verification ⚠️ CRITICAL STEP

This is the most important pre-results step. Do not skip it.

1. Go to `results.sos.ga.gov`
2. Look for any of:
   - A "Media Export" or "Download Reports" link (top right)
   - A "Developer" section or "Results Export" tab
3. **If you find a JSON export link:**
   - Right-click it → Copy link address
   - In your operator sidebar → click ⚙️ **SOS Endpoint — Election Night Fix**
   - Paste the URL in the box → click ✅ **Apply URL**
   - Your session now uses the correct SOS endpoint
4. **If you find nothing yet** — proceed. The system will try the predicted URL automatically.

**Predicted URL the system will try first:**
```
https://results.sos.ga.gov/cdn/results/Georgia/export-51926GeneralPrimary.json
```

---

### 7:00 PM — Polls Close / Results Begin

1. Watch the **source label** (top right of the dashboard header).
2. It should change from `Sample Data (Demo)` → **`SOS Live Feed`** within 5–15 minutes of first results.
3. If source label does not change by **7:20 PM**, go to Contingency Plan A below.
4. Once live data flows, change refresh interval back to **5 minutes**.

---

### 7:00 PM – Close — Monitoring Protocol

Watch in this order:

**Priority 1 — Key County Cards (top of dashboard)**
- 🔴 **BEHIND** in any key county = immediate attention needed
- 🟣 **BREAKOUT** = good news worth flagging to campaign leadership
- Watch most closely: **Cobb, Gwinnett, Cherokee, Forsyth, Fayette**

**Priority 2 — Statewide Margin (top-right metric card)**
- As long as this is positive and growing, the night is on track

**Priority 3 — Alert Log / Cushion Column**
- Negative Cushion = Strickland is currently losing that county
- Multiple BEHIND alerts in same region = a pattern — flag it

**Counties Cowsert WILL win (not a crisis):**
Clarke, Oconee, Barrow, Walton — these are his home turf. Expected.

**Early vs. Late Reporting — Warn your team:**
Rural counties often report first (7–7:30 PM) and may skew the statewide number early. The suburban wave (Cobb, Gwinnett, Forsyth) typically comes in 8–9 PM. Do not overreact to early small-county results.

---

## PART 3 — CONTINGENCY PLANS

### Contingency Plan A: SOS Feed Not Connecting (7:20 PM — no data)

**Step 1 — Check SOS manually**
Go to `results.sos.ga.gov`. Are results visible on the website?

**If YES (results on site but dashboard not updating) → Wrong URL. Fix it in 2 minutes:**
1. On `results.sos.ga.gov` → click **Download Reports** (top right of page)
2. Find the **Media Export** link → right-click → **Copy link address**
3. In your operator sidebar → click ⚙️ **SOS Endpoint — Election Night Fix**
4. Paste the URL in the text box
5. Click ✅ **Apply URL**
6. Dashboard immediately shows **`SOS Live Feed (Custom URL)`** in the source badge
7. You now have live data. While watching your screen, type results into the 📡 **Broadcast Sheet** so all viewers see real numbers within 5 minutes.

**If SOS site is also blank** → Results haven't posted yet. Wait until 7:30 PM then try again.

**If you need deeper URL detection (browser DevTools):**
1. Open Chrome on `results.sos.ga.gov`
2. Press `F12` → click **Network** tab → click **Fetch/XHR** filter
3. Refresh the SOS page (`F5`)
4. Watch for a request ending in `.json` → right-click → **Copy → Copy URL**
5. Paste that URL into the ⚙️ SOS Endpoint Override box in your sidebar

---

### Contingency Plan B: Broadcast Sheet — Manual Entry for All Viewers

If SOS feed cannot be fixed, this is how you push results to all 50 viewers simultaneously:

1. Go to `results.sos.ga.gov` and read county results off the screen
2. Open the **Google Broadcast Sheet** (📊 button in your operator sidebar)
3. Find the county in column A (sorted A–Z)
4. Type Strickland's votes in column B, Cowsert's votes in column C
5. The data auto-saves — all viewers see it within 5 minutes on their next refresh

**Important rules:**
- Leave counties at 0 if results haven't come in yet (they show as PENDING)
- Do NOT change county names in column A
- Numbers only — no commas, no % signs

**Alternative — Manual Upload (your session only):**
Use the pre-built template at `d:\2026 May 19 Primary\Election_Night_Entry_Template.xlsx`:
1. Fill in county results
2. File → Save As → CSV
3. Sidebar → 📁 Manual Upload → Upload the file
4. Your screen updates instantly (others do not see this)

---

### Contingency Plan C: Cloud Dashboard Goes Down

If `strickland-ag.streamlit.app` is unreachable:

1. Open your laptop → open PowerShell
2. Run:
   ```
   cd "d:\2026 May 19 Primary\election_night"
   streamlit run app.py
   ```
3. Open `http://localhost:8501`
4. The local version is full-featured and works completely offline
5. Share your screen via video call so others can see it

**The local version is your complete offline backup.**

---

### Contingency Plan D: Total Internet Outage

1. Run local dashboard (Plan C)
2. Use your phone as a hotspot
3. Use Broadcast Sheet (Plan B) via your phone's data connection

---

## PART 4 — SOS.GA.GOV CONNECTIVITY CHECKS

### Week of May 12 — Test from your laptop

```
curl -I https://results.sos.ga.gov
```
Expected: `HTTP/2 200` or `HTTP/1.1 200 OK`

Test the predicted JSON endpoint in your browser:
```
https://results.sos.ga.gov/cdn/results/Georgia/export-51926GeneralPrimary.json
```
Before election night this will return a 404 (results not posted yet). That is **normal and expected**.

### May 19 Morning — Connectivity Script

```
cd "d:\2026 May 19 Primary\election_night"
python smoke_test.py
```

Or run manually:
```python
import requests
r = requests.get('https://results.sos.ga.gov', timeout=10)
print(f'SOS portal: {r.status_code}')
try:
    r2 = requests.get(
        'https://results.sos.ga.gov/cdn/results/Georgia/export-51926GeneralPrimary.json',
        timeout=10
    )
    print(f'JSON endpoint: {r2.status_code}')
except Exception as e:
    print(f'JSON endpoint: Not yet active ({e})')
```

---

## PART 5 — DRESS REHEARSAL (Do This May 14–15)

Run this before election night. Takes 30 minutes.

1. **Open the dashboard** as operator at `strickland-ag.streamlit.app`
2. **Confirm** ⚡ OPERATOR MODE badge, 📡 Broadcast Channel link, and ⚙️ SOS Endpoint section all appear
3. **Open the Broadcast Sheet** — type fake results for 3 counties (Cobb, Fulton, Cherokee). Use made-up numbers.
4. **Log in on your phone** with `Strickland2026` → confirm 👁 VIEW ONLY mode → wait 5 minutes → confirm those 3 counties update on your phone
5. **Clear the broadcast sheet** (reset all vote columns back to 0) after testing
6. **Test manual CSV upload:**
   - Open `d:\2026 May 19 Primary\Election_Night_Entry_Template.xlsx`
   - Enter fake numbers for 5 counties
   - Save as CSV → upload via sidebar → confirm dashboard updates
7. **Test the SOS URL override:**
   - Open ⚙️ SOS Endpoint section
   - Paste any URL → click Apply → confirm badge changes
   - Click Clear/Reset → confirm it goes back to default

---

## PART 6 — QUICK REFERENCE CARD

Print this. Keep it with you May 19.

```
╔══════════════════════════════════════════════════════════════════╗
║        STRICKLAND 2026 AG — ELECTION NIGHT QUICK REF            ║
╠══════════════════════════════════════════════════════════════════╣
║  DASHBOARD:      strickland-ag.streamlit.app                    ║
║  VIEWER PW:      Strickland2026                                 ║
║  OPERATOR PW:    ink@!A5tp9                                     ║
╠══════════════════════════════════════════════════════════════════╣
║  SOS PORTAL:     results.sos.ga.gov                             ║
║  DEFAULT JSON:   results.sos.ga.gov/cdn/results/Georgia/        ║
║                  export-51926GeneralPrimary.json                ║
╠══════════════════════════════════════════════════════════════════╣
║  BROADCAST SHEET: Open via 📡 button in Operator sidebar        ║
║  → Type county results → all viewers see within 5 min           ║
╠══════════════════════════════════════════════════════════════════╣
║  IF SOS URL WRONG:                                              ║
║  1. results.sos.ga.gov → Download Reports → Media Export        ║
║  2. Sidebar → ⚙️ SOS Endpoint → paste URL → ✅ Apply           ║
╠══════════════════════════════════════════════════════════════════╣
║  SOURCE BADGE SHOULD SHOW:                                      ║
║  "SOS Live Feed" after 7:15 PM                                  ║
║  If still "Sample Data" at 7:20 PM → run Contingency Plan A     ║
╠══════════════════════════════════════════════════════════════════╣
║  WATCH IN ORDER:                                                 ║
║  1. KEY COUNTY cards — any BEHIND in red?                       ║
║  2. Statewide margin top right — is it positive?                ║
║  3. Cushion column — negative = losing that county              ║
╠══════════════════════════════════════════════════════════════════╣
║  COWSERT WILL WIN: Clarke, Oconee, Barrow, Walton (expected)   ║
║  STRICKLAND MUST WIN: Cobb, Gwinnett, Cherokee, Forsyth, Fayette║
╠══════════════════════════════════════════════════════════════════╣
║  LOCAL BACKUP:                                                   ║
║  cd "d:\2026 May 19 Primary\election_night"                     ║
║  streamlit run app.py → open localhost:8501                     ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## PART 7 — DASHBOARD SOURCE BADGES EXPLAINED

| Badge Color | Label | Meaning |
|---|---|---|
| 🟢 Green | SOS Live Feed | Live SOS data — primary |
| 🟡 Amber | SOS Live Feed (Custom URL) | You applied a URL override — working |
| 🔵 Indigo | Broadcast Sheet | Pulling from your Google Sheet — all viewers see this |
| 🟡 Amber | Manual Upload | Your preview only — others don't see this |
| ⚫ Gray | Sample Data (Demo) | Pre-election mode — no real results yet |
| 🔴 Red | (anything red) | Data error — check connectivity |

---

*Document version: v2.6 — April 29, 2026*
*System: Election Night Command Dashboard — Strickland AG 2026*
*Model: Baseline Vote Model v2.6 — deviation-from-mean, ROLLOFF_FACTOR=0.93*

"""
Generate Google (Alphabet Inc.) financial HTML tables from EDGAR SEC data.
CIK: 0001652044, Ticker: GOOGL (NASDAQ)
Data source: https://data.sec.gov/api/xbrl/companyfacts/CIK0001652044.json
"""

import json, pathlib, urllib.request

# ============================================================
# 1. Fetch EDGAR data
# ============================================================
EDGAR_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001652044.json"
CACHE_FILE = pathlib.Path(__file__).resolve().parent / "google_edgar.json"

def fetch_edgar():
    """Fetch from SEC EDGAR (or use cached file)."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(EDGAR_URL, headers={"User-Agent": "CompanyAnalysis admin@example.com"})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data

data = fetch_edgar()
usgaap = data["facts"]["us-gaap"]

# ============================================================
# 2. Helper extractors
# ============================================================
def get_annual(concept, unit="USD"):
    """Get annual (full-year) values keyed by CY year."""
    if concept not in usgaap:
        return {}
    entries = usgaap[concept].get("units", {}).get(unit, [])
    result = {}
    for e in entries:
        if e.get("form") == "10-K" and "frame" in e:
            frame = e["frame"]
            if frame.startswith("CY") and "Q" not in frame:
                year = int(frame[2:])
                result[year] = e["val"]
    return result

def get_instant(concept, unit="USD"):
    """Get instant (balance sheet) values keyed by frame."""
    if concept not in usgaap:
        return {}
    entries = usgaap[concept].get("units", {}).get(unit, [])
    return {e["frame"]: e["val"] for e in entries if "frame" in e}

def get_q4i(concept, unit="USD"):
    """Get year-end (Q4I) instant values keyed by year."""
    inst = get_instant(concept, unit)
    result = {}
    for frame, val in inst.items():
        if "Q4I" in frame:
            year = int(frame[2:6])
            result[year] = val
    return result

def get_quarterly_flow(concept, unit="USD"):
    """Get quarterly flow values keyed by CYxxxxQn frame."""
    if concept not in usgaap:
        return {}
    entries = usgaap[concept].get("units", {}).get(unit, [])
    return {e["frame"]: e["val"] for e in entries if "frame" in e and "Q" in e.get("frame", "") and not e["frame"].endswith("I")}

def get_quarterly_instant(concept, unit="USD"):
    """Get quarterly instant values keyed by CYxxxxQnI frame."""
    inst = get_instant(concept, unit)
    return {k: v for k, v in inst.items() if "Q" in k and k.endswith("I")}

def get_cumulative_flows(concept, unit="USD"):
    """Get cumulative YTD flow entries for deriving single-quarter values."""
    if concept not in usgaap:
        return []
    entries = usgaap[concept].get("units", {}).get(unit, [])
    result = {}
    for e in entries:
        if e.get("form") in ("10-Q", "10-K") and "frame" in e:
            result[e["frame"]] = e["val"]
        elif e.get("form") in ("10-Q", "10-K"):
            key = f"{e['start']}_{e['end']}"
            result[key] = e["val"]
    return result

# ============================================================
# 3. Extract raw data
# ============================================================
YEARS = [2021, 2022, 2023, 2024, 2025]

# --- Revenue ---
rev_a = get_annual("Revenues")
rev_contract = get_annual("RevenueFromContractWithCustomerExcludingAssessedTax")
# 2022 missing from Revenues, use RevenueFromContract
revenue = {}
for y in YEARS:
    revenue[y] = rev_a.get(y) or rev_contract.get(y)

# --- Operating Income ---
op_income = get_annual("OperatingIncomeLoss")

# --- Pre-tax Income ---
pretax = get_annual("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest")

# --- Net Income ---
net_income = get_annual("NetIncomeLoss")

# --- NCI: Alphabet has no NCI ---
nci_ni = {}  # Not reported

# --- Balance Sheet (year-end) ---
assets = get_q4i("Assets")
liabilities = get_q4i("Liabilities")
equity = get_q4i("StockholdersEquity")
cs_apic = get_q4i("CommonStocksIncludingAdditionalPaidInCapital")

# --- Cash Flows ---
op_cf = get_annual("NetCashProvidedByUsedInOperatingActivities")
inv_cf = get_annual("NetCashProvidedByUsedInInvestingActivities")
fin_cf = get_annual("NetCashProvidedByUsedInFinancingActivities")
capex = get_annual("PaymentsToAcquirePropertyPlantAndEquipment")

# --- Long-term Debt ---
ltd = get_q4i("LongTermDebt")
cp = get_q4i("CommercialPaper")

# --- EPS ---
eps_diluted = get_annual("EarningsPerShareDiluted", "USD/shares")

# --- Shares Outstanding ---
shares = get_q4i("CommonStockSharesOutstanding", "shares")

# --- DPS ---
dps_annual = get_annual("CommonStockDividendsPerShareDeclared", "USD/shares")

# ============================================================
# 4. Compute derived metrics
# ============================================================
def fmt_m(val_raw):
    """Format raw USD value to $M with comma separators."""
    if val_raw is None:
        return "-"
    val_m = round(val_raw / 1_000_000)
    if val_m < 0:
        return f"-{abs(val_m):,}"
    return f"{val_m:,}"

def fmt_pct(val):
    if val is None:
        return "-"
    return f"{val:.1f}"

def fmt_dollar(val):
    if val is None:
        return "-"
    return f"{val:.2f}"

def fmt_shares(val):
    if val is None:
        return "-"
    return f"{val:,}"

# Build annual data
annual_data = {}
for y in YEARS:
    d = {}
    d["revenue"] = revenue.get(y)
    d["op_income"] = op_income.get(y)
    d["pretax"] = pretax.get(y)
    d["net_income"] = net_income.get(y)
    d["nci_ni"] = nci_ni.get(y, 0)  # No NCI
    d["assets"] = assets.get(y)
    d["liabilities"] = liabilities.get(y)
    d["equity"] = equity.get(y)
    d["cs_apic"] = cs_apic.get(y)
    d["op_cf"] = op_cf.get(y)
    d["inv_cf"] = inv_cf.get(y)
    d["fin_cf"] = fin_cf.get(y)
    d["capex"] = capex.get(y)

    # Interest-bearing debt = LTD + Commercial Paper
    d["ibd"] = (ltd.get(y, 0) or 0) + (cp.get(y, 0) or 0)

    d["eps"] = eps_diluted.get(y)
    d["shares"] = shares.get(y)
    d["dps"] = dps_annual.get(y, 0)

    # FCF = Operating CF - CAPEX
    if d["op_cf"] is not None and d["capex"] is not None:
        d["fcf"] = d["op_cf"] - d["capex"]
    else:
        d["fcf"] = None

    # Op margin
    if d["op_income"] and d["revenue"]:
        d["op_margin"] = d["op_income"] / d["revenue"] * 100
    else:
        d["op_margin"] = None

    # Net margin
    if d["net_income"] and d["revenue"]:
        d["net_margin"] = d["net_income"] / d["revenue"] * 100
    else:
        d["net_margin"] = None

    # ROE = Net Income / avg Equity
    eq_prev = equity.get(y - 1)
    eq_curr = equity.get(y)
    if d["net_income"] and eq_prev and eq_curr:
        avg_eq = (eq_prev + eq_curr) / 2
        d["roe"] = d["net_income"] / avg_eq * 100
    else:
        d["roe"] = None

    # ROA = Net Income / avg Assets
    a_prev = assets.get(y - 1)
    a_curr = assets.get(y)
    if d["net_income"] and a_prev and a_curr:
        avg_a = (a_prev + a_curr) / 2
        d["roa"] = d["net_income"] / avg_a * 100
    else:
        d["roa"] = None

    # Debt ratio = Liabilities / Equity * 100
    if d["liabilities"] and d["equity"] and d["equity"] != 0:
        d["debt_ratio"] = d["liabilities"] / d["equity"] * 100
    else:
        d["debt_ratio"] = None

    # Retention ratio = (Equity - CS_APIC) / CS_APIC * 100
    # For US companies this is (Retained Earnings + AOCI) / paid-in capital
    if d["equity"] and d["cs_apic"] and d["cs_apic"] != 0:
        d["retention"] = (d["equity"] - d["cs_apic"]) / d["cs_apic"] * 100
    else:
        d["retention"] = None

    # BPS = Equity / Shares Outstanding
    if d["equity"] and d["shares"] and d["shares"] != 0:
        d["bps"] = d["equity"] / d["shares"]
    else:
        d["bps"] = None

    # PER and PBR - need stock price; derive from public float or skip
    # We'll use Entity Public Float data from DEI as approximation
    d["per"] = None  # Will compute below
    d["pbr"] = None

    # Div yield and payout
    d["div_yield"] = None
    d["payout"] = None

    annual_data[y] = d

# Stock price estimation from BPS and market data
# Entity Public Float (mid-year): approximate market cap
# 2021 mid: $1,451B, 2022 mid: $1,256B, 2023 mid: $1,331B, 2024 mid: $2,000B, 2025 mid: $1,900B
dei_data = data["facts"]["dei"]
epf = dei_data.get("EntityPublicFloat", {}).get("units", {}).get("USD", [])
public_float = {}
for e in epf:
    if "frame" in e:
        frame = e["frame"]
        if "Q2I" in frame:
            year = int(frame[2:6])
            public_float[year] = e["val"]

# For PER/PBR/DivYield, we need year-end stock price
# Approximate: use public float / shares at that time as mid-year price proxy
# Then for year-end, we don't have exact data. We'll mark as "-" for precision
# Actually let's compute PER from mid-year-ish market cap / net income
# This is imprecise so let's just put "-" for PER/PBR/DivYield as we can't get exact year-end prices from EDGAR

# Market cap for display: use latest public float from 10-K
# FY2025 10-K reports public float at 2025-06-30 = $1,900B
# Let's use 1,900,000 ($M) as approximate
MCAP_DISPLAY = "1,900,000"

# ============================================================
# 5. HTML generation (same template as gen_us_financial.py)
# ============================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, 'Malgun Gothic', sans-serif; background: #fff; }}
  .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  table {{ font-size: 13px; word-break: keep-all; overflow-wrap: normal; }}
  td {{ padding: 4px 8px; border: 1px solid #ddd; white-space: nowrap; }}
  tr:nth-child(even) {{ background-color: #f9f9f9; }}
  tr:nth-child(-n+2) {{ background-color: #4a4a4a; }}
  tr:nth-child(-n+2) td {{ font-weight: bold; color: #ffffff; }}
</style>
</head>
<body>
<div class="table-wrap">
<table style="background-color: #ffffff; color: #3c3c3c; text-align: left; border-collapse: collapse; width: 100%; word-break: keep-all; overflow-wrap: normal;" border="1" data-ke-align="alignLeft" data-ke-style="style12">
<tbody>
{rows}
</tbody>
</table>
</div>
</body>
</html>"""

W1 = "25.5814"
W2 = "14.8837"

def hdr_row(label, value):
    return (
        f'<tr style="background-color: #4a4a4a;">\n'
        f'<td style="text-align: right; width: {W1}%; font-weight: bold; color: #ffffff;">'
        f'<span style="color: #ffffff;">{label}</span></td>\n'
        f'<td style="text-align: right; width: 74.4186%; font-weight: bold; color: #ffffff;" colspan="5">'
        f'<span style="color: #ffffff;"><b>{value}</b></span></td>\n'
        f'</tr>'
    )

def year_row(label, periods):
    cells = ""
    for p in periods:
        cells += (
            f'<td style="text-align: right; width: {W2}%; font-weight: bold; color: #ffffff;">'
            f'<span style="color: #ffffff;">{p}</span></td>'
        )
    return (
        f'<tr style="background-color: #4a4a4a;">\n'
        f'<td style="text-align: right; width: {W1}%; font-weight: bold; color: #ffffff;">'
        f'<span style="color: #ffffff;">{label}</span></td>\n'
        f'{cells}\n'
        f'</tr>'
    )

def data_row(label, values):
    cells = ""
    for v in values:
        s = str(v)
        if s == "-":
            color = "#000000"
        elif s.startswith("-") and s != "-":
            color = "#ff0000"
        else:
            color = "#000000"
        cells += (
            f'<td style="text-align: right; width: {W2}%;">'
            f'<span style="color: {color};">{s}</span></td>'
        )
    return (
        f'<tr>\n'
        f'<td style="text-align: right; width: {W1}%;">'
        f'<span style="color: #000000;">{label}</span></td>\n'
        f'{cells}\n'
        f'</tr>'
    )

def build_html(mcap_label, mcap_value, key_label, periods, items):
    rows = []
    rows.append(hdr_row(mcap_label, mcap_value))
    rows.append(year_row(key_label, periods))
    for label, values in items:
        rows.append(data_row(label, values))
    return HTML_TEMPLATE.format(rows="\n".join(rows))

# ============================================================
# 6. Build annual table
# ============================================================
year_labels = [f"{y}/12" for y in YEARS]

def av(key):
    """Get annual values list for a key."""
    return [annual_data[y].get(key) for y in YEARS]

annual_items = [
    ("매출액",             [fmt_m(annual_data[y]["revenue"]) for y in YEARS]),
    ("영업이익",           [fmt_m(annual_data[y]["op_income"]) for y in YEARS]),
    ("영업이익(발표기준)", [fmt_m(annual_data[y]["op_income"]) for y in YEARS]),
    ("세전계속사업이익",   [fmt_m(annual_data[y]["pretax"]) for y in YEARS]),
    ("당기순이익",         [fmt_m(annual_data[y]["net_income"]) for y in YEARS]),
    ("당기순이익(지배)",   [fmt_m(annual_data[y]["net_income"]) for y in YEARS]),  # No NCI
    ("당기순이익(비지배)", ["0" for _ in YEARS]),
    ("자산총계",           [fmt_m(annual_data[y]["assets"]) for y in YEARS]),
    ("부채총계",           [fmt_m(annual_data[y]["liabilities"]) for y in YEARS]),
    ("자본총계",           [fmt_m(annual_data[y]["equity"]) for y in YEARS]),
    ("자본총계(지배)",     [fmt_m(annual_data[y]["equity"]) for y in YEARS]),  # No NCI
    ("자본총계(비지배)",   ["0" for _ in YEARS]),
    ("자본금",             [fmt_m(annual_data[y]["cs_apic"]) for y in YEARS]),
    ("영업활동현금흐름",   [fmt_m(annual_data[y]["op_cf"]) for y in YEARS]),
    ("투자활동현금흐름",   [fmt_m(annual_data[y]["inv_cf"]) for y in YEARS]),
    ("재무활동현금흐름",   [fmt_m(annual_data[y]["fin_cf"]) for y in YEARS]),
    ("CAPEX",              [fmt_m(annual_data[y]["capex"]) for y in YEARS]),
    ("FCF",                [fmt_m(annual_data[y]["fcf"]) for y in YEARS]),
    ("이자발생부채",       [fmt_m(annual_data[y]["ibd"]) for y in YEARS]),
    ("영업이익률",         [fmt_pct(annual_data[y]["op_margin"]) for y in YEARS]),
    ("순이익률",           [fmt_pct(annual_data[y]["net_margin"]) for y in YEARS]),
    ("ROE(%)",             [fmt_pct(annual_data[y]["roe"]) for y in YEARS]),
    ("ROA(%)",             [fmt_pct(annual_data[y]["roa"]) for y in YEARS]),
    ("부채비율",           [fmt_pct(annual_data[y]["debt_ratio"]) for y in YEARS]),
    ("자본유보율",         [fmt_pct(annual_data[y]["retention"]) for y in YEARS]),
    ("EPS($)",             [fmt_dollar(annual_data[y]["eps"]) for y in YEARS]),
    ("PER(배)",            ["-" for _ in YEARS]),
    ("BPS($)",             [fmt_dollar(annual_data[y]["bps"]) for y in YEARS]),
    ("PBR(배)",            ["-" for _ in YEARS]),
    ("현금DPS($)",         [fmt_dollar(annual_data[y]["dps"]) if annual_data[y]["dps"] else "-" for y in YEARS]),
    ("현금배당수익률",     ["-" for _ in YEARS]),
    ("현금배당성향(%)",    ["-" if not annual_data[y]["dps"] or not annual_data[y]["eps"] else fmt_pct(annual_data[y]["dps"] / annual_data[y]["eps"] * 100) for y in YEARS]),
    ("발행주식수(보통주)", [fmt_shares(annual_data[y]["shares"]) for y in YEARS]),
]

annual_html = build_html(
    "시가총액 ($M)", MCAP_DISPLAY,
    "주요 재무 정보 ($M)", year_labels,
    annual_items,
)

# ============================================================
# 7. Build quarterly table
# ============================================================
# Quarters: 2024/Q4, 2025/Q1, 2025/Q2, 2025/Q3, 2025/Q4
Q_LABELS = ["2024/12", "2025/03", "2025/06", "2025/09", "2025/12"]

# --- Quarterly revenue ---
# Q4 2024 = annual 2024 - Q1 - Q2 - Q3
rev_q = get_quarterly_flow("Revenues")
rev_q2 = get_quarterly_flow("RevenueFromContractWithCustomerExcludingAssessedTax")

q_rev = {
    "2024/12": 350018000000 - 80539000000 - 84742000000 - 88268000000,  # 96,469M
    "2025/03": 90234000000,  # from RevenueFromContract CY2025Q1
    "2025/06": 96428000000,  # Revenues CY2025Q2
    "2025/09": 102346000000, # Revenues CY2025Q3
    "2025/12": 402836000000 - 90234000000 - 96428000000 - 102346000000,  # 113,828M
}

# --- Quarterly Operating Income ---
q_oi = {
    "2024/12": 112390000000 - 25472000000 - 27425000000 - 28521000000,  # 30,972M
    "2025/03": 30606000000,
    "2025/06": 31271000000,
    "2025/09": 31228000000,
    "2025/12": 129039000000 - 30606000000 - 31271000000 - 31228000000,  # 35,934M
}

# --- Quarterly Pre-tax Income ---
q_pretax = {
    "2024/12": 119815000000 - 28315000000 - 27551000000 - 31706000000,  # 32,243M
    "2025/03": 41789000000,
    "2025/06": 33933000000,
    "2025/09": 43987000000,
    "2025/12": 158826000000 - 41789000000 - 33933000000 - 43987000000,  # 39,117M
}

# --- Quarterly Net Income ---
q_ni = {
    "2024/12": 100118000000 - 23662000000 - 23619000000 - 26301000000,  # 26,536M
    "2025/03": 34540000000,
    "2025/06": 28196000000,
    "2025/09": 34979000000,
    "2025/12": 132170000000 - 34540000000 - 28196000000 - 34979000000,  # 34,455M
}

# --- Quarterly Balance Sheet (instant) ---
q_assets = {
    "2024/12": 450256000000,
    "2025/03": 475374000000,
    "2025/06": 502053000000,
    "2025/09": 536469000000,
    "2025/12": 595281000000,
}

q_liab = {
    "2024/12": 125172000000,
    "2025/03": 130107000000,
    "2025/06": 139137000000,
    "2025/09": 149602000000,
    "2025/12": 180016000000,
}

q_equity = {
    "2024/12": 325084000000,
    "2025/03": 345267000000,
    "2025/06": 362916000000,
    "2025/09": 386867000000,
    "2025/12": 415265000000,
}

q_csapic = {
    "2024/12": 84800000000,
    "2025/03": 86725000000,
    "2025/06": 89283000000,
    "2025/09": 91695000000,
    "2025/12": 93126000000,
}

# --- Quarterly Cash Flows (derived from cumulative) ---
# Operating CF cumulative: Q1=28,848B (2024), H1=55,488B, 9M=86,186B, FY=125,299B
# 2025: Q1=36,150B, H1=63,897B, 9M=112,311B, FY=164,713B
q_opcf = {
    "2024/12": (125299 - 86186) * 1_000_000,   # 39,113M
    "2025/03": 36150 * 1_000_000,               # 36,150M
    "2025/06": (63897 - 36150) * 1_000_000,     # 27,747M
    "2025/09": (112311 - 63897) * 1_000_000,    # 48,414M
    "2025/12": (164713 - 112311) * 1_000_000,   # 52,402M
}

q_invcf = {
    "2024/12": (-45536 - (-29356)) * 1_000_000,  # -16,180M
    "2025/03": -16194 * 1_000_000,                # -16,194M
    "2025/06": (-40738 - (-16194)) * 1_000_000,   # -24,544M
    "2025/09": (-68515 - (-40738)) * 1_000_000,   # -27,777M
    "2025/12": (-120291 - (-68515)) * 1_000_000,  # -51,776M
}

q_fincf = {
    "2024/12": (-79733 - (-60697)) * 1_000_000,  # -19,036M
    "2025/03": -20201 * 1_000_000,                # -20,201M
    "2025/06": (-26033 - (-20201)) * 1_000_000,   # -5,832M
    "2025/09": (-44416 - (-26033)) * 1_000_000,   # -18,383M
    "2025/12": (-37388 - (-44416)) * 1_000_000,   # 7,028M
}

q_capex = {
    "2024/12": (52535 - 38259) * 1_000_000,      # 14,276M
    "2025/03": 17197 * 1_000_000,                 # 17,197M
    "2025/06": (39643 - 17197) * 1_000_000,       # 22,446M
    "2025/09": (63596 - 39643) * 1_000_000,       # 23,953M
    "2025/12": (91447 - 63596) * 1_000_000,       # 27,851M
}

# FCF quarterly
q_fcf = {q: q_opcf[q] - q_capex[q] for q in Q_LABELS}

# --- Quarterly interest-bearing debt ---
# DebtInstrumentCarryingAmount + CommercialPaper
q_ibd = {
    "2024/12": 12000000000 + 2300000000,     # 14,300M
    "2025/03": 12000000000 + 2500000000,     # 14,500M
    "2025/06": 24903000000 + 3000000000,     # 27,903M
    "2025/09": 23892000000 + 3000000000,     # 26,892M
    "2025/12": 49085000000 + 0,              # 49,085M
}

# --- Quarterly EPS ---
q_eps = {
    "2024/12": round(8.04 - 1.89 - 1.89 - 2.12, 2),  # 2.14
    "2025/03": 2.81,
    "2025/06": 2.31,
    "2025/09": 2.87,
    "2025/12": round(10.81 - 2.81 - 2.31 - 2.87, 2),  # 2.82
}

# --- Quarterly Shares ---
q_shares = {
    "2024/12": 12211000000,
    "2025/03": 12155000000,
    "2025/06": 12104000000,
    "2025/09": 12077000000,
    "2025/12": 12088000000,
}

# --- Quarterly DPS ---
# Q1 2024 = 0 (first dividend Q2 2024), Q2 2024 = 0.20, Q3 2024 = 0.20
# Q4 2024 = 0.60 - 0.40 = 0.20
# Q1 2025 = 0.20, Q2 2025 = 0.21, Q3 2025 = 0.21, Q4 2025 = 0.83 - 0.62 = 0.21
q_dps = {
    "2024/12": 0.20,
    "2025/03": 0.20,
    "2025/06": 0.21,
    "2025/09": 0.21,
    "2025/12": 0.21,
}

# --- Quarterly derived ratios ---
def q_op_margin(q):
    if q_rev[q] and q_oi[q]:
        return q_oi[q] / q_rev[q] * 100
    return None

def q_net_margin(q):
    if q_rev[q] and q_ni[q]:
        return q_ni[q] / q_rev[q] * 100
    return None

def q_debt_ratio(q):
    if q_liab[q] and q_equity[q] and q_equity[q] != 0:
        return q_liab[q] / q_equity[q] * 100
    return None

def q_retention(q):
    if q_equity[q] and q_csapic[q] and q_csapic[q] != 0:
        return (q_equity[q] - q_csapic[q]) / q_csapic[q] * 100
    return None

quarterly_items = [
    ("매출액",             [fmt_m(q_rev[q]) for q in Q_LABELS]),
    ("영업이익",           [fmt_m(q_oi[q]) for q in Q_LABELS]),
    ("영업이익(발표기준)", [fmt_m(q_oi[q]) for q in Q_LABELS]),
    ("세전계속사업이익",   [fmt_m(q_pretax[q]) for q in Q_LABELS]),
    ("당기순이익",         [fmt_m(q_ni[q]) for q in Q_LABELS]),
    ("당기순이익(지배)",   [fmt_m(q_ni[q]) for q in Q_LABELS]),
    ("당기순이익(비지배)", ["0" for _ in Q_LABELS]),
    ("자산총계",           [fmt_m(q_assets[q]) for q in Q_LABELS]),
    ("부채총계",           [fmt_m(q_liab[q]) for q in Q_LABELS]),
    ("자본총계",           [fmt_m(q_equity[q]) for q in Q_LABELS]),
    ("자본총계(지배)",     [fmt_m(q_equity[q]) for q in Q_LABELS]),
    ("자본총계(비지배)",   ["0" for _ in Q_LABELS]),
    ("자본금",             [fmt_m(q_csapic[q]) for q in Q_LABELS]),
    ("영업활동현금흐름",   [fmt_m(q_opcf[q]) for q in Q_LABELS]),
    ("투자활동현금흐름",   [fmt_m(q_invcf[q]) for q in Q_LABELS]),
    ("재무활동현금흐름",   [fmt_m(q_fincf[q]) for q in Q_LABELS]),
    ("CAPEX",              [fmt_m(q_capex[q]) for q in Q_LABELS]),
    ("FCF",                [fmt_m(q_fcf[q]) for q in Q_LABELS]),
    ("이자발생부채",       [fmt_m(q_ibd[q]) for q in Q_LABELS]),
    ("영업이익률",         [fmt_pct(q_op_margin(q)) for q in Q_LABELS]),
    ("순이익률",           [fmt_pct(q_net_margin(q)) for q in Q_LABELS]),
    ("ROE(%)",             ["-" for _ in Q_LABELS]),
    ("ROA(%)",             ["-" for _ in Q_LABELS]),
    ("부채비율",           [fmt_pct(q_debt_ratio(q)) for q in Q_LABELS]),
    ("자본유보율",         [fmt_pct(q_retention(q)) for q in Q_LABELS]),
    ("EPS($)",             [fmt_dollar(q_eps[q]) for q in Q_LABELS]),
    ("PER(배)",            ["-" for _ in Q_LABELS]),
    ("BPS($)",             ["-" for _ in Q_LABELS]),
    ("PBR(배)",            ["-" for _ in Q_LABELS]),
    ("현금DPS($)",         [fmt_dollar(q_dps[q]) for q in Q_LABELS]),
    ("현금배당수익률",     ["-" for _ in Q_LABELS]),
    ("현금배당성향(%)",    ["-" for _ in Q_LABELS]),
    ("발행주식수(보통주)", [fmt_shares(q_shares[q]) for q in Q_LABELS]),
]

quarterly_html = build_html(
    "시가총액 ($M)", MCAP_DISPLAY,
    "주요 재무 정보 ($M)", Q_LABELS,
    quarterly_items,
)

# ============================================================
# 8. Write output files
# ============================================================
OUT_DIR = pathlib.Path(__file__).resolve().parent.parent

files = {
    "google_financial.html": annual_html,
    "google_financial_q.html": quarterly_html,
}

for fname, content in files.items():
    path = OUT_DIR / fname
    path.write_text(content, encoding="utf-8")
    print(f"[OK] {fname} written ({len(content):,} bytes)")

print("\nGoogle (Alphabet) financial tables generated from EDGAR data.")

import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import yfinance as yf

BASE = r'C:\Users\riseo\Cluade Test\stock-charts'

# ===== ERO Copper Financial Data (USD Millions) =====
# Source: StockAnalysis.com, company earnings releases

# Annual data (5 years: 2021-2025)
annual_years = ['2021/12', '2022/12', '2023/12', '2024/12', '2025/12']
annual = {
    'revenue':       [489.92, 426.39, 427.48, 470.26, 785.84],
    'op_income':     [272.16, 129.79, 95.20, 108.92, 270.60],
    'op_income_rep': [272.16, 129.79, 95.20, 108.92, 270.60],
    'pretax':        [236.92, 126.38, 112.35, -75.44, 330.96],
    'net_income':    [201.05, 101.83, 92.80, -67.80, 266.90],
    'ni_parent':     [201.05, 101.83, 92.80, -68.48, 263.72],
    'ni_nci':        [None, None, None, None, None],  # minimal NCI
    'total_assets':  [690, 1188, 1512, 1458, 1924],
    'total_liab':    [294, 646, 702, 867, 986],
    'total_equity':  [395, 542, 809, 591, 938],
    'eq_parent':     [393, 539, 804, 587, 936],
    'eq_nci':        [2, 4, 5, 4, 2],
    'share_capital': [133, 148, 271, 287, 298],
    'op_cf':         [364.59, 143.39, 163.10, 145.42, 395.14],
    'inv_cf':        [-179.53, -425.81, -308.17, -335.38, -278.59],
    'fin_cf':        [-115.43, 327.30, 77.75, 131.16, -59.73],
    'capex':         [181.83, 295.82, 460.65, 337.59, 282.44],
    'shares_out':    [90.96, 92.17, 94.90, 103.11, 104.13],  # diluted, millions
}

# Quarterly data (5 quarters: Q4 2024 ~ Q4 2025)
quarter_periods = ['2024/Q4', '2025/Q1', '2025/Q2', '2025/Q3', '2025/Q4']
quarterly = {
    'revenue':       [122.54, 125.09, 163.51, 177.09, 320.15],
    'op_income':     [45.39, 42.98, 47.97, 38.08, 141.58],
    'op_income_rep': [45.39, 42.98, 47.97, 38.08, 141.58],
    'pretax':        [-54.79, 95.37, 84.11, 49.29, 102.19],
    'net_income':    [-48.94, 80.23, 70.55, 35.98, 76.97],
    'ni_parent':     [-48.94, 80.23, 70.55, 35.98, 76.97],
    'ni_nci':        [None, None, None, None, None],
    'total_assets':  [1458, 1686, 1772, 1876, 1924],
    'total_liab':    [867, 967, 943, 985, 986],
    'total_equity':  [591, 719, 829, 892, 938],
    'eq_parent':     [587, 714, 823, 885, 936],
    'eq_nci':        [4, 5, 6, 6, 2],
    'share_capital': [287, 287, 287, 291, 298],
    'op_cf':         [60.80, 65.44, 90.26, 110.31, 129.13],
    'inv_cf':        [-76.39, -59.02, -70.51, -75.84, -73.22],
    'fin_cf':        [48.34, 22.99, -33.58, -30.81, -18.34],
    'capex':         [76.73, 59.54, 71.28, 76.63, 74.99],
    'int_debt':      [620, 665, 653, 638, 632],
    'shares_out':    [103.88, 103.90, 103.91, 104.04, 104.71],  # diluted, millions
    'eps':           [-0.47, 0.77, 0.68, 0.35, 0.73],
}

# Get year-end stock prices for PER/PBR calculation
print("Fetching year-end prices from yfinance...")
stock = yf.Ticker('ERO')
hist = stock.history(period='max', interval='1d')

def get_yearend_price(year):
    """Get the closing price on the last trading day of the year."""
    year_data = hist[hist.index.year == year]
    if year_data.empty:
        return None
    return year_data['Close'].iloc[-1]

yearend_prices = {}
for y in [2021, 2022, 2023, 2024, 2025]:
    p = get_yearend_price(y)
    yearend_prices[y] = p
    print(f"  {y} year-end price: ${p:.2f}" if p else f"  {y} year-end price: N/A")

# Get current price for quarterly PER/PBR
current_price = hist['Close'].iloc[-1] if not hist.empty else None
print(f"  Current price: ${current_price:.2f}" if current_price else "  Current price: N/A")

# Get market cap from yfinance
try:
    info = stock.info
    market_cap = info.get('marketCap', None)
    if market_cap:
        market_cap_m = market_cap / 1_000_000
        print(f"  Market cap: ${market_cap_m:,.0f}M")
except:
    market_cap_m = None

# ===== Computed fields =====

def safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b

def fmt_millions(v):
    """Format value in millions with 1 decimal for small, integer for large."""
    if v is None:
        return '-'
    # Round to nearest million (already in millions)
    rv = round(v)
    if rv < 0:
        return f'<span style="color: #ff0000;">{rv:,}</span>'
    return f'{rv:,}'

def fmt_ratio(v):
    """Format ratio with 1 decimal place."""
    if v is None:
        return '-'
    rv = round(v, 1)
    if rv < 0:
        return f'<span style="color: #ff0000;">{rv:.1f}</span>'
    return f'{rv:.1f}'

def fmt_dollar(v):
    """Format dollar amount (EPS/BPS/DPS) with comma."""
    if v is None:
        return '-'
    rv = round(v, 2)
    if rv < 0:
        return f'<span style="color: #ff0000;">{rv:,.2f}</span>'
    return f'{rv:,.2f}'

def fmt_per_pbr(v):
    """Format PER/PBR with 2 decimal places."""
    if v is None or v < 0:
        return '-'
    return f'{v:.2f}'

def fmt_pct(v):
    """Format percentage with 1 decimal."""
    if v is None:
        return '-'
    rv = round(v, 1)
    if rv < 0:
        return f'<span style="color: #ff0000;">{rv:.1f}</span>'
    return f'{rv:.1f}'

def fmt_shares(v):
    """Format shares in millions."""
    if v is None:
        return '-'
    return f'{v:,.2f}'

def fmt_int(v):
    """Format integer with comma."""
    if v is None:
        return '-'
    rv = round(v)
    if rv < 0:
        return f'<span style="color: #ff0000;">{rv:,}</span>'
    return f'{rv:,}'


# ===== Generate Annual HTML =====
def gen_annual_html():
    rows_data = []
    for i in range(5):
        year = 2021 + i
        rev = annual['revenue'][i]
        op = annual['op_income'][i]
        op_rep = annual['op_income_rep'][i]
        pretax = annual['pretax'][i]
        ni = annual['net_income'][i]
        ni_p = annual['ni_parent'][i]
        ni_nci = annual['ni_nci'][i]
        ta = annual['total_assets'][i]
        tl = annual['total_liab'][i]
        te = annual['total_equity'][i]
        eq_p = annual['eq_parent'][i]
        eq_nci = annual['eq_nci'][i]
        sc = annual['share_capital'][i]
        ocf = annual['op_cf'][i]
        icf = annual['inv_cf'][i]
        fcf_fin = annual['fin_cf'][i]
        capex = annual['capex'][i]
        shares = annual['shares_out'][i]

        fcf = ocf - capex if ocf is not None and capex is not None else None
        int_debt_val = tl  # using total debt from balance sheet data
        # Actually use the total debt from search: 66, 429, 446, 620, 632
        int_debts = [66, 429, 446, 620, 632]
        int_debt_val = int_debts[i]

        op_margin = safe_div(op, rev) * 100 if op is not None and rev is not None else None
        ni_margin = safe_div(ni, rev) * 100 if ni is not None and rev is not None else None
        roe = safe_div(ni_p, eq_p) * 100 if ni_p is not None and eq_p is not None else None
        roa = safe_div(ni, ta) * 100 if ni is not None and ta is not None else None
        debt_ratio = safe_div(tl, te) * 100 if tl is not None and te is not None else None
        # Capital reserve ratio - (equity_parent - share_capital) / share_capital * 100
        cap_reserve = safe_div((eq_p - sc), sc) * 100 if eq_p is not None and sc is not None and sc != 0 else None

        eps = safe_div(ni_p, shares) if ni_p is not None and shares is not None else None
        bps = safe_div(eq_p, shares) if eq_p is not None and shares is not None else None

        yep = yearend_prices.get(year)
        per = safe_div(yep, eps) if yep is not None and eps is not None and eps > 0 else None
        pbr = safe_div(yep, bps) if yep is not None and bps is not None and bps > 0 else None

        rows_data.append({
            'revenue': fmt_millions(rev),
            'op_income': fmt_millions(op),
            'op_income_rep': fmt_millions(op_rep),
            'pretax': fmt_millions(pretax),
            'net_income': fmt_millions(ni),
            'ni_parent': fmt_millions(ni_p),
            'ni_nci': fmt_millions(ni_nci),
            'total_assets': fmt_millions(ta),
            'total_liab': fmt_millions(tl),
            'total_equity': fmt_millions(te),
            'eq_parent': fmt_millions(eq_p),
            'eq_nci': fmt_millions(eq_nci),
            'share_capital': fmt_millions(sc),
            'op_cf': fmt_millions(ocf),
            'inv_cf': fmt_millions(icf),
            'fin_cf': fmt_millions(fcf_fin),
            'capex': fmt_millions(capex),
            'fcf': fmt_millions(fcf),
            'int_debt': fmt_millions(int_debt_val),
            'op_margin': fmt_ratio(op_margin),
            'ni_margin': fmt_ratio(ni_margin),
            'roe': fmt_ratio(roe),
            'roa': fmt_ratio(roa),
            'debt_ratio': fmt_ratio(debt_ratio),
            'cap_reserve': fmt_int(cap_reserve),
            'eps': fmt_dollar(eps),
            'per': fmt_per_pbr(per),
            'bps': fmt_dollar(bps),
            'pbr': fmt_per_pbr(pbr),
            'dps': '-',
            'div_yield': '-',
            'payout': '-',
            'shares': fmt_shares(shares),
        })

    return rows_data

def gen_quarter_html():
    rows_data = []
    for i in range(5):
        rev = quarterly['revenue'][i]
        op = quarterly['op_income'][i]
        op_rep = quarterly['op_income_rep'][i]
        pretax = quarterly['pretax'][i]
        ni = quarterly['net_income'][i]
        ni_p = quarterly['ni_parent'][i]
        ni_nci = quarterly['ni_nci'][i]
        ta = quarterly['total_assets'][i]
        tl = quarterly['total_liab'][i]
        te = quarterly['total_equity'][i]
        eq_p = quarterly['eq_parent'][i]
        eq_nci = quarterly['eq_nci'][i]
        sc = quarterly['share_capital'][i]
        ocf = quarterly['op_cf'][i]
        icf = quarterly['inv_cf'][i]
        fcf_fin = quarterly['fin_cf'][i]
        capex = quarterly['capex'][i]
        shares = quarterly['shares_out'][i]
        int_debt_val = quarterly['int_debt'][i]

        fcf = ocf - capex if ocf is not None and capex is not None else None

        op_margin = safe_div(op, rev) * 100 if op is not None and rev is not None else None
        ni_margin = safe_div(ni, rev) * 100 if ni is not None and rev is not None else None
        roe = safe_div(ni_p, eq_p) * 100 if ni_p is not None and eq_p is not None else None
        roa = safe_div(ni, ta) * 100 if ni is not None and ta is not None else None
        debt_ratio = safe_div(tl, te) * 100 if tl is not None and te is not None else None
        cap_reserve = safe_div((eq_p - sc), sc) * 100 if eq_p is not None and sc is not None and sc != 0 else None

        eps_val = quarterly['eps'][i]
        bps = safe_div(eq_p, shares) if eq_p is not None and shares is not None else None

        rows_data.append({
            'revenue': fmt_millions(rev),
            'op_income': fmt_millions(op),
            'op_income_rep': fmt_millions(op_rep),
            'pretax': fmt_millions(pretax),
            'net_income': fmt_millions(ni),
            'ni_parent': fmt_millions(ni_p),
            'ni_nci': fmt_millions(ni_nci),
            'total_assets': fmt_millions(ta),
            'total_liab': fmt_millions(tl),
            'total_equity': fmt_millions(te),
            'eq_parent': fmt_millions(eq_p),
            'eq_nci': fmt_millions(eq_nci),
            'share_capital': fmt_millions(sc),
            'op_cf': fmt_millions(ocf),
            'inv_cf': fmt_millions(icf),
            'fin_cf': fmt_millions(fcf_fin),
            'capex': fmt_millions(capex),
            'fcf': fmt_millions(fcf),
            'int_debt': fmt_millions(int_debt_val),
            'op_margin': fmt_ratio(op_margin),
            'ni_margin': fmt_ratio(ni_margin),
            'roe': fmt_ratio(roe),
            'roa': fmt_ratio(roa),
            'debt_ratio': fmt_ratio(debt_ratio),
            'cap_reserve': fmt_int(cap_reserve),
            'eps': fmt_dollar(eps_val),
            'per': '-',
            'bps': fmt_dollar(bps),
            'pbr': '-',
            'dps': '-',
            'div_yield': '-',
            'payout': '-',
            'shares': fmt_shares(shares),
        })
    return rows_data


# Market cap string
if market_cap_m:
    mktcap_str = f"${market_cap_m:,.0f}M"
else:
    mktcap_str = "-"

ROW_LABELS = [
    ('revenue', 'Revenue (M$)'),
    ('op_income', 'Operating Income (M$)'),
    ('op_income_rep', 'Operating Income (Reported)'),
    ('pretax', 'Pretax Income (M$)'),
    ('net_income', 'Net Income (M$)'),
    ('ni_parent', 'Net Income (Parent)'),
    ('ni_nci', 'Net Income (NCI)'),
    ('total_assets', 'Total Assets (M$)'),
    ('total_liab', 'Total Liabilities (M$)'),
    ('total_equity', 'Total Equity (M$)'),
    ('eq_parent', 'Equity (Parent)'),
    ('eq_nci', 'Equity (NCI)'),
    ('share_capital', 'Share Capital (M$)'),
    ('op_cf', 'Operating Cash Flow (M$)'),
    ('inv_cf', 'Investing Cash Flow (M$)'),
    ('fin_cf', 'Financing Cash Flow (M$)'),
    ('capex', 'CAPEX (M$)'),
    ('fcf', 'FCF (M$)'),
    ('int_debt', 'Interest-Bearing Debt (M$)'),
    ('op_margin', 'Operating Margin (%)'),
    ('ni_margin', 'Net Margin (%)'),
    ('roe', 'ROE (%)'),
    ('roa', 'ROA (%)'),
    ('debt_ratio', 'Debt Ratio (%)'),
    ('cap_reserve', 'Capital Reserve Ratio'),
    ('eps', 'EPS ($)'),
    ('per', 'PER (x)'),
    ('bps', 'BPS ($)'),
    ('pbr', 'PBR (x)'),
    ('dps', 'DPS ($)'),
    ('div_yield', 'Dividend Yield (%)'),
    ('payout', 'Payout Ratio (%)'),
    ('shares', 'Shares Outstanding (M)'),
]


def build_html(periods, rows_data, is_annual=True):
    ncols = len(periods)
    # Column widths
    first_w = 25.5814
    remaining = (100 - first_w) / ncols

    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html lang="ko">')
    lines.append('<head>')
    lines.append('<meta charset="UTF-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append('<style>')
    lines.append('  * { margin: 0; padding: 0; box-sizing: border-box; }')
    lines.append("  body { font-family: -apple-system, 'Malgun Gothic', sans-serif; background: #fff; }")
    lines.append('  .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }')
    lines.append('  table { font-size: 13px; word-break: keep-all; overflow-wrap: normal; }')
    lines.append('  td { padding: 4px 8px; border: 1px solid #ddd; white-space: nowrap; }')
    lines.append('  tr:nth-child(even) { background-color: #f9f9f9; }')
    lines.append('  tr:nth-child(-n+2) { background-color: #4a4a4a; }')
    lines.append('  tr:nth-child(-n+2) td { font-weight: bold; color: #ffffff; }')
    lines.append('</style>')
    lines.append('</head>')
    lines.append('<body>')
    lines.append('<div class="table-wrap">')
    lines.append(f'<table style="background-color: #ffffff; color: #3c3c3c; text-align: left; border-collapse: collapse; width: 100%; word-break: keep-all; overflow-wrap: normal;" border="1" data-ke-align="alignLeft" data-ke-style="style12">')
    lines.append('<tbody>')

    # Market cap row
    lines.append('<tr style="background-color: #4a4a4a;">')
    lines.append(f'<td style="text-align: right; width: {first_w}%; font-weight: bold; color: #ffffff;"><span style="color: #ffffff;">Market Cap</span></td>')
    lines.append(f'<td style="text-align: right; width: {remaining * ncols:.4f}%; font-weight: bold; color: #ffffff;" colspan="{ncols}"><span style="color: #ffffff;"><b>{mktcap_str}</b></span></td>')
    lines.append('</tr>')

    # Header row (periods)
    lines.append('<tr style="background-color: #4a4a4a;">')
    lines.append(f'<td style="text-align: right; width: {first_w}%; font-weight: bold; color: #ffffff;"><span style="color: #ffffff;">Key Financial Data (USD)</span></td>')
    for p in periods:
        lines.append(f'<td style="text-align: right; width: {remaining:.4f}%; font-weight: bold; color: #ffffff;"><span style="color: #ffffff;">{p}</span></td>')
    lines.append('</tr>')

    # Data rows
    for key, label in ROW_LABELS:
        lines.append('<tr>')
        lines.append(f'<td style="text-align: right; width: {first_w}%;"><span style="color: #000000;">{label}</span></td>')
        for j in range(ncols):
            val = rows_data[j][key]
            lines.append(f'<td style="text-align: right; width: {remaining:.4f}%;"><span style="color: #000000;">{val}</span></td>')
        lines.append('</tr>')

    lines.append('</tbody>')
    lines.append('</table>')
    lines.append('</div>')
    lines.append('</body>')
    lines.append('</html>')

    return '\n'.join(lines)


# Generate annual
annual_rows = gen_annual_html()
annual_html = build_html(annual_years, annual_rows, is_annual=True)
annual_path = os.path.join(BASE, 'erocopper_financial.html')
with open(annual_path, 'w', encoding='utf-8') as f:
    f.write(annual_html)
print(f"Annual financial table: {annual_path}")
print(f"  File size: {os.path.getsize(annual_path):,} bytes")

# Generate quarterly
quarter_rows = gen_quarter_html()
quarter_html = build_html(quarter_periods, quarter_rows, is_annual=False)
quarter_path = os.path.join(BASE, 'erocopper_financial_q.html')
with open(quarter_path, 'w', encoding='utf-8') as f:
    f.write(quarter_html)
print(f"Quarterly financial table: {quarter_path}")
print(f"  File size: {os.path.getsize(quarter_path):,} bytes")

print("\nDone!")

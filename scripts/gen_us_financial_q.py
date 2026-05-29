"""
Generate standardized US company QUARTERLY financial HTML tables
matching the Korean update_financial.py quarterly output format.
"""

HTML_Q_TEMPLATE = """<!DOCTYPE html>
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

def year_row(label, quarters):
    cells = ""
    for q in quarters:
        cells += (
            f'<td style="text-align: right; width: {W2}%; font-weight: bold; color: #ffffff;">'
            f'<span style="color: #ffffff;">{q}</span></td>'
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

def build_q_html(mcap_label, mcap_value, key_label, quarters, items):
    rows = []
    rows.append(hdr_row(mcap_label, mcap_value))
    rows.append(year_row(key_label, quarters))
    for label, values in items:
        rows.append(data_row(label, values))
    return HTML_Q_TEMPLATE.format(rows="\n".join(rows))

import pathlib
OUT_DIR = pathlib.Path(__file__).resolve().parent.parent

# ============================================================
# 1. Vertiv Holdings (VRT) - Quarterly
# ============================================================
vertiv_q = build_q_html(
    "Market Cap ($M)", "96,568",
    "Key Financials ($M)",
    ["2024/06", "2024/09", "2025/03", "2025/06", "2025/09"],
    [
        ("Revenue",                ["1,953", "2,074", "2,036", "2,638", "2,676"]),
        ("Operating Income",       ["336", "372", "291", "442", "517"]),
        ("Operating Income (Reported)",  ["336", "372", "291", "442", "517"]),
        ("Income Before Tax",         ["265", "268", "265", "421", "492"]),
        ("Net Income",             ["178", "177", "164", "324", "398"]),
        ("Net Income (Parent)",    ["178", "177", "164", "324", "398"]),
        ("Net Income (NCI)",       ["0", "0", "0", "0", "0"]),
        ("Total Assets",           ["8,108", "8,891", "9,451", "10,406", "10,816"]),
        ("Total Liabilities",      ["6,571", "7,078", "6,785", "7,281", "7,308"]),
        ("Total Equity",           ["1,538", "1,814", "2,666", "3,125", "3,509"]),
        ("Equity (Parent)",        ["1,538", "1,814", "2,666", "3,125", "3,509"]),
        ("Equity (NCI)",           ["0", "0", "0", "0", "0"]),
        ("Paid-in Capital",           ["0", "0", "0", "0", "0"]),
        ("Operating CF",           ["-", "-", "303", "-", "-"]),
        ("Investing CF",           ["-", "-", "-39", "-", "-"]),
        ("Financing CF",           ["-", "-", "-25", "-", "-"]),
        ("CAPEX",                  ["34", "36", "36", "45", "45"]),
        ("FCF",                    ["-", "-", "267", "-", "-"]),
        ("Interest-bearing Debt",  ["2,935", "2,931", "2,925", "2,922", "2,918"]),
        ("Op. Margin (%)",         ["17.2", "17.9", "14.3", "16.8", "19.3"]),
        ("Net Margin (%)",         ["9.1", "8.5", "8.1", "12.3", "14.9"]),
        ("ROE (%)",                ["-", "-", "-", "-", "-"]),
        ("ROA (%)",                ["-", "-", "-", "-", "-"]),
        ("Debt Ratio (%)",         ["427.4", "390.2", "254.5", "233.0", "208.3"]),
        ("Capital Reserve Ratio (%)",    ["-", "-", "-", "-", "-"]),
        ("EPS ($)",                ["0.48", "0.47", "0.43", "0.85", "1.04"]),
        ("PER (x)",                ["-", "-", "-", "-", "-"]),
        ("BPS ($)",                ["-", "-", "-", "-", "-"]),
        ("PBR (x)",                ["-", "-", "-", "-", "-"]),
        ("Cash DPS ($)",                ["-", "-", "-", "-", "-"]),
        ("Cash Div. Yield (%)",         ["-", "-", "-", "-", "-"]),
        ("Payout Ratio (%)",       ["-", "-", "-", "-", "-"]),
        ("Shares Outstanding",     ["375,113,127", "375,249,753", "381,001,144", "381,803,828", "382,258,808"]),
    ]
)

# ============================================================
# 2. Freeport-McMoRan (FCX) - Quarterly
# ============================================================
freeport_q = build_q_html(
    "Market Cap ($M)", "53,132",
    "Key Financials ($M)",
    ["2024/12", "2025/03", "2025/06", "2025/09", "2025/12"],
    [
        ("Revenue",                ["5,720", "5,728", "7,582", "6,972", "5,633"]),
        ("Operating Income",       ["1,243", "1,303", "2,432", "1,972", "811"]),
        ("Operating Income (Reported)",  ["1,243", "1,303", "2,432", "1,972", "811"]),
        ("Income Before Tax",         ["1,240", "1,291", "2,391", "1,924", "766"]),
        ("Net Income",             ["721", "793", "1,547", "1,247", "565"]),
        ("Net Income (Parent)",    ["274", "352", "772", "674", "406"]),
        ("Net Income (NCI)",       ["447", "441", "775", "573", "159"]),
        ("Total Assets",           ["54,848", "56,022", "56,492", "56,828", "58,167"]),
        ("Total Liabilities",      ["26,070", "26,808", "26,496", "26,431", "27,401"]),
        ("Total Equity",           ["28,778", "29,214", "29,996", "30,397", "30,766"]),
        ("Equity (Parent)",        ["17,581", "17,688", "18,208", "18,685", "18,899"]),
        ("Equity (NCI)",           ["11,197", "11,526", "11,788", "11,712", "11,867"]),
        ("Paid-in Capital",           ["162", "163", "163", "163", "163"]),
        ("Operating CF",           ["1,436", "1,058", "2,195", "1,664", "693"]),
        ("Investing CF",           ["-1,231", "-1,176", "-1,256", "-1,010", "-1,030"]),
        ("Financing CF",           ["-1,510", "155", "-1,063", "-825", "-143"]),
        ("CAPEX",                  ["1,239", "1,172", "1,261", "1,056", "1,005"]),
        ("FCF",                    ["197", "-114", "934", "608", "-312"]),
        ("Interest-bearing Debt",  ["8,948", "9,404", "9,379", "9,379", "9,379"]),
        ("Op. Margin (%)",         ["21.7", "22.7", "32.1", "28.3", "14.4"]),
        ("Net Margin (%)",         ["12.6", "13.8", "20.4", "17.9", "10.0"]),
        ("ROE (%)",                ["1.6", "2.0", "4.2", "3.6", "2.1"]),
        ("ROA (%)",                ["1.3", "1.4", "2.7", "2.2", "1.0"]),
        ("Debt Ratio (%)",         ["90.6", "91.8", "88.3", "87.0", "89.1"]),
        ("Capital Reserve Ratio (%)",    ["10,753", "10,752", "11,071", "11,363", "11,495"]),
        ("EPS ($)",                ["0.19", "0.24", "0.53", "0.46", "0.28"]),
        ("PER (x)",                ["-", "-", "-", "-", "-"]),
        ("BPS ($)",                ["12.23", "12.32", "12.68", "13.01", "13.16"]),
        ("PBR (x)",                ["-", "-", "-", "-", "-"]),
        ("Cash DPS ($)",                ["0.15", "0.15", "0.15", "0.15", "0.15"]),
        ("Cash Div. Yield (%)",         ["-", "-", "-", "-", "-"]),
        ("Payout Ratio (%)",       ["-", "-", "-", "-", "-"]),
        ("Shares Outstanding",     ["1,437,432,081", "1,436,201,550", "1,436,201,550", "1,436,201,550", "1,436,201,550"]),
    ]
)

# ============================================================
# 3. Ero Copper (ERO) - Quarterly
# ============================================================
erocopper_q = build_q_html(
    "Market Cap ($M)", "2,561",
    "Key Financials ($M)",
    ["2024/12", "2025/03", "2025/06", "2025/09", "2025/12"],
    [
        ("Revenue",                ["123", "125", "164", "177", "320"]),
        ("Operating Income",       ["45", "43", "48", "38", "142"]),
        ("Operating Income (Reported)",  ["45", "43", "48", "38", "142"]),
        ("Income Before Tax",         ["-55", "95", "84", "49", "102"]),
        ("Net Income",             ["-49", "80", "71", "36", "77"]),
        ("Net Income (Parent)",    ["-49", "80", "71", "36", "77"]),
        ("Net Income (NCI)",       ["-", "-", "-", "-", "-"]),
        ("Total Assets",           ["1,458", "1,686", "1,772", "1,876", "1,924"]),
        ("Total Liabilities",      ["867", "967", "943", "985", "986"]),
        ("Total Equity",           ["591", "719", "829", "892", "938"]),
        ("Equity (Parent)",        ["587", "714", "823", "885", "936"]),
        ("Equity (NCI)",           ["4", "5", "6", "6", "2"]),
        ("Paid-in Capital",           ["287", "287", "287", "291", "298"]),
        ("Operating CF",           ["61", "65", "90", "110", "129"]),
        ("Investing CF",           ["-76", "-59", "-71", "-76", "-73"]),
        ("Financing CF",           ["48", "23", "-34", "-31", "-18"]),
        ("CAPEX",                  ["77", "60", "71", "77", "75"]),
        ("FCF",                    ["-16", "6", "19", "34", "54"]),
        ("Interest-bearing Debt",  ["620", "665", "653", "638", "632"]),
        ("Op. Margin (%)",         ["37.0", "34.4", "29.3", "21.5", "44.2"]),
        ("Net Margin (%)",         ["-39.9", "64.1", "43.1", "20.3", "24.0"]),
        ("ROE (%)",                ["-8.3", "11.2", "8.6", "4.1", "8.2"]),
        ("ROA (%)",                ["-3.4", "4.8", "4.0", "1.9", "4.0"]),
        ("Debt Ratio (%)",         ["146.7", "134.5", "113.8", "110.4", "105.1"]),
        ("Capital Reserve Ratio (%)",    ["105", "149", "187", "204", "214"]),
        ("EPS ($)",                ["-0.47", "0.77", "0.68", "0.35", "0.73"]),
        ("PER (x)",                ["-", "-", "-", "-", "-"]),
        ("BPS ($)",                ["5.65", "6.87", "7.92", "8.51", "8.94"]),
        ("PBR (x)",                ["-", "-", "-", "-", "-"]),
        ("Cash DPS ($)",                ["-", "-", "-", "-", "-"]),
        ("Cash Div. Yield (%)",         ["-", "-", "-", "-", "-"]),
        ("Payout Ratio (%)",       ["-", "-", "-", "-", "-"]),
        ("Shares Outstanding",     ["103,880,000", "103,900,000", "103,910,000", "104,040,000", "104,710,000"]),
    ]
)

# ============================================================
# 4. Teck Resources (TECK) - Quarterly (CAD)
# ============================================================
teck_q = build_q_html(
    "Market Cap (CAD M)", "29,201",
    "Key Financials (CAD M)",
    ["2023/12", "2024/03", "2024/06", "2024/09", "2024/12"],
    [
        ("Revenue",                ["2,786", "2,290", "2,023", "3,385", "3,058"]),
        ("Operating Income",       ["160", "325", "262", "496", "349"]),
        ("Operating Income (Reported)",  ["160", "325", "262", "496", "349"]),
        ("Income Before Tax",         ["256", "450", "125", "289", "792"]),
        ("Net Income",             ["399", "370", "206", "281", "544"]),
        ("Net Income (Parent)",    ["258", "313", "101", "133", "525"]),
        ("Net Income (NCI)",       ["141", "57", "105", "148", "19"]),
        ("Total Assets",           ["47,037", "45,893", "42,967", "44,550", "45,436"]),
        ("Total Liabilities",      ["19,941", "18,927", "17,617", "18,745", "19,429"]),
        ("Total Equity",           ["27,096", "26,966", "25,350", "25,805", "26,007"]),
        ("Equity (Parent)",        ["26,077", "25,821", "24,380", "24,923", "25,096"]),
        ("Equity (NCI)",           ["1,019", "1,145", "970", "882", "911"]),
        ("Paid-in Capital",           ["6,441", "6,368", "6,245", "6,218", "6,230"]),
        ("Operating CF",           ["1,288", "-515", "88", "647", "1,259"]),
        ("Investing CF",           ["-552", "-307", "-414", "-526", "-663"]),
        ("Financing CF",           ["-848", "-543", "-819", "-228", "-256"]),
        ("CAPEX",                  ["504", "393", "403", "536", "730"]),
        ("FCF",                    ["784", "-908", "-315", "111", "529"]),
        ("Interest-bearing Debt",  ["9,965", "9,930", "9,419", "9,634", "9,607"]),
        ("Op. Margin (%)",         ["5.7", "14.2", "13.0", "14.7", "11.4"]),
        ("Net Margin (%)",         ["14.3", "16.2", "10.2", "8.3", "17.8"]),
        ("ROE (%)",                ["1.0", "1.2", "0.4", "0.5", "2.1"]),
        ("ROA (%)",                ["0.8", "0.8", "0.5", "0.6", "1.2"]),
        ("Debt Ratio (%)",         ["73.6", "70.2", "69.5", "72.6", "74.7"]),
        ("Capital Reserve Ratio (%)",    ["304.9", "305.5", "290.4", "300.8", "302.8"]),
        ("EPS (CAD)",              ["0.51", "0.63", "0.21", "0.27", "1.07"]),
        ("PER (x)",                ["-", "-", "-", "-", "-"]),
        ("BPS (CAD)",              ["51.50", "51.61", "49.70", "51.08", "51.38"]),
        ("PBR (x)",                ["1.12", "1.29", "1.37", "1.35", "1.05"]),
        ("Cash DPS (CAD)",              ["0.33", "0.33", "0.33", "0.33", "0.33"]),
        ("Cash Div. Yield (%)",         ["2.3", "2.0", "1.9", "1.9", "2.4"]),
        ("Payout Ratio (%)",       ["-", "-", "-", "-", "-"]),
        ("Shares Outstanding",     ["506,000,000", "500,000,000", "491,000,000", "488,000,000", "488,000,000"]),
    ]
)

files = {
    "vertiv_financial_q.html": vertiv_q,
    "freeport_financial_q.html": freeport_q,
    "erocopper_financial_q.html": erocopper_q,
    "teck_financial_q.html": teck_q,
}

for fname, content in files.items():
    path = OUT_DIR / fname
    path.write_text(content, encoding="utf-8")
    print(f"[OK] {fname} written ({len(content):,} bytes)")

print("\nAll 4 US quarterly financial tables regenerated in standard format.")

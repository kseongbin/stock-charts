"""
Generate standardized US company financial HTML tables
matching the Korean update_financial.py output format.
"""

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
    """Market cap header row"""
    return (
        f'<tr style="background-color: #4a4a4a;">\n'
        f'<td style="text-align: right; width: {W1}%; font-weight: bold; color: #ffffff;">'
        f'<span style="color: #ffffff;">{label}</span></td>\n'
        f'<td style="text-align: right; width: 74.4186%; font-weight: bold; color: #ffffff;" colspan="5">'
        f'<span style="color: #ffffff;"><b>{value}</b></span></td>\n'
        f'</tr>'
    )

def year_row(label, years):
    """Year header row"""
    cells = ""
    for y in years:
        cells += (
            f'<td style="text-align: right; width: {W2}%; font-weight: bold; color: #ffffff;">'
            f'<span style="color: #ffffff;">{y}</span></td>'
        )
    return (
        f'<tr style="background-color: #4a4a4a;">\n'
        f'<td style="text-align: right; width: {W1}%; font-weight: bold; color: #ffffff;">'
        f'<span style="color: #ffffff;">{label}</span></td>\n'
        f'{cells}\n'
        f'</tr>'
    )

def data_row(label, values):
    """Regular data row with auto red for negatives"""
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

def build_html(mcap_label, mcap_value, key_label, years, items):
    rows = []
    rows.append(hdr_row(mcap_label, mcap_value))
    rows.append(year_row(key_label, years))
    for label, values in items:
        rows.append(data_row(label, values))
    return HTML_TEMPLATE.format(rows="\n".join(rows))

import os, pathlib

OUT_DIR = pathlib.Path(__file__).resolve().parent.parent

# ============================================================
# 1. Vertiv Holdings (VRT) - USD, NYSE
# ============================================================
vertiv = build_html(
    "Market Cap ($M)", "96,568",
    "Key Financials ($M)",
    ["2020/12", "2021/12", "2022/12", "2023/12", "2024/12"],
    [
        ("Revenue",                ["4,371", "4,998", "5,692", "6,863", "8,012"]),
        ("Operating Income",       ["214", "260", "223", "872", "1,367"]),
        ("Operating Income (Reported)",  ["214", "260", "223", "872", "1,367"]),
        ("Income Before Tax",         ["-255", "166", "167", "534", "765"]),
        ("Net Income",             ["-327", "120", "77", "460", "496"]),
        ("Net Income (Parent)",    ["-327", "120", "77", "460", "496"]),
        ("Net Income (NCI)",       ["0", "0", "0", "0", "0"]),
        ("Total Assets",           ["5,074", "6,940", "7,096", "7,998", "9,132"]),
        ("Total Liabilities",      ["4,562", "5,522", "5,654", "5,984", "6,698"]),
        ("Total Equity",           ["512", "1,418", "1,442", "2,015", "2,434"]),
        ("Equity (Parent)",        ["512", "1,418", "1,442", "2,015", "2,434"]),
        ("Equity (NCI)",           ["0", "0", "0", "0", "0"]),
        ("Paid-in Capital",           ["0", "0", "0", "0", "0"]),
        ("Operating CF",           ["209", "211", "-153", "900", "1,319"]),
        ("Investing CF",           ["-46", "-1,217", "-112", "-139", "-202"]),
        ("Financing CF",           ["141", "915", "100", "-248", "-652"]),
        ("CAPEX",                  ["44", "73", "100", "128", "167"]),
        ("FCF",                    ["164", "138", "-253", "773", "1,152"]),
        ("Interest-bearing Debt",  ["2,152", "2,972", "3,191", "2,941", "2,928"]),
        ("Op. Margin (%)",         ["4.9", "5.2", "3.9", "12.7", "17.1"]),
        ("Net Margin (%)",         ["-7.5", "2.4", "1.3", "6.7", "6.2"]),
        ("ROE (%)",                ["-63.9", "8.4", "5.3", "22.8", "20.4"]),
        ("ROA (%)",                ["-6.5", "1.7", "1.1", "5.8", "5.4"]),
        ("Debt Ratio (%)",         ["890.8", "389.5", "392.1", "297.0", "275.2"]),
        ("Capital Reserve Ratio (%)",    ["-", "-", "-", "-", "-"]),
        ("EPS ($)",                ["-1.07", "0.34", "0.20", "1.21", "1.32"]),
        ("PER (x)",                ["-", "73.15", "68.05", "39.58", "85.92"]),
        ("BPS ($)",                ["1.50", "3.77", "3.82", "5.28", "6.39"]),
        ("PBR (x)",                ["12.39", "6.60", "3.56", "9.07", "17.75"]),
        ("Cash DPS ($)",                ["0.01", "0.01", "0.01", "0.02", "0.11"]),
        ("Cash Div. Yield (%)",         ["0.1", "0.0", "0.1", "0.0", "0.1"]),
        ("Payout Ratio (%)",       ["-", "2.9", "5.0", "1.7", "8.3"]),
        ("Shares Outstanding",     ["342,024,612", "375,801,857", "377,368,837", "381,788,876", "380,703,974"]),
    ]
)

# ============================================================
# 2. Freeport-McMoRan (FCX) - USD, NYSE
# ============================================================
freeport = build_html(
    "Market Cap ($M)", "53,132",
    "Key Financials ($M)",
    ["2021/12", "2022/12", "2023/12", "2024/12", "2025/12"],
    [
        ("Revenue",                ["22,845", "22,780", "22,855", "25,455", "25,915"]),
        ("Operating Income",       ["8,366", "7,037", "6,225", "6,864", "6,518"]),
        ("Operating Income (Reported)",  ["8,366", "7,037", "6,225", "6,864", "6,518"]),
        ("Income Before Tax",         ["7,659", "6,715", "6,006", "6,907", "6,372"]),
        ("Net Income",             ["5,365", "4,479", "3,751", "4,399", "4,152"]),
        ("Net Income (Parent)",    ["4,306", "3,468", "1,848", "1,889", "2,204"]),
        ("Net Income (NCI)",       ["1,059", "1,011", "1,903", "2,510", "1,948"]),
        ("Total Assets",           ["48,022", "51,093", "52,506", "54,848", "58,167"]),
        ("Total Liabilities",      ["25,003", "26,222", "25,196", "26,070", "27,401"]),
        ("Total Equity",           ["23,019", "24,871", "27,310", "28,778", "30,766"]),
        ("Equity (Parent)",        ["13,980", "15,555", "16,693", "17,581", "18,899"]),
        ("Equity (NCI)",           ["9,039", "9,316", "10,617", "11,197", "11,867"]),
        ("Paid-in Capital",           ["160", "161", "162", "162", "163"]),
        ("Operating CF",           ["7,715", "5,139", "5,279", "7,160", "5,610"]),
        ("Investing CF",           ["-1,964", "-3,440", "-4,956", "-5,028", "-4,472"]),
        ("Financing CF",           ["-1,340", "-1,623", "-2,650", "-3,284", "-1,876"]),
        ("CAPEX",                  ["2,115", "3,469", "4,824", "4,808", "4,494"]),
        ("FCF",                    ["5,600", "1,670", "455", "2,352", "1,116"]),
        ("Interest-bearing Debt",  ["9,450", "10,620", "9,422", "8,948", "9,379"]),
        ("Op. Margin (%)",         ["36.6", "30.9", "27.2", "27.0", "25.2"]),
        ("Net Margin (%)",         ["23.5", "19.7", "16.4", "17.3", "16.0"]),
        ("ROE (%)",                ["30.8", "22.3", "11.1", "10.7", "11.7"]),
        ("ROA (%)",                ["11.2", "8.8", "7.1", "8.0", "7.1"]),
        ("Debt Ratio (%)",         ["108.6", "105.4", "92.3", "90.6", "89.1"]),
        ("Capital Reserve Ratio (%)",    ["8,638", "9,562", "10,204", "10,753", "11,495"]),
        ("EPS ($)",                ["2.93", "2.40", "1.28", "1.31", "1.53"]),
        ("PER (x)",                ["13.38", "15.14", "32.27", "28.56", "33.11"]),
        ("BPS ($)",                ["9.60", "10.88", "11.63", "12.23", "13.16"]),
        ("PBR (x)",                ["4.09", "3.34", "3.55", "3.06", "3.85"]),
        ("Cash DPS ($)",                ["0.38", "0.60", "0.60", "0.60", "0.60"]),
        ("Cash Div. Yield (%)",         ["1.0", "1.7", "1.5", "1.6", "1.2"]),
        ("Payout Ratio (%)",       ["12.8", "24.9", "46.6", "45.7", "39.1"]),
        ("Shares Outstanding",     ["1,457,394,804", "1,430,457,312", "1,435,174,932", "1,437,432,081", "1,436,201,550"]),
    ]
)

# ============================================================
# 3. Ero Copper (ERO) - USD, NYSE/TSX
# ============================================================
erocopper = build_html(
    "Market Cap ($M)", "2,561",
    "Key Financials ($M)",
    ["2021/12", "2022/12", "2023/12", "2024/12", "2025/12"],
    [
        ("Revenue",                ["490", "426", "427", "470", "786"]),
        ("Operating Income",       ["272", "130", "95", "109", "271"]),
        ("Operating Income (Reported)",  ["272", "130", "95", "109", "271"]),
        ("Income Before Tax",         ["237", "126", "112", "-75", "331"]),
        ("Net Income",             ["201", "102", "93", "-68", "267"]),
        ("Net Income (Parent)",    ["201", "102", "93", "-68", "264"]),
        ("Net Income (NCI)",       ["-", "-", "-", "-", "-"]),
        ("Total Assets",           ["690", "1,188", "1,512", "1,458", "1,924"]),
        ("Total Liabilities",      ["294", "646", "702", "867", "986"]),
        ("Total Equity",           ["395", "542", "809", "591", "938"]),
        ("Equity (Parent)",        ["393", "539", "804", "587", "936"]),
        ("Equity (NCI)",           ["2", "4", "5", "4", "2"]),
        ("Paid-in Capital",           ["133", "148", "271", "287", "298"]),
        ("Operating CF",           ["365", "143", "163", "145", "395"]),
        ("Investing CF",           ["-180", "-426", "-308", "-335", "-279"]),
        ("Financing CF",           ["-115", "327", "78", "131", "-60"]),
        ("CAPEX",                  ["182", "296", "461", "338", "282"]),
        ("FCF",                    ["183", "-152", "-298", "-192", "113"]),
        ("Interest-bearing Debt",  ["66", "429", "446", "620", "632"]),
        ("Op. Margin (%)",         ["55.6", "30.4", "22.3", "23.2", "34.4"]),
        ("Net Margin (%)",         ["41.0", "23.9", "21.7", "-14.4", "34.0"]),
        ("ROE (%)",                ["51.2", "18.9", "11.5", "-11.7", "28.2"]),
        ("ROA (%)",                ["29.1", "8.6", "6.1", "-4.7", "13.9"]),
        ("Debt Ratio (%)",         ["74.4", "119.2", "86.8", "146.7", "105.1"]),
        ("Capital Reserve Ratio (%)",    ["195", "264", "197", "105", "214"]),
        ("EPS ($)",                ["2.21", "1.10", "0.98", "-0.66", "2.53"]),
        ("PER (x)",                ["6.92", "12.45", "16.15", "-", "11.17"]),
        ("BPS ($)",                ["4.32", "5.85", "8.47", "5.69", "8.99"]),
        ("PBR (x)",                ["3.54", "2.35", "1.86", "2.37", "3.15"]),
        ("Cash DPS ($)",                ["-", "-", "-", "-", "-"]),
        ("Cash Div. Yield (%)",         ["-", "-", "-", "-", "-"]),
        ("Payout Ratio (%)",       ["-", "-", "-", "-", "-"]),
        ("Shares Outstanding",     ["90,960,000", "92,170,000", "94,900,000", "103,110,000", "104,130,000"]),
    ]
)

# ============================================================
# 4. Teck Resources (TECK) - CAD, TSX/NYSE
# ============================================================
teck = build_html(
    "Market Cap (CAD M)", "29,201",
    "Key Financials (CAD M)",
    ["2020/12", "2021/12", "2022/12", "2023/12", "2024/12"],
    [
        ("Revenue",                ["8,948", "12,766", "17,316", "6,476", "9,065"]),
        ("Operating Income",       ["469", "4,851", "7,188", "36", "778"]),
        ("Operating Income (Reported)",  ["469", "4,851", "6,986", "222", "-9"]),
        ("Income Before Tax",         ["-1,044", "4,688", "6,565", "-75", "-718"]),
        ("Net Income",             ["-864", "2,868", "3,317", "2,409", "406"]),
        ("Net Income (Parent)",    ["-864", "2,868", "3,298", "2,308", "283"]),
        ("Net Income (NCI)",       ["0", "0", "19", "101", "123"]),
        ("Total Assets",           ["41,278", "47,368", "52,359", "56,193", "47,037"]),
        ("Total Liabilities",      ["20,570", "23,595", "25,848", "27,901", "19,941"]),
        ("Total Equity",           ["20,708", "23,773", "26,511", "28,292", "27,096"]),
        ("Equity (Parent)",        ["20,019", "23,005", "25,473", "26,988", "26,077"]),
        ("Equity (NCI)",           ["689", "768", "1,038", "1,304", "1,019"]),
        ("Paid-in Capital",           ["6,091", "6,139", "6,139", "6,464", "6,441"]),
        ("Operating CF",           ["2,094", "4,738", "7,983", "4,084", "2,790"]),
        ("Investing CF",           ["-1,861", "-4,819", "-5,680", "-4,757", "6,173"]),
        ("Financing CF",           ["-316", "1,056", "-1,990", "-469", "-2,565"]),
        ("CAPEX",                  ["1,804", "4,633", "5,465", "4,340", "2,635"]),
        ("FCF",                    ["290", "105", "2,518", "-256", "155"]),
        ("Interest-bearing Debt",  ["9,697", "9,331", "10,017", "11,092", "9,965"]),
        ("Op. Margin (%)",         ["5.2", "38.0", "41.5", "0.6", "8.6"]),
        ("Net Margin (%)",         ["-9.7", "22.5", "19.2", "37.2", "4.5"]),
        ("ROE (%)",                ["-4.3", "12.5", "12.9", "8.6", "1.1"]),
        ("ROA (%)",                ["-2.1", "6.1", "6.3", "4.3", "0.9"]),
        ("Debt Ratio (%)",         ["99.3", "99.3", "97.5", "98.6", "73.6"]),
        ("Capital Reserve Ratio (%)",    ["228.7", "274.7", "314.9", "317.5", "304.9"]),
        ("EPS (CAD)",              ["-1.61", "5.36", "6.42", "4.46", "0.56"]),
        ("PER (x)",                ["-", "6.36", "7.61", "12.23", "103.18"]),
        ("BPS (CAD)",              ["37.22", "43.02", "49.59", "52.17", "51.50"]),
        ("PBR (x)",                ["0.58", "0.79", "0.99", "1.05", "1.12"]),
        ("Cash DPS (CAD)",              ["0.20", "0.20", "1.00", "1.00", "1.00"]),
        ("Cash Div. Yield (%)",         ["0.9", "0.6", "2.0", "1.8", "1.7"]),
        ("Payout Ratio (%)",       ["-", "3.7", "15.6", "22.4", "178.9"]),
        ("Shares Outstanding",     ["538,000,000", "535,000,000", "514,000,000", "517,000,000", "506,000,000"]),
    ]
)

# Write all files
files = {
    "vertiv_financial.html": vertiv,
    "freeport_financial.html": freeport,
    "erocopper_financial.html": erocopper,
    "teck_financial.html": teck,
}

for fname, content in files.items():
    path = OUT_DIR / fname
    path.write_text(content, encoding="utf-8")
    print(f"[OK] {fname} written ({len(content):,} bytes)")

print("\nAll 4 US financial tables regenerated in standard format.")

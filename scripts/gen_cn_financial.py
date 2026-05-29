"""
Generate standardized China mainland company financial HTML tables
matching the Korean update_financial.py output format.
Source: yfinance (300750.SZ) API only — 4 years
No web-scraped data. No quarterly (API limitation).
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
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
W2 = "18.6047"  # 74.4186% / 4 columns

def hdr_row(label, value):
    return (
        f'<tr style="background-color: #4a4a4a;">\n'
        f'<td style="text-align: right; width: {W1}%; font-weight: bold; color: #ffffff;">'
        f'<span style="color: #ffffff;">{label}</span></td>\n'
        f'<td style="text-align: right; width: 74.4186%; font-weight: bold; color: #ffffff;" colspan="4">'
        f'<span style="color: #ffffff;"><b>{value}</b></span></td>\n'
        f'</tr>'
    )

def year_row(label, years):
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

import pathlib
OUT_DIR = pathlib.Path(__file__).resolve().parent.parent

# ============================================================
# CATL / 宁德时代 (300750.SZ) - CNY, SZSE
# Source: yfinance API only (4 years)
# Calendar year (Dec). 1:1.8 stock split Apr 2023.
# All per-share data split-adjusted by yfinance.
# Market cap from yfinance info.marketCap.
# ============================================================
catl = build_html(
    "Market Cap (CNY M)", "1,836,957",
    "主要财务信息(CNY M)",
    ["2022/12", "2023/12", "2024/12", "2025/12"],
    [
        ("营业收入",                ["328,594", "400,917", "362,013", "423,702"]),
        ("营业利润",       ["35,086", "51,646", "64,544", "81,538"]),
        ("营业利润(披露基准)",  ["35,086", "51,646", "64,544", "81,538"]),
        ("利润总额",         ["36,673", "53,914", "63,182", "89,527"]),
        ("净利润",             ["33,457", "46,761", "54,007", "76,786"]),
        ("归属母公司净利润",    ["30,729", "44,121", "50,745", "72,201"]),
        ("少数股东损益",       ["2,728", "2,640", "3,262", "4,585"]),
        ("资产总计",           ["600,952", "717,168", "786,658", "974,828"]),
        ("负债总计",      ["424,043", "497,285", "513,202", "603,801"]),
        ("所有者权益合计",           ["176,909", "219,883", "273,456", "371,026"]),
        ("归属母公司权益",        ["164,481", "197,708", "246,930", "337,108"]),
        ("少数股东权益",           ["12,428", "22,175", "26,526", "33,919"]),
        ("实收资本",           ["2,443", "4,399", "4,403", "4,564"]),
        ("经营活动现金流",           ["61,209", "92,826", "96,990", "133,220"]),
        ("投资活动现金流",           ["-64,140", "-29,188", "-48,875", "-94,476"]),
        ("筹资活动现金流",           ["82,266", "14,716", "-14,524", "-6,310"]),
        ("资本支出",                  ["48,215", "33,625", "31,180", "42,345"]),
        ("自由现金流",                    ["12,994", "59,201", "65,810", "90,875"]),
        ("带息负债",  ["100,497", "125,159", "136,402", "119,656"]),
        ("营业利润率(%)",         ["10.7", "12.9", "17.8", "19.2"]),
        ("净利润率(%)",         ["9.4", "11.0", "14.0", "17.0"]),
        ("ROE(%)",                ["18.7", "22.3", "20.6", "21.4"]),
        ("ROA(%)",                ["5.1", "6.2", "6.5", "7.4"]),
        ("资产负债率(%)",         ["257.8", "251.5", "207.8", "179.1"]),
        ("资本公积率(%)",    ["63,243", "103,245", "126,602", "174,629"]),
        ("每股收益(CNY)",              ["6.99", "10.03", "11.52", "15.82"]),
        ("PER(x)",                ["28.6", "14.3", "21.7", "23.2"]),
        ("每股净资产(CNY)",              ["37.41", "44.94", "56.08", "73.87"]),
        ("PBR(x)",                ["5.3", "3.2", "4.5", "5.0"]),
        ("每股现金股利(CNY)",              ["2.52", "5.03", "5.78", "1.01"]),
        ("现金股息率(%)",         ["1.3", "3.5", "2.3", "0.3"]),
        ("现金分红率(%)",       ["36.1", "50.1", "50.2", "6.4"]),
        ("总股本",     ["4,396,526,143", "4,399,041,236", "4,403,466,458", "4,563,803,488"]),
    ]
)

with open(OUT_DIR / "catl_financial.html", "w", encoding="utf-8") as f:
    f.write(catl)
print("Created catl_financial.html")

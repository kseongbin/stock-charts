"""
Generate standardized Hong Kong company financial HTML tables
matching the Korean update_financial.py output format.
Source: yfinance (0700.HK) API only — 4 years
No web-scraped data. No quarterly (API limitation).
Tencent reports in CNY (RMB). Market cap in HKD.
PER/PBR: HKD price converted to CNY using year-end HKDCNY rate.
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
# Tencent / 腾讯控股 (0700.HK) - CNY reported, HKD listed
# Source: yfinance API only (4 years)
# Calendar year (Dec). Reports in CNY/RMB.
# Market cap in HKD (from yfinance info.marketCap).
# PER/PBR: year-end HKD price × HKDCNY rate → CNY price / EPS or BPS
# HKDCNY rates: 2021=0.8140, 2022=0.8837, 2023=0.9094, 2024=0.9385
# ============================================================
tencent = build_html(
    "Market Cap (HKD M)", "4,479,406",
    "主要财务信息(HKD M)",
    ["2021/12", "2022/12", "2023/12", "2024/12"],
    [
        ("营业收入",                ["560,118", "554,552", "609,015", "660,257"]),
        ("营业利润",       ["122,341", "113,940", "165,658", "208,786"]),
        ("营业利润(披露基准)",  ["122,341", "113,940", "165,658", "208,786"]),
        ("利润总额",         ["248,062", "210,225", "161,324", "241,485"]),
        ("净利润",             ["227,810", "188,709", "118,048", "196,467"]),
        ("归属母公司净利润",    ["224,822", "188,243", "115,216", "194,073"]),
        ("少数股东损益",       ["2,988", "466", "2,832", "2,394"]),
        ("资产总计",           ["1,612,364", "1,578,131", "1,577,246", "1,780,995"]),
        ("负债总计",      ["735,671", "795,271", "703,565", "727,099"]),
        ("所有者权益合计",           ["876,693", "782,860", "873,681", "1,053,896"]),
        ("归属母公司权益",        ["806,299", "721,391", "808,591", "973,548"]),
        ("少数股东权益",           ["70,394", "61,469", "65,090", "80,348"]),
        ("实收资本",           ["0", "0", "0", "0"]),
        ("经营活动现金流",           ["175,186", "146,091", "221,962", "258,521"]),
        ("投资活动现金流",           ["-178,549", "-104,871", "-125,161", "-122,187"]),
        ("筹资活动现金流",           ["21,620", "-59,953", "-82,573", "-176,494"]),
        ("资本支出",                  ["62,165", "50,850", "47,407", "96,048"]),
        ("自由现金流",                    ["113,021", "95,241", "174,555", "162,473"]),
        ("带息负债",  ["323,476", "359,141", "371,240", "358,112"]),
        ("营业利润率(%)",         ["21.8", "20.5", "27.2", "31.6"]),
        ("净利润率(%)",         ["40.1", "33.9", "18.9", "29.4"]),
        ("ROE(%)",                ["27.9", "26.1", "14.2", "19.9"]),
        ("ROA(%)",                ["13.9", "11.9", "7.3", "10.9"]),
        ("资产负债率(%)",         ["91.2", "110.2", "87.0", "74.7"]),
        ("资本公积率(%)",    ["669,911", "705,981", "813,911", "892,030"]),
        ("每股收益(CNY)",              ["23.40", "19.67", "12.27", "21.23"]),
        ("PER(x)",                ["14.0", "15.0", "21.8", "18.2"]),
        ("每股净资产(CNY)",              ["83.92", "75.39", "86.10", "106.49"]),
        ("PBR(x)",                ["3.9", "3.9", "3.1", "3.6"]),
        ("每股现金股利(HKD)",              ["1.60", "2.40", "3.40", "4.50"]),
        ("现金股息率(%)",         ["0.4", "0.7", "1.2", "1.1"]),
        ("现金分红率(%)",       ["5.6", "10.8", "25.2", "19.9"]),
        ("总股本",     ["9,608,378,469", "9,568,738,935", "9,391,209,351", "9,142,175,160"]),
    ]
)

with open(OUT_DIR / "tencent_financial.html", "w", encoding="utf-8") as f:
    f.write(tencent)
print("Created tencent_financial.html")

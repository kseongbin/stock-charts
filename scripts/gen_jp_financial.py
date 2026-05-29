"""
Generate standardized Japan company financial HTML tables
matching the Korean update_financial.py output format.
Source: EDINET API (金融庁) + yfinance
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
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
# 1. Tokyo Electron (8035.T) - JPY, TSE
# Source: EDINET (E02652, docID S100VX9R) + yfinance
# Fiscal year ends March. 3:1 stock split Apr 2024.
# All per-share data split-adjusted.
# ============================================================
tokyoelectron = build_html(
    "Market Cap (\u00a5M)", "18,514,801",
    "主要財務情報(¥M)",
    ["2021/03", "2022/03", "2023/03", "2024/03", "2025/03"],
    [
        ("売上高",                ["1,399,102", "2,003,805", "2,209,025", "1,830,527", "2,431,568"]),
        ("営業利益",       ["320,686", "599,271", "617,724", "456,264", "697,321"]),
        ("営業利益(発表基準)",  ["320,686", "599,271", "617,724", "456,264", "697,321"]),
        ("税引前当期純利益",         ["317,037", "596,698", "624,856", "473,438", "706,113"]),
        ("当期純利益",             ["242,941", "437,076", "471,584", "363,963", "544,133"]),
        ("親会社株主帰属当期純利益",    ["242,941", "437,076", "471,584", "363,963", "544,133"]),
        ("非支配株主帰属当期純利益",       ["0", "0", "0", "0", "0"]),
        ("資産合計",           ["1,425,364", "1,894,457", "2,311,594", "2,456,462", "2,625,981"]),
        ("負債合計",      ["400,802", "547,409", "712,070", "696,282", "770,772"]),
        ("純資産合計",           ["1,024,562", "1,347,048", "1,599,524", "1,760,180", "1,855,209"]),
        ("株主資本合計",        ["1,024,562", "1,347,048", "1,599,524", "1,760,180", "1,855,209"]),
        ("非支配株主持分",           ["0", "0", "0", "0", "0"]),
        ("資本金",           ["54,961", "54,961", "54,961", "54,961", "54,961"]),
        ("営業活動によるCF",           ["145,888", "283,387", "426,270", "434,720", "582,174"]),
        ("投資活動によるCF",           ["-18,274", "-55,632", "-41,756", "-125,148", "-169,609"]),
        ("財務活動によるCF",           ["-114,525", "-167,256", "-256,534", "-325,012", "-388,836"]),
        ("設備投資額",                  ["53,806", "56,153", "66,897", "116,993", "158,374"]),
        ("FCF",                    ["92,082", "227,234", "359,373", "317,727", "423,800"]),
        ("有利子負債",  ["0", "0", "0", "0", "0"]),
        ("営業利益率(%)",         ["22.9", "29.9", "28.0", "24.9", "28.7"]),
        ("純利益率(%)",         ["17.4", "21.8", "21.4", "19.9", "22.4"]),
        ("ROE(%)",                ["26.5", "37.2", "32.3", "21.8", "30.3"]),
        ("ROA(%)",                ["17.0", "23.1", "20.4", "14.8", "20.7"]),
        ("負債比率(%)",         ["39.1", "40.6", "44.5", "39.6", "41.6"]),
        ("資本留保率(%)",    ["969,601", "1,292,087", "1,544,563", "1,705,219", "1,800,248"]),
        ("EPS(¥)",           ["517.76", "931.30", "1,003.86", "781.20", "1,179.08"]),
        ("PER(x)",                ["29.95", "22.53", "15.92", "50.49", "17.01"]),
        ("BPS(¥)",           ["2,170.73", "2,857.48", "3,389.68", "3,773.11", "4,016.34"]),
        ("PBR(x)",                ["7.14", "7.34", "4.71", "10.45", "4.99"]),
        ("配当金(¥)",           ["260", "468", "570", "393", "592"]),
        ("配当利回り(%)",         ["1.7", "2.2", "3.6", "1.0", "3.0"]),
        ("配当性向(%)",       ["50.3", "50.2", "56.8", "50.3", "50.2"]),
        ("発行済株式数",     ["471,632,733", "471,632,733", "471,632,733", "471,632,733", "471,632,733"]),
    ]
)

with open(OUT_DIR / "tokyoelectron_financial.html", "w", encoding="utf-8") as f:
    f.write(tokyoelectron)
print("Created tokyoelectron_financial.html")

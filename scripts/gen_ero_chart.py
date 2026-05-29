import sys
sys.stdout.reconfigure(encoding='utf-8')

import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

BASE = r'C:\Users\riseo\Cluade Test\stock-charts'

ticker = 'ERO'
name = 'Ero Copper'
code = 'ERO'
filename = 'erocopper.html'

MA_DAYS = 60
MA_COLOR = '#FF9800'

print(f'[{name}] Downloading daily data...')
stock = yf.Ticker(ticker)
df_daily = stock.history(period='max', interval='1d')

if df_daily.empty:
    print(f'[{name}] ERROR: no data')
    sys.exit(1)

df_daily[f'MA{MA_DAYS}'] = df_daily['Close'].rolling(window=MA_DAYS).mean()
df = df_daily.resample('W').agg({
    'Open': 'first', 'High': 'max', 'Low': 'min',
    'Close': 'last', 'Volume': 'sum'
}).dropna(subset=['Close'])
df[f'MA{MA_DAYS}'] = df_daily[f'MA{MA_DAYS}'].resample('W').last()

fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=[0.75, 0.25],
)

fig.add_trace(go.Candlestick(
    x=df.index, open=df['Open'], high=df['High'],
    low=df['Low'], close=df['Close'], name='Weekly',
    increasing=dict(line=dict(color='#EF5350'), fillcolor='#EF5350'),
    decreasing=dict(line=dict(color='#2962FF'), fillcolor='#2962FF'),
), row=1, col=1)

ma_data = df[f'MA{MA_DAYS}'].dropna()
fig.add_trace(go.Scatter(
    x=ma_data.index, y=ma_data, mode='lines', name='60D MA',
    line=dict(color=MA_COLOR, width=1.2),
    hovertemplate='60D MA: $%{y:,.2f}<extra></extra>'
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=df.index, y=df['Volume'], name='Volume',
    mode='lines', fill='tozeroy',
    line=dict(color='#7986CB', width=0.5),
    fillcolor='rgba(121,134,203,0.4)',
    hovertemplate='Volume: %{y:,.0f}<extra></extra>'
), row=2, col=1)

fig.update_layout(
    title=dict(text=f'{name} ({code}) Weekly Chart',
               font=dict(size=18, color='#333333'), x=0.5, y=0.97),
    template='plotly_white', height=500, showlegend=True,
    legend=dict(orientation='h', yanchor='top', y=1.025,
                xanchor='right', x=1.0, font=dict(size=10)),
    hovermode='x unified',
    margin=dict(l=10, r=10, t=105, b=30),
    dragmode='pan',
    newshape=dict(line=dict(color='#000000', width=2)),
    xaxis2=dict(type='date'),
    xaxis=dict(type='date', rangeslider=dict(visible=False)),
    yaxis=dict(tickformat=',', tickprefix='$', hoverformat=',.2f', side='right', fixedrange=True, automargin=True),
    yaxis2=dict(showticklabels=False, fixedrange=True),
)

fig.update_xaxes(
    rangeselector=dict(
        buttons=[
            dict(count=3, label='3M', step='month', stepmode='backward'),
            dict(count=6, label='6M', step='month', stepmode='backward'),
            dict(count=1, label='1Y', step='year', stepmode='backward'),
            dict(count=3, label='3Y', step='year', stepmode='backward'),
            dict(count=5, label='5Y', step='year', stepmode='backward'),
            dict(label='ALL', step='all')
        ],
        font=dict(size=10), bgcolor='#f0f0f0', activecolor='#2962FF',
        x=0, y=1.06,
    ),
)

chart_config = {
    'displayModeBar': True, 'displaylogo': False, 'scrollZoom': False,
    'modeBarButtonsToAdd': ['drawline'],
    'modeBarButtonsToRemove': ['toImage', 'zoom2d', 'select2d', 'lasso2d',
        'autoScale2d', 'resetScale2d', 'zoomIn2d', 'zoomOut2d'],
}

autofit_js = """<script>
(function() {
    var gd = document.querySelectorAll('.plotly-graph-div')[0];
    if (!gd) return;
    var busy = false;
    var dataXMin, dataXMax;
    function hasLen(a) { return a && typeof a.length === 'number' && a.length > 0; }
    function calcBounds() {
        dataXMin = Infinity; dataXMax = -Infinity;
        var traces = gd._fullData || gd.data;
        for (var t = 0; t < traces.length; t++) {
            var tr = traces[t];
            if (!hasLen(tr.x)) continue;
            for (var i = 0; i < tr.x.length; i++) {
                if (tr.x[i] == null) continue;
                var ts = new Date(tr.x[i]).getTime();
                if (!isNaN(ts)) {
                    if (ts < dataXMin) dataXMin = ts;
                    if (ts > dataXMax) dataXMax = ts;
                }
            }
        }
    }
    function autofit() {
        if (!gd._fullData || !gd._fullLayout) return;
        if (dataXMin === undefined) calcBounds();
        var xRange = gd._fullLayout.xaxis.range;
        if (!xRange) return;
        var xMin = new Date(xRange[0]).getTime();
        var xMax = new Date(xRange[1]).getTime();
        if (isNaN(xMin) || isNaN(xMax)) return;
        var update = {};
        var clamped = false;
        if (xMin < dataXMin) { xMin = dataXMin; clamped = true; }
        if (xMax > dataXMax) { xMax = dataXMax; clamped = true; }
        if (clamped) {
            update['xaxis.range'] = [new Date(xMin).toISOString(), new Date(xMax).toISOString()];
        }
        var yMin = Infinity, yMax = -Infinity;
        var traces = gd._fullData;
        for (var t = 0; t < traces.length; t++) {
            var tr = traces[t];
            if (!hasLen(tr.x)) continue;
            if (tr.yaxis === 'y2' || tr.type === 'bar') continue;
            if (tr.type === 'candlestick' || tr.type === 'ohlc') {
                var high = tr.high, low = tr.low;
                if (!hasLen(high) || !hasLen(low)) continue;
                for (var i = 0; i < tr.x.length; i++) {
                    var ts = new Date(tr.x[i]).getTime();
                    if (ts < xMin || ts > xMax) continue;
                    var h = high[i], l = low[i];
                    if (h === h && h > yMax) yMax = h;
                    if (l === l && l < yMin) yMin = l;
                }
            } else if (hasLen(tr.y)) {
                for (var i = 0; i < tr.x.length; i++) {
                    var ts = new Date(tr.x[i]).getTime();
                    if (ts < xMin || ts > xMax) continue;
                    var v = tr.y[i];
                    if (v === v) {
                        if (v < yMin) yMin = v;
                        if (v > yMax) yMax = v;
                    }
                }
            }
        }
        if (yMin < Infinity && yMax > -Infinity) {
            var range = yMax - yMin;
            var pad = Math.max(range * 0.08, yMax * 0.02, 1);
            update['yaxis.range'] = [yMin - pad, yMax + pad];
            update['yaxis.autorange'] = false;
        }
        if (Object.keys(update).length > 0) {
            busy = true;
            Plotly.relayout(gd, update).then(function() {
                setTimeout(function() { busy = false; }, 50);
            });
        }
    }
    gd.on('plotly_relayout', function(ed) {
        if (busy) return;
        var keys = Object.keys(ed || {});
        for (var i = 0; i < keys.length; i++) {
            if (keys[i].indexOf('xaxis') === 0) {
                setTimeout(autofit, 50);
                return;
            }
        }
    });
    setTimeout(autofit, 500);
    function addClearBtn() {
        var modeBar = document.querySelector('.modebar-group');
        if (!modeBar) { setTimeout(addClearBtn, 300); return; }
        var btn = document.createElement('a');
        btn.className = 'modebar-btn';
        btn.setAttribute('data-title', 'Clear lines');
        btn.setAttribute('data-toggle', 'false');
        btn.style.cursor = 'pointer';
        btn.innerHTML = '<svg viewBox="0 0 1000 1000" height="1em" width="1em"><path d="M742 167L500 408 258 167 167 258 408 500 167 742 258 833 500 592 742 833 833 742 592 500 833 258z" fill="currentColor"/></svg>';
        btn.addEventListener('click', function() {
            Plotly.relayout(gd, {shapes: []});
        });
        modeBar.appendChild(btn);
    }
    setTimeout(addClearBtn, 600);
})();
</script>"""

out_path = os.path.join(BASE, filename)
html = fig.to_html(include_plotlyjs=True, full_html=True, config=chart_config)
html = html.replace('</body>', autofit_js + '</body>')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'[{name}] Done -> {filename}')
fsize = os.path.getsize(out_path)
print(f'File size: {fsize:,} bytes')

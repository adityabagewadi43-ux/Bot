import requests
import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime
import time

# PARAMETERS
COIN_ID = "bitcoin"        # or "ethereum", "solana"
VS_CURRENCY = "usd"
DAYS = "7"

# 1. Live price (CoinGecko simple price)
def get_live_price(coin_id, vs_currency):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id, "vs_currencies": vs_currency}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        return data[coin_id][vs_currency]
    except Exception as e:
        print("Live price error:", e)
        return None

# 2. OHLC data for candlestick
def get_ohlc_data(coin_id, vs_currency, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {"vs_currency": vs_currency, "days": days}
    try:
        resp = requests.get(url, params=params, timeout=20)
        data = resp.json()
        df = pd.DataFrame(data, columns=["Timestamp", "Open", "High", "Low", "Close"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df = df.sort_values("Timestamp").reset_index(drop=True)
        return df
    except Exception as e:
        print("OHLC error:", e)
        return None

# 3. Build attractive candlestick figure
def make_candlestick_figure(df, coin_id, vs_currency):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["Timestamp"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name=f"{coin_id.upper()} / {vs_currency.upper()}",
                increasing_line_color="cyan",
                decreasing_line_color="red",
                line_width=0.8,
            )
        ]
    )

    # Dark trading‑style theme
    fig.update_layout(
        template="plotly_dark",  # dark background
        title={
            "text": f"🔮 {coin_id.upper()} Trading Dashboard ({vs_currency.upper()})",
            "font": {"size": 20},
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Time",
        yaxis_title=f"Price ({vs_currency.upper()})",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        plot_bgcolor="rgb(10, 10, 20)",    # very dark
        paper_bgcolor="rgb(5, 5, 15)",     # dark outer area
        font_color="lightgray",
        margin=dict(l=40, r=40, t=70, b=40),
    )

    # Simple MA overlay (optional)
    df["MA7"] = df["Close"].rolling(7).mean()
    fig.add_trace(
        go.Scatter(
            x=df["Timestamp"],
            y=df["MA7"],
            mode="lines",
            line=dict(color="yellow", width=1.2),
            name="MA(7)",
            opacity=0.8,
        )
    )

    return fig

# START DASH APP
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Crypto Trading Simulator"

app.layout = dbc.Container(
    [
        html.Div(
            [
                html.H1(
                    "CRYPTO TRADING DASHBOARD",
                    style={
                        "textAlign": "center",
                        "color": "#00bfff",
                        "fontWeight": "bold",
                        "marginBottom": "5px",
                    },
                ),
                html.H4(
                    "Live candlestick + moving price action",
                    style={"textAlign": "center", "color": "lightgray"},
                ),
            ]
        ),
        html.Div(
            id="live-price-box",
            style={
                "textAlign": "center",
                "fontSize": "24px",
                "fontWeight": "bold",
                "color": "cyan",
                "marginBottom": "16px",
                "backgroundColor": "rgb(30,30,50)",
                "padding": "10px",
                "borderRadius": "8px",
            },
        ),
        dcc.Graph(id="candlestick-chart", style={"height": "70vh"}),
        dcc.Interval(
            id="interval", interval=5_000, n_intervals=0  # update every 5 seconds
        ),
    ],
    fluid=True,
    style={"backgroundColor": "rgb(8,8,16)", "padding": "16px"},
)

@app.callback(
    [Output("candlestick-chart", "figure"), Output("live-price-box", "children")],
    Input("interval", "n_intervals"),
)
def update_chart(n):
    live_price = get_live_price(COIN_ID, VS_CURRENCY)
    df = get_ohlc_data(COIN_ID, VS_CURRENCY, DAYS)

    if df is not None and not df.empty:
        fig = make_candlestick_figure(df, COIN_ID, VS_CURRENCY)
    else:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            title="No data loaded yet...",
            xaxis_title="Time",
            yaxis_title="Price",
        )

    live_text = f"🟢 Live Price: {live_price:.2f} {VS_CURRENCY.upper()}" if live_price else "🟡 Live price loading..."
    return fig, live_text

if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=8050)

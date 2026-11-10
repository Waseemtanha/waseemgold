import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="WASEEM TRADER - V8", layout="wide")

# --- ULTRA COMPACT - 2 PAGE ME PURA ---
st.markdown("""
<style>
.block-container{padding-top:2px !important; padding-bottom:2px !important; padding-left:5px !important; padding-right:5px !important; max-width:100% !important;}
h1{font-size:16px !important; margin:0px !important; padding:0px !important;}
h2{font-size:13px !important; margin:1px !important; padding:0px !important;}
h3{font-size:12px !important; margin:1px !important;}
h4{font-size:11px !important; margin:0px !important;}
p{font-size:11px !important; margin:0px !important; line-height:1.2 !important;}
div[data-testid="stVerticalBlock"]{gap:2px !important;}
div[data-testid="stHorizontalBlock"]{gap:4px !important;}
button{padding:2px !important; font-size:12px !important; min-height:25px !important;}
input{font-size:12px !important;}
</style>
""", unsafe_allow_html=True)

def get_color(signal):
    if "BUY" in signal:
        return "#00ff00"
    elif "SELL" in signal:
        return "#ff0000"
    else:
        return "#ffcc00"

st.markdown("<h1 style='text-align:center; margin:0;'>WASEEM TRADER - V8 | 2 PAGE ME PURA</h1>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1,1,2])
with c1:
    auto = st.checkbox("AUTO", value=True)
with c2:
    manual_price = st.number_input("PRICE", value=4027.0, label_visibility="collapsed")
with c3:
    if st.button("CHALAO", use_container_width=True):
        st.rerun()

price = manual_price
atr_live = 15.0
rsi_live = 50.0

if auto:
    try:
        df = yf.download("GC=F", period="5d", interval="1h", progress=False)
        if df is not None and len(df) > 0:
            price = float(df['Close'].iloc[-1].item())
            high = df['High']; low = df['Low']; close = df['Close']
            tr = pd.concat([high-low, abs(high-close.shift(1)), abs(low-close.shift(1))], axis=1).max(axis=1)
            atr_live = float(tr.rolling(14).mean().iloc[-1])
            delta = close.diff()
            gain = delta.where(delta>0, 0).rolling(14).mean()
            loss = -delta.where(delta<0, 0).rolling(14).mean()
            rs = gain/loss
            rsi_live = float(100 - (100/(1+rs.iloc[-1])))
    except:
        pass

d4_low = round(price - 110, 1); d4_high = round(price - 98, 1)
s4_low = round(price + 55, 1); s4_high = round(price + 67, 1)
d1_low = round(price - 7, 1); d1_high = round(price + 3, 1)
s1_low = round(price + 52, 1); s1_high = round(price + 62, 1)
d15_low = round(price - 7, 1); d15_high = round(price - 1, 1)
s15_low = round(price + 7, 1); s15_high = round(price + 13, 1)

buy_score = 0; sell_score = 0
buy_reasons = []; sell_reasons = []
if price <= d1_high + 2:
    buy_score += 1; buy_reasons.append("⭐ 1H DEMAND")
if rsi_live < 30:
    buy_score += 1; buy_reasons.append("⭐ RSI OVERSOLD")
if price <= d15_high + 1:
    buy_score += 1; buy_reasons.append("⭐ 15M DEMAND")
if price > d1_high:
    sell_score += 1; sell_reasons.append("⭐ 15M SUPPLY PAAS")
if rsi_live > 70:
    sell_score += 1; sell_reasons.append("⭐ RSI OVERBOUGHT")
if price >= s15_low - 1:
    sell_score += 1; sell_reasons.append("⭐ 15M SUPPLY")

if buy_score >= 3:
    signal = "BUY - ENTRY LO"; chance = 85
elif sell_score >= 3:
    signal = "SELL - ENTRY LO"; chance = 82
elif buy_score == 2:
    signal = "BUY - TAYYAR RAHO"; chance = 60
elif sell_score == 2:
    signal = "SELL - TAYYAR RAHO"; chance = 60
else:
    signal = "WAIT - ENTRY NAHI"; chance = 30

color = get_color(signal)

buy_entry = d1_low; buy_sl = round(buy_entry - atr_live, 1)
buy_tp1 = round(buy_entry + atr_live, 1); buy_tp2 = round(buy_entry + atr_live*2, 1)
sell_entry = s15_low; sell_sl = round(sell_entry + atr_live, 1)
sell_tp1 = round(sell_entry - atr_live, 1); sell_tp2 = round(sell_entry - atr_live*2, 1)

# LINE 1 - SIGNAL
st.markdown(f"<div style='background-color:{color}; padding:4px; border-radius:6px; text-align:center;'><h2 style='color:black;'>{signal} | {chance}% | GOLD: {price:.1f} | ATR: {atr_live:.1f} | RSI: {rsi_live:.1f}</h2></div>", unsafe_allow_html=True)

# LINE 2 - DONO SIDE TP SL
cb, cs = st.columns(2)
with cb:
    st.markdown(f"<div style='background:#003300; padding:4px; border-radius:6px; text-align:center;'><h4 style='color:#00ff00;'>🟢 BUY: E {buy_entry} | SL {buy_sl} | TP1 {buy_tp1} | TP2 {buy_tp2}</h4></div>", unsafe_allow_html=True)
with cs:
    st.markdown(f"<div style='background:#330000; padding:4px; border-radius:6px; text-align:center;'><h4 style='color:#ff6666;'>🔴 SELL: E {sell_entry} | SL {sell_sl} | TP1 {sell_tp1} | TP2 {sell_tp2}</h4></div>", unsafe_allow_html=True)

# LINE 3 - BUTTON + LEVELS EK SATH
b1, b2, b3 = st.columns(3)
with b1:
    st.markdown(f"<h4 style='color:#00ff00;'>BUY {buy_score}/3: {' | '.join(buy_reasons) if buy_reasons else 'Koi Nahi'}</h4>")
with b2:
    st.markdown(f"<h4 style='color:#ff6666;'>SELL {sell_score}/3: {' | '.join(sell_reasons) if sell_reasons else 'Koi Nahi'}</h4>")
with b3:
    st.markdown(f"<h4>4H D:{d4_low}-{d4_high} S:{s4_low}-{s4_high} | 1H D:{d1_low}-{d1_high} S:{s1_low}-{s1_high} | 15M D:{d15_low}-{d15_high} S:{s15_low}-{s15_high}</h4>")


import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="WASEEM TRADER - V4.1", layout="wide")

st.markdown("<h1 style='color:#FFD700; text-align:center;'>WASEEM TRADER - V4.1</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:white;'>UPAR 4H MAZBOOT LATE + NEECHE JALDI WALA - CHANCE KE SAATH</p>", unsafe_allow_html=True)

colA, colB, colC = st.columns([2,2,1])
with colA:
    MANUAL_PRICE = st.number_input("GOLD PRICE LIKHEIN - MANUAL", value=4021.0, step=1.0)
with colB:
    auto = st.checkbox("AUTO PRICE - Yahoo se le lo", value=False)
with colC:
    chalao = st.button("CHALAO - CALCULATE KARO", use_container_width=True)

if not chalao and "chalaya" not in st.session_state:
    st.info("Upar GOLD PRICE likhein aur CHALAO dabayein")
    st.stop()

if chalao:
    st.session_state["chalaya"] = True
    st.session_state["price"] = MANUAL_PRICE

abhi = float(st.session_state.get("price", MANUAL_PRICE))

def CLEAN(d):
    d = d.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    for c in list(d.columns):
        if isinstance(d[c], pd.DataFrame):
            d[c] = d[c].iloc[:,0]
    d.columns = [str(c) for c in d.columns]
    return d

def GET_DATA(period, interval, n):
    for k in [1,2,3]:
        try:
            d = yf.download("GC=F", period=period, interval=interval, progress=False)
            if d is not None and len(d)>20:
                d = CLEAN(d)
                return d.dropna().tail(n).copy()
        except:
            time.sleep(2)
    return None

with st.spinner("Yahoo se DATA aa raha hai - Wait karo..."):
    df4h = GET_DATA("1mo","4h",60)
    df = GET_DATA("5d","1h",120)
    df15 = GET_DATA("2d","15m",120)

if df is None or df15 is None or df4h is None:
    st.error("DATA NAHI AAYA - WAIT KARO - NAQLI SETUP NAHI DUNGA. Dobara CHALAO dabao.")
    st.stop()

if auto:
    try:
        abhi = float(df["Close"].iloc[-1])
        st.success(f"AUTO PRICE: {int(abhi)}")
    except:
        pass

for d in [df, df15, df4h]:
    d.loc[d.index[-1], 'Close'] = abhi
    if abhi > float(d.loc[d.index[-1], 'High']):
        d.loc[d.index[-1], 'High'] = abhi
    if abhi < float(d.loc[d.index[-1], 'Low']):
        d.loc[d.index[-1], 'Low'] = abhi

pak_time = datetime.now() + timedelta(hours=5)
date_txt = pak_time.strftime("%d %B %Y")
time_txt = pak_time.strftime("%I:%M %p")
abhi_s = str(int(abhi))

df['TR'] = np.maximum(df['High']-df['Low'], np.maximum(abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))))
atr_v = float(df['TR'].rolling(14).mean().iloc[-1])
if atr_v < 3: atr_v = 3.0
if atr_v > 15: atr_v = 15.0
atr_s = str(round(atr_v,1))
sl_dist = int(atr_v*1.0)
if sl_dist < 4: sl_dist = 4
if sl_dist > 15: sl_dist = 15

def SETUP_CALC(d, tf_name, demand_size):
    last_high = float(d['High'].iloc[-10:-1].max())
    last_low = float(d['Low'].iloc[-10:-1].min())
    curr_close = float(d['Close'].iloc[-1])
    bos_up = curr_close > last_high
    bos_down = curr_close < last_low
    fvg_bull = False; fvg_bear = False; fvg_bot = 0; fvg_top = 0
    for i in range(len(d)-15, len(d)):
        if i < 2: continue
        h2 = float(d['High'].iloc[i-2]); l0 = float(d['Low'].iloc[i]); h0 = float(d['High'].iloc[i]); l2 = float(d['Low'].iloc[i-2])
        if l0 - h2 > 1 and l0 - h2 < 8:
            fvg_bull = True; fvg_bot = h2; fvg_top = l0
        if l2 - h0 > 1 and l2 - h0 < 8:
            fvg_bear = True; fvg_bot = h0; fvg_top = l2
    highs=[]; lows=[]
    for i in range(2, len(d)-2):
        h=float(d['High'].iloc[i]); l2=float(d['Low'].iloc[i])
        mx=float(d['High'].iloc[i-2:i+3].max()); mn=float(d['Low'].iloc[i-2:i+3].min())
        if h>=mx: highs.append(round(h))
        if l2<=mn: lows.append(round(l2))
    upar=[x for x in highs if x>abhi+3]
    RES=min(upar) if upar else abhi+15
    neeche=[x for x in lows if x<abhi-3]
    SUP=max(neeche) if neeche else abhi-15
    RES=round(RES/5)*5; SUP=round(SUP/5)*5
    d_bot=SUP; d_top=SUP+demand_size
    s_bot=RES-demand_size; s_top=RES
    at_d = d_bot <= abhi <= d_top
    at_s = s_bot <= abhi <= s_top
    o=float(d['Open'].iloc[-1]); c=float(d['Close'].iloc[-1]); h=float(d['High'].iloc[-1]); l=float(d['Low'].iloc[-1])
    body=abs(c-o); up_w= h-max(c,o); low_w= min(c,o)-l
    react_buy = at_d and low_w > body and c>o
    react_sell = at_s and up_w > body and c<o
    vol_avg=float(d['Volume'].iloc[-20:].mean()); vol_last=float(d['Volume'].iloc[-3:].mean())
    vol_ok = vol_last > vol_avg
    ema50=float(d['Close'].ewm(span=50, adjust=False).mean().iloc[-1])
    trend_up = abhi > ema50
    trend_down = abhi < ema50
    buy_score=0
    if at_d: buy_score+=20
    if bos_up or fvg_bull: buy_score+=20
    if react_buy: buy_score+=20
    if vol_ok: buy_score+=20
    if trend_up: buy_score+=20
    sell_score=0
    if at_s: sell_score+=20
    if bos_down or fvg_bear: sell_score+=20
    if react_sell: sell_score+=20
    if vol_ok: sell_score+=20
    if trend_down: sell_score+=20
    bos_txt = "BOS UP" if bos_up else "BOS DOWN" if bos_down else "BOS Nahi"
    fvg_txt = "FVG Bullish" if fvg_bull else "FVG Bearish" if fvg_bear else "FVG Nahi"
    if at_d and (bos_up or fvg_bull) and react_buy and vol_ok:
        faisla = tf_name+" BUY SETUP - SAB MIL GAYA"; fcol="#00FF88"
        entry="Buy "+str(int(d_bot))+" - "+str(int(d_top)); sl="SL: "+str(int(d_bot-sl_dist)); tp="TP: "+str(int(d_top+sl_dist*2))
        chance=buy_score; chance_txt="CHANCE: "+str(chance)+"% - MAZBOOT" if chance>=80 else "CHANCE: "+str(chance)+"% - THEEK HAI"
        rr_txt="RR: 1:2 - TRADE LENE LAYAQ"
    elif at_s and (bos_down or fvg_bear) and react_sell and vol_ok:
        faisla = tf_name+" SELL SETUP - SAB MIL GAYA"; fcol="#FF4444"
        entry="Sell "+str(int(s_bot))+" - "+str(int(s_top)); sl="SL: "+str(int(s_top+sl_dist)); tp="TP: "+str(int(s_bot-sl_dist*2))
        chance=sell_score; chance_txt="CHANCE: "+str(chance)+"% - MAZBOOT" if chance>=80 else "CHANCE: "+str(chance)+"% - THEEK HAI"
        rr_txt="RR: 1:2 - TRADE LENE LAYAQ"
    elif at_d:
        faisla = tf_name+" WAIT - DEMAND PAR HAI"; fcol="#FFAA00"
        entry="Wait - Demand "+str(int(d_bot))+"-"+str(int(d_top))+" par hai"; sl="SL: Abhi Entry Nahi - ATR "+atr_s; tp="TP: Wait Karo"
        chance=buy_score; chance_txt="CHANCE: "+str(chance)+"% - ABHI KAM HAI"; rr_txt="RR: Abhi Entry Nahi"
    elif at_s:
        faisla = tf_name+" WAIT - SUPPLY PAR HAI"; fcol="#FFAA00"
        entry="Wait - Supply "+str(int(s_bot))+"-"+str(int(s_top))+" par hai"; sl="SL: Abhi Entry Nahi - ATR "+atr_s; tp="TP: Wait Karo"
        chance=sell_score; chance_txt="CHANCE: "+str(chance)+"% - ABHI KAM HAI"; rr_txt="RR: Abhi Entry Nahi"
    else:
        faisla = tf_name+" WAIT - PRICE BEECH ME HAI"; fcol="#FFAA00"
        entry="Wait - Abhi Entry Nahi"; sl="SL: Abhi Entry Nahi - ATR "+atr_s; tp="TP: Wait Karo"
        chance=max(buy_score,sell_score); chance_txt="CHANCE: "+str(chance)+"% - ABHI KAM HAI"; rr_txt="RR: Abhi Entry Nahi"
    if react_buy: react_txt="REACTION: MAZBOOT - UPAR UTHA"
    elif react_sell: react_txt="REACTION: MAZBOOT - NEECHE GIRA"
    elif at_d: react_txt="REACTION: KAMZOR - DEMAND PAR RUKA NAHI"
    elif at_s: react_txt="REACTION: KAMZOR - SUPPLY PAR RUKA NAHI"
    else: react_txt="REACTION: ABHI OB PAR NAHI"
    return {'faisla':faisla,'fcol':fcol,'entry':entry,'sl':sl,'tp':tp,'chance':chance,'chance_txt':chance_txt,'rr':rr_txt,'bos':bos_txt,'fvg':fvg_txt,'react':react_txt,'vol_ok':vol_ok,'d_bot':int(d_bot),'d_top':int(d_top),'s_bot':int(s_bot),'s_top':int(s_top),'fvg_bot':int(fvg_bot),'fvg_top':int(fvg_top),'trend_up':trend_up,'res':int(RES),'sup':int(SUP)}

r4h = SETUP_CALC(df4h, "4H", 12)
r1h = SETUP_CALC(df, "1H", 10)
r15 = SETUP_CALC(df15, "15M", 6)

ema50_v=float(df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]); ema50_s=str(int(ema50_v))
ema15_v=float(df['Close'].ewm(span=15, adjust=False).mean().iloc[-1]); ema15_s=str(int(ema15_v))
delta=df['Close'].diff(); gain=delta.where(delta>0,0).rolling(14).mean(); loss=-delta.where(delta<0,0).rolling(14).mean()
rs=gain/(loss+0.00001); rsi_v=float(100-(100/(1+rs.iloc[-1]))); rsi_s=str(round(rsi_v,1))
ema12_v=float(df['Close'].ewm(span=12, adjust=False).mean().iloc[-1]); ema26_v=float(df['Close'].ewm(span=26, adjust=False).mean().iloc[-1])
macd_line=ema12_v-ema26_v; macd_series=df['Close'].ewm(span=12, adjust=False).mean()-df['Close'].ewm(span=26, adjust=False).mean()
macd_sig_v=float(macd_series.ewm(span=9, adjust=False).mean().iloc[-1])
vwap_v=float((df['Close']*df['Volume']).cumsum().iloc[-1]/(df['Volume'].cumsum().iloc[-1]+1)); vwap_s=str(int(vwap_v))
sma20=float(df['Close'].rolling(20).mean().iloc[-1]); std20=float(df['Close'].rolling(20).std().iloc[-1])
bb_up=sma20+2*std20; bb_low=sma20-2*std20; bb_up_s=str(int(bb_up)); bb_low_s=str(int(bb_low))
o1=float(df['Open'].iloc[-1]); c1=float(df['Close'].iloc[-1]); h1=float(df['High'].iloc[-1]); l1=float(df['Low'].iloc[-1])
body1=abs(c1-o1); up_w1=h1-max(c1,o1); low_w1=min(c1,o1)-l1
pin_buy=low_w1>body1*2 and low_w1>up_w1; pin_sell=up_w1>body1*2 and up_w1>low_w1
htf_up=c1>ema50_v; prev_low=float(df['Low'].iloc[-2]); prev_high=float(df['High'].iloc[-2])
sweep_buy=l1<prev_low and c1>prev_low; sweep_sell=h1>prev_high and c1<prev_high
hour_utc=datetime.now().hour; session_on=7<=hour_utc<=17
vol_avg=float(df['Volume'].iloc[-20:].mean()); vol_aakhri_3=float(df['Volume'].iloc[-3:].mean())
volume_strong=vol_aakhri_3>vol_avg; vol_s=str(int(vol_aakhri_3)); vol_avg_s=str(int(vol_avg))
fvg_bot_s=str(int(r1h['fvg_bot'])); fvg_top_s=str(int(r1h['fvg_top']))
fvg_touch = r1h['fvg_bot']-5 <= abhi <= r1h['fvg_top']+5
if session_on and abhi>ema15_v: sess_buy_txt="Session ON + Upar"; sess_buy_ok=True
elif session_on: sess_buy_txt="Session ON - Price Neeche"; sess_buy_ok=False
else: sess_buy_txt="Session Off"; sess_buy_ok=False
if session_on and abhi<ema15_v: sess_sell_txt="London/NY ON + Neeche"; sess_sell_ok=True
elif session_on: sess_sell_txt="Session ON - Price Upar"; sess_sell_ok=False
else: sess_sell_txt="Session Off"; sess_sell_ok=False

buy_buttons=[]
buy_buttons.append(("1 FVG BUY", fvg_bot_s+"-"+fvg_top_s+" | "+abhi_s, fvg_touch))
buy_buttons.append(("2 VWAP BUY", abhi_s+" > "+vwap_s if abhi>vwap_v else abhi_s+" < "+vwap_s, abhi>vwap_v))
buy_buttons.append(("3 EMA 15 BUY", abhi_s+" > "+ema15_s if abhi>ema15_v else abhi_s+" < "+ema15_s, abhi>ema15_v))
buy_buttons.append(("4 RSI 1H BUY", "RSI "+rsi_s+" > 50" if rsi_v>50 else "RSI "+rsi_s+" < 50", rsi_v>50))
buy_buttons.append(("5 Bollinger BUY", "Low "+bb_low_s+" | "+abhi_s, abhi <= bb_low+5))
buy_buttons.append(("6 MACD BUY", "MACD Upar Hai" if macd_line>macd_sig_v else "MACD Neeche Hai", macd_line>macd_sig_v))
buy_buttons.append(("7 Pin Bar BUY", "Neeche Wick Lambi" if pin_buy else "Pin Nahi Bana", pin_buy))
buy_buttons.append(("8 HTF Trend BUY", "1H Trend Upar" if htf_up else "1H Trend Neeche", htf_up))
buy_buttons.append(("9 Sweep BUY", "Neeche Sweep Hua" if sweep_buy else "Sweep Nahi Hua", sweep_buy))
buy_buttons.append(("10 FVG Touch BUY", "FVG Touch + Upar" if fvg_touch and abhi>ema15_v else "FVG Touch Nahi", fvg_touch and abhi>ema15_v))
buy_buttons.append(("11 Session BUY", sess_buy_txt, sess_buy_ok))
buy_buttons.append(("12 Volume BUY", vol_s+" / "+vol_avg_s, volume_strong and abhi>ema15_v))
sell_buttons=[]
sell_buttons.append(("1 FVG SELL", abhi_s+" < "+fvg_bot_s if abhi<r1h['fvg_bot']-5 else abhi_s+" > "+fvg_bot_s, abhi<r1h['fvg_bot']-5))
sell_buttons.append(("2 VWAP SELL", abhi_s+" < "+vwap_s if abhi<vwap_v else abhi_s+" > "+vwap_s, abhi<vwap_v))
sell_buttons.append(("3 EMA 15 SELL", abhi_s+" < "+ema15_s if abhi<ema15_v else abhi_s+" > "+ema15_s, abhi<ema15_v))
sell_buttons.append(("4 RSI 1H SELL", "RSI "+rsi_s+" < 50" if rsi_v<50 else "RSI "+rsi_s+" > 50", rsi_v<50))
sell_buttons.append(("5 Bollinger SELL", "Up "+bb_up_s+" | "+abhi_s, abhi >= bb_up-5))
sell_buttons.append(("6 MACD SELL", "MACD Neeche Hai" if macd_line<macd_sig_v else "MACD Upar Hai", macd_line<macd_sig_v))
sell_buttons.append(("7 Pin Bar SELL", "Upar Wick Lambi" if pin_sell else "Pin Nahi Bana", pin_sell))
sell_buttons.append(("8 HTF Trend SELL", "1H Trend Neeche" if not htf_up else "1H Trend Upar", not htf_up))
sell_buttons.append(("9 Sweep SELL", "Upar Sweep Hua" if sweep_sell else "Sweep Nahi Hua", sweep_sell))
sell_buttons.append(("10 FVG Touch SELL", "FVG Touch + Neeche" if fvg_touch and abhi<ema15_v else "FVG Touch Nahi", fvg_touch and abhi<ema15_v))
sell_buttons.append(("11 Session SELL", sess_sell_txt, sess_sell_ok))
sell_buttons.append(("12 Volume SELL", "VOL STRONG" if volume_strong else "VOL KAM", (not volume_strong) and abhi<ema15_v))
buy_c=sum(1 for _,_,v in buy_buttons if v); sell_c=sum(1 for _,_,v in sell_buttons if v)

st.markdown(f"<p style='text-align:center; color:white;'>{date_txt} | {time_txt} | PAKISTAN TIME</p>", unsafe_allow_html=True)
st.markdown(f"<div style='border:2px solid #FFD700; background:#1A1A1A; padding:12px; border-radius:10px; text-align:center;'><h2 style='color:white;'>GOLD: {abhi_s} [MANUAL] | ATR: {atr_s}</h2><p style='color:#FFD700;'>4H = MAZBOOT LATE | 1H = BEECH | 15M = JALDI</p></div>", unsafe_allow_html=True)
st.markdown(f"<div style='border:2px solid {r4h['fcol']}; background:#1A1A1A; padding:12px; border-radius:10px; text-align:center; margin-top:10px;'><h3 style='color:#FFD700;'>4H SETUP - MAZBOOT WALA - LATE - DIN ME 1 BAAR</h3><h3 style='color:{r4h['fcol']};'>{r4h['faisla']}</h3><p style='color:white;'>{r4h['entry']} | {r4h['sl']} | {r4h['tp']}</p><p style='color:white;'>BOS: {r4h['bos']} | {r4h['fvg']} | {r4h['react']}</p><p style='color:white;'>4H D: {r4h['d_bot']}-{r4h['d_top']} | 4H S: {r4h['s_bot']}-{r4h['s_top']} | VOL: {'MAZBOOT' if r4h['vol_ok'] else 'KAMZOR'}</p><p style='color:#00FF88;'><b>{r4h['chance_txt']} | {r4h['rr']}</b></p></div>", unsafe_allow_html=True)
st.markdown(f"<div style='background:#FFD700; color:black; text-align:center; padding:10px; border-radius:8px; font-weight:bold; margin-top:10px;'>BUTTON - SIRF ANDAZA - FAISLA NAHI KARTA<br>BUY {buy_c}/12 | SELL {sell_c}/12 | Resistance 1H: {r1h['res']} | Support 1H: {r1h['sup']} | RSI: {rsi_s}</div>", unsafe_allow_html=True)
bcol, scol = st.columns(2)
with bcol:
    st.markdown(f"<h3 style='color:#00FF88; text-align:center;'>BUY - SIRF ANDAZA<br>BUY: {buy_c}/12</h3>", unsafe_allow_html=True)
    for naam, val, ok in buy_buttons:
        bg = "#003311" if ok else "#1A1A1A"
        txt = "SABZ" if ok else "NAHI"
        st.markdown(f"<div style='background:{bg}; border:1px solid #555; padding:8px; border-radius:6px; margin:4px 0; color:white;'><b>{naam}</b><br>{val} - <b>{txt}</b></div>", unsafe_allow_html=True)
with scol:
    st.markdown(f"<h3 style='color:#FF4444; text-align:center;'>SELL - SIRF ANDAZA<br>SELL: {sell_c}/12</h3>", unsafe_allow_html=True)
    for naam, val, ok in sell_buttons:
        bg = "#330000" if ok else "#1A1A1A"
        txt = "LAL" if ok else "NAHI"
        st.markdown(f"<div style='background:{bg}; border:1px solid #555; padding:8px; border-radius:6px; margin:4px 0; color:white;'><b>{naam}</b><br>{val} - <b>{txt}</b></div>", unsafe_allow_html=True)
st.markdown("<div style='background:#FFD700; color:black; text-align:center; padding:10px; border-radius:8px; font-weight:bold; margin-top:15px;'>NEECHE WALA - JALDI WALA - BUTTON KE NEECHE</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"<div style='border:2px solid {r15['fcol']}; background:#1A1A1A; padding:10px; border-radius:10px; text-align:center;'><h3 style='color:#FFD700;'>15M - JALDI WALA</h3><h3 style='color:{r15['fcol']};'>{r15['faisla']}</h3><p style='color:white;'>{r15['entry']}</p><p style='color:white;'>{r15['sl']} | {r15['tp']}</p><p style='color:white;'>BOS: {r15['bos']} | {r15['fvg']}</p><p style='color:white;'>{r15['react']} | VOL: {'MAZBOOT' if r15['vol_ok'] else 'KAMZOR'}</p><p style='color:white;'>15M D: {r15['d_bot']}-{r15['d_top']} | S: {r15['s_bot']}-{r15['s_top']}</p><p style='color:white;'><b>{r15['chance_txt']} | {r15['rr']}</b></p></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div style='border:2px solid {r1h['fcol']}; background:#1A1A1A; padding:10px; border-radius:10px; text-align:center;'><h3 style='color:#FFD700;'>1H - BEECH WALA</h3><h3 style='color:{r1h['fcol']};'>{r1h['faisla']}</h3><p style='color:white;'>{r1h['entry']}</p><p style='color:white;'>{r1h['sl']} | {r1h['tp']}</p><p style='color:white;'>BOS: {r1h['bos']} | {r1h['fvg']}</p><p style='color:white;'>{r1h['react']} | VOL: {'MAZBOOT' if r1h['vol_ok'] else 'KAMZOR'}</p><p style='color:white;'>1H D: {r1h['d_bot']}-{r1h['d_top']} | S: {r1h['s_bot']}-{r1h['s_top']}</p><p style='color:white;'><b>{r1h['chance_txt']} | {r1h['rr']}</b></p></div>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:white;'>CHANCE 80%+ HO TO HI MAZBOOT SAMJHO - 60% SE KAM HO TO WAIT KARO</p>", unsafe_allow_html=True)

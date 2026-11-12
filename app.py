# WASEEM - V4.4 - FINAL FIXED - POORA SCRIPT - USTAD JI WALA
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import requests, io
import streamlit.components.v1 as components

st.set_page_config(page_title="WASEEM TRADER - V4.4", layout="centered")
st.title("WASEEM TRADER - V4.4 - INDICATOR SACH BOLEGA")

if "next_count" not in st.session_state:
    st.session_state.next_count = 0

col_next1, col_next2 = st.columns([1,3])
with col_next1:
    if st.button("NEXT ➡️", use_container_width=True):
        st.session_state.next_count += 1
        st.rerun()
with col_next2:
    st.write(f"NEXT dabaya gaya: {st.session_state.next_count} baar")

MANUAL_PRICE = st.number_input("MANUAL PRICE - SIRF MT5 SE MILANE KE LIYE - JAISE 3994.0", value=3994.0, key="manual_v44")
CHALAO = st.button("SIGNAL BANAO", key="signal_v44")

if CHALAO:
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
    df4h = GET_DATA("1mo","4h",60)
    df = GET_DATA("5d","1h",120)
    df15 = GET_DATA("2d","15m",120)
    if df is None or df15 is None or df4h is None:
        st.error("DATA NAHI AAYA - WAIT KARO - NAQLI SETUP NAHI DUNGA")
        st.stop()
    abhi = float(df['Close'].iloc[-1])
    manual_show = float(MANUAL_PRICE)
    pak_time = datetime.now() + timedelta(hours=5)
    date_txt = pak_time.strftime("%d %B %Y")
    time_txt = pak_time.strftime("%I:%M %p")
    abhi_s = str(int(abhi))
    manual_s = str(int(manual_show))
    farq = int(manual_show - abhi)
    farq_txt = "MT5 SE FARQ: " + str(farq) + " $"
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
        buy_n = 0
        if at_d: buy_n+=1
        if bos_up or fvg_bull: buy_n+=1
        if react_buy: buy_n+=1
        if vol_ok: buy_n+=1
        if trend_up: buy_n+=1
        sell_n = 0
        if at_s: sell_n+=1
        if bos_down or fvg_bear: sell_n+=1
        if react_sell: sell_n+=1
        if vol_ok: sell_n+=1
        if trend_down: sell_n+=1
        buy_score = buy_n*20
        sell_score = sell_n*20
        bos_txt = "BOS UP" if bos_up else "BOS DOWN" if bos_down else "BOS Nahi"
        fvg_txt = "FVG Bullish" if fvg_bull else "FVG Bearish" if fvg_bear else "FVG Nahi"
        if buy_n>=3 and buy_n>=sell_n:
            faisla = tf_name+f" BUY SETUP - {buy_n}/5 MIL GAYA"; fcol="#00FF88"
            entry="Buy "+str(int(d_bot))+" - "+str(int(d_top)); sl="SL: "+str(int(d_bot-sl_dist)); tp="TP: "+str(int(d_top+sl_dist*2))
            chance=buy_score; chance_txt="CHANCE: "+str(chance)+"% - MAZBOOT" if chance>=80 else "CHANCE: "+str(chance)+"% - THEEK HAI"
            rr_txt="RR: 1:2 - TRADE LENE LAYAQ"
        elif sell_n>=3:
            faisla = tf_name+f" SELL SETUP - {sell_n}/5 MIL GAYA"; fcol="#FF4444"
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
        if react_buy: react_txt="REACTION: MAZBOOT - UPAR UTHA"; react_ok=True
        elif react_sell: react_txt="REACTION: MAZBOOT - NEECHE GIRA"; react_ok=True
        elif at_d: react_txt="REACTION: KAMZOR - DEMAND PAR RUKA NAHI"; react_ok=False
        elif at_s: react_txt="REACTION: KAMZOR - SUPPLY PAR RUKA NAHI"; react_ok=False
        else: react_txt="REACTION: ABHI OB PAR NAHI"; react_ok=False
        return {'faisla':faisla,'fcol':fcol,'entry':entry,'sl':sl,'tp':tp,'chance':chance,'chance_txt':chance_txt,'rr':rr_txt,'bos':bos_txt,'fvg':fvg_txt,'react':react_txt,'react_ok':react_ok,'vol_ok':vol_ok,'d_bot':int(d_bot),'d_top':int(d_top),'s_bot':int(s_bot),'s_top':int(s_top),'fvg_bot':int(fvg_bot),'fvg_top':int(fvg_top),'trend_up':trend_up,'res':int(RES),'sup':int(SUP),'buy_n':buy_n,'sell_n':sell_n}
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
    buy_buttons.append(("1 FVG BUY ★", fvg_bot_s+"-"+fvg_top_s+" | "+abhi_s, fvg_touch))
    buy_buttons.append(("2 VWAP BUY", abhi_s+" > "+vwap_s if abhi>vwap_v else abhi_s+" < "+vwap_s, abhi>vwap_v))
    buy_buttons.append(("3 EMA 15 BUY", abhi_s+" > "+ema15_s if abhi>ema15_v else abhi_s+" < "+ema15_s, abhi>ema15_v))
    buy_buttons.append(("4 RSI 1H BUY", "RSI "+rsi_s+" > 50" if rsi_v>50 else "RSI "+rsi_s+" < 50", rsi_v>50))
    buy_buttons.append(("5 Bollinger BUY", "Low "+bb_low_s+" | "+abhi_s, abhi <= bb_low+5))
    buy_buttons.append(("6 MACD BUY", "MACD Upar Hai" if macd_line>macd_sig_v else "MACD Neeche Hai", macd_line>macd_sig_v))
    buy_buttons.append(("7 Pin Bar BUY ★", "Neeche Wick Lambi" if pin_buy else "Pin Nahi Bana", pin_buy))
    buy_buttons.append(("8 HTF Trend BUY ★", "1H Trend Upar" if htf_up else "1H Trend Neeche", htf_up))
    buy_buttons.append(("9 Sweep BUY ★", "Neeche Sweep Hua" if sweep_buy else "Sweep Nahi Hua", sweep_buy))
    buy_buttons.append(("10 FVG Touch BUY", "FVG Touch + Upar" if fvg_touch and abhi>ema15_v else "FVG Touch Nahi", fvg_touch and abhi>ema15_v))
    buy_buttons.append(("11 Session BUY", sess_buy_txt, sess_buy_ok))
    buy_buttons.append(("12 Volume BUY ★", vol_s+" / "+vol_avg_s, volume_strong and abhi>ema15_v))
    sell_buttons=[]
    sell_buttons.append(("1 FVG SELL ★", abhi_s+" < "+fvg_bot_s if abhi<r1h['fvg_bot']-5 else abhi_s+" > "+fvg_bot_s, abhi<r1h['fvg_bot']-5))
    sell_buttons.append(("2 VWAP SELL", abhi_s+" < "+vwap_s if abhi<vwap_v else abhi_s+" > "+vwap_s, abhi<vwap_v))
    sell_buttons.append(("3 EMA 15 SELL", abhi_s+" < "+ema15_s if abhi<ema15_v else abhi_s+" > "+ema15_s, abhi<ema15_v))
    sell_buttons.append(("4 RSI 1H SELL", "RSI "+rsi_s+" < 50" if rsi_v<50 else "RSI "+rsi_s+" > 50", rsi_v<50))
    sell_buttons.append(("5 Bollinger SELL", "Up "+bb_up_s+" | "+abhi_s, abhi >= bb_up-5))
    sell_buttons.append(("6 MACD SELL", "MACD Neeche Hai" if macd_line<macd_sig_v else "MACD Upar Hai", macd_line<macd_sig_v))
    sell_buttons.append(("7 Pin Bar SELL ★", "Upar Wick Lambi" if pin_sell else "Pin Nahi Bana", pin_sell))
    sell_buttons.append(("8 HTF Trend SELL ★", "1H Trend Neeche" if not htf_up else "1H Trend Upar", not htf_up))
    sell_buttons.append(("9 Sweep SELL ★", "Upar Sweep Hua" if sweep_sell else "Sweep Nahi Hua", sweep_sell))
    sell_buttons.append(("10 FVG Touch SELL", "FVG Touch + Neeche" if fvg_touch and abhi<ema15_v else "FVG Touch Nahi", fvg_touch and abhi<ema15_v))
    sell_buttons.append(("11 Session SELL", sess_sell_txt, sess_sell_ok))
    sell_buttons.append(("12 Volume SELL ★", "VOL STRONG" if volume_strong else "VOL KAM", (not volume_strong) and abhi<ema15_v))
    buy_c=sum(1 for _,_,v in buy_buttons if v); sell_c=sum(1 for _,_,v in sell_buttons if v)
    st.session_state['has_data']=True
    st.session_state['last_r4h']=r4h; st.session_state['last_r1h']=r1h; st.session_state['last_r15']=r15
    st.session_state['last_buy_buttons']=buy_buttons; st.session_state['last_sell_buttons']=sell_buttons
    st.session_state['last_buy_c']=buy_c; st.session_state['last_sell_c']=sell_c
    st.session_state['last_abhi_s']=abhi_s; st.session_state['last_manual_s']=manual_s; st.session_state['last_farq']=farq_txt
    st.session_state['last_rsi_s']=rsi_s; st.session_state['last_atr_s']=atr_s
    st.session_state['last_date']=date_txt; st.session_state['last_time']=time_txt
    st.success("HISAB HO GAYA - INDICATOR YAHOO SE - MANUAL SE KOI CONNECTION NAHI")

if st.session_state.get('has_data', False):
    r4h = st.session_state['last_r4h']
    r1h = st.session_state['last_r1h']
    r15 = st.session_state['last_r15']
    buy_buttons = st.session_state['last_buy_buttons']
    sell_buttons = st.session_state['last_sell_buttons']
    buy_c = st.session_state['last_buy_c']
    sell_c = st.session_state['last_sell_c']
    abhi_s = st.session_state['last_abhi_s']
    manual_s = st.session_state['last_manual_s']
    farq_txt = st.session_state['last_farq']
    rsi_s = st.session_state['last_rsi_s']
    atr_s = st.session_state['last_atr_s']
    date_txt = st.session_state['last_date']
    time_txt = st.session_state['last_time']
    fig,ax = plt.subplots(figsize=(10,19))
    ax.set_xlim(0,10); ax.set_ylim(0,19); ax.axis('off')
    fig.patch.set_facecolor('#0A0A0A'); ax.set_facecolor('#0A0A0A')
    box = patches.FancyBboxPatch
    ax.add_patch(box((0.3,18.3),9.4,0.6, boxstyle="round,pad=0.1", facecolor='#0A0A0A', edgecolor='#FFD700', linewidth=2.5))
    ax.text(5,18.60,'WASEEM  TRADER - V4.4', ha='center',va='center', color='#FFD700', fontsize=20,weight='bold')
    ax.add_patch(box((0.3,17.65),9.4,0.50, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor='#FFD700', linewidth=1))
    ax.text(5,17.90,date_txt + "  |  " + time_txt + "  |  PAKISTAN TIME", ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
    ax.add_patch(box((0.3,16.90),9.4,0.65, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor='#FFD700', linewidth=1.2))
    ax.text(5,17.30,'GOLD YAHOO: ' + abhi_s + '  |  ATR: ' + atr_s, ha='center',va='center', fontsize=18,weight='bold', color='white')
    ax.text(5,17.02,'MT5 MANUAL: ' + manual_s + '  |  ' + farq_txt, ha='center',va='center', fontsize=8,weight='bold', color='#FFD700')
    ax.add_patch(box((0.3,15.15),9.4,1.60, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r4h['fcol'], linewidth=2))
    ax.text(5,16.50,'4H SETUP - MAZBOOT WALA', ha='center',va='center', fontsize=10,weight='bold', color='#FFD700')
    ax.text(5,16.15,r4h['faisla'], ha='center',va='center', fontsize=9,weight='bold', color=r4h['fcol'])
    ax.text(5,15.80,r4h['entry']+"  |  "+r4h['sl']+"  |  "+r4h['tp'], ha='center',va='center', fontsize=8,weight='bold', color='white')
    ax.text(5,15.45,'BOS: '+r4h['bos']+' | '+r4h['fvg']+' | '+r4h['react'], ha='center',va='center', fontsize=7.5,color='white')
    ax.text(5,15.20,r4h['chance_txt']+"  |  "+r4h['rr'], ha='center',va='center', fontsize=8.5,weight='bold', color='#00FF88' if r4h['chance']>=80 else '#FFAA00')
    ax.add_patch(box((0.3,14.60),9.4,0.45, boxstyle="round,pad=0.1", facecolor='#FFD700'))
    ax.text(5,14.82,'BUTTON - SIRF ANDAZA - FAISLA NAHI KARTA', ha='center',va='center', fontsize=9,weight='bold', color='black')
    ax.text(5,14.65,'BUY '+str(buy_c)+'/12  |  SELL '+str(sell_c)+'/12  |  RSI: '+rsi_s, ha='center',va='center', fontsize=7.5,color='black')
    ax.add_patch(box((0.3,5.20),4.6,9.30, boxstyle="round,pad=0.1", facecolor='#0A1A0A', edgecolor='#00FF88', linewidth=1.8))
    ax.text(2.6,14.20,'BUY - SIRF ANDAZA', ha='center', va='center', fontsize=10, weight='bold', color='#00FF88')
    ax.text(2.6,13.85,'BUY: ' + str(buy_c) + '/12', ha='center', va='center', fontsize=10, weight='bold', color='white')
    for i,(naam,val,ok) in enumerate(buy_buttons):
        y = 13.40 - i*0.68
        is_star = "★" in naam
        if ok: rang = '#00FF88'; face = '#003311'; txt = "SABZ"
        else: rang = '#555555'; face = '#1A1A1A'; txt = "NAHI"
        edge = '#FFD700' if is_star else rang; lw = 2.0 if is_star else 1.0
        ax.add_patch(patches.Rectangle((0.5,y-0.28),4.2,0.58, facecolor=face, edgecolor=edge, linewidth=lw))
        ax.text(0.65,y+0.12,naam, ha='left', va='center', fontsize=7.5, weight='bold', color='#FFD700' if is_star else 'white')
        ax.text(0.65,y-0.12,val, ha='left', va='center', fontsize=6.5, color='white')
        ax.text(4.55,y,txt, ha='right', va='center', fontsize=6.5, weight='bold', color=rang)
    ax.add_patch(box((5.1,5.20),4.6,9.30, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor='#FF4444', linewidth=1.8))
    ax.text(7.4,14.20,'SELL - SIRF ANDAZA', ha='center', va='center', fontsize=10, weight='bold', color='#FF4444')
    ax.text(7.4,13.85,'SELL: ' + str(sell_c) + '/12', ha='center', va='center', fontsize=10, weight='bold', color='white')
    for i,(naam,val,ok) in enumerate(sell_buttons):
        y = 13.40 - i*0.68
        is_star = "★" in naam
        if ok: rang = '#FF4444'; face = '#330000'; txt = "LAL"
        else: rang = '#555555'; face = '#1A1A1A'; txt = "NAHI"
        edge = '#FFD700' if is_star else rang; lw = 2.0 if is_star else 1.0
        ax.add_patch(patches.Rectangle((5.3,y-0.28),4.2,0.58, facecolor=face, edgecolor=edge, linewidth=lw))
        ax.text(5.45,y+0.12,naam, ha='left', va='center', fontsize=7.5, weight='bold', color='#FFD700' if is_star else 'white')
        ax.text(5.45,y-0.12,val, ha='left', va='center', fontsize=6.5, color='white')
        ax.text(9.35,y,txt, ha='right', va='center', fontsize=6.5, weight='bold', color=rang)
    ax.plot([5.0, 5.0], [5.20, 14.50], color='red', linewidth=3)
    ax.add_patch(box((0.3,4.65),9.4,0.45, boxstyle="round,pad=0.1", facecolor='#FFD700'))
    ax.text(5,4.87,'NEECHE WALA - JALDI WALA - INDICATOR KE QAREEB', ha='center',va='center', fontsize=8,weight='bold', color='black')
    ax.add_patch(box((0.3,2.35),4.45,2.20, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r15['fcol'], linewidth=2))
    ax.text(2.52,4.35,'15M - JALDI WALA', ha='center',va='center', fontsize=8,weight='bold', color='#FFD700')
    ax.text(2.52,4.00,r15['faisla'], ha='center',va='center', fontsize=7.5,weight='bold', color=r15['fcol'])
    ax.text(2.52,3.65,r15['entry'], ha='center',va='center', fontsize=7.5,weight='bold', color='white')
    ax.text(2.52,3.30,r15['sl']+"  |  "+r15['tp'], ha='center',va='center', fontsize=7,color='white')
    ax.text(2.52,2.95,r15['react'], ha='center',va='center', fontsize=7,color='white')
    ax.text(2.52,2.55,r15['chance_txt'], ha='center',va='center', fontsize=7.5,weight='bold', color='#00FF88' if r15['chance']>=80 else '#FFAA00')
    ax.add_patch(box((5.25,2.35),4.45,2.20, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r1h['fcol'], linewidth=2))
    ax.text(7.47,4.35,'1H - BEECH WALA', ha='center',va='center', fontsize=8,weight='bold', color='#FFD700')
    ax.text(7.47,4.00,r1h['faisla'], ha='center',va='center', fontsize=7.5,weight='bold', color=r1h['fcol'])
    ax.text(7.47,3.65,r1h['entry'], ha='center',va='center', fontsize=7.5,weight='bold', color='white')
    ax.text(7.47,3.30,r1h['sl']+"  |  "+r1h['tp'], ha='center',va='center', fontsize=7,color='white')
    ax.text(7.47,2.95,r1h['react'], ha='center',va='center', fontsize=7,color='white')
    ax.text(7.47,2.55,r1h['chance_txt'], ha='center',va='center', fontsize=7.5,weight='bold', color='#00FF88' if r1h['chance']>=80 else '#FFAA00')
    ax.plot([5.0, 5.0], [2.35, 4.60], color='red', linewidth=3)
    ax.text(5,1.85,'★ = ZAROORI BUTTON  |  CHANCE 60%+ HO TO SETUP', ha='center',va='center', fontsize=8,weight='bold', color='#FFD700')
    ax.text(5,1.45,'INDICATOR YAHOO SE - MANUAL SIRF MILANE KE LIYE', ha='center',va='center', fontsize=7,color='#AAAAAA')
    ax.text(5,1.05,'MT5 SE FARQ DEKHO - AGAR ZYADA FARQ HO TO WAIT KARO', ha='center',va='center', fontsize=7,weight='bold', color='white')
    ax.text(5,0.60,'PEHLE DISCUSS KARO - PHIR TRADE KARO', ha='center',va='center', fontsize=8,weight='bold', color='#FFD700')
    st.pyplot(fig)
else:
    st.info("👆 PEHLE MANUAL PRICE DALO - PHIR SIGNAL BANAO DABAO - PHIR TASVEER AAYEGI")

# ============ USTAD JI - PEHLA PAGE - FINAL WALA ============
st.markdown("<h3 style='text-align:center;color:#0a1f44'>USTAD JI - PEHLA PAGE - FINAL WALA</h3>", unsafe_allow_html=True)
mt5_raw = st.text_input("Ustad Ji, MT5 wali price daalein (misal 3983)", value="3983")
try:
    mt5 = float(mt5_raw)
except:
    mt5 = 3983.0
if mt5 < 1000 or mt5 > 5000:
    st.error(f"USTAD JI, PRICE GALAT HAI - Aap ne daali: {mt5_raw} - Puri price daalo - Misal 3983")
    st.stop()
health = []
def health_add(name, ok):
    health.append(f"{name} {'OK' if ok else 'FAIL'}")
health_add("PRICE", True)
now_dt = datetime.now()
now_min = now_dt.minute
age_5m = now_min % 5
age_15m = now_min % 15
age_1h = now_min % 60
hour_now = now_dt.hour
health_add("TIME", True)
if 11 <= hour_now < 15:
    session_name = "LONDON KILL ZONE"; session_note = "London Kill Zone Hai - Asli Move Aayega"; session_score_bonus = 10
elif 17 <= hour_now < 22:
    session_name = "NEW YORK KILL ZONE"; session_note = "New York Kill Zone Hai - Sab Se Zyada Volume"; session_score_bonus = 10
elif 0 <= hour_now < 8:
    session_name = "ASIA"; session_note = "Asia Hai - Sirf Manipulation Hogi - Range Banegi"; session_score_bonus = -10
else:
    session_name = "OFF"; session_note = "Session Off Hai - Manipulation Wala Time"; session_score_bonus = -5
corner_warnings = []
def yahoo_fetch(symbol, interval, range_):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_}"
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=12)
        j = r.json(); res = j['chart']['result'][0]; q = res['indicators']['quote'][0]
        closes=q['close']; highs=q['high']; lows=q['low']; opens=q['open']; vols=q['volume']
        c2=[];h2=[];l2=[];o2=[];v2=[]
        for i in range(len(closes)):
            if closes[i] is not None and highs[i] is not None and lows[i] is not None and opens[i] is not None:
                c2.append(closes[i]); h2.append(highs[i]); l2.append(lows[i]); o2.append(opens[i]); v2.append(vols[i] if vols[i] is not None else None)
        price = res['meta']['regularMarketPrice']
        if price is None or len(c2) < 50: return {"ok":False}
        return {"ok":True,"closes":c2,"highs":h2,"lows":l2,"opens":o2,"vols":v2,"price":price,"symbol":symbol}
    except: return {"ok":False}
def repair_line(d):
    if not d["ok"]: return d
    vols=d["vols"]; last_good_vol=None
    for v in reversed(vols):
        if v is not None and v!=0 and v>0: last_good_vol=v; break
    new_vols=[]
    for v in vols:
        if v is None or v==0: new_vols.append(last_good_vol if last_good_vol is not None else None)
        else: new_vols.append(v); last_good_vol=v
    d["vols"]=new_vols
    for key in ["closes","highs","lows","opens"]:
        arr=d[key]; new_arr=[]; last_good=arr[0] if len(arr)>0 else mt5
        for val in arr:
            if val is None or val==0: new_arr.append(last_good)
            else: new_arr.append(val); last_good=val
        d[key]=new_arr
    return d
def get_one_time(interval_yahoo):
    d2 = yahoo_fetch("XAUUSD=X", interval_yahoo, "5d")
    if d2["ok"]: return repair_line(d2), "SPOT"
    d3 = yahoo_fetch("GC=F", interval_yahoo, "5d")
    if d3["ok"]: return repair_line(d3), "FUTURE"
    return {"ok":False}, "KHALI"
d5_raw, src5 = get_one_time("5m")
d15_raw, src15 = get_one_time("15m")
d1h_raw, src1h = get_one_time("60m")
health_add("DATA", d5_raw["ok"] or d15_raw["ok"] or d1h_raw["ok"])
if d5_raw["ok"]: yahoo_price_raw = d5_raw["price"]
elif d15_raw["ok"]: yahoo_price_raw = d15_raw["price"]
elif d1h_raw["ok"]: yahoo_price_raw = d1h_raw["price"]
else: yahoo_price_raw = mt5
farq_asli = yahoo_price_raw - mt5
if abs(farq_asli) > 20:
    if "Farq-Zyada" not in corner_warnings: corner_warnings.append("Farq-Zyada")
shift = mt5 - yahoo_price_raw
def apply_shift(d):
    if not d["ok"]: return d
    d2=dict(d); d2["closes"]=[x+shift for x in d["closes"]]; d2["highs"]=[x+shift for x in d["highs"]]; d2["lows"]=[x+shift for x in d["lows"]]; d2["opens"]=[x+shift for x in d["opens"]]; d2["price"]=d["price"]+shift; return d2
d5=apply_shift(d5_raw); d15=apply_shift(d15_raw); d1h=apply_shift(d1h_raw)
if d5["ok"]: yahoo_price=d5["price"]
elif d15["ok"]: yahoo_price=d15["price"]
elif d1h["ok"]: yahoo_price=d1h["price"]
else: yahoo_price=mt5
farq=farq_asli
if farq < -4: side_farq="SELL"; machhli=f"MACHHLI SELL - Farq {farq:.2f}"
elif farq > 4: side_farq="BUY"; machhli=f"MACHHLI BUY - Farq {farq:.2f}"
else:
    if farq>=0: side_farq="BUY"; machhli=f"MACHHLI HALKI BUY - Farq {farq:.2f}"
    else: side_farq="SELL"; machhli=f"MACHHLI HALKI SELL - Farq {farq:.2f}"
def get_pakki_arrays(d):
    if not d["ok"] or len(d["closes"])<3: return d
    d2=dict(d); d2["closes"]=d["closes"][:-1]; d2["highs"]=d["highs"][:-1]; d2["lows"]=d["lows"][:-1]; d2["opens"]=d["opens"][:-1]; d2["vols"]=d["vols"][:-1] if len(d["vols"])==len(d["closes"]) else d["vols"]; return d2
d5_pakki=get_pakki_arrays(d5); d15_pakki=get_pakki_arrays(d15); d1h_pakki=get_pakki_arrays(d1h)
health_add("PAKKI-CANDLE", True)
def calc_rsi(closes, period=14):
    if len(closes)<period+1: return None
    gains=0; losses=0
    for i in range(len(closes)-period, len(closes)):
        diff=closes[i]-closes[i-1]
        if diff>0: gains+=diff
        else: losses+=-diff
    avg_g=gains/period; avg_l=losses/period
    if avg_l==0: return 100.0
    rs=avg_g/avg_l; return 100-(100/(1+rs))
def calc_atr_list(highs,lows,closes,period=14):
    atrs=[None]*len(closes)
    for i in range(1,len(closes)):
        if i<period: atrs[i]=None
        else:
            trs=[]
            for k in range(i-period+1,i+1):
                tr2=max(highs[k]-lows[k], abs(highs[k]-closes[k-1]), abs(lows[k]-closes[k-1])); trs.append(tr2)
            atrs[i]=sum(trs)/len(trs)
    return atrs
def calc_vwap_single(d1h_pakki):
    if not d1h_pakki["ok"]: return None
    closes=d1h_pakki["closes"]; highs=d1h_pakki["highs"]; lows=d1h_pakki["lows"]; vols=d1h_pakki.get("vols",[]); total_pv=0; total_v=0
    for i in range(max(0,len(closes)-50), len(closes)):
        tp=(highs[i]+lows[i]+closes[i])/3; v=vols[i] if i<len(vols) and vols[i] is not None and vols[i]!=0 else 1; total_pv+=tp*v; total_v+=v
    if total_v==0: return None
    return total_pv/total_v
vwap_common=calc_vwap_single(d1h_pakki)
if vwap_common is not None: vwap_common_side="VWAP Upar" if mt5>vwap_common else "VWAP Neeche"
else: vwap_common_side="VWAP Nahi"
health_add("VWAP", vwap_common is not None)
if session_name=="ASIA":
    regime = "RANGE"
elif d1h_pakki["ok"] and vwap_common is not None:
    dist_vwap = abs(mt5 - vwap_common)
    if dist_vwap < 8: regime = "RANGE"
    else: regime = "TREND"
else: regime = "RANGE"
try:
    dxy_data = yahoo_fetch("DX-Y.NYB", "60m", "5d")
    if dxy_data["ok"] and len(dxy_data["closes"])>5:
        dxy_now = dxy_data["closes"][-1]; dxy_old = dxy_data["closes"][-5]
        dxy_up = dxy_now > dxy_old
        dxy_txt = "DXY Upar" if dxy_up else "DXY Neeche"
    else: dxy_up=False; dxy_txt="DXY Nahi"
except: dxy_up=False; dxy_txt="DXY Nahi"
try:
    yield_data = yahoo_fetch("^TNX", "60m", "5d")
    if yield_data["ok"] and len(yield_data["closes"])>2:
        yield_now = yield_data["closes"][-1]
        yield_txt = f"Yield {yield_now:.2f}%"
        yield_high = yield_now > 5.0
    else: yield_now=0; yield_txt="Yield Nahi"; yield_high=False
except: yield_now=0; yield_txt="Yield Nahi"; yield_high=False
health_add("MACRO-DXY", dxy_txt!="DXY Nahi")
def check_pin(o,h,l,c):
    body=abs(c-o)
    if body<0.01: body=0.01
    up=h-max(o,c); low=min(o,c)-l
    if low>body*1.5 and low>up*1.5: return "Pin BUY"
    if up>body*1.5 and up>low*1.5: return "Pin SELL"
    return "Pin Nahi"
def check_fvg(h,l):
    if len(h)<3: return "FVG Nahi"
    if l[-1]>h[-3]: return "FVG BUY"
    if h[-1]<l[-3]: return "FVG SELL"
    return "FVG Nahi"
def check_choch(h,l):
    if len(h)<20: return "CHoCH Nahi"
    ph=max(h[-20:-5]); pl=min(l[-20:-5])
    if h[-1]>ph: return "CHoCH BUY"
    if l[-1]<pl: return "CHoCH SELL"
    return "CHoCH Nahi"
def check_liquidity_sweep(highs,lows,closes):
    if len(highs)<25: return "Liq Nahi"
    prev_high=max(highs[-21:-1]); prev_low=min(lows[-21:-1]); last_high=highs[-1]; last_low=lows[-1]; last_close=closes[-1]
    if last_high>prev_high and last_close<prev_high: return "Liq Sweep SELL"
    if last_low<prev_low and last_close>prev_low: return "Liq Sweep BUY"
    return "Liq Nahi"
def check_sweep_displacement(d_pakki, liq_txt):
    if "Sweep" not in liq_txt: return False, "Sweep Nahi"
    if not d_pakki["ok"] or len(d_pakki["closes"])<5: return False, "Sweep Jhoota"
    closes=d_pakki["closes"]; highs=d_pakki["highs"]; lows=d_pakki["lows"]
    atrs=calc_atr_list(highs,lows,closes); atr_now=atrs[-1] if atrs[-1] is not None else 5
    move = abs(closes[-1]-closes[-3])
    if move >= atr_now*0.8: return True, "Sweep SACHA + Displacement"
    else: return False, "Sweep JHOOTA - Displacement Nahi"
def check_order_block(opens,closes,highs,lows):
    if len(closes)<5: return "OB Nahi", None, None
    cur=closes[-1]
    for i in range(len(closes)-4, len(closes)-1):
        o=opens[i]; c=closes[i]; o_next=opens[i+1]; c_next=closes[i+1]; body=abs(c-o); body_next=abs(c_next-o_next)
        if body_next>body*1.5:
            if c_next<o_next and c>o:
                ob_low=min(o,c); ob_high=max(o,c)
                if ob_low<=cur<=ob_high+2: return "OB BUY Me Hai", ob_low, ob_high
                elif cur>ob_high: return "OB BUY Tor Diya", ob_low, ob_high
            if c_next>o_next and c<o:
                ob_low=min(o,c); ob_high=max(o,c)
                if ob_low-2<=cur<=ob_high: return "OB SELL Me Hai", ob_low, ob_high
                elif cur<ob_low: return "OB SELL Tor Diya", ob_low, ob_high
    return "OB Nahi", None, None
def calc_volume(vols, src_name):
    if src_name=="FUTURE": return {"text":"Vol FUTURE Me Nahi","trend":"FUTURE","pct":0}
    if not vols or len(vols)<22: return {"text":"Vol Nahi","trend":"NAHI","pct":0}
    last=None
    for v in reversed(vols[-3:]):
        if v is not None and v!=0: last=v; break
    if last is None: return {"text":"Vol FUTURE Me Nahi","trend":"FUTURE","pct":0}
    avg_list=[v for v in vols[-22:-2] if v is not None and v!=0]
    if len(avg_list)<5: return {"text":"Vol FUTURE Me Nahi","trend":"FUTURE","pct":0}
    avg=sum(avg_list)/len(avg_list)
    if avg==0: return {"text":"Vol FUTURE Me Nahi","trend":"FUTURE","pct":0}
    pct=int((last-avg)*100/avg)
    if last>avg*1.2: return {"text":f"Vol +{pct}%","trend":"BADH","pct":pct}
    elif last<avg*0.8: return {"text":f"Vol {pct}%","trend":"GIR","pct":pct}
    else: return {"text":f"Vol {pct}%","trend":"NORMAL","pct":pct}
def calc_tp_hit_both(opens,closes,highs,lows,atrs,look_ahead,tp_mult):
    buy_pins=[]; sell_pins=[]
    for i in range(max(20,len(closes)-150), len(closes)-1):
        if atrs[i] is None or atrs[i]==0: continue
        oo=opens[i]; cc=closes[i]; hh=highs[i]; ll=lows[i]; b=abs(cc-oo)
        if b<0.01: b=0.01
        lw=min(oo,cc)-ll; uw=hh-max(oo,cc); bull=lw>b*1.5; bear=uw>b*1.5
        if bull or bear:
            E=cc; atr_here=atrs[i]; sl=atr_here*1.5; tp_small=atr_here*1.5; tp1=atr_here*tp_mult
            if bull:
                slP=E-sl; tpSP=E+tp_small; tpP=E+tp1; hit_small="NAHI"; hit_big="NAHI"
                for j in range(i+1, min(i+1+look_ahead, len(closes))):
                    if highs[j]>=tpSP and hit_small=="NAHI": hit_small="TP"
                    if highs[j]>=tpP and hit_big=="NAHI": hit_big="TP"
                    if lows[j]<=slP: break
                buy_pins.append((hit_small,hit_big))
            else:
                slP=E+sl; tpSP=E-tp_small; tpP=E-tp1; hit_small="NAHI"; hit_big="NAHI"
                for j in range(i+1, min(i+1+look_ahead, len(closes))):
                    if lows[j]<=tpSP and hit_small=="NAHI": hit_small="TP"
                    if lows[j]<=tpP and hit_big=="NAHI": hit_big="TP"
                    if highs[j]>=slP: break
                sell_pins.append((hit_small,hit_big))
    buy_pins=buy_pins[-20:]; sell_pins=sell_pins[-20:]
    def make(pins):
        if len(pins)==0: return {"pct":0,"small_pct":0,"txt":"TP Data Nahi"}
        ws=sum(1 for x in pins if x[0]=="TP"); wb=sum(1 for x in pins if x[1]=="TP"); t=len(pins); ps=int(ws*100/t); pb=int(wb*100/t); return {"pct":pb,"small_pct":ps,"txt":f"TP {pb}% - {wb}/{t}"}
    return {"buy":make(buy_pins),"sell":make(sell_pins)}
def process(d_pakki, age_min, adhuri_limit, src_name, look_ahead, tp_mult):
    if not d_pakki["ok"]:
        return {"rsi":"Nahi","atr":"Nahi","pin":"Data Nahi","fvg":"Data Nahi","choch":"Data Nahi","liq":"Data Nahi","ob":"Data Nahi","ob_low":None,"ob_high":None,"vwap_side":vwap_common_side,"vol":{"text":"Vol Nahi","trend":"NAHI","pct":0},"tp":{"buy":{"pct":0,"small_pct":0,"txt":""},"sell":{"pct":0,"small_pct":0,"txt":""}},"E":mt5,"adhuri":True,"rsi_val":None,"age":age_min,"src":src_name,"sweep_sacha":False,"sweep_note":"Sweep Nahi","trap":""}
    closes=d_pakki["closes"]; highs=d_pakki["highs"]; lows=d_pakki["lows"]; opens=d_pakki["opens"]; vols=d_pakki.get("vols",[])
    rsi=calc_rsi(closes); atrs=calc_atr_list(highs,lows,closes); atr=atrs[-1]
    pin=check_pin(opens[-1],highs[-1],lows[-1],closes[-1]); fvg=check_fvg(highs,lows); choch=check_choch(highs,lows); liq=check_liquidity_sweep(highs,lows,closes); ob, ob_low, ob_high = check_order_block(opens,closes,highs,lows); vol=calc_volume(vols,src_name); tp=calc_tp_hit_both(opens,closes,highs,lows,atrs,look_ahead,tp_mult); adhuri=False
    if age_min<adhuri_limit: adhuri=True
    E=closes[-1]
    sweep_sacha, sweep_note = check_sweep_displacement(d_pakki, liq)
    trap=""
    if choch=="CHoCH BUY" and vol["trend"]!="BADH" and rsi is not None and rsi>70:
        trap="BULL TRAP"
    elif choch=="CHoCH SELL" and vol["trend"]!="BADH" and rsi is not None and rsi<30:
        trap="BEAR TRAP"
    return {"rsi":f"{rsi:.0f}" if rsi is not None else "Nahi","atr":f"{atr:.2f}" if atr is not None else "Nahi","pin":pin,"fvg":fvg,"choch":choch,"liq":liq,"ob":ob,"ob_low":ob_low,"ob_high":ob_high,"vwap_side":vwap_common_side,"vol":vol,"tp":tp,"E":E,"adhuri":adhuri,"rsi_val":rsi,"age":age_min,"src":src_name,"sweep_sacha":sweep_sacha,"sweep_note":sweep_note,"trap":trap}
p5=process(d5_pakki, age_5m, 4, src5, 10, 2.5)
p15=process(d15_pakki, age_15m, 12, src15, 5, 2.0)
p1h=process(d1h_pakki, age_1h, 45, src1h, 3, 1.5)
health_add("SETUP", True)
if p1h["rsi_val"] is not None and p1h["rsi_val"]<20:
    if "RSI-Oversold" not in corner_warnings: corner_warnings.append("RSI-Oversold")
elif p1h["rsi_val"] is not None and p1h["rsi_val"]>80:
    if "RSI-Overbought" not in corner_warnings: corner_warnings.append("RSI-Overbought")
if p5["trap"]!="" or p15["trap"]!="" or p1h["trap"]!="":
    if "TRAP" not in corner_warnings: corner_warnings.append("TRAP")
def candle_side_sach(p):
    buy_count = sum([1 for x in [p["pin"],p["fvg"],p["choch"],p["liq"]] if "BUY" in x])
    sell_count = sum([1 for x in [p["pin"],p["fvg"],p["choch"],p["liq"]] if "SELL" in x])
    if buy_count==0 and sell_count==0:
        return side_farq, "KUCH NAHI BANA"
    if buy_count>0 and sell_count>0:
        if buy_count > sell_count: return "BUY", "ANDAR MIXED - BUY Zyada"
        elif sell_count > buy_count: return "SELL", "ANDAR MIXED - SELL Zyada"
        else: return side_farq, "ANDAR MIXED - BARABAR - MACHHLI PAR"
    if buy_count>0: return "BUY", "SAAF"
    if sell_count>0: return "SELL", "SAAF"
    return side_farq, "MACHHLI PAR"
c5, note5 = candle_side_sach(p5)
c15, note15 = candle_side_sach(p15)
c1h, note1h = candle_side_sach(p1h)
def calc_chance_advance(p, candle):
    if candle=="BUY": tp_pct=p["tp"]["buy"]["pct"]
    else: tp_pct=p["tp"]["sell"]["pct"]
    score_tp = tp_pct * 0.35
    if candle==side_farq: score_machhli=5 if abs(farq)>=4 else 3
    else: score_machhli=0
    if p["vol"]["trend"]=="BADH": score_vol=15
    elif p["vol"]["trend"]=="NORMAL": score_vol=10
    elif p["vol"]["trend"]=="GIR": score_vol=3
    else: score_vol=10
    rsi_v=p["rsi_val"]; score_rsi=5
    if rsi_v is not None:
        if candle=="BUY" and rsi_v<70: score_rsi=10
        elif candle=="SELL" and rsi_v>30: score_rsi=10
        else: score_rsi=2
    score_adhuri=2 if p["adhuri"] else 10
    score_liq=0
    if candle=="BUY" and "BUY" in p["liq"]:
        score_liq=20 if p["sweep_sacha"] else 0
    elif candle=="SELL" and "SELL" in p["liq"]:
        score_liq=20 if p["sweep_sacha"] else 0
    score_ob=0
    score_vwap=0
    if candle=="BUY" and "Upar" in p["vwap_side"]: score_vwap=5
    elif candle=="SELL" and "Neeche" in p["vwap_side"]: score_vwap=5
    elif candle=="BUY" and "Neeche" in p["vwap_side"]: score_vwap=-5
    elif candle=="SELL" and "Upar" in p["vwap_side"]: score_vwap=-5
    score_session=session_score_bonus
    score_regime=0
    if regime=="RANGE" and score_liq==0: score_regime=-3
    score_macro=0
    if candle=="BUY" and dxy_up: score_macro-=10
    if candle=="SELL" and not dxy_up: score_macro-=5
    if candle=="BUY" and yield_high: score_macro-=10
    score_trap=0
    if p["trap"]!="": score_trap=-7
    total=int(round(score_tp+score_machhli+score_vol+score_rsi+score_adhuri+score_liq+score_ob+score_vwap+score_session+score_regime+score_macro+score_trap))
    if total < 1: total = 1
    if total > 95: total = 95
    return total, tp_pct
ch5,tp5=calc_chance_advance(p5,c5); ch15,tp15=calc_chance_advance(p15,c15); ch1h,tp1h=calc_chance_advance(p1h,c1h)
def equity_for(chance):
    if chance>=80: return ("0.05","2%","FULL ENTRY")
    elif chance>=70: return ("0.03","1.5%","BADI ENTRY")
    elif chance>=60: return ("0.02","1%","NORMAL ENTRY")
    elif chance>=50: return ("0.01","0.5%","CHOTI ENTRY")
    else: return ("0.00","0%","TRADE NAHI - CHANCE KAM HAI")
buy_count_final = sum([1 for x in [c5,c15,c1h] if x=="BUY"])
sell_count_final = sum([1 for x in [c5,c15,c1h] if x=="SELL"])
mixed=False
if not (c5==c15==c1h):
    mixed=True
    if "MIXED" not in corner_warnings: corner_warnings.append("MIXED")
if src5=="FUTURE" or src15=="FUTURE" or src1h=="FUTURE":
    if "Future-Vol" not in corner_warnings: corner_warnings.append("Future-Vol")
if "Sweep" in p5["liq"] or "Sweep" in p15["liq"] or "Sweep" in p1h["liq"]:
    if "Liq-Sweep" not in corner_warnings: corner_warnings.append("Liq-Sweep")
all_below_50=(ch5<50 and ch15<50 and ch1h<50)
candidates=[(ch5,c5,"5M"),(ch15,c15,"15M"),(ch1h,c1h,"1H")]
if buy_count_final > sell_count_final:
    majority_side="BUY"
    majority_candidates=[x for x in candidates if x[1]=="BUY"]
elif sell_count_final > buy_count_final:
    majority_side="SELL"
    majority_candidates=[x for x in candidates if x[1]=="SELL"]
else:
    majority_side=None
    majority_candidates=candidates
majority_sorted=sorted(majority_candidates, key=lambda x: x[0], reverse=True)
final_chance, final_side, final_time=majority_sorted[0]
if majority_side is not None:
    final_side=majority_side
final_p = p5 if final_time=="5M" else p15 if final_time=="15M" else p1h
def get_entry_info(p, side):
    return p["E"], True
final_entry_price, final_has_entry = get_entry_info(final_p, final_side)
health_add("ENTRY", True)
health_add("FINAL", True)
lot_final, risk_final, entry_final = equity_for(final_chance)
def ob_corner_text(p):
    if p["ob_low"] is not None and p["ob_high"] is not None:
        return f"OB INFO: {p['ob']} {p['ob_low']:.2f}-{p['ob_high']:.2f} | Tumhari Marzi - Lagana Hai To Lagao, Nahi To Mat Lagao"
    else:
        return f"OB INFO: {p['ob']} | Tumhari Marzi - Lagana Hai To Lagao, Nahi To Mat Lagao"
def box_data(p, auto_side, chance, note):
    if p["atr"]=="Nahi": return "<div style='padding:4px;text-align:center;font-size:9px'>Data Nahi</div>"
    atr=float(p["atr"])
    entry_price, has_entry = get_entry_info(p, auto_side)
    if auto_side=="BUY":
        entry_txt = f"ENTRY {entry_price:.2f} - {entry_price+3.0:.2f} SE BUY KARO"
        sl=entry_price-atr*1.5; tp1=entry_price+atr*1.5; tp2=entry_price+atr*2.5
    else:
        entry_txt = f"ENTRY {entry_price:.2f} - {entry_price-3.0:.2f} SE SELL KARO"
        sl=entry_price+atr*1.5; tp1=entry_price-atr*1.5; tp2=entry_price-atr*2.5
    entry_box = f"<div style='background:#0a1f44;color:#ffd700;font-weight:bold;font-size:9px;padding:3px;border-radius:3px;margin:2px 0'>{entry_txt}</div>"
    sl_tp_txt = f"SL {sl:.2f} | TP1 {tp1:.2f}<br>TP2 {tp2:.2f}"
    if auto_side=="BUY": tp_txt=p['tp']['buy']['txt']; head="BUY"; bg="#22c55e"; bg2="#f0fdf4"; border="#22c55e"
    else: tp_txt=p['tp']['sell']['txt']; head="SELL"; bg="#ef4444"; bg2="#fef2f2"; border="#ef4444"
    if chance>=70: chance_color="#0a7a2e"; chance_txt="ACHA"
    elif chance>=50: chance_color="#d97706"; chance_txt="HALKA"
    else: chance_color="#e60000"; chance_txt="KAM - TRADE NAHI"
    extra_line=""
    if "Sweep" in p["liq"]: extra_line=f"<div style='font-size:8px;color:#7c3aed;font-weight:bold'>{p['sweep_note']}</div>"
    if p["trap"]!="": extra_line+=f"<div style='font-size:8px;color:#e60000;font-weight:bold'>⚠️ {p['trap']}</div>"
    lot_c, risk_c, entry_c = equity_for(chance)
    ob_txt = ob_corner_text(p)
    return f"""<div style="border:1.5px solid {border};border-radius:4px;overflow:hidden;background:{bg2}">
    <div style="background:{bg};color:#fff;text-align:center;padding:3px;font-weight:bold;font-size:11px">{head}</div>
    <div style="padding:3px;font-size:9px;line-height:1.3;text-align:center">{extra_line}
    <div style="font-size:7px;color:#555">{note}</div>
    {entry_box}
    {sl_tp_txt} | {tp_txt}<br>{p['vol']['text']} | RSI {p['rsi']} | {p['vwap_side']}<br><b>LOT {lot_c} | RISK {risk_c}</b>
    <div style="background:#fff;border:1.5px solid {chance_color};border-radius:3px;padding:2px;margin-top:2px"><div style="font-size:16px;font-weight:bold;color:{chance_color};line-height:1">{chance}%</div><div style="font-size:8px;font-weight:bold;color:{chance_color}">{chance_txt} CHANCE</div></div>
    <div style="background:#fef9c3;border:1px dashed #a16207;border-radius:3px;padding:2px;margin-top:2px;font-size:7px;color:#713f12">{ob_txt}</div>
    </div></div>"""
if len(corner_warnings)==0: warning_strip="<div style='background:#0a7a2e;color:#fff;text-align:center;font-size:8px;font-weight:bold;padding:2px;border-radius:3px;margin:2px 0'>✅ OK - Sab Sahi Hai</div>"
else: warning_strip=f"<div style='background:#e60000;color:#fff;text-align:center;font-size:8px;font-weight:bold;padding:2px;border-radius:3px;margin:2px 0'>⚠️ {' | '.join(corner_warnings)}</div>"
if mixed and all_below_50:
    final_bg="#7f1d1d"; final_side_text_full=f"FINAL: TRADE NAHI - MIXED - {buy_count_final} BUY vs {sell_count_final} SELL - Best {final_side} {final_chance}%"
elif mixed:
    final_bg="#7f1d1d"; final_side_text_full=f"FINAL: TRADE NAHI - MIXED - {buy_count_final} BUY vs {sell_count_final} SELL - Best {final_side} {final_chance}%"
elif all_below_50:
    final_bg="#7f1d1d"; final_side_text_full=f"FINAL: TRADE NAHI - Teenon 50 se Neeche Hain - Best {final_side} {final_chance}% - MARNA HAI TO MARO, KARNA HAI TO KARO, NAHI KARNA TO MAT KARO"
else:
    final_bg="#14532d" if final_side=="BUY" else "#7f1d1d"; final_side_text_full=f"FINAL: {final_side} - {final_time} Wala {final_chance}% Chance - KARNA HAI TO KARO"
if final_chance < 50:
    lot_final, risk_final, entry_final = "0.00","0%","TRADE NAHI - CHANCE KAM HAI"
if final_side=="BUY":
    final_entry_txt = f"FINAL ENTRY: {final_entry_price:.2f} - {final_entry_price+3.0:.2f} SE BUY KARO"
else:
    final_entry_txt = f"FINAL ENTRY: {final_entry_price:.2f} - {final_entry_price-3.0:.2f} SE SELL KARO"
health_txt = " | ".join(health)
now = datetime.now() + timedelta(hours=3)
date_str=now.strftime("%I:%M")
final_ob_txt = ob_corner_text(p1h)
html=f"""
<div id="capture" style="max-width:400px;margin:auto;font-family:Arial;background:#fff;padding:2px;color:#000;position:relative" dir="rtl">
<div style="background:#0a1f44;color:#d4af37;text-align:center;padding:4px;border-radius:4px"><b style="font-size:12px">USTAD JI - GOLD - FINAL WALA - OB DRAMA KHATAM</b><div style="color:#fff;font-size:8px">{date_str} | {session_name} - {session_note} | Pakki Candle Wala</div></div>
{warning_strip}
<div style="background:#0a7a2e;color:#fff;text-align:center;font-size:7px;font-weight:bold;padding:2px;border-radius:3px;margin:2px 0">SYSTEM CHECK: {health_txt}</div>
<div style="border:1px solid #0a1f44;border-radius:4px;padding:3px;margin:3px 0;background:#fdf6e3;font-size:9px;text-align:center">
<b>BADI MACHHLI: {machhli}</b> | Bahar {yahoo_price_raw:.2f} | MT5 {mt5:.2f} | Farq {farq:.2f} | Shift {shift:.2f} | LOCK KHATAM<br>
<span style="font-size:8px;color:#555">DUNIYA: Upar 4074 | Neeche 3950 | Regime {regime} | {dxy_txt} | {yield_txt} | 5M: {src5} | 15M: {src15} | 1H: {src1h}</span>
</div>
<div style="display:flex;gap:3px;margin:2px 0" dir="ltr">
<div style="flex:1"><div style="background:#0a1f44;color:#fff;text-align:center;padding:2px;font-weight:bold;font-size:10px">5M - {c5} - {src5}</div>{box_data(p5,c5,ch5,note5)}</div>
<div style="flex:1"><div style="background:#0a1f44;color:#fff;text-align:center;padding:2px;font-weight:bold;font-size:10px">15M - {c15} - {src15}</div>{box_data(p15,c15,ch15,note15)}</div>
<div style="flex:1"><div style="background:#0a1f44;color:#fff;text-align:center;padding:2px;font-weight:bold;font-size:10px">1H - {c1h} - {src1h}</div>{box_data(p1h,c1h,ch1h,note1h)}</div>
</div>
<div style="font-size:9px;text-align:center;background:#eef7f0;padding:2px;border-radius:3px">5M: {p5['pin']} | {p5['fvg']} | {p5['choch']} | {p5['liq']}<br>15M: {p15['pin']} | {p15['fvg']} | {p15['choch']} | {p15['liq']}<br>1H: {p1h['pin']} | {p1h['fvg']} | {p1h['choch']} | {p1h['liq']}</div>
<div style="background:#fef9c3;border:1px dashed #a16207;border-radius:4px;padding:4px;margin-top:3px;text-align:center;font-size:8px;color:#713f12"><b>OB KONE ME INFO:</b> {final_ob_txt}<br><span style="font-size:7px">OB ka time hai - Tumhari Marzi - Lagana Hai To Lagao, Nahi Lagana Hai To Mat Lagao - Setup aur Chance Wese Hi Rahenge</span></div>
<div style="background:{final_bg};color:#fff;text-align:center;padding:5px;border-radius:4px;font-weight:bold;font-size:11px;margin-top:3px">{final_side_text_full}<br><span style="font-size:10px;color:#ffd700">{final_entry_txt}</span></div>
<div style="background:#0a1f44;color:#ffd700;text-align:center;padding:5px;border-radius:4px;font-weight:bold;font-size:11px;margin-top:3px">EQUITY: LOT {lot_final} | RISK {risk_final} | {entry_final}</div>
<div style="text-align:center;font-size:8px;color:#000;background:#fff3cd;padding:2px;border-radius:3px;margin-top:2px"><b>Pakki Candle Se Bana Hai</b> | 5M: {age_5m} min | 15M: {age_15m} min | {session_note}</div>
<div style="text-align:center;font-size:8px;color:#555">Final Wala - OB Drama Khatam - OB Sirf Kone Me - Setup + Chance Wese Hi</div>
</div>
"""
components.html(html, height=950, scrolling=True)
st.info(f"HO GAYA - 5M {c5} {ch5}% - 15M {c15} {ch15}% - 1H {c1h} {ch1h}% - Final {final_side} {final_chance}% - LOT {lot_final}")

if st.button("NEXT ➡️ - Dobara Naya Data Dekho", use_container_width=True):
    st.session_state.next_count += 1
    st.rerun()

# ============================================================
# USTAD JI - TELEGRAM WALA - SIRF WAHI JO BAAT HUI THI
# PEHLA PAGE NAHI CHHEDA - SIRF TELEGRAM WALA HISSA
# ============================================================
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")
def telegram_bhejo(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        return True
    except:
        return False
def telegram_tasveer_bhejo(image_bytes, caption_text):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {"photo": ("page.png", image_bytes)}
        data = {"chat_id": CHAT_ID, "caption": caption_text}
        requests.post(url, data=data, files=files, timeout=20)
        return True
    except:
        return False

teenon_buy = (c5=="BUY" and c15=="BUY" and c1h=="BUY")
teenon_sell = (c5=="SELL" and c15=="SELL" and c1h=="SELL")
teenon_ek = teenon_buy or teenon_sell
koi_ek_48 = (ch5>=48 or ch15>=48 or ch1h>=48)

def kandle_ginti(p):
    buy_g = sum([1 for x in [p["pin"], p["fvg"], p["choch"], p["liq"]] if "BUY" in x])
    sell_g = sum([1 for x in [p["pin"], p["fvg"], p["choch"], p["liq"]] if "SELL" in x])
    return buy_g, sell_g
b5, s5 = kandle_ginti(p5)
b15, s15 = kandle_ginti(p15)
b1h, s1h = kandle_ginti(p1h)
total_buy_kandle = b5 + b15 + b1h
total_sell_kandle = s5 + s15 + s1h
if teenon_buy:
    final_side_msg = "TEENON BUY - TEENON GREEN"
else:
    final_side_msg = "TEENON SELL - TEENON RED"

# ---- USTAD JI - ONE WALA - SIRF KANDLE WALA PAGE ----
def pehle_page_ki_tasveer_banao(yahoo_price_input):
    fig2, ax2 = plt.subplots(figsize=(8, 11))
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 11); ax2.axis('off')
    fig2.patch.set_facecolor('white'); ax2.set_facecolor('white')
    ax2.add_patch(plt.Rectangle((0.2, 10.2), 9.6, 0.6, facecolor='#0a1f44'))
    ax2.text(5, 10.5, 'USTAD JI - ONE - KANDLE WALA PAGE', ha='center', va='center', color='#ffd700', fontsize=13, weight='bold')
    ax2.add_patch(plt.Rectangle((0.2, 9.4), 9.6, 0.7, facecolor='#fdf6e3', edgecolor='#0a1f44'))
    ax2.text(5, 9.75, f'BADI MACHHLI: {machhli}', ha='center', va='center', fontsize=10, weight='bold', color='black')
    ax2.text(5, 9.5, f'YAHOO LIVE: {yahoo_price_input:.2f}', ha='center', va='center', fontsize=9, color='black')
    datas = [(p5, c5, ch5, '5M'), (p15, c15, ch15, '15M'), (p1h, c1h, ch1h, '1H')]
    y_top = [9.2, 6.2, 3.2]
    for idx, (p, side, ch, name) in enumerate(datas):
        y0 = y_top[idx]
        col = '#22c55e' if side == 'BUY' else '#ef4444'
        ax2.add_patch(plt.Rectangle((0.2, y0-2.6), 9.6, 2.8, facecolor='white', edgecolor=col, linewidth=2))
        ax2.add_patch(plt.Rectangle((0.2, y0), 9.6, 0.45, facecolor=col))
        ax2.text(5, y0+0.22, f'{name} - {side} - {ch}% CHANCE', ha='center', va='center', color='white', fontsize=11, weight='bold')
        kandle_list = [('Pin', p["pin"]), ('FVG', p["fvg"]), ('CHoCH', p["choch"]), ('Liq', p["liq"])]
        for k_i, (k_name, k_val) in enumerate(kandle_list):
            x = 0.6 + k_i * 2.4
            if 'BUY' in k_val:
                k_col = '#22c55e'; k_txt = 'GREEN - BUY'
            elif 'SELL' in k_val:
                k_col = '#ef4444'; k_txt = 'RED - SELL'
            else:
                k_col = '#888888'; k_txt = 'NAHI BANA'
            ax2.add_patch(plt.Rectangle((x, y0-1.5), 2.1, 0.9, facecolor=k_col))
            ax2.text(x+1.05, y0-1.15, k_name, ha='center', va='center', color='white', fontsize=9, weight='bold')
            ax2.text(x+1.05, y0-1.4, k_txt, ha='center', va='center', color='white', fontsize=7, weight='bold')
        ax2.text(5, y0-1.9, f'{kandle_list[0][1]} | {kandle_list[1][1]}', ha='center', va='center', fontsize=7, color='black')
        ax2.text(5, y0-2.2, f'{kandle_list[2][1]} | {kandle_list[3][1]} | Vol {p["vol"]["text"]} | RSI {p["rsi"]}', ha='center', va='center', fontsize=7, color='black')
    ax2.text(5, 0.4, f'KANDLE HISAB: 12 Me Se {total_buy_kandle} BUY (GREEN) | 12 Me Se {total_sell_kandle} SELL (RED)', ha='center', va='center', fontsize=10, weight='bold', color='black')
    ax2.text(5, 0.05, 'Pakki Candle Se Bana Hai - Pehle Discuss Karo - Phir Trade Karo', ha='center', va='center', fontsize=8, color='#555555')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=180)
    plt.close(fig2)
    buf.seek(0)
    return buf.getvalue()

# ---- USTAD JI - TWO WALA - FINAL WALA PAGE - WAHI PURANA ----
def doosre_page_ki_tasveer_banao(yahoo_price_input):
    fig2, ax2 = plt.subplots(figsize=(8, 11))
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 11); ax2.axis('off')
    fig2.patch.set_facecolor('white'); ax2.set_facecolor('white')
    ax2.add_patch(plt.Rectangle((0.2, 10.2), 9.6, 0.6, facecolor='#0a1f44'))
    ax2.text(5, 10.5, 'USTAD JI - GOLD - FINAL WALA', ha='center', va='center', color='#ffd700', fontsize=13, weight='bold')
    ax2.add_patch(plt.Rectangle((0.2, 9.4), 9.6, 0.7, facecolor='#fdf6e3', edgecolor='#0a1f44'))
    ax2.text(5, 9.75, f'BADI MACHHLI: {machhli}', ha='center', va='center', fontsize=10, weight='bold', color='black')
    ax2.text(5, 9.5, f'YAHOO LIVE: {yahoo_price_input:.2f}', ha='center', va='center', fontsize=9, color='black')
    colors = {'BUY': '#22c55e', 'SELL': '#ef4444'}
    datas = [(p5, c5, ch5, '5M'), (p15, c15, ch15, '15M'), (p1h, c1h, ch1h, '1H')]
    x_start = [0.2, 3.5, 6.8]
    for idx, (p, side, ch, name) in enumerate(datas):
        x = x_start[idx]
        col = colors.get(side, '#555555')
        ax2.add_patch(plt.Rectangle((x, 6.0), 3.0, 3.2, facecolor='white', edgecolor=col, linewidth=2))
        ax2.add_patch(plt.Rectangle((x, 8.7), 3.0, 0.5, facecolor=col))
        ax2.text(x+1.5, 8.95, f'{name} - {side}', ha='center', va='center', color='white', fontsize=11, weight='bold')
        ax2.text(x+1.5, 8.3, f'ENTRY {p["E"]:.2f}', ha='center', va='center', fontsize=9, weight='bold', color='black')
        ax2.text(x+1.5, 7.8, f'{p["pin"]} | {p["fvg"]}', ha='center', va='center', fontsize=7, color='black')
        ax2.text(x+1.5, 7.4, f'{p["choch"]} | {p["liq"]}', ha='center', va='center', fontsize=7, color='black')
        ax2.text(x+1.5, 6.9, f'{ch}% CHANCE', ha='center', va='center', fontsize=14, weight='bold', color=col)
        ax2.text(x+1.5, 6.4, f'LOT {equity_for(ch)[0]} | RISK {equity_for(ch)[1]}', ha='center', va='center', fontsize=8, color='black')
    if mixed:
        ax2.add_patch(plt.Rectangle((0.2, 4.8), 9.6, 1.0, facecolor='#7f1d1d'))
        ax2.text(5, 5.5, f'FINAL: TRADE NAHI - MIXED - {buy_count_final} BUY vs {sell_count_final} SELL', ha='center', va='center', color='white', fontsize=11, weight='bold')
    else:
        ax2.add_patch(plt.Rectangle((0.2, 4.8), 9.6, 1.0, facecolor='#14532d' if final_side=="BUY" else '#7f1d1d'))
        ax2.text(5, 5.5, f'FINAL: {final_side} - {final_chance}% Chance', ha='center', va='center', color='white', fontsize=12, weight='bold')
    ax2.text(5, 5.05, f'FINAL ENTRY: {final_entry_price:.2f} | LOT {lot_final} | RISK {risk_final}', ha='center', va='center', color='#ffd700', fontsize=10, weight='bold')
    ax2.text(5, 4.3, f'KANDLE HISAB: 12 Me Se {total_buy_kandle} BUY | 12 Me Se {total_sell_kandle} SELL', ha='center', va='center', fontsize=10, weight='bold', color='black')
    ax2.text(5, 3.8, 'Pakki Candle Se Bana Hai - Pehle Discuss Karo - Phir Trade Karo', ha='center', va='center', fontsize=8, color='#555555')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=180)
    plt.close(fig2)
    buf.seek(0)
    return buf.getvalue()

# SIRF YEHI WALA ALARM - TEENON EK + KOI EK 48 SE UPAR - BAS 2 TASVEER
if teenon_ek and koi_ek_48:
    poora_msg = f"USTAD JI - TEENON EK HO GAYE\n{final_side_msg}\n\n5M: {c5} {ch5}% - YAHOO LIVE {yahoo_price_raw:.2f}\n15M: {c15} {ch15}% - YAHOO LIVE {yahoo_price_raw:.2f}\n1H: {c1h} {ch1h}% - YAHOO LIVE {yahoo_price_raw:.2f}\n\nKANDLE WALA HISAB:\n12 Me Se {total_buy_kandle} BUY Par Hain\n12 Me Se {total_sell_kandle} SELL Par Hain\n\nFinal: {final_side} {final_chance}% - YAHOO LIVE {yahoo_price_raw:.2f}"
    telegram_bhejo(poora_msg)
    tasveer_1 = pehle_page_ki_tasveer_banao(yahoo_price_raw)
    telegram_tasveer_bhejo(tasveer_1, "USTAD JI - PEHLA PAGE - Kandle Wala - Yahoo Live")
    tasveer_2 = doosre_page_ki_tasveer_banao(yahoo_price_raw)
    telegram_tasveer_bhejo(tasveer_2, "USTAD JI - DOOSRA PAGE - Teenon Ek Wala - Yahoo Live")
    st.success("USTAD JI - MESSAGE + DONON TASVEER BHEJ DI - Teenon Ek + Ek 48% Par")
else:
    st.info(f"Abhi auto nahi bheja - Teenon Ek: {teenon_ek} - Koi 48 par: {koi_ek_48}")

# WASEEM - V4.4 - STREAMLIT WALA - HISSA 1 - MANUAL PRICE KA CONNECTION KHATAM
# PURANI FILE KHALI KAR KE YAHI PASTE KARO - PHIR HISSA 2 NEECHE LAGANA
# IS ME MANUAL PRICE INDICATOR KO NAHI CHUEGI - SIRF DIKHANE KE LIYE HAI
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="WASEEM TRADER - V4.4", layout="centered")
st.title("WASEEM TRADER - V4.4 - INDICATOR SACH BOLEGA")

# استاد جی - YAH SIRF DIKHANE KE LIYE HAI - MT5 SE MILANE KE LIYE - INDICATOR ME NAHI JAYEGI
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
    # استاد جی - YAHI BADLA HAI - PEHLE YAHAN MANUAL PRICE KO CANDLE ME DALTE THE - AB NAHI DALENGE
    # AB YAHOO WALI PRICE HI SACH HAI - MANUAL PRICE KO CANDLE ME NAHI DALA
    abhi = float(df['Close'].iloc[-1])  # YAHOO WALI SACHI PRICE - INDICATOR ISI PAR BANEGA
    manual_show = float(MANUAL_PRICE)  # SIRF DIKHANE KE LIYE
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
    # استاد جی - YAH SAB INDICATOR SIRF YAHOO SE HAIN - MANUAL PRICE YAHAN KAHIN NAHI HAI
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
    # WASEEM - V4.4 - STREAMLIT WALA - HISSA 2 - BOARD UPAR - KHALI JAGAH KHATAM
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
    ax.add_patch(box((5.1,5.20),4.6,9.30, boxstyle="round,pad=0.1", facecolor='#1A1A0A', edgecolor='#FF4444', linewidth=1.8))
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
    # USTAD JI - STREAMLIT WALA - FINAL - OB DRAMA KHATAM - NEXT BUTTON WALA
import streamlit as st
import requests, datetime

st.set_page_config(page_title="USTAD JI - GOLD", layout="centered")
st.markdown("<h2 style='text-align:center;color:#0a1f44'>USTAD JI - GOLD - FINAL WALA</h2>", unsafe_allow_html=True)

# --- NEXT BUTTON WALA HISAB ---
# Jab NEXT dabayenge to naya data aayega
if "next_count" not in st.session_state:
    st.session_state.next_count = 0

col1, col2 = st.columns([3,1])
with col1:
    mt5_raw = st.text_input("Ustad Ji, MT5 wali price daalein (misal 3983)", value="3983")
with col2:
    st.write("")
    st.write("")
    next_dabaya = st.button("NEXT ➡️", use_container_width=True)

if next_dabaya:
    st.session_state.next_count += 1
    st.rerun()

try:
    mt5 = float(mt5_raw)
except:
    mt5 = 3983.0

if mt5 < 1000 or mt5 > 5000:
    st.error(f"USTAD JI, PRICE GALAT HAI - Aap ne daali: {mt5_raw} - Puri price daalo - Misal 3983")
    st.stop()

st.info(f"NEXT dabaya gaya: {st.session_state.next_count} baar | MT5 Price: {mt5}")

# --- YAHAN SE AAP WALA PURANA SYSTEM SHURU ---
# Neeche wahi wala system hai jo pehle tha
# Pin + FVG + CHoCH + Liq + VWAP + RSI + Volume + Trap + Machhli + OB Kone Me

now_dt = datetime.datetime.now()
now_min = now_dt.minute
age_5m = now_min % 5
age_15m = now_min % 15
age_1h = now_min % 60
hour_now = now_dt.hour

if 11 <= hour_now < 15:
    session_name = "LONDON KILL ZONE"; session_score_bonus = 10
elif 17 <= hour_now < 22:
    session_name = "NEW YORK KILL ZONE"; session_score_bonus = 10
elif 0 <= hour_now < 8:
    session_name = "ASIA"; session_score_bonus = -10
else:
    session_name = "OFF"; session_score_bonus = -5

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

def get_one_time(interval_yahoo):
    d2 = yahoo_fetch("XAUUSD=X", interval_yahoo, "5d")
    if d2["ok"]: return d2, "SPOT"
    d3 = yahoo_fetch("GC=F", interval_yahoo, "5d")
    if d3["ok"]: return d3, "FUTURE"
    return {"ok":False}, "KHALI"

# 12 CANDLE WALA HISAB - AAP WALA PURANA
# Yahan 12 candle ka data bhi rakha hai, taake website pe 12 candle bhi dikhen
d5_raw, src5 = get_one_time("5m")
d15_raw, src15 = get_one_time("15m")
d1h_raw, src1h = get_one_time("60m")

if d5_raw["ok"]: yahoo_price_raw = d5_raw["price"]
elif d15_raw["ok"]: yahoo_price_raw = d15_raw["price"]
elif d1h_raw["ok"]: yahoo_price_raw = d1h_raw["price"]
else: yahoo_price_raw = mt5

farq_asli = yahoo_price_raw - mt5
shift = mt5 - yahoo_price_raw

def apply_shift(d):
    if not d["ok"]: return d
    d2=dict(d); d2["closes"]=[x+shift for x in d["closes"]]; d2["highs"]=[x+shift for x in d["highs"]]; d2["lows"]=[x+shift for x in d["lows"]]; d2["opens"]=[x+shift for x in d["opens"]]; d2["price"]=d["price"]+shift; return d2

d5=apply_shift(d5_raw); d15=apply_shift(d15_raw); d1h=apply_shift(d1h_raw)

if farq_asli < -4: side_farq="SELL"; machhli=f"MACHHLI SELL - Farq {farq_asli:.2f}"
elif farq_asli > 4: side_farq="BUY"; machhli=f"MACHHLI BUY - Farq {farq_asli:.2f}"
else:
    if farq_asli>=0: side_farq="BUY"; machhli=f"MACHHLI HALKI BUY - Farq {farq_asli:.2f}"
    else: side_farq="SELL"; machhli=f"MACHHLI HALKI SELL - Farq {farq_asli:.2f}"

def get_pakki_arrays(d):
    if not d["ok"] or len(d["closes"])<3: return d
    d2=dict(d); d2["closes"]=d["closes"][:-1]; d2["highs"]=d["highs"][:-1]; d2["lows"]=d["lows"][:-1]; d2["opens"]=d["opens"][:-1]; d2["vols"]=d["vols"][:-1] if len(d["vols"])==len(d["closes"]) else d["vols"]; return d2

d5_pakki=get_pakki_arrays(d5); d15_pakki=get_pakki_arrays(d15); d1h_pakki=get_pakki_arrays(d1h)

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
vwap_common_side="VWAP Upar" if vwap_common is not None and mt5>vwap_common else "VWAP Neeche" if vwap_common is not None else "VWAP Nahi"

if session_name=="ASIA": regime="RANGE"
elif d1h_pakki["ok"] and vwap_common is not None:
    regime="RANGE" if abs(mt5-vwap_common)<8 else "TREND"
else: regime="RANGE"

# DXY + YIELD
try:
    dxy_data = yahoo_fetch("DX-Y.NYB", "60m", "5d")
    if dxy_data["ok"] and len(dxy_data["closes"])>5:
        dxy_up = dxy_data["closes"][-1] > dxy_data["closes"][-5]
        dxy_txt = "DXY Upar" if dxy_up else "DXY Neeche"
    else: dxy_up=False; dxy_txt="DXY Nahi"
except: dxy_up=False; dxy_txt="DXY Nahi"

try:
    yield_data = yahoo_fetch("^TNX", "60m", "5d")
    if yield_data["ok"] and len(yield_data["closes"])>2:
        yield_now = yield_data["closes"][-1]; yield_txt=f"Yield {yield_now:.2f}%"; yield_high=yield_now>5.0
    else: yield_txt="Yield Nahi"; yield_high=False
except: yield_txt="Yield Nahi"; yield_high=False

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

def check_order_block(opens,closes,highs,lows):
    if len(closes)<5: return "OB Nahi", None, None
    cur=closes[-1]
    for i in range(len(closes)-4, len(closes)-1):
        o=opens[i]; c=closes[i]; o_next=opens[i+1]; c_next=closes[i+1]; body=abs(c-o); body_next=abs(c_next-o_next)
        if body_next>body*1.5:
            if c_next<o_next and c>o:
                ob_low=min(o,c); ob_high=max(o,c)
                if ob_low<=cur<=ob_high+2: return "OB BUY Me Hai", ob_low, ob_high
            if c_next>o_next and c<o:
                ob_low=min(o,c); ob_high=max(o,c)
                if ob_low-2<=cur<=ob_high: return "OB SELL Me Hai", ob_low, ob_high
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

def process(d_pakki, age_min, adhuri_limit, src_name):
    if not d_pakki["ok"]:
        return {"rsi":"Nahi","atr":"Nahi","pin":"Data Nahi","fvg":"Data Nahi","choch":"Data Nahi","liq":"Data Nahi","ob":"Data Nahi","ob_low":None,"ob_high":None,"vwap_side":vwap_common_side,"vol":{"text":"Vol Nahi","trend":"NAHI","pct":0},"E":mt5,"adhuri":True,"rsi_val":None,"age":age_min,"src":src_name,"trap":""}
    closes=d_pakki["closes"]; highs=d_pakki["highs"]; lows=d_pakki["lows"]; opens=d_pakki["opens"]; vols=d_pakki.get("vols",[])
    rsi=calc_rsi(closes); atrs=calc_atr_list(highs,lows,closes); atr=atrs[-1]
    pin=check_pin(opens[-1],highs[-1],lows[-1],closes[-1]); fvg=check_fvg(highs,lows); choch=check_choch(highs,lows); liq=check_liquidity_sweep(highs,lows,closes); ob, ob_low, ob_high = check_order_block(opens,closes,highs,lows); vol=calc_volume(vols,src_name)
    adhuri=True if age_min<adhuri_limit else False
    E=closes[-1]
    trap=""
    if choch=="CHoCH BUY" and vol["trend"]!="BADH" and rsi is not None and rsi>70: trap="BULL TRAP"
    elif choch=="CHoCH SELL" and vol["trend"]!="BADH" and rsi is not None and rsi<30: trap="BEAR TRAP"
    return {"rsi":f"{rsi:.0f}" if rsi is not None else "Nahi","atr":f"{atr:.2f}" if atr is not None else "Nahi","pin":pin,"fvg":fvg,"choch":choch,"liq":liq,"ob":ob,"ob_low":ob_low,"ob_high":ob_high,"vwap_side":vwap_common_side,"vol":vol,"E":E,"adhuri":adhuri,"rsi_val":rsi,"age":age_min,"src":src_name,"trap":trap}

p5=process(d5_pakki, age_5m, 4, src5)
p15=process(d15_pakki, age_15m, 12, src15)
p1h=process(d1h_pakki, age_1h, 45, src1h)

def candle_side_sach(p):
    buy_count = sum([1 for x in [p["pin"],p["fvg"],p["choch"],p["liq"]] if "BUY" in x])
    sell_count = sum([1 for x in [p["pin"],p["fvg"],p["choch"],p["liq"]] if "SELL" in x])
    if buy_count==0 and sell_count==0: return side_farq, "KUCH NAHI BANA"
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

def calc_chance(p, candle):
    score_vol=15 if p["vol"]["trend"]=="BADH" else 10 if p["vol"]["trend"]=="NORMAL" else 3 if p["vol"]["trend"]=="GIR" else 10
    rsi_v=p["rsi_val"]; score_rsi=10 if rsi_v is not None and ((candle=="BUY" and rsi_v<70) or (candle=="SELL" and rsi_v>30)) else 2 if rsi_v is not None else 5
    score_adhuri=2 if p["adhuri"] else 10
    score_machhli=5 if candle==side_farq and abs(farq_asli)>=4 else 3 if candle==side_farq else 0
    score_vwap=5 if (candle=="BUY" and "Upar" in p["vwap_side"]) or (candle=="SELL" and "Neeche" in p["vwap_side"]) else -5 if (candle=="BUY" and "Neeche" in p["vwap_side"]) or (candle=="SELL" and "Upar" in p["vwap_side"]) else 0
    score_trap=-7 if p["trap"]!="" else 0
    score_macro=0
    if candle=="BUY" and dxy_up: score_macro-=10
    if candle=="SELL" and not dxy_up: score_macro-=5
    if candle=="BUY" and yield_high: score_macro-=10
    total=int(round(score_vol+score_rsi+score_adhuri+score_machhli+score_vwap+score_trap+session_score_bonus+score_macro))
    if total<1: total=1
    if total>95: total=95
    return total

ch5=calc_chance(p5,c5); ch15=calc_chance(p15,c15); ch1h=calc_chance(p1h,c1h)

def equity_for(chance):
    if chance>=80: return ("0.05","2%","FULL ENTRY")
    elif chance>=70: return ("0.03","1.5%","BADI ENTRY")
    elif chance>=60: return ("0.02","1%","NORMAL ENTRY")
    elif chance>=50: return ("0.01","0.5%","CHOTI ENTRY")
    else: return ("0.00","0%","TRADE NAHI - CHANCE KAM HAI")

buy_count_final = sum([1 for x in [c5,c15,c1h] if x=="BUY"])
sell_count_final = sum([1 for x in [c5,c15,c1h] if x=="SELL"])
mixed = not (c5==c15==c1h)
candidates=[(ch5,c5,"5M"),(ch15,c15,"15M"),(ch1h,c1h,"1H")]
majority_side="BUY" if buy_count_final>sell_count_final else "SELL" if sell_count_final>buy_count_final else None
majority_candidates=[x for x in candidates if x[1]==majority_side] if majority_side else candidates
final_chance, final_side, final_time=sorted(majority_candidates, key=lambda x: x[0], reverse=True)[0]
if majority_side: final_side=majority_side
final_p = p5 if final_time=="5M" else p15 if final_time=="15M" else p1h
lot_final, risk_final, entry_final = equity_for(final_chance)
if final_chance<50: lot_final, risk_final, entry_final = "0.00","0%","TRADE NAHI - CHANCE KAM HAI"

# --- WEBSITE PE DIKHANA ---
st.markdown(f"<div style='background:#0a1f44;color:#fff;padding:8px;border-radius:6px;text-align:center'><b>BADI MACHHLI: {machhli}</b><br>Bahar {yahoo_price_raw:.2f} | MT5 {mt5:.2f} | Farq {farq_asli:.2f} | {session_name} | Regime {regime} | {dxy_txt} | {yield_txt}</div>", unsafe_allow_html=True)

# 12 CANDLE WALI TABLE - AAP WALI PURANI
if d5_pakki["ok"]:
    st.subheader("12 Candle - 5M Wala")
    last12 = list(zip(d5_pakki["opens"][-12:], d5_pakki["highs"][-12:], d5_pakki["lows"][-12:], d5_pakki["closes"][-12:]))
    st.table([{"Open":f"{o:.2f}","High":f"{h:.2f}","Low":f"{l:.2f}","Close":f"{c:.2f}"} for o,h,l,c in last12])

colA, colB, colC = st.columns(3)
def show_box(p, side, chance, note, title):
    lot_c, risk_c, entry_c = equity_for(chance)
    atr = float(p["atr"]) if p["atr"]!="Nahi" else 5
    E = p["E"]
    if side=="BUY": entry_txt=f"ENTRY {E:.2f} - {E+3.0:.2f} SE BUY KARO"; sl=E-atr*1.5; tp1=E+atr*1.5; tp2=E+atr*2.5
    else: entry_txt=f"ENTRY {E:.2f} - {E-3.0:.2f} SE SELL KARO"; sl=E+atr*1.5; tp1=E-atr*1.5; tp2=E-atr*2.5
    ob_txt = f"OB INFO: {p['ob']} | Tumhari Marzi - Lagana Hai To Lagao, Nahi To Mat Lagao" if p["ob_low"] is None else f"OB INFO: {p['ob']} {p['ob_low']:.2f}-{p['ob_high']:.2f} | Tumhari Marzi"
    st.markdown(f"### {title} - {side} - {chance}%")
    st.write(f"{p['pin']} | {p['fvg']} | {p['choch']} | {p['liq']}")
    st.write(f"{note} | {p['vol']['text']} | RSI {p['rsi']} | {p['vwap_side']} | TRAP: {p['trap'] if p['trap'] else 'Nahi'}")
    st.success(entry_txt)
    st.write(f"SL {sl:.2f} | TP1 {tp1:.2f} | TP2 {tp2:.2f} | LOT {lot_c} | RISK {risk_c}")
    st.warning(ob_txt)

with colA: show_box(p5,c5,ch5,note5,"5M")
with colB: show_box(p15,c15,ch15,note15,"15M")
with colC: show_box(p1h,c1h,ch1h,note1h,"1H")

if mixed:
    st.error(f"FINAL: TRADE NAHI - MIXED - {buy_count_final} BUY vs {sell_count_final} SELL - Best {final_side} {final_chance}%")
elif final_chance<50:
    st.error(f"FINAL: TRADE NAHI - Teenon 50 se Neeche Hain - Best {final_side} {final_chance}% - MARNA HAI TO MARO, KARNA HAI TO KARO, NAHI KARNA TO MAT KARO")
else:
    st.success(f"FINAL: {final_side} - {final_time} Wala {final_chance}% Chance - KARNA HAI TO KARO")
    if final_side=="BUY": st.success(f"FINAL ENTRY: {final_p['E']:.2f} - {final_p['E']+3.0:.2f} SE BUY KARO")
    else: st.success(f"FINAL ENTRY: {final_p['E']:.2f} - {final_p['E']-3.0:.2f} SE SELL KARO")

st.markdown(f"<div style='background:#0a1f44;color:#ffd700;padding:8px;border-radius:6px;text-align:center'><b>EQUITY: LOT {lot_final} | RISK {risk_final} | {entry_final}</b></div>", unsafe_allow_html=True)
st.markdown(f"<div style='background:#fef9c3;padding:6px;border-radius:6px;text-align:center;font-size:12px'>OB KONE ME INFO: {p1h['ob']} | Tumhari Marzi - Lagana Hai To Lagao, Nahi To Mat Lagao</div>", unsafe_allow_html=True)

# DOBARA NEXT BUTTON - NEECHE BHI
if st.button("NEXT ➡️ - Dobara Naya Data Dekho", use_container_width=True):
    st.session_state.next_count += 1
    st.rerun()

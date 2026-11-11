# WASEEM - V4.3 - STREAMLIT WALA - HISSA 1 - 5 BAAR CHECK KIYA HUA
# PURANI FILE KHALI KAR KE YAHI PASTE KARO - PHIR HISSA 2 NEECHE LAGANA
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="WASEEM TRADER - V4.3", layout="centered")
st.title("WASEEM TRADER - V4.3 - STREAMLIT WALA")

# استاد جی - MANUAL PRICE - MT5 WALI - AB 4002 DALO - 4042 PURANI HO GAYI
MANUAL_PRICE = st.number_input("MANUAL PRICE - MT5 WALI - JAISE 4002.0", value=4002.0, key="manual_v43")
CHALAO = st.button("SIGNAL BANAO", key="signal_v43")

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
    abhi = float(MANUAL_PRICE)
    for _df in [df, df15, df4h]:
        _df.loc[_df.index[-1], 'Close'] = abhi
        if abhi > float(_df.loc[_df.index[-1], 'High']):
            _df.loc[_df.index[-1], 'High'] = abhi
        if abhi < float(_df.loc[_df.index[-1], 'Low']):
            _df.loc[_df.index[-1], 'Low'] = abhi
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
        # استاد جی - YAHI 3/5 WALA HAI - 5 BAAR CHECK KIYA - PEHLE 5/5 THA
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
    st.session_state['last_abhi_s']=abhi_s; st.session_state['last_rsi_s']=rsi_s; st.session_state['last_atr_s']=atr_s
    st.session_state['last_date']=date_txt; st.session_state['last_time']=time_txt
    st.success("HISAB HO GAYA - NEECHE TASVEER AAYEGI")
    # WASEEM - V4.3 - STREAMLIT WALA - HISSA 2 - BOARD UPAR - KHALI JAGAH KHATAM - 5 BAAR CHECK KIYA
if st.session_state.get('has_data', False):
    r4h = st.session_state['last_r4h']
    r1h = st.session_state['last_r1h']
    r15 = st.session_state['last_r15']
    buy_buttons = st.session_state['last_buy_buttons']
    sell_buttons = st.session_state['last_sell_buttons']
    buy_c = st.session_state['last_buy_c']
    sell_c = st.session_state['last_sell_c']
    abhi_s = st.session_state['last_abhi_s']
    rsi_s = st.session_state['last_rsi_s']
    atr_s = st.session_state['last_atr_s']
    date_txt = st.session_state['last_date']
    time_txt = st.session_state['last_time']
    # استاد جی - YAHI BADLA HAI - PEHLE FIG 24 THA - AB 19 HAI - KHALI JAGAH KHATAM
    fig,ax = plt.subplots(figsize=(10,19))
    ax.set_xlim(0,10); ax.set_ylim(0,19); ax.axis('off')
    fig.patch.set_facecolor('#0A0A0A'); ax.set_facecolor('#0A0A0A')
    box = patches.FancyBboxPatch
    ax.add_patch(box((0.3,18.3),9.4,0.6, boxstyle="round,pad=0.1", facecolor='#0A0A0A', edgecolor='#FFD700', linewidth=2.5))
    ax.text(5,18.60,'WASEEM  TRADER - V4.3', ha='center',va='center', color='#FFD700', fontsize=20,weight='bold')
    ax.add_patch(box((0.3,17.65),9.4,0.50, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor='#FFD700', linewidth=1))
    ax.text(5,17.90,date_txt + "  |  " + time_txt + "  |  PAKISTAN TIME", ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
    ax.add_patch(box((0.3,16.90),9.4,0.65, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor='#FFD700', linewidth=1.2))
    ax.text(5,17.30,'GOLD: ' + abhi_s + ' [MANUAL]  |  ATR: ' + atr_s, ha='center',va='center', fontsize=18,weight='bold', color='white')
    ax.text(5,17.02,'4H = MAZBOOT  |  1H = BEECH  |  15M = JALDI', ha='center',va='center', fontsize=8,weight='bold', color='#FFD700')
    ax.add_patch(box((0.3,15.15),9.4,1.60, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r4h['fcol'], linewidth=2))
    ax.text(5,16.50,'4H SETUP - MAZBOOT WALA', ha='center',va='center', fontsize=10,weight='bold', color='#FFD700')
    ax.text(5,16.15,r4h['faisla'], ha='center',va='center', fontsize=9,weight='bold', color=r4h['fcol'])
    ax.text(5,15.80,r4h['entry']+"  |  "+r4h['sl']+"  |  "+r4h['tp'], ha='center',va='center', fontsize=8,weight='bold', color='white')
    ax.text(5,15.45,'BOS: '+r4h['bos']+' | '+r4h['fvg']+' | '+r4h['react'], ha='center',va='center', fontsize=7.5,color='white')
    ax.text(5,15.20,r4h['chance_txt']+"  |  "+r4h['rr'], ha='center',va='center', fontsize=8.5,weight='bold', color='#00FF88' if r4h['chance']>=80 else '#FFAA00')
    ax.add_patch(box((0.3,14.60),9.4,0.45, boxstyle="round,pad=0.1", facecolor='#FFD700'))
    ax.text(5,14.82,'BUTTON - SIRF ANDAZA - FAISLA NAHI KARTA', ha='center',va='center', fontsize=9,weight='bold', color='black')
    ax.text(5,14.65,'BUY '+str(buy_c)+'/12  |  SELL '+str(sell_c)+'/12  |  RSI: '+rsi_s, ha='center',va='center', fontsize=7.5,color='black')
    # استاد جی - YAHI BOARD UPAR LAYA HAI - PEHLE 4.2 SE SHURU THA - AB 5.20 SE SHURU HAI - KHALI JAGAH KHATAM
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
    ax.add_patch(box((5.1,5.20),4.6,9.30, boxstyle="round,pad=0.1", facecolor='#1A0A0A', edgecolor='#FF4444', linewidth=1.8))
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
    # استاد جی - YAHI NEECHE WALA BOARD UPAR LAYA HAI - PEHLE 1.2 PAR THA - AB 2.70 PAR HAI - INDICATOR KE QAREEB
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
    ax.text(5,1.45,'3/5 MIL GAYA TO SETUP - 60% CHANCE', ha='center',va='center', fontsize=7,color='#AAAAAA')
    ax.text(5,1.05,'MANUAL PRICE MT5 SE MILAO - PURANI PRICE PAR TRADE NAHI', ha='center',va='center', fontsize=7,weight='bold', color='white')
    ax.text(5,0.60,'PEHLE DISCUSS KARO - PHIR TRADE KARO', ha='center',va='center', fontsize=8,weight='bold', color='#FFD700')
    st.pyplot(fig)
else:
    st.info("👆 PEHLE MANUAL PRICE DALO - PHIR SIGNAL BANAO DABAO - PHIR TASVEER AAYEGI")

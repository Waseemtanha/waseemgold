# WASEEM - V4.1 FINAL - STREAMLIT + TELEGRAM - SETUP SAME HAI
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="WASEEM TRADER - V4.1", layout="centered")
st.title("WASEEM TRADER - V4.1")

# استاد جی - پرائس مینوئل ہے - MT5 والی پرائس ڈالنی ہے
MANUAL_PRICE = st.number_input("MANUAL PRICE DALO - MT5 WALI PRICE", value=4045.0)

# TELEGRAM - YE 2 CHEEZEIN STREAMLIT KE SECRET ME DALNI HAIN
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

# استاد جی - صرف میسج جائے گا، تصویر نہیں جائے گی
def TELEGRAM_BHEJO(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        if r.status_code == 200:
            st.success("TELEGRAM PE BHEJ DIYA - CHECK KARO")
        else:
            st.error("TELEGRAM NAHI GAYA: " + str(r.text))
        return r
    except Exception as e:
        st.error(f"TELEGRAM ME GALTI: {e}")
        return None

if st.button("TEST TELEGRAM - SIRF MESSAGE"):
    TELEGRAM_BHEJO("TEST - WASEEM TRADER BOT CHAL RAHA HAI")

if st.button("SIGNAL BANAO"):
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
    df.loc[df.index[-1], 'Close'] = abhi
    if abhi > float(df.loc[df.index[-1], 'High']):
        df.loc[df.index[-1], 'High'] = abhi
    if abhi < float(df.loc[df.index[-1], 'Low']):
        df.loc[df.index[-1], 'Low'] = abhi
    df15.loc[df15.index[-1], 'Close'] = abhi
    if abhi > float(df15.loc[df15.index[-1], 'High']):
        df15.loc[df15.index[-1], 'High'] = abhi
    if abhi < float(df15.loc[df15.index[-1], 'Low']):
        df15.loc[df15.index[-1], 'Low'] = abhi
    df4h.loc[df4h.index[-1], 'Close'] = abhi
    if abhi > float(df4h.loc[df4h.index[-1], 'High']):
        df4h.loc[df4h.index[-1], 'High'] = abhi
    if abhi < float(df4h.loc[df4h.index[-1], 'Low']):
        df4h.loc[df4h.index[-1], 'Low'] = abhi

    pak_time = datetime.now() + timedelta(hours=5)
    date_txt = pak_time.strftime("%d %B %Y")
    time_txt = pak_time.strftime("%I:%M %p")
    abhi_s = str(int(abhi))

    df['TR'] = np.maximum(df['High']-df['Low'], np.maximum(abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))))
    atr_v = float(df['TR'].rolling(14).mean().iloc[-1])
    if atr_v < 3: atr_v = 3.0
    if atr_v > 15: atr_v = 15.0
    atr_s = str(round(atr_v,1))

    # استاد جی - آپ والا فکس حساب - ATR سے نہیں بنے گا
    sl_dist = 6
    tp1_dist = 11
    tp2_dist = 22

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
            entry="Buy "+str(int(d_bot))+" - "+str(int(d_top)); sl="SL: "+str(int(d_bot-sl_dist))+" - 6 DOLLAR"; tp="TP1: "+str(int(d_top+tp1_dist))+" - 11 DOLLAR | TP2: "+str(int(d_top+tp2_dist))+" - 22 DOLLAR"
            chance=buy_score; chance_txt="CHANCE: "+str(chance)+"% - MAZBOOT" if chance>=80 else "CHANCE: "+str(chance)+"% - THEEK HAI"
            rr_txt="SL 6 | TP1 11 | TP2 22"
        elif at_s and (bos_down or fvg_bear) and react_sell and vol_ok:
            faisla = tf_name+" SELL SETUP - SAB MIL GAYA"; fcol="#FF4444"
            entry="Sell "+str(int(s_bot))+" - "+str(int(s_top)); sl="SL: "+str(int(s_top+sl_dist))+" - 6 DOLLAR"; tp="TP1: "+str(int(s_bot-tp1_dist))+" - 11 DOLLAR | TP2: "+str(int(s_bot-tp2_dist))+" - 22 DOLLAR"
            chance=sell_score; chance_txt="CHANCE: "+str(chance)+"% - MAZBOOT" if chance>=80 else "CHANCE: "+str(chance)+"% - THEEK HAI"
            rr_txt="SL 6 | TP1 11 | TP2 22"
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
        return {'faisla':faisla,'fcol':fcol,'entry':entry,'sl':sl,'tp':tp,'chance':chance,'chance_txt':chance_txt,'rr':rr_txt,'bos':bos_txt,'fvg':fvg_txt,'react':react_txt,'react_ok':react_ok,'vol_ok':vol_ok,'d_bot':int(d_bot),'d_top':int(d_top),'s_bot':int(s_bot),'s_top':int(s_top),'fvg_bot':int(fvg_bot),'fvg_top':int(fvg_top),'trend_up':trend_up,'res':int(RES),'sup':int(SUP)}

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

    # PART 2 - TASVEER - AAP KA WAHI DESIGN - SAME HAI
    fig,ax = plt.subplots(figsize=(10,30))
    ax.set_xlim(0,10); ax.set_ylim(0,30); ax.axis('off')
    fig.patch.set_facecolor('#0A0A0A'); ax.set_facecolor('#0A0A0A')
    box = patches.FancyBboxPatch
    ax.add_patch(box((0.3,29.0),9.4,0.9, boxstyle="round,pad=0.1", facecolor='#0A0A0A', edgecolor='#FFD700', linewidth=3))
    ax.text(5,29.45,'WASEEM  TRADER - V4.1', ha='center',va='center', color='#FFD700', fontsize=26,weight='bold')
    ax.text(5,29.15,'UPAR 4H MAZBOOT LATE + NEECHE JALDI WALA - CHANCE KE SAATH', ha='center',va='center', color='white',fontsize=9)
    ax.add_patch(box((0.3,28.3),9.4,0.55, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor='#FFD700', linewidth=1))
    ax.text(5,28.57,date_txt + "  |  " + time_txt + "  |  PAKISTAN TIME", ha='center',va='center', fontsize=11,weight='bold', color='#FFD700')
    ax.add_patch(box((0.3,27.3),9.4,0.85, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor='#FFD700', linewidth=1.5))
    ax.text(5,27.8,'GOLD: ' + abhi_s + ' [MANUAL MT5]  |  ATR: ' + atr_s, ha='center',va='center', fontsize=22,weight='bold', color='white')
    ax.text(5,27.45,'4H = MAZBOOT LATE  |  1H = BEECH  |  15M = JALDI - TEENO ALAG ALAG', ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
    ax.add_patch(box((0.3,24.0),9.4,3.0, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r4h['fcol'], linewidth=2.5))
    ax.text(5,26.65,'4H SETUP - MAZBOOT WALA - LATE - DIN ME 1 BAAR', ha='center',va='center', fontsize=11,weight='bold', color='#FFD700')
    ax.text(5,26.25,r4h['faisla'], ha='center',va='center', fontsize=11,weight='bold', color=r4h['fcol'])
    ax.text(5,25.85,r4h['entry']+"  |  "+r4h['sl']+"  |  "+r4h['tp'], ha='center',va='center', fontsize=9,weight='bold', color='white')
    ax.text(5,25.45,'BOS: '+r4h['bos']+' | '+r4h['fvg']+' | '+r4h['react'], ha='center',va='center', fontsize=8,color='white')
    ax.text(5,25.05,'4H D: '+str(r4h['d_bot'])+"-"+str(r4h['d_top'])+'  |  4H S: '+str(r4h['s_bot'])+"-"+str(r4h['s_top'])+'  |  VOL: '+('MAZBOOT' if r4h['vol_ok'] else 'KAMZOR'), ha='center',va='center', fontsize=8,color='white')
    ax.text(5,24.45,r4h['chance_txt']+"  |  "+r4h['rr'], ha='center',va='center', fontsize=10,weight='bold', color='#00FF88' if r4h['chance']>=80 else '#FFAA00')
    ax.text(5,24.15,'4H WALA KISI KO NAHI ROKTA - APNA ALAG HAI', ha='center',va='center', fontsize=8,color='#AAAAAA')
    ax.add_patch(box((0.3,23.25),9.4,0.65, boxstyle="round,pad=0.1", facecolor='#FFD700'))
    ax.text(5,23.65,'BUTTON - SIRF ANDAZA - FAISLA NAHI KARTA', ha='center',va='center', fontsize=10,weight='bold', color='black')
    ax.text(5,23.35,'BUY '+str(buy_c)+'/12  |  SELL '+str(sell_c)+'/12  |  Resistance 1H: '+str(r1h['res'])+' | Support 1H: '+str(r1h['sup'])+' | RSI: '+rsi_s, ha='center',va='center', fontsize=8,color='black')
    ax.add_patch(box((0.3,7.2),4.6,15.9, boxstyle="round,pad=0.1", facecolor='#0A1A0A', edgecolor='#00FF88', linewidth=2))
    ax.text(2.6,22.70,'BUY - SIRF ANDAZA', ha='center', va='center', fontsize=11, weight='bold', color='#00FF88')
    ax.text(2.6,22.30,'BUY: ' + str(buy_c) + '/12', ha='center', va='center', fontsize=12, weight='bold', color='white')
    for i,(naam,val,ok) in enumerate(buy_buttons):
        y = 21.75 - i*0.95
        is_star = "★" in naam
        if ok: rang = '#00FF88'; face = '#003311'; txt = "SABZ"
        else: rang = '#555555'; face = '#1A1A1A'; txt = "NAHI"
        edge = '#FFD700' if is_star else rang; lw = 2.2 if is_star else 1.2
        ax.add_patch(patches.Rectangle((0.5,y-0.40),4.2,0.80, facecolor=face, edgecolor=edge, linewidth=lw))
        ax.text(0.65,y+0.18,naam, ha='left', va='center', fontsize=8, weight='bold', color='#FFD700' if is_star else 'white')
        ax.text(0.65,y-0.18,val, ha='left', va='center', fontsize=7, color='white')
        ax.text(4.55,y,txt, ha='right', va='center', fontsize=7, weight='bold', color=rang)
    ax.add_patch(box((5.1,7.2),4.6,15.9, boxstyle="round,pad=0.1", facecolor='#1A0A0A', edgecolor='#FF4444', linewidth=2))
    ax.text(7.4,22.70,'SELL - SIRF ANDAZA', ha='center', va='center', fontsize=11, weight='bold', color='#FF4444')
    ax.text(7.4,22.30,'SELL: ' + str(sell_c) + '/12', ha='center', va='center', fontsize=12, weight='bold', color='white')
    for i,(naam,val,ok) in enumerate(sell_buttons):
        y = 21.75 - i*0.95
        is_star = "★" in naam
        if ok: rang = '#FF4444'; face = '#330000'; txt = "LAL"
        else: rang = '#555555'; face = '#1A1A1A'; txt = "NAHI"
        edge = '#FFD700' if is_star else rang; lw = 2.2 if is_star else 1.2
        ax.add_patch(patches.Rectangle((5.3,y-0.40),4.2,0.80, facecolor=face, edgecolor=edge, linewidth=lw))
        ax.text(5.45,y+0.18,naam, ha='left', va='center', fontsize=8, weight='bold', color='#FFD700' if is_star else 'white')
        ax.text(5.45,y-0.18,val, ha='left', va='center', fontsize=7, color='white')
        ax.text(9.35,y,txt, ha='right', va='center', fontsize=7, weight='bold', color=rang)
    ax.plot([5.0, 5.0], [7.2, 23.1], color='red', linewidth=4)
    ax.add_patch(box((0.3,6.5),9.4,0.55, boxstyle="round,pad=0.1", facecolor='#FFD700'))
    ax.text(5,6.77,'NEECHE WALA - JALDI WALA - BUTTON KE NEECHE - DONO MAZBOOT - CHANCE KE SAATH', ha='center',va='center', fontsize=9,weight='bold', color='black')
    ax.add_patch(box((0.3,3.0),4.45,3.3, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r15['fcol'], linewidth=2.5))
    ax.text(2.52,6.05,'15M - JALDI WALA - DIN ME 3-4 BAAR', ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
    ax.text(2.52,5.65,r15['faisla'], ha='center',va='center', fontsize=8.5,weight='bold', color=r15['fcol'])
    ax.text(2.52,5.25,r15['entry'], ha='center',va='center', fontsize=8,weight='bold', color='white')
    ax.text(2.52,4.85,r15['sl']+"  |  "+r15['tp'], ha='center',va='center', fontsize=8,color='white')
    ax.text(2.52,4.45,'BOS: '+r15['bos']+' | '+r15['fvg'], ha='center',va='center', fontsize=7.5,color='white')
    ax.text(2.52,4.05,r15['react']+' | VOL: '+('MAZBOOT' if r15['vol_ok'] else 'KAMZOR'), ha='center',va='center', fontsize=7.5,color='white')
    ax.text(2.52,3.65,'15M D: '+str(r15['d_bot'])+"-"+str(r15['d_top'])+' | S: '+str(r15['s_bot'])+"-"+str(r15['s_top']), ha='center',va='center', fontsize=7.5,color='white')
    ax.text(2.52,3.20,r15['chance_txt']+"  |  "+r15['rr'], ha='center',va='center', fontsize=8.5,weight='bold', color='#00FF88' if r15['chance']>=80 else '#FFAA00')
    ax.add_patch(box((5.25,3.0),4.45,3.3, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r1h['fcol'], linewidth=2.5))
    ax.text(7.47,6.05,'1H - BEECH WALA - DIN ME 2-3 BAAR', ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
    ax.text(7.47,5.65,r1h['faisla'], ha='center',va='center', fontsize=8.5,weight='bold', color=r1h['fcol'])
    ax.text(7.47,5.25,r1h['entry'], ha='center',va='center', fontsize=8,weight='bold', color='white')
    ax.text(7.47,4.85,r1h['sl']+"  |  "+r1h['tp'], ha='center',va='center', fontsize=8,color='white')
    ax.text(7.47,4.45,'BOS: '+r1h['bos']+' | '+r1h['fvg'], ha='center',va='center', fontsize=7.5,color='white')
    ax.text(7.47,4.05,r1h['react']+' | VOL: '+('MAZBOOT' if r1h['vol_ok'] else 'KAMZOR'), ha='center',va='center', fontsize=7.5,color='white')
    ax.text(7.47,3.65,'1H D: '+str(r1h['d_bot'])+"-"+str(r1h['d_top'])+' | S: '+str(r1h['s_bot'])+"-"+str(r1h['s_top']), ha='center',va='center', fontsize=7.5,color='white')
    ax.text(7.47,3.20,r1h['chance_txt']+"  |  "+r1h['rr'], ha='center',va='center', fontsize=8.5,weight='bold', color='#00FF88' if r1h['chance']>=80 else '#FFAA00')
    ax.plot([5.0, 5.0], [3.0, 6.3], color='red', linewidth=4)
    ax.text(5,2.55,'★ = ZAROORI BUTTON - YE HONA HI CHAHIYE', ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
    ax.text(5,2.15,'CHANCE 80%+ HO TO HI MAZBOOT SAMJHO - 60% SE KAM HO TO WAIT KARO', ha='center',va='center', fontsize=9,weight='bold', color='white')
    ax.text(5,1.75,'UPAR WALA 4H KISI KO NAHI ROKTA - NEECHE WALA APNA ALAG HAI', ha='center',va='center', fontsize=8,color='#AAAAAA')
    plt.savefig("Waseem_Buy_Sell_V4_1.jpg",dpi=200)
    st.pyplot(fig)

    # استاد جی - ٹیلیگرام والا میسج - صرف یہی جائے گا
    msg = f"""WASEEM TRADER - V4.1
GOLD PRICE: {abhi_s} [MT5 MANUAL] | ATR: {atr_s}
DATE: {date_txt} | {time_txt}

4H: {r4h['faisla']}
{r4h['entry']} | {r4h['sl']} | {r4h['tp']}
{r4h['chance_txt']}

1H: {r1h['faisla']}
{r1h['entry']} | {r1h['sl']} | {r1h['tp']}
{r1h['chance_txt']}

15M: {r15['faisla']}
{r15['entry']} | {r15['sl']} | {r15['tp']}
{r15['chance_txt']}

SETUP 12 WALA:
BUY: {buy_c}/12 | SELL: {sell_c}/12
RSI: {rsi_s} | EMA 15: {ema15_s} | EMA 50: {ema50_s}
VWAP: {vwap_s}
RES 1H: {r1h['res']} | SUP 1H: {r1h['sup']}
SL: 6 DOLLAR | TP1: 11 DOLLAR | TP2: 22 DOLLAR
"""

    # استاد جی - آپ والا بریک آؤٹ - 12 والا حساب - صرف ایک جگہ
    breakout_hua = False
    breakout_wajah = ""
    if "SAB MIL GAYA" in r4h['faisla'] or "SAB MIL GAYA" in r1h['faisla'] or "SAB MIL GAYA" in r15['faisla']:
        breakout_hua = True
        breakout_wajah = "SETUP MIL GAYA - BREAKOUT"
    elif buy_c >= 6:
        breakout_hua = True
        breakout_wajah = f"BUY MAZBOOT - BUY {buy_c}/12 HO GAYA - 6 YA 7"
    elif sell_c >= 5:
        breakout_hua = True
        breakout_wajah = f"SELL MAZBOOT - SELL {sell_c}/12 HO GAYA - 5 SE ZYADA"

    if breakout_hua:
        msg = f"🚨 BREAKOUT HO GAYA 🚨\n{breakout_wajah}\n\n" + msg
        TELEGRAM_BHEJO(msg)
        st.success("BREAKOUT HUA - MESSAGE KHUD CHALA GAYA")
    else:
        st.warning(f"ABHI BREAKOUT NAHI - BUY {buy_c}/12 | SELL {sell_c}/12 - WAIT KARO")

    # استاد جی - FIX - میسج کو محفوظ کر لیا، تاکہ نیچے والا بٹن دبانے پر ختم نہ ہو
    st.session_state['last_msg'] = msg

# استاد جی - FIX - یہ بٹن باہر ہے، بالکل آخر میں - اب ٹیسٹ کی طرح ہمیشہ چلے گا
if 'last_msg' in st.session_state:
    st.write("---")
    st.write("SIGNAL TAYYAR HAI - NEECHE WALA BUTTON DABAO")
    if st.button("TELEGRAM PE BHEJO - SIRF MESSAGE"):
        TELEGRAM_BHEJO(st.session_state['last_msg'])
        # WASEEM - V4.5 - FULL SCRIPT - PAGE 1 WASEEM + PAGE 2 BLACK GOLD + AUTO TELEGRAM
# IS KO PURANI FILE KE NEECHE PASTE KARO
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="WASEEM TRADER - V4.5", layout="centered")

# WASEEM - V4.7 - EK HI FILE - PURANI KO KHALI KAR KE YAHI PASTE KARO
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="WASEEM TRADER - V4.7", layout="centered")

if 'page' not in st.session_state:
    st.session_state['page'] = 1

# استاد جی - NEXT / BACK
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    if st.button("⬅ BACK", key="back_v47"):
        if st.session_state['page'] > 1:
            st.session_state['page'] -= 1
            st.rerun()
with c3:
    if st.button("NEXT ➡", key="next_v47"):
        if st.session_state['page'] < 2:
            st.session_state['page'] += 1
            st.rerun()

st.write(f"PAGE: {st.session_state['page']} / 2 - 1 = WASEEM WALA | 2 = BLACK GOLD WALA")
st.title("WASEEM TRADER - V4.7")

# استاد جی - PRICE WALA - AUTO + MANUAL DONO
price_mode = st.radio("PRICE KAHA SE LEIN?", ["AUTO - YAHOO WALI", "MANUAL - KHUD DALO - TRADINGVIEW WALI"], key="price_mode_v47", horizontal=True)
manual_price = st.number_input("MANUAL PRICE - JAISE 4060.33 - YAHAN ADJUST KARO", value=4060.33, key="manual_v47")

# استاد جی - YAHOO WALI AUTO PRICE
try:
    yf_data = yf.download("GC=F", period="1d", interval="1m", progress=False)
    if isinstance(yf_data.columns, pd.MultiIndex):
        yf_data.columns = yf_data.columns.get_level_values(0)
    yahoo_price = float(yf_data['Close'].iloc[-1])
except:
    yahoo_price = float(manual_price)

if price_mode == "AUTO - YAHOO WALI":
    FINAL_PRICE = float(yahoo_price)
    st.info(f"AUTO PRICE CHAL RAHI HAI - YAHOO WALI: {FINAL_PRICE} | MANUAL ME AAPNE DALI THI: {manual_price}")
else:
    FINAL_PRICE = float(manual_price)
    st.success(f"MANUAL PRICE CHAL RAHI HAI - AAP WALI: {FINAL_PRICE} | YAHOO WALI THI: {yahoo_price}")

AUTO_ON = st.checkbox("AUTO ON - SETUP BANTE HI TELEGRAM KHUD JAYEGA", value=False, key="auto_v47")
AUTO_MINUTE = st.selectbox("KITNI DEER BAAD CHECK KARE?", [1, 5, 15], index=1, key="auto_min_v47")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def TELEGRAM_BHEJO(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        return requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        st.error(f"TELEGRAM ME GALTI: {e}")
        return None

def ALAG_ALAG_BHEJO(m1, m2, m3, m4, m5, m6):
    for m in [m1, m2, m3, m4, m5, m6]:
        if m and m.strip() != "":
            TELEGRAM_BHEJO(m)
            time.sleep(1)

if st.button("TEST TELEGRAM", key="test_v47"):
    TELEGRAM_BHEJO("TEST - WASEEM TRADER V4.7 CHAL RAHA HAI")

abhi = float(FINAL_PRICE)
abhi_s = str(abhi)

CHALAO = st.button("SIGNAL BANAO", key="signal_v47") or AUTO_ON

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
        st.error("DATA NAHI AAYA - WAIT KARO")
        st.stop()

    for d in [df, df15, df4h]:
        d.loc[d.index[-1], 'Close'] = abhi
        if abhi > float(d.loc[d.index[-1], 'High']):
            d.loc[d.index[-1], 'High'] = abhi
        if abhi < float(d.loc[d.index[-1], 'Low']):
            d.loc[d.index[-1], 'Low'] = abhi

    pak_time = datetime.now() + timedelta(hours=5)
    date_txt = pak_time.strftime("%d %B %Y")
    time_txt = pak_time.strftime("%I:%M %p")

    # استاد جی - INDICATOR WALA HISAB
    df['TR'] = np.maximum(df['High']-df['Low'], np.maximum(abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))))
    atr_v = float(df['TR'].rolling(14).mean().iloc[-1])
    if atr_v < 3: atr_v = 3.0
    if atr_v > 15: atr_v = 15.0
    atr_s = str(round(atr_v,1))

    # استاد جی - BLACK GOLD WALA STRUCTURE - BREAKOUT + PULLBACK + FVG + BOS
    def BLACK_GOLD_STRUCTURE(d):
        # BOS - Break of Structure
        last_high = float(d['High'].iloc[-10:-1].max())
        last_low = float(d['Low'].iloc[-10:-1].min())
        bos_up = abhi > last_high
        bos_down = abhi < last_low
        # FVG
        fvg_bull = False; fvg_bear = False; fvg_bot = 0; fvg_top = 0
        for i in range(len(d)-15, len(d)):
            if i < 2: continue
            h2 = float(d['High'].iloc[i-2]); l0 = float(d['Low'].iloc[i]); h0 = float(d['High'].iloc[i]); l2 = float(d['Low'].iloc[i-2])
            if l0 - h2 > 1 and l0 - h2 < 8:
                fvg_bull = True; fvg_bot = h2; fvg_top = l0
            if l2 - h0 > 1 and l2 - h0 < 8:
                fvg_bear = True; fvg_bot = h0; fvg_top = l2
        # EMA TREND
        ema50 = float(d['Close'].ewm(span=50, adjust=False).mean().iloc[-1])
        trend_up = abhi > ema50
        # CANDLE REACTION
        o=float(d['Open'].iloc[-1]); c=float(d['Close'].iloc[-1]); h=float(d['High'].iloc[-1]); l=float(d['Low'].iloc[-1])
        body=abs(c-o); up_w=h-max(c,o); low_w=min(c,o)-l
        pin_buy = low_w > body*1.5 and c>o
        pin_sell = up_w > body*1.5 and c<o
        return {"bos_up":bos_up,"bos_down":bos_down,"fvg_bull":fvg_bull,"fvg_bear":fvg_bear,"fvg_bot":fvg_bot,"fvg_top":fvg_top,"trend_up":trend_up,"ema50":ema50,"pin_buy":pin_buy,"pin_sell":pin_sell,"last_high":last_high,"last_low":last_low}

    bg_1h = BLACK_GOLD_STRUCTURE(df)
    bg_15 = BLACK_GOLD_STRUCTURE(df15)
    bg_4h = BLACK_GOLD_STRUCTURE(df4h)

    # استاد جی - WASEEM WALA SIMPLE SETUP
    def SETUP_CALC(d, tf_name, demand_size):
        last_high = float(d['High'].iloc[-10:-1].max())
        last_low = float(d['Low'].iloc[-10:-1].min())
        curr_close = float(d['Close'].iloc[-1])
        bos_up = curr_close > last_high; bos_down = curr_close < last_low
        highs=[]; lows=[]
        for i in range(2, len(d)-2):
            h=float(d['High'].iloc[i]); l2=float(d['Low'].iloc[i])
            mx=float(d['High'].iloc[i-2:i+3].max()); mn=float(d['Low'].iloc[i-2:i+3].min())
            if h>=mx: highs.append(round(h))
            if l2<=mn: lows.append(round(l2))
        upar=[x for x in highs if x>abhi+3]; RES=min(upar) if upar else abhi+15
        neeche=[x for x in lows if x<abhi-3]; SUP=max(neeche) if neeche else abhi-15
        RES=round(RES/5)*5; SUP=round(SUP/5)*5
        d_bot=SUP; d_top=SUP+demand_size; s_bot=RES-demand_size; s_top=RES
        at_d = d_bot <= abhi <= d_top; at_s = s_bot <= abhi <= s_top
        return {"d_bot":int(d_bot),"d_top":int(d_top),"s_bot":int(s_bot),"s_top":int(s_top),"res":int(RES),"sup":int(SUP),"at_d":at_d,"at_s":at_s,"bos_up":bos_up,"bos_down":bos_down}

    r1h = SETUP_CALC(df, "1H", 10)
    r15 = SETUP_CALC(df15, "15M", 6)
    r4h = SETUP_CALC(df4h, "4H", 12)

    # استاد جی - 12 WALA INDICATOR
    ema50_v=float(df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]); ema50_s=str(int(ema50_v))
    ema15_v=float(df['Close'].ewm(span=15, adjust=False).mean().iloc[-1]); ema15_s=str(int(ema15_v))
    delta=df['Close'].diff(); gain=delta.where(delta>0,0).rolling(14).mean(); loss=-delta.where(delta<0,0).rolling(14).mean()
    rs=gain/(loss+0.00001); rsi_v=float(100-(100/(1+rs.iloc[-1]))); rsi_s=str(round(rsi_v,1))
    vwap_v=float((df['Close']*df['Volume']).cumsum().iloc[-1]/(df['Volume'].cumsum().iloc[-1]+1)); vwap_s=str(int(vwap_v))
    macd_line=float(df['Close'].ewm(span=12, adjust=False).mean().iloc[-1]-df['Close'].ewm(span=26, adjust=False).mean().iloc[-1])
    macd_series=df['Close'].ewm(span=12, adjust=False).mean()-df['Close'].ewm(span=26, adjust=False).mean()
    macd_sig_v=float(macd_series.ewm(span=9, adjust=False).mean().iloc[-1])
    sma20=float(df['Close'].rolling(20).mean().iloc[-1]); std20=float(df['Close'].rolling(20).std().iloc[-1])
    bb_up=sma20+2*std20; bb_low=sma20-2*std20
    o1=float(df['Open'].iloc[-1]); c1=float(df['Close'].iloc[-1]); h1=float(df['High'].iloc[-1]); l1=float(df['Low'].iloc[-1])
    body1=abs(c1-o1); up_w1=h1-max(c1,o1); low_w1=min(c1,o1)-l1
    pin_buy=low_w1>body1*2 and low_w1>up_w1; pin_sell=up_w1>body1*2 and up_w1>low_w1
    htf_up=c1>ema50_v; prev_low=float(df['Low'].iloc[-2]); prev_high=float(df['High'].iloc[-2])
    sweep_buy=l1<prev_low and c1>prev_low; sweep_sell=h1>prev_high and c1<prev_high
    hour_utc=datetime.now().hour; session_on=7<=hour_utc<=17
    vol_avg=float(df['Volume'].iloc[-20:].mean()); vol_aakhri_3=float(df['Volume'].iloc[-3:].mean())
    volume_strong=vol_aakhri_3>vol_avg
    fvg_touch = bg_1h['fvg_bot']-5 <= abhi <= bg_1h['fvg_top']+5
    buy_buttons=[("1 FVG BUY", fvg_touch),("2 VWAP BUY", abhi>vwap_v),("3 EMA 15 BUY", abhi>ema15_v),("4 RSI BUY", rsi_v>50),("5 Bollinger BUY", abhi <= bb_low+5),("6 MACD BUY", macd_line>macd_sig_v),("7 Pin Bar BUY", pin_buy),("8 HTF Trend BUY", htf_up),("9 Sweep BUY", sweep_buy),("10 FVG Touch BUY", fvg_touch and abhi>ema15_v),("11 Session BUY", session_on and abhi>ema15_v),("12 Volume BUY", volume_strong and abhi>ema15_v)]
    sell_buttons=[("1 FVG SELL", abhi<bg_1h['fvg_bot']-5),("2 VWAP SELL", abhi<vwap_v),("3 EMA 15 SELL", abhi<ema15_v),("4 RSI SELL", rsi_v<50),("5 Bollinger SELL", abhi >= bb_up-5),("6 MACD SELL", macd_line<macd_sig_v),("7 Pin Bar SELL", pin_sell),("8 HTF Trend SELL", not htf_up),("9 Sweep SELL", sweep_sell),("10 FVG Touch SELL", fvg_touch and abhi<ema15_v),("11 Session SELL", session_on and abhi<ema15_v),("12 Volume SELL", (not volume_strong) and abhi<ema15_v)]
    buy_c=sum(1 for _,v in buy_buttons if v); sell_c=sum(1 for _,v in sell_buttons if v)

    # استاد جی - PAGE 1 - WASEEM WALA
    if st.session_state['page'] == 1:
        st.write(f"### PAGE 1 - WASEEM WALA - PRICE: {abhi_s}")
        st.write(f"BUY: {buy_c}/12 | SELL: {sell_c}/12 | RSI: {rsi_s} | EMA 15: {ema15_s} | VWAP: {vwap_s}")
        st.write(f"1H DEMAND: {r1h['d_bot']}-{r1h['d_top']} | SUPPLY: {r1h['s_bot']}-{r1h['s_top']}")
        st.write(f"15M DEMAND: {r15['d_bot']}-{r15['d_top']} | SUPPLY: {r15['s_bot']}-{r15['s_top']}")

    # استاد جی - PAGE 2 - BLACK GOLD WALA - KHUBSURAT WALA - STRUCTURE + INDICATOR DONO
    if st.session_state['page'] == 2:
        BG_BUY_BOT = 4053; BG_BUY_TOP = 4056; BG_SL = 4048; BG_TP1 = 4061; BG_TP2 = 4066; BG_TP3 = 4071
        # استاد جی - STRUCTURE CHECK - BLACK GOLD JAISE
        breakout_up = bg_1h['bos_up'] or bg_15['bos_up']
        pullback_in_zone = BG_BUY_BOT <= abhi <= BG_BUY_TOP
        fvg_ok = bg_1h['fvg_bull'] or bg_15['fvg_bull']
        trend_ok = bg_1h['trend_up']
        pin_ok = bg_1h['pin_buy'] or bg_15['pin_buy']

        st.markdown("---")
        st.markdown("### 🖤💛 BLACK GOLD - GOLD SETUP")
        st.markdown(f"**PRICE ABHI: {abhi_s} | DATE: {date_txt} | TIME: {time_txt}**")

        # استاد جی - KHUBSURAT BOX
        colA, colB, colC = st.columns(3)
        with colA:
            st.markdown(f"**🟢 BUY ZONE**\n\n### {BG_BUY_BOT} - {BG_BUY_TOP}")
        with colB:
            st.markdown(f"**🔴 STOP LOSS**\n\n### {BG_SL}")
        with colC:
            st.markdown(f"**🎯 TAKE PROFIT**\n\n### {BG_TP1} | {BG_TP2} | {BG_TP3}")

        st.write(f"**STRUCTURE:** BOS UP: {'✅ HUA' if breakout_up else '❌ NAHI'} | FVG BULL: {'✅ HAI' if fvg_ok else '❌ NAHI'} | TREND UP: {'✅ HAI' if trend_ok else '❌ NAHI'} | PIN BAR BUY: {'✅ HAI' if pin_ok else '❌ NAHI'}")
        st.write(f"**INDICATOR:** BUY {buy_c}/12 | SELL {sell_c}/12 | RSI {rsi_s} | EMA 15 {ema15_s} | VWAP {vwap_s} | ATR {atr_s}")
        st.write(f"**KULIYA:** Breakout hua, ab Pullback ka wait hai - Zone me aaye to BUY - SL ke neeche gaya to FAIL")

        if pullback_in_zone and (breakout_up or fvg_ok or buy_c>=6):
            st.success("🚨 BLACK GOLD - PULLBACK AA GAYA - BUY SETUP BAN GAYA - PAHUNCHO 🚨")
            st.success(f"BUY KARO {BG_BUY_BOT} - {BG_BUY_TOP} ME | SL {BG_SL} | TP1 {BG_TP1} | TP2 {BG_TP2} | TP3 {BG_TP3} OPEN")
        elif abhi > BG_BUY_TOP:
            st.warning(f"PRICE UPAR HAI {abhi_s} - PULLBACK KA WAIT HAI - ZONE {BG_BUY_BOT}-{BG_BUY_TOP} ME AAYE TO BUY HOGA")
            if abhi >= BG_TP1:
                st.success(f"✅ TP1 {BG_TP1} LAG GAYA")
            if abhi >= BG_TP2:
                st.success(f"✅ TP2 {BG_TP2} LAG GAYA")
            if abhi >= BG_TP3:
                st.success(f"✅ TP3 {BG_TP3} LAG GAYA - AB OPEN CHHODO")
        elif abhi < BG_SL:
            st.error(f"❌ SL LAG GAYA - PRICE {abhi_s} < SL {BG_SL} - SETUP FAIL - AB DOBARA NAHI LENA")
        else:
            st.warning(f"⏳ PRICE BEECH ME HAI {abhi_s} - WAIT KARO - ZONE ME AANE DO")

        # استاد جی - CHART - BLACK GOLD WALA
        fig_bg, ax_bg = plt.subplots(figsize=(10,4))
        fig_bg.patch.set_facecolor('white'); ax_bg.set_facecolor('white')
        d_bg = df15.tail(50).copy()
        ax_bg.axhspan(BG_BUY_BOT, BG_BUY_TOP, color='#00FF88', alpha=0.25)
        ax_bg.text(len(d_bg)-1, BG_BUY_TOP+1, f"PULLBACK BUY {BG_BUY_BOT}-{BG_BUY_TOP}", fontsize=8, color='#00AA55', weight='bold', ha='right')
        ax_bg.axhline(BG_SL, color='red', linestyle='--', linewidth=1.2)
        ax_bg.text(len(d_bg)-1, BG_SL, f" SL {BG_SL}", fontsize=8, color='red', weight='bold', va='bottom')
        ax_bg.axhline(BG_TP1, color='green', linestyle='--', linewidth=1)
        ax_bg.text(len(d_bg)-1, BG_TP1, f" TP1 {BG_TP1}", fontsize=8, color='green', weight='bold', va='bottom')
        ax_bg.axhline(BG_TP2, color='green', linestyle='--', linewidth=1)
        ax_bg.text(len(d_bg)-1, BG_TP2, f" TP2 {BG_TP2}", fontsize=8, color='green', weight='bold', va='bottom')
        ax_bg.axhline(BG_TP3, color='green', linestyle='--', linewidth=1)
        ax_bg.text(len(d_bg)-1, BG_TP3, f" TP3 {BG_TP3}", fontsize=8, color='green', weight='bold', va='bottom')
        for i in range(len(d_bg)):
            o=float(d_bg['Open'].iloc[i]); c=float(d_bg['Close'].iloc[i]); h=float(d_bg['High'].iloc[i]); l=float(d_bg['Low'].iloc[i])
            col = '#00C853' if c>=o else '#FF1744'
            ax_bg.plot([i,i],[l,h], color=col, linewidth=1)
            ax_bg.add_patch(patches.Rectangle((i-0.35, min(o,c)), 0.7, max(abs(c-o),0.5), facecolor=col, edgecolor=col))
        ax_bg.axhline(abhi, color='black', linestyle='--', linewidth=1, alpha=0.6)
        ax_bg.text(len(d_bg)-1, abhi, f" {abhi_s}", fontsize=9, weight='bold', color='black', va='center')
        ax_bg.set_xlim(-1, len(d_bg)); ax_bg.grid(False); ax_bg.set_xticks([])
        for spine in ax_bg.spines.values():
            spine.set_visible(False)
        st.pyplot(fig_bg)

    # استاد جی - MESSAGE WALA - TELEGRAM + WHATSAPP COPY - DONO KE LIYE
    BG_BUY_BOT = 4053; BG_BUY_TOP = 4056; BG_SL = 4048; BG_TP1 = 4061; BG_TP2 = 4066; BG_TP3 = 4071
    bg_in_zone = BG_BUY_BOT <= abhi <= BG_BUY_TOP
    bg_alert = ""
    if bg_in_zone:
        bg_alert = f"🚨 BLACK GOLD - BUY SETUP BAN GAYA - PAHUNCHO 🚨\nBUY KARO - TIME HO GAYA HAI\n\nBUY ZONE: {BG_BUY_BOT} SE {BG_BUY_TOP} TAK HAI\n\nPRICE ABHI: {abhi_s}\nDATE: {date_txt} | TIME: {time_txt}\n\nTP1: {BG_TP1}\nTP2: {BG_TP2}\nTP3: {BG_TP3} - OPEN\nSL: {BG_SL}\n\nSTRUCTURE: BOS UP + FVG BULL + PULLBACK\nINDICATOR: BUY {buy_c}/12 | SELL {sell_c}/12 | RSI {rsi_s}"

    msg_status = f"STATUS - WASEEM TRADER\nPRICE: {abhi_s}\nATR: {atr_s} | DATE: {date_txt} | {time_txt}\nRSI: {rsi_s} | EMA 15: {ema15_s} | EMA 50: {ema50_s} | VWAP: {vwap_s}"
    msg_buysell = f"BUY / SELL - 12 WALA\nBUY: {buy_c}/12\nSELL: {sell_c}/12"
    msg_4h = f"4H SIGNAL\nPRICE: {abhi_s}\nDEMAND: {r4h['d_bot']}-{r4h['d_top']} | SUPPLY: {r4h['s_bot']}-{r4h['s_top']}"
    msg_1h = f"1H SIGNAL\nPRICE: {abhi_s}\nDEMAND: {r1h['d_bot']}-{r1h['d_top']} | SUPPLY: {r1h['s_bot']}-{r1h['s_top']}"
    msg_15m = f"15M SIGNAL\nPRICE: {abhi_s}\nDEMAND: {r15['d_bot']}-{r15['d_top']} | SUPPLY: {r15['s_bot']}-{r15['s_top']}"
    msg_alert = bg_alert

    st.session_state['m1']=msg_status; st.session_state['m2']=msg_buysell; st.session_state['m3']=msg_4h; st.session_state['m4']=msg_1h; st.session_state['m5']=msg_15m; st.session_state['m6']=msg_alert; st.session_state['bg_msg']=bg_alert

    # استاد جی - WHATSAPP KE LIYE COPY - YAHIN RAHEGA
    if bg_alert != "":
        st.write("---")
        st.write("### 📋 WHATSAPP KE LIYE COPY - YAHAN SE COPY KAR KE WHATSAPP PAR BHEJO")
        st.code(bg_alert)

    if AUTO_ON:
        last = st.session_state.get('last_bg_bheja', '')
        abhi_key = f"{bg_alert}-{abhi_s}"
        if bg_alert != "" and last != abhi_key:
            ALAG_ALAG_BHEJO(msg_status, msg_buysell, msg_4h, msg_1h, msg_15m, msg_alert)
            st.session_state['last_bg_bheja'] = abhi_key
            st.success("AUTO - TELEGRAM PE KHUD CHALA GAYA - BLACK GOLD WALA")
        elif bg_alert != "":
            st.write("YE WALA PEHLE HI BHEJ DIYA HAI - DOBARA NAHI BHEJUNGA")
        else:
            st.warning(f"AUTO CHECK HO RAHA HAI - BUY {buy_c}/12 | SELL {sell_c}/12 - ABHI ZONE ME NAHI HAI - IS LIYE NAHI BHEJA")
        time.sleep(AUTO_MINUTE * 60)
        st.rerun()
    else:
        if bg_alert != "":
            st.success("SETUP BAN GAYA - NEECHE WALA BUTTON DABAO - TELEGRAM PE JAYEGA")

if 'm1' in st.session_state and not AUTO_ON:
    st.write("---")
    if st.button("TELEGRAM PE BHEJO - ALAG ALAG MESSAGE", key="send_v47"):
        ALAG_ALAG_BHEJO(st.session_state['m1'], st.session_state['m2'], st.session_state['m3'], st.session_state['m4'], st.session_state['m5'], st.session_state['m6'])

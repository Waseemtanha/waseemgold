# WASEEM - V5.2 - HISSA 1 - UPAR WALA + HISAB WALA
# PURANI FILE KHALI KAR KE YAHI PASTE KARO - PHIR HISSA 2 NEECHE LAGANA
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="WASEEM TRADER - V5.2", layout="centered")

# استاد جی - PAGE WALA - SAB SE UPAR - SIGNAL SE PEHLE - IS LIYE NEXT KABHI NAHI RUKEGA
if 'page' not in st.session_state:
    st.session_state['page'] = 1
b1, b2 = st.columns(2)
with b1:
    if st.button("⬅ BACK", key="back_v52", use_container_width=True):
        if st.session_state['page'] > 1:
            st.session_state['page'] -= 1
            st.rerun()
with b2:
    if st.button("NEXT ➡", key="next_v52", use_container_width=True):
        if st.session_state['page'] < 3:
            st.session_state['page'] += 1
            st.rerun()
st.write(f"PAGE: {st.session_state['page']} / 3 - 1 = WASEEM | 2 = BLACK GOLD | 3 = WAJAH")
st.title("WASEEM TRADER - V5.2")

# استاد جی - PRICE WALA - AUTO + MANUAL DONO
price_mode = st.radio("PRICE KAHA SE LEIN?", ["AUTO - YAHOO WALI", "MANUAL - KHUD DALO - TRADINGVIEW WALI"], key="price_mode_v52", horizontal=True)
manual_price = st.number_input("MANUAL PRICE - JAISE 4060.33", value=4060.33, key="manual_v52")
try:
    yf_data = yf.download("GC=F", period="1d", interval="1m", progress=False)
    if isinstance(yf_data.columns, pd.MultiIndex):
        yf_data.columns = yf_data.columns.get_level_values(0)
    yahoo_price = float(yf_data['Close'].iloc[-1])
except:
    yahoo_price = float(manual_price)
if price_mode == "AUTO - YAHOO WALI":
    FINAL_PRICE = float(yahoo_price)
    st.info(f"AUTO PRICE: {FINAL_PRICE} | MANUAL THI: {manual_price}")
else:
    FINAL_PRICE = float(manual_price)
    st.success(f"MANUAL PRICE: {FINAL_PRICE} | YAHOO THI: {yahoo_price}")

AUTO_ON = st.checkbox("AUTO ON - SETUP BANTE HI TELEGRAM KHUD JAYEGA", value=False, key="auto_v52")
AUTO_MINUTE = st.selectbox("KITNI DEER BAAD CHECK KARE?", [1, 5, 15], index=1, key="auto_min_v52")
TRAILING_ON = st.checkbox("TRAILING ON - TP1 PAR SL B/E PAR", value=True, key="trail_v52")
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
if st.button("TEST TELEGRAM", key="test_v52"):
    TELEGRAM_BHEJO("TEST - WASEEM TRADER V5.2 CHAL RAHA HAI")

abhi = float(FINAL_PRICE)
abhi_s = str(abhi)
CHALAO = st.button("SIGNAL BANAO", key="signal_v52") or AUTO_ON

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
    df['TR'] = np.maximum(df['High']-df['Low'], np.maximum(abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))))
    atr_v = float(df['TR'].rolling(14).mean().iloc[-1])
    if atr_v < 3: atr_v = 3.0
    if atr_v > 15: atr_v = 15.0
    atr_s = str(round(atr_v,1))

    def NAYA_SETUP(d, tf_name, demand_size):
        last_high = float(d['High'].iloc[-10:-1].max())
        last_low = float(d['Low'].iloc[-10:-1].min())
        bos_up = abhi > last_high
        bos_down = abhi < last_low
        fvg_bull=False; fvg_bear=False; fvg_bot=0; fvg_top=0
        for i in range(len(d)-15, len(d)):
            if i < 2: continue
            h2=float(d['High'].iloc[i-2]); l0=float(d['Low'].iloc[i]); h0=float(d['High'].iloc[i]); l2=float(d['Low'].iloc[i-2])
            if l0-h2>1 and l0-h2<8:
                fvg_bull=True; fvg_bot=h2; fvg_top=l0
            if l2-h0>1 and l2-h0<8:
                fvg_bear=True; fvg_bot=h0; fvg_top=l2
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
        at_d = d_bot-3 <= abhi <= d_top+3
        at_s = s_bot-3 <= abhi <= s_top+3
        ema50=float(d['Close'].ewm(span=50, adjust=False).mean().iloc[-1])
        delta=d['Close'].diff(); gain=delta.where(delta>0,0).rolling(14).mean(); loss=-delta.where(delta<0,0).rolling(14).mean()
        rs=gain/(loss+0.00001); rsi=float(100-(100/(1+rs.iloc[-1])))
        o=float(d['Open'].iloc[-1]); c=float(d['Close'].iloc[-1]); h=float(d['High'].iloc[-1]); l=float(d['Low'].iloc[-1])
        body=abs(c-o); up_w=h-max(c,o); low_w=min(c,o)-l
        pin_buy=low_w>body and c>o; pin_sell=up_w>body and c<o
        buy_score=0
        if at_d: buy_score+=1
        if bos_up or fvg_bull: buy_score+=1
        if abhi>ema50: buy_score+=1
        if rsi>50: buy_score+=1
        if pin_buy: buy_score+=1
        sell_score=0
        if at_s: sell_score+=1
        if bos_down or fvg_bear: sell_score+=1
        if abhi<ema50: sell_score+=1
        if rsi<50: sell_score+=1
        if pin_sell: sell_score+=1
        sl_dist=6; tp1_dist=11; tp2_dist=22; tp3_dist=33
        if buy_score>=3:
            entry_bot=int(d_bot); entry_top=int(d_top); entry_mid=int((d_bot+d_top)/2)
            sl=int(entry_bot-sl_dist)
            tp1=int(entry_top+tp1_dist); tp2=int(entry_top+tp2_dist); tp3=int(entry_top+tp3_dist)
            tp1_gol=round(tp1/10)*10
            if abs(tp1_gol-tp1)<=5: tp1=tp1_gol
            # استاد جی - TRAILING FIX - TP1 LAGNE SE PEHLE SL NAHI HILEGA
            sl_show=sl; trail_txt="SL FIX HAI - 6 DOLLAR"
            if TRAILING_ON:
                if abhi>=tp1:
                    sl_show=entry_mid; trail_txt=f"TP1 LAG GAYA - SL AB B/E PAR {sl_show}"
                if abhi>=tp2:
                    sl_show=tp1; trail_txt=f"TP2 LAG GAYA - SL AB TP1 PAR {sl_show} - 11 PAKKA"
            return {'side':'BUY','faisla':f"{tf_name} BUY SETUP - {buy_score}/5 MIL GAYA",'fcol':'#00FF88','entry':f"Buy {entry_bot} - {entry_top}",'entry_bot':entry_bot,'entry_top':entry_top,'entry_mid':entry_mid,'sl':sl,'sl_show':sl_show,'tp1':tp1,'tp2':tp2,'tp3':tp3,'tp_txt':f"TP1: {tp1} | TP2: {tp2} | TP3: {tp3} OPEN",'sl_txt':f"SL: {sl_show} - {trail_txt}",'chance':buy_score*20,'chance_txt':f"CHANCE: {buy_score*20}%",'rr':"SL 6 | TP1 11 | TP2 22 | TP3 OPEN",'bos':"BOS UP" if bos_up else "BOS Nahi",'fvg':"FVG Bullish" if fvg_bull else "FVG Nahi",'d_bot':entry_bot,'d_top':entry_top,'s_bot':int(s_bot),'s_top':int(s_top),'res':int(RES),'sup':int(SUP),'fvg_bot':int(fvg_bot),'fvg_top':int(fvg_top),'rsi':rsi,'ema50':ema50,'trail_txt':trail_txt,'buy_score':buy_score,'sell_score':sell_score}
        if sell_score>=3:
            entry_bot=int(s_bot); entry_top=int(s_top); entry_mid=int((s_bot+s_top)/2)
            sl=int(entry_top+sl_dist)
            tp1=int(entry_bot-tp1_dist); tp2=int(entry_bot-tp2_dist); tp3=int(entry_bot-tp3_dist)
            tp1_gol=round(tp1/10)*10
            if abs(tp1_gol-tp1)<=5: tp1=tp1_gol
            sl_show=sl; trail_txt="SL FIX HAI - 6 DOLLAR"
            if TRAILING_ON:
                if abhi<=tp1:
                    sl_show=entry_mid; trail_txt=f"TP1 LAG GAYA - SL AB B/E PAR {sl_show}"
                if abhi<=tp2:
                    sl_show=tp1; trail_txt=f"TP2 LAG GAYA - SL AB TP1 PAR {sl_show} - 11 PAKKA"
            return {'side':'SELL','faisla':f"{tf_name} SELL SETUP - {sell_score}/5 MIL GAYA",'fcol':'#FF4444','entry':f"Sell {entry_bot} - {entry_top}",'entry_bot':entry_bot,'entry_top':entry_top,'entry_mid':entry_mid,'sl':sl,'sl_show':sl_show,'tp1':tp1,'tp2':tp2,'tp3':tp3,'tp_txt':f"TP1: {tp1} | TP2: {tp2} | TP3: {tp3} OPEN",'sl_txt':f"SL: {sl_show} - {trail_txt}",'chance':sell_score*20,'chance_txt':f"CHANCE: {sell_score*20}%",'rr':"SL 6 | TP1 11 | TP2 22 | TP3 OPEN",'bos':"BOS DOWN" if bos_down else "BOS Nahi",'fvg':"FVG Bearish" if fvg_bear else "FVG Nahi",'d_bot':int(d_bot),'d_top':int(d_top),'s_bot':entry_bot,'s_top':entry_top,'res':int(RES),'sup':int(SUP),'fvg_bot':int(fvg_bot),'fvg_top':int(fvg_top),'rsi':rsi,'ema50':ema50,'trail_txt':trail_txt,'buy_score':buy_score,'sell_score':sell_score}
        return {'side':'WAIT','faisla':f"{tf_name} WAIT - {buy_score}/5 BUY | {sell_score}/5 SELL - 3 CHAHIYE",'fcol':'#FFAA00','entry':f"Wait - Demand {int(d_bot)}-{int(d_top)} | Supply {int(s_bot)}-{int(s_top)}",'entry_bot':int(d_bot),'entry_top':int(d_top),'entry_mid':int((d_bot+d_top)/2),'sl':0,'sl_show':0,'tp1':0,'tp2':0,'tp3':0,'tp_txt':"TP: Wait Karo",'sl_txt':f"SL: Abhi Entry Nahi - ATR {atr_s}",'chance':max(buy_score,sell_score)*20,'chance_txt':f"CHANCE: {max(buy_score,sell_score)*20}% - KAM HAI",'rr':"RR: Abhi Entry Nahi",'bos':"BOS UP" if bos_up else "BOS DOWN" if bos_down else "BOS Nahi",'fvg':"FVG Bullish" if fvg_bull else "FVG Bearish" if fvg_bear else "FVG Nahi",'d_bot':int(d_bot),'d_top':int(d_top),'s_bot':int(s_bot),'s_top':int(s_top),'res':int(RES),'sup':int(SUP),'fvg_bot':int(fvg_bot),'fvg_top':int(fvg_top),'rsi':rsi,'ema50':ema50,'trail_txt':"",'buy_score':buy_score,'sell_score':sell_score}
    r4h = NAYA_SETUP(df4h, "4H", 12)
    r1h = NAYA_SETUP(df, "1H", 10)
    r15 = NAYA_SETUP(df15, "15M", 6)
    ema50_v=float(df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]); ema50_s=str(int(ema50_v))
    ema15_v=float(df['Close'].ewm(span=15, adjust=False).mean().iloc[-1]); ema15_s=str(int(ema15_v))
    delta=df['Close'].diff(); gain=delta.where(delta>0,0).rolling(14).mean(); loss=-delta.where(delta<0,0).rolling(14).mean()
    rs=gain/(loss+0.00001); rsi_v=float(100-(100/(1+rs.iloc[-1]))); rsi_s=str(round(rsi_v,1))
    vwap_v=float((df['Close']*df['Volume']).cumsum().iloc[-1]/(df['Volume'].cumsum().iloc[-1]+1)); vwap_s=str(int(vwap_v))
    macd_line=float(df['Close'].ewm(span=12, adjust=False).mean().iloc[-1]-df['Close'].ewm(span=26, adjust=False).mean().iloc[-1])
    macd_series=df['Close'].ewm(span=12, adjust=False).mean()-df['Close'].ewm(span=26, adjust=False).mean()
    macd_sig_v=float(macd_series.ewm(span=9, adjust=False).mean().iloc[-1])
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
    fvg_touch = r1h['fvg_bot']-5 <= abhi <= r1h['fvg_top']+5
    buy_buttons=[]
    buy_buttons.append(("1 FVG BUY ★", str(r1h['fvg_bot'])+"-"+str(r1h['fvg_top'])+" | "+abhi_s, fvg_touch))
    buy_buttons.append(("2 VWAP BUY", abhi_s+" > "+vwap_s if abhi>vwap_v else abhi_s+" < "+vwap_s, abhi>vwap_v))
    buy_buttons.append(("3 EMA 15 BUY", abhi_s+" > "+ema15_s if abhi>ema15_v else abhi_s+" < "+ema15_s, abhi>ema15_v))
    buy_buttons.append(("4 RSI 1H BUY", "RSI "+rsi_s+" > 50" if rsi_v>50 else "RSI "+rsi_s+" < 50", rsi_v>50))
    buy_buttons.append(("5 Bollinger BUY", "Low "+bb_low_s+" | "+abhi_s, abhi <= bb_low+5))
    buy_buttons.append(("6 MACD BUY", "MACD Upar Hai" if macd_line>macd_sig_v else "MACD Neeche Hai", macd_line>macd_sig_v))
    buy_buttons.append(("7 Pin Bar BUY ★", "Neeche Wick Lambi" if pin_buy else "Pin Nahi Bana", pin_buy))
    buy_buttons.append(("8 HTF Trend BUY ★", "1H Trend Upar" if htf_up else "1H Trend Neeche", htf_up))
    buy_buttons.append(("9 Sweep BUY ★", "Neeche Sweep Hua" if sweep_buy else "Sweep Nahi Hua", sweep_buy))
    buy_buttons.append(("10 FVG Touch BUY", "FVG Touch + Upar" if fvg_touch and abhi>ema15_v else "FVG Touch Nahi", fvg_touch and abhi>ema15_v))
    buy_buttons.append(("11 Session BUY", "Session ON + Upar" if session_on and abhi>ema15_v else "Session Off / Neeche", session_on and abhi>ema15_v))
    buy_buttons.append(("12 Volume BUY ★", vol_s+" / "+vol_avg_s, volume_strong and abhi>ema15_v))
    sell_buttons=[]
    sell_buttons.append(("1 FVG SELL ★", abhi_s+" < "+str(r1h['fvg_bot']) if abhi<r1h['fvg_bot']-5 else abhi_s+" > "+str(r1h['fvg_bot']), abhi<r1h['fvg_bot']-5))
    sell_buttons.append(("2 VWAP SELL", abhi_s+" < "+vwap_s if abhi<vwap_v else abhi_s+" > "+vwap_s, abhi<vwap_v))
    sell_buttons.append(("3 EMA 15 SELL", abhi_s+" < "+ema15_s if abhi<ema15_v else abhi_s+" > "+ema15_s, abhi<ema15_v))
    sell_buttons.append(("4 RSI 1H SELL", "RSI "+rsi_s+" < 50" if rsi_v<50 else "RSI "+rsi_s+" > 50", rsi_v<50))
    sell_buttons.append(("5 Bollinger SELL", "Up "+bb_up_s+" | "+abhi_s, abhi >= bb_up-5))
    sell_buttons.append(("6 MACD SELL", "MACD Neeche Hai" if macd_line<macd_sig_v else "MACD Upar Hai", macd_line<macd_sig_v))
    sell_buttons.append(("7 Pin Bar SELL ★", "Upar Wick Lambi" if pin_sell else "Pin Nahi Bana", pin_sell))
    sell_buttons.append(("8 HTF Trend SELL ★", "1H Trend Neeche" if not htf_up else "1H Trend Upar", not htf_up))
    sell_buttons.append(("9 Sweep SELL ★", "Upar Sweep Hua" if sweep_sell else "Sweep Nahi Hua", sweep_sell))
    sell_buttons.append(("10 FVG Touch SELL", "FVG Touch + Neeche" if fvg_touch and abhi<ema15_v else "FVG Touch Nahi", fvg_touch and abhi<ema15_v))
    sell_buttons.append(("11 Session SELL", "London/NY ON + Neeche" if session_on and abhi<ema15_v else "Session Off / Upar", session_on and abhi<ema15_v))
    sell_buttons.append(("12 Volume SELL ★", "VOL STRONG" if volume_strong else "VOL KAM", (not volume_strong) and abhi<ema15_v))
    buy_c=sum(1 for _,_,v in buy_buttons if v); sell_c=sum(1 for _,_,v in sell_buttons if v)
    # استاد جی - FIX - SIGNAL KO YAAD RAKHO - NEXT DABANE PAR BHI NA BHULE
    st.session_state['has_data'] = True
    st.session_state['last_r4h'] = r4h
    st.session_state['last_r1h'] = r1h
    st.session_state['last_r15'] = r15
    st.session_state['last_buy_buttons'] = buy_buttons
    st.session_state['last_sell_buttons'] = sell_buttons
    st.session_state['last_buy_c'] = buy_c
    st.session_state['last_sell_c'] = sell_c
    st.session_state['last_abhi'] = abhi
    st.session_state['last_abhi_s'] = abhi_s
    st.session_state['last_rsi_s'] = rsi_s
    st.session_state['last_ema15_s'] = ema15_s
    st.session_state['last_ema50_s'] = ema50_s
    st.session_state['last_vwap_s'] = vwap_s
    st.session_state['last_atr_s'] = atr_s
    st.session_state['last_date'] = date_txt
    st.session_state['last_time'] = time_txt
    st.session_state['last_df15'] = df15.tail(50).copy()
    # WASEEM - V5.2 - HISSA 2 - PAGE 1 + PAGE 2 + PAGE 3 + TELEGRAM
# IS KO HISSA 1 KE BILKUL NEECHE LAGAO - YE if CHALAO KE BAHAR HAI - IS LIYE NEXT KAM KAREGA
if st.session_state.get('has_data', False):
    r4h = st.session_state['last_r4h']
    r1h = st.session_state['last_r1h']
    r15 = st.session_state['last_r15']
    buy_buttons = st.session_state['last_buy_buttons']
    sell_buttons = st.session_state['last_sell_buttons']
    buy_c = st.session_state['last_buy_c']
    sell_c = st.session_state['last_sell_c']
    abhi = st.session_state['last_abhi']
    abhi_s = st.session_state['last_abhi_s']
    rsi_s = st.session_state['last_rsi_s']
    ema15_s = st.session_state['last_ema15_s']
    ema50_s = st.session_state['last_ema50_s']
    vwap_s = st.session_state['last_vwap_s']
    atr_s = st.session_state['last_atr_s']
    date_txt = st.session_state['last_date']
    time_txt = st.session_state['last_time']
    df15_show = st.session_state['last_df15']

    # استاد جی - PAGE 1 - WASEEM WALA - TASVEER - SHAPE WAHI WALI
    if st.session_state['page'] == 1:
        fig,ax = plt.subplots(figsize=(10,30))
        ax.set_xlim(0,10); ax.set_ylim(0,30); ax.axis('off')
        fig.patch.set_facecolor('#0A0A0A'); ax.set_facecolor('#0A0A0A')
        box = patches.FancyBboxPatch
        ax.add_patch(box((0.3,29.0),9.4,0.9, boxstyle="round,pad=0.1", facecolor='#0A0A0A', edgecolor='#FFD700', linewidth=3))
        ax.text(5,29.45,'WASEEM  TRADER - V5.2', ha='center',va='center', color='#FFD700', fontsize=26,weight='bold')
        ax.text(5,29.15,'ALLIANCE WALA - CHoCH + RETEST + ROUND 2 + TRAILING', ha='center',va='center', color='white',fontsize=9)
        ax.add_patch(box((0.3,28.3),9.4,0.55, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor='#FFD700', linewidth=1))
        ax.text(5,28.57,date_txt + "  |  " + time_txt + "  |  PAKISTAN TIME", ha='center',va='center', fontsize=11,weight='bold', color='#FFD700')
        ax.add_patch(box((0.3,27.3),9.4,0.85, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor='#FFD700', linewidth=1.5))
        ax.text(5,27.8,'GOLD: ' + abhi_s + '  |  ATR: ' + atr_s, ha='center',va='center', fontsize=22,weight='bold', color='white')
        ax.text(5,27.45,'4H = MAZBOOT  |  1H = BEECH  |  15M = JALDI', ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
        ax.add_patch(box((0.3,24.0),9.4,3.0, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r4h['fcol'], linewidth=2.5))
        ax.text(5,26.65,'4H SETUP - ALLIANCE WALA', ha='center',va='center', fontsize=11,weight='bold', color='#FFD700')
        ax.text(5,26.25,r4h['faisla'], ha='center',va='center', fontsize=11,weight='bold', color=r4h['fcol'])
        ax.text(5,25.85,r4h['entry']+"  |  "+r4h['sl_txt']+"  |  "+r4h['tp_txt'], ha='center',va='center', fontsize=9,weight='bold', color='white')
        ax.text(5,25.45,'BOS: '+r4h['bos']+' | '+r4h['fvg'], ha='center',va='center', fontsize=8,color='white')
        ax.text(5,25.05,'4H D: '+str(r4h['d_bot'])+"-"+str(r4h['d_top'])+'  |  4H S: '+str(r4h['s_bot'])+"-"+str(r4h['s_top']), ha='center',va='center', fontsize=8,color='white')
        ax.text(5,24.45,r4h['chance_txt']+"  |  "+r4h['rr'], ha='center',va='center', fontsize=10,weight='bold', color='#00FF88' if r4h['chance']>=60 else '#FFAA00')
        ax.text(5,24.15,r4h['trail_txt'], ha='center',va='center', fontsize=8,color='#AAAAAA')
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
        ax.text(5,6.77,'NEECHE WALA - JALDI WALA - DONO MAZBOOT', ha='center',va='center', fontsize=9,weight='bold', color='black')
        ax.add_patch(box((0.3,3.0),4.45,3.3, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r15['fcol'], linewidth=2.5))
        ax.text(2.52,6.05,'15M - JALDI WALA', ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
        ax.text(2.52,5.65,r15['faisla'], ha='center',va='center', fontsize=8.5,weight='bold', color=r15['fcol'])
        ax.text(2.52,5.25,r15['entry'], ha='center',va='center', fontsize=8,weight='bold', color='white')
        ax.text(2.52,4.85,r15['sl_txt']+"  |  "+r15['tp_txt'], ha='center',va='center', fontsize=7,color='white')
        ax.text(2.52,4.45,'BOS: '+r15['bos']+' | '+r15['fvg'], ha='center',va='center', fontsize=7.5,color='white')
        ax.text(2.52,4.05,r15['trail_txt'], ha='center',va='center', fontsize=7.5,color='white')
        ax.text(2.52,3.65,'15M D: '+str(r15['d_bot'])+"-"+str(r15['d_top'])+' | S: '+str(r15['s_bot'])+"-"+str(r15['s_top']), ha='center',va='center', fontsize=7.5,color='white')
        ax.text(2.52,3.20,r15['chance_txt']+"  |  "+r15['rr'], ha='center',va='center', fontsize=8.5,weight='bold', color='#00FF88' if r15['chance']>=60 else '#FFAA00')
        ax.add_patch(box((5.25,3.0),4.45,3.3, boxstyle="round,pad=0.1", facecolor='#1A1A1A', edgecolor=r1h['fcol'], linewidth=2.5))
        ax.text(7.47,6.05,'1H - BEECH WALA', ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
        ax.text(7.47,5.65,r1h['faisla'], ha='center',va='center', fontsize=8.5,weight='bold', color=r1h['fcol'])
        ax.text(7.47,5.25,r1h['entry'], ha='center',va='center', fontsize=8,weight='bold', color='white')
        ax.text(7.47,4.85,r1h['sl_txt']+"  |  "+r1h['tp_txt'], ha='center',va='center', fontsize=7,color='white')
        ax.text(7.47,4.45,'BOS: '+r1h['bos']+' | '+r1h['fvg'], ha='center',va='center', fontsize=7.5,color='white')
        ax.text(7.47,4.05,r1h['trail_txt'], ha='center',va='center', fontsize=7.5,color='white')
        ax.text(7.47,3.65,'1H D: '+str(r1h['d_bot'])+"-"+str(r1h['d_top'])+' | S: '+str(r1h['s_bot'])+"-"+str(r1h['s_top']), ha='center',va='center', fontsize=7.5,color='white')
        ax.text(7.47,3.20,r1h['chance_txt']+"  |  "+r1h['rr'], ha='center',va='center', fontsize=8.5,weight='bold', color='#00FF88' if r1h['chance']>=60 else '#FFAA00')
        ax.plot([5.0, 5.0], [3.0, 6.3], color='red', linewidth=4)
        ax.text(5,2.55,'★ = ZAROORI BUTTON', ha='center',va='center', fontsize=9,weight='bold', color='#FFD700')
        ax.text(5,2.15,'CHANCE 60%+ HO TO SETUP - 60% SE KAM HO TO WAIT', ha='center',va='center', fontsize=9,weight='bold', color='white')
        ax.text(5,1.75,'TRAILING ON HAI TO TP1 PAR SL B/E PAR AA JAYEGA', ha='center',va='center', fontsize=8,color='#AAAAAA')
        plt.savefig("Waseem_Buy_Sell_V5_2.jpg",dpi=200)
        st.pyplot(fig)

    # استاد جی - PAGE 2 - BLACK GOLD WALA - AB FIX NAHI - 1H SE BANEGA - INDICATOR DEKH KAR
    if st.session_state['page'] == 2:
        bg = r1h
        if bg['side'] == 'BUY':
            BG_BOT=bg['entry_bot']; BG_TOP=bg['entry_top']; BG_SL=bg['sl']; BG_TP1=bg['tp1']; BG_TP2=bg['tp2']; BG_TP3=bg['tp3']; BG_TXT="BUY"
        elif bg['side'] == 'SELL':
            BG_BOT=bg['entry_bot']; BG_TOP=bg['entry_top']; BG_SL=bg['sl']; BG_TP1=bg['tp1']; BG_TP2=bg['tp2']; BG_TP3=bg['tp3']; BG_TXT="SELL"
        else:
            BG_BOT=bg['d_bot']; BG_TOP=bg['d_top']; BG_SL=bg['d_bot']-6; BG_TP1=bg['d_top']+11; BG_TP2=bg['d_top']+22; BG_TP3=bg['d_top']+33; BG_TXT="WAIT"
        st.markdown("---")
        st.markdown("### 🖤💛 BLACK GOLD - GOLD SETUP - V5.2")
        st.markdown(f"**PRICE ABHI: {abhi_s} | DATE: {date_txt} | TIME: {time_txt}**")
        colA, colB, colC = st.columns(3)
        with colA:
            st.markdown(f"**🟢 {BG_TXT} ZONE**\n\n### {BG_BOT} - {BG_TOP}")
        with colB:
            st.markdown(f"**🔴 STOP LOSS**\n\n### {BG_SL} - 6 DOLLAR")
        with colC:
            st.markdown(f"**🎯 TAKE PROFIT**\n\n### {BG_TP1} | {BG_TP2} | {BG_TP3}")
        st.write(f"**SETUP:** {bg['faisla']} | {bg['chance_txt']} | {bg['rr']}")
        st.write(f"**STRUCTURE:** {bg['bos']} | {bg['fvg']} | INDICATOR: BUY {buy_c}/12 | SELL {sell_c}/12 | RSI {rsi_s} | ATR {atr_s}")
        st.write(f"**TRAILING:** {bg['trail_txt']}")
        if bg['side'] in ['BUY','SELL']:
            st.success(f"🚨 BLACK GOLD - {BG_TXT} SETUP BAN GAYA 🚨 - {BG_BOT}-{BG_TOP} | SL {BG_SL} | TP1 {BG_TP1} | TP2 {BG_TP2} | TP3 {BG_TP3} OPEN")
            st.info(f"ROUND 2 - AGAR PRICE WAPAS {BG_BOT}-{BG_TOP} PAR AAYE TO PHIR SE {BG_TXT} KARNA - SAME SL / SAME TP")
        else:
            st.warning(f"⏳ PRICE BEECH ME HAI {abhi_s} - WAIT KARO - ZONE ME AANE DO - DEMAND {BG_BOT}-{BG_TOP}")
        fig_bg, ax_bg = plt.subplots(figsize=(10,4))
        fig_bg.patch.set_facecolor('white'); ax_bg.set_facecolor('white')
        d_bg = df15_show.copy()
        ax_bg.axhspan(BG_BOT, BG_TOP, color='#00FF88' if BG_TXT=='BUY' else '#FF4444' if BG_TXT=='SELL' else '#FFAA00', alpha=0.25)
        ax_bg.text(len(d_bg)-1, BG_TOP+1, f"{BG_TXT} {BG_BOT}-{BG_TOP}", fontsize=8, color='black', weight='bold', ha='right')
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

    # استاد جی - PAGE 3 - WAJAH WALA - KYUN SETUP DIYA?
    if st.session_state['page'] == 3:
        st.markdown("---")
        st.markdown("### 📖 PAGE 3 - WAJAH WALA - MAIN IS LIYE SETUP DE RAHA HOON")
        st.markdown(f"**PRICE ABHI: {abhi_s} | DATE: {date_txt} | TIME: {time_txt} | RSI: {rsi_s} | ATR: {atr_s}**")
        st.markdown("**استاد جی، سیٹ اپ اپنی مرضی سے نہیں دیا، انڈیکیٹر دیکھ کر دیا ہے۔**")
        def WAJAH_BANAO(r, tf_name):
            lines = []
            lines.append(f"**{tf_name} WALA - {r['faisla']}**")
            lines.append(f"**CHANCE: {r['chance_txt']} | {r['rr']}**")
            lines.append(f"**ENTRY: {r['entry']} | {r['sl_txt']} | {r['tp_txt']}**")
            lines.append("")
            if r['side'] == 'BUY':
                lines.append("استاد جی، اوپر والا BUY میں اس لیے دے رہا ہوں کہ:")
                lines.append(f"**۱۔** پرائس ڈیمانڈ زون **{r['d_bot']} - {r['d_top']}** پر آ گئی ہے، یہاں سے پہلے بھی اوپر اٹھی تھی۔")
                lines.append(f"**۲۔** **{r['bos']}** ہو گیا ہے، مطلب ٹرینڈ اوپر بن گیا ہے۔")
                lines.append(f"**۳۔** **{r['fvg']} - {r['fvg_bot']} - {r['fvg_top']}** ہے، مطلب نیچے سے اوپر کی طرف جگہ ہے۔")
                lines.append(f"**۴۔** **RSI {round(r['rsi'],1)} ہے**، 50 سے اوپر ہے، مطلب بائے والا طاقتور ہے۔")
                lines.append(f"**۵۔** **EMA 50 {int(r['ema50'])} ہے**، پرائس اس کے اوپر ہے، مطلب بڑا ٹرینڈ بھی اوپر ہے۔")
                lines.append(f"**۶۔** **{r['trail_txt']}**")
                lines.append("**اس لیے BUY دے رہا ہوں۔**")
            elif r['side'] == 'SELL':
                lines.append("استاد جی، اوپر والا SELL میں اس لیے دے رہا ہوں کہ:")
                lines.append(f"**۱۔** پرائس سپلائی زون **{r['s_bot']} - {r['s_top']}** پر آ گئی ہے، یہاں سے پہلے بھی نیچے گری تھی۔")
                lines.append(f"**۲۔** **{r['bos']}** ہو گیا ہے، مطلب ٹرینڈ نیچے بن گیا ہے۔")
                lines.append(f"**۳۔** **{r['fvg']} - {r['fvg_bot']} - {r['fvg_top']}** ہے، مطلب اوپر سے نیچے کی طرف جگہ ہے۔")
                lines.append(f"**۴۔** **RSI {round(r['rsi'],1)} ہے**، 50 سے نیچے ہے، مطلب سیلر طاقتور ہیں، بائے والا دباؤ ہی نہیں ہے۔")
                lines.append(f"**۵۔** **EMA 50 {int(r['ema50'])} ہے**، پرائس اس کے نیچے ہے، مطلب بڑا ٹرینڈ بھی نیچے ہے۔")
                lines.append(f"**۶۔** **{r['trail_txt']}**")
                lines.append("**اس لیے SELL دے رہا ہوں۔**")
            else:
                lines.append("استاد جی، اوپر والا WAIT میں اس لیے بول رہا ہوں کہ:")
                lines.append(f"**۱۔** پرائس بیچ میں ہے، نہ ڈیمانڈ **{r['d_bot']} - {r['d_top']}** پر ہے، نہ سپلائی **{r['s_bot']} - {r['s_top']}** پر ہے۔")
                lines.append(f"**۲۔** 5 میں سے صرف **{int(r['chance']/20)} چیزیں** ملی ہیں، **3 چاہیے تھیں**۔")
                lines.append(f"**۳۔** **RSI {round(r['rsi'],1)} ہے**، بیچ میں ہے۔")
                lines.append(f"**۴۔** **BOS: {r['bos']} | FVG: {r['fvg']}** - ابھی پورا نہیں بنا۔")
                lines.append("**اس لیے WAIT بولا ہے، تاکہ غلط انٹری نہ ہو۔**")
            return "\n\n".join(lines)
        st.markdown("---")
        st.markdown(WAJAH_BANAO(r4h, "4H"))
        st.markdown("---")
        st.markdown(WAJAH_BANAO(r1h, "1H"))
        st.markdown("---")
        st.markdown(WAJAH_BANAO(r15, "15M"))
        st.markdown("---")
        bg_r = r1h
        st.markdown("### 🖤💛 BLACK GOLD WALI WAJAH - ALAG SE")
        if bg_r['side'] in ['BUY','SELL']:
            st.markdown(f"**BLACK GOLD والا {bg_r['side']} میں اس لیے دے رہا ہوں کہ 1H والا بھی وہی بول رہا ہے۔**")
            st.markdown(WAJAH_BANAO(bg_r, "BLACK GOLD - 1H SE"))
            st.markdown(f"**ROUND 2 - اگر پرائس واپس {bg_r['entry_bot']} - {bg_r['entry_top']} پر آئے تو پھر سے {bg_r['side']} کرنا، اسی وجہ سے۔**")
        else:
            st.markdown("**BLACK GOLD والا WAIT میں اس لیے بول رہا ہے کہ 1H والا بھی WAIT بول رہا ہے۔**")
            st.markdown(WAJAH_BANAO(bg_r, "BLACK GOLD - 1H SE"))
        wajah_msg = f"WAJAH WALA - V5.2\nPRICE: {abhi_s} | {date_txt} | {time_txt}\n\n4H: {r4h['faisla']}\n1H: {r1h['faisla']}\n15M: {r15['faisla']}\nBLACK GOLD: {bg_r['faisla']}"
        st.session_state['m_wajah'] = wajah_msg
        st.write("---")
        st.write("### 📋 WHATSAPP KE LIYE COPY - WAJAH WALA")
        st.code(wajah_msg)

    # استاد جی - TELEGRAM WALA - SIRF SETUP BHEJEGA
    main = r1h
    if main['side'] in ['BUY','SELL']:
        bg_alert = f"🚨 {main['side']} SETUP BAN GAYA - PAHUNCHO 🚨\n\n{main['side']} ZONE: {main['entry_bot']} SE {main['entry_top']} TAK HAI\n\nPRICE ABHI: {abhi_s}\nDATE: {date_txt} | TIME: {time_txt}\n\nTP1: {main['tp1']}\nTP2: {main['tp2']}\nTP3: {main['tp3']} - OPEN\nSL: {main['sl_show']} - 6 DOLLAR\n\n{main['trail_txt']}\nCHANCE: {main['chance_txt']}\n\nROUND 2 - PRICE WAPAS ZONE PAR AAYE TO PHIR SE {main['side']} KARNA"
    else:
        bg_alert = ""
    msg_status = f"STATUS - WASEEM TRADER V5.2\nPRICE: {abhi_s}\nATR: {atr_s} | DATE: {date_txt} | {time_txt}\nRSI: {rsi_s} | EMA 15: {ema15_s} | EMA 50: {ema50_s} | VWAP: {vwap_s}"
    msg_buysell = f"BUY / SELL - 12 WALA\nBUY: {buy_c}/12\nSELL: {sell_c}/12"
    msg_4h = f"4H: {r4h['faisla']}\n{r4h['entry']} | {r4h['sl_txt']} | {r4h['tp_txt']}\n{r4h['chance_txt']}"
    msg_1h = f"1H: {r1h['faisla']}\n{r1h['entry']} | {r1h['sl_txt']} | {r1h['tp_txt']}\n{r1h['chance_txt']}"
    msg_15m = f"15M: {r15['faisla']}\n{r15['entry']} | {r15['sl_txt']} | {r15['tp_txt']}\n{r15['chance_txt']}"
    msg_alert = bg_alert
    st.session_state['m1']=msg_status; st.session_state['m2']=msg_buysell; st.session_state['m3']=msg_4h; st.session_state['m4']=msg_1h; st.session_state['m5']=msg_15m; st.session_state['m6']=msg_alert
    if bg_alert != "":
        st.write("---")
        st.write("### 📋 WHATSAPP KE LIYE COPY")
        st.code(bg_alert)
    if AUTO_ON:
        last = st.session_state.get('last_bg_bheja', '')
        abhi_key = f"{bg_alert}-{abhi_s}"
        if bg_alert != "" and last != abhi_key:
            ALAG_ALAG_BHEJO(msg_status, msg_buysell, msg_4h, msg_1h, msg_15m, msg_alert)
            st.session_state['last_bg_bheja'] = abhi_key
            st.success("AUTO - TELEGRAM PE KHUD CHALA GAYA - V5.2 WALA")
        elif bg_alert != "":
            st.write("YE WALA PEHLE HI BHEJ DIYA HAI")
        else:
            st.warning(f"AUTO CHECK HO RAHA HAI - BUY {buy_c}/12 | SELL {sell_c}/12 - ABHI SETUP NAHI BANA")
        time.sleep(AUTO_MINUTE * 60)
        st.rerun()
    else:
        if bg_alert != "":
            st.success("SETUP BAN GAYA - NEECHE WALA BUTTON DABAO - TELEGRAM PE JAYEGA")
else:
    st.info("👆 PEHLE SIGNAL BANAO DABAO - PHIR NEXT DABAO - PAGE 2 / PAGE 3 KHOLEGA")

if 'm1' in st.session_state and not AUTO_ON and st.session_state.get('has_data', False):
    st.write("---")
    if st.button("TELEGRAM PE BHEJO - ALAG ALAG MESSAGE", key="send_v52"):
        ALAG_ALAG_BHEJO(st.session_state['m1'], st.session_state['m2'], st.session_state['m3'], st.session_state['m4'], st.session_state['m5'], st.session_state['m6'])

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from catch_engine import CatchDataEngine
from analysis_engine import GoldAnalysisEngine
from chart_engine import FinancialVisualizer
from strategy_engine import StrategyEngine
from datetime import datetime, timedelta

# 配置頁面
st.set_page_config(
    page_title="黃金市場量化分析系統",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 使用 Streamlit 緩存機制優化性能
@st.cache_data(ttl=3600)  # 數據緩存 1 小時
def get_market_data(main_ticker: str, sec_ticker: str, period: str, interval: str):
    """
    封裝分析邏輯，並在抓取後立即進行跨標的索引對齊。
    """
    engine_main = CatchDataEngine(main_ticker)
    engine_sec = CatchDataEngine(sec_ticker)
    
    df_main = engine_main.fetch_data(period=period, interval=interval)
    df_sec = engine_sec.fetch_data(period=period, interval=interval)
    
    if df_main.empty or df_sec.empty:
        return None, None
        
    # 解決時區衝突：強制移除時區資訊 (tz-naive)，避免 corr() 或 align 報錯
    if df_main.index.tz is not None:
        df_main.index = df_main.index.tz_localize(None)
    if df_sec.index.tz is not None:
        df_sec.index = df_sec.index.tz_localize(None)
        
    # 核心邏輯：移除共同未交易日，確保兩者數據集 1:1 對齊
    aligned_main, aligned_sec = CatchDataEngine.align_datasets(df_main, df_sec)
    
    return aligned_main, aligned_sec


    
def main():
    st.title("📊 黃金市場量化分析系統")
    st.markdown("---")

    # 側邊欄設定
    st.sidebar.header("控制面板")
    # ticker = st.sidebar.text_input("標的代碼", value="GC=F", help="黃金期貨代碼為 GC=F，台股黃金 ETF 可輸入 00635U.TW")
    # ticker = "GC=F"
    # 標的輸入
    user_ticker = st.sidebar.text_input("輸入對比標的代號 (Yahoo格式)", value="00635U.TW").upper()
    main_ticker = st.sidebar.selectbox("分析標的", [user_ticker, "GC=F", "DX-Y.NYB"], index=0)
    sec_ticker = st.sidebar.selectbox("對比標的", ["GC=F", "DX-Y.NYB"], index=0)
    
    period_options = {
        "1天": "1d",
        "3天": "3d",
        "5天": "5d",
        "1個月": "1mo",
        "3個月": "3mo",
        "6個月": "6mo",
        "1年": "1y"
    }
    selected_period_label = st.sidebar.selectbox("回測期間", options=list(period_options.keys()), index=1)
    period = period_options[selected_period_label]
    
    interval = st.sidebar.selectbox("資料頻率", options=["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"], index=1)

    # 滾動相關性窗口設定
    st.sidebar.markdown("---")
    st.sidebar.subheader("宏觀參數")
    corr_window = st.sidebar.slider("相關性滾動視窗 (Periods)", min_value=5, max_value=60, value=20, help="計算資產與美元指數之間相關係數的時間長度")

    # 1. 執行分析
    with st.spinner("正在獲取數據並同步市場交易日..."):
        main_df, sec_df = get_market_data(main_ticker, sec_ticker, period, interval)

    if main_df is None or main_df.empty or sec_df is None or sec_df.empty:
        st.error("無法獲取數據，請檢查代號或期間設定。")
        return

    # 2. 技術指標計算 (利用向量化運算引擎)
    analysis = GoldAnalysisEngine(main_df)
    processed_df = analysis.calculate_indicators()
    sec_analysis = GoldAnalysisEngine(sec_df)
    sec_processed_df = sec_analysis.calculate_indicators()

    # 3. 策略訊號與結論產生
    signals = StrategyEngine.detect_signals(processed_df)
    summary = StrategyEngine.get_signal_summary(processed_df, signals)

    # 4. 顯示策略結論區塊 (位於頂部最顯眼處)
    st.subheader("🎯 策略決策建議")
    s_col1, s_col2, s_col3 = st.columns([2, 1, 1])
    
    with s_col1:
        # 根據建議狀態顯示不同顏色的提醒
        if "買入" in summary["當前建議"]:
            st.success(f"### {summary['當前建議']}")
        elif "賣出" in summary["當前建議"]:
            st.warning(f"### {summary['當前建議']}")
        else:
            st.info(f"### {summary['當前建議']}")
            
    with s_col2:
        st.metric("趨勢狀態", summary["趨勢狀態"])
    with s_col3:
        st.metric("分析日期", summary["日期"])

    # 5. 實例化視覺化工具與主圖表
    viz = FinancialVisualizer()
    st.subheader("核心技術面分析")
    main_fig = viz.create_main_chart(processed_df, sec_processed_df, sec_ticker)
    st.plotly_chart(main_fig, use_container_width=True)
        
    st.markdown("---")

    # 6. 數據指標摘要 (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    correlation = processed_df['Close'].corr(sec_df['Close'])
    
    col1.metric("當前收盤價", f"${processed_df['Close'].iloc[-1]:,.2f}")
    col2.metric("宏觀相關性", f"{correlation:.4f}")
    col3.metric("RSI (14)", f"{processed_df['RSI'].iloc[-1]:.2f}")
    # 額外顯示 MACD 柱狀體數值
    col4.metric("MACD Hist", f"{processed_df['MACD_Hist'].iloc[-1]:.4f}")

    # 7. 跨市場宏觀對比圖
    st.subheader(f"宏觀環境深度對比：{main_ticker} vs {sec_ticker}")
    macro_fig = viz.create_macro_chart(processed_df, sec_df, window=corr_window)
    st.plotly_chart(macro_fig, use_container_width=True)
    
    with st.expander("📝 策略邏輯說明"):
        st.write("""
        本系統採用**趨勢過濾 + 震盪指標**的複合邏輯：
        1. **趨勢過濾**：當價格位於 MA50 (藍線) 之上時才考慮買入。
        2. **買入訊號**：趨勢偏多且符合 (RSI < 30 或 MACD 金叉)。
        3. **賣出訊號**：RSI > 70 或 MACD 死叉。
        """)

if __name__ == "__main__":
    main()
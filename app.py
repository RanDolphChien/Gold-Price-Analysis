import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from catch_engine import CatchDataEngine
from analysis_engine import GoldAnalysisEngine
from chart_engine import FinancialVisualizer
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
def get_data(ticker: str, period: str, interval: str):
    """
    封裝分析邏輯，利用緩存避免重複的網路請求與計算。
    """
    analyzer = CatchDataEngine(ticker)
    df = analyzer.fetch_data(period=period, interval=interval)
    if df.empty:
        return None, None
    
    return df


    
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
    with st.spinner("正在獲取數據並計算技術指標..."):
        main_df = get_data(main_ticker, period, interval)
        sec_df = get_data(sec_ticker, period, interval)

    if main_df is None or main_df.empty or sec_df is None or sec_df.empty:
        st.error("無法獲取數據，請檢查代號或期間設定。")
        return

    # 2. 技術指標計算 (利用向量化運算引擎)
    analysis = GoldAnalysisEngine(main_df)
    processed_df = analysis.calculate_indicators()

    # 3. 實例化視覺化工具
    viz = FinancialVisualizer()
    # 4. 呼叫主技術圖表 (Price, Volume, MACD, RSI)
    st.subheader("核心技術面分析")
    main_fig = viz.create_main_chart(processed_df)
    st.plotly_chart(main_fig, use_container_width=True)
        
    st.markdown("---")

    # 5. 數據指標摘要 (Metrics)
    col1, col2, col3 = st.columns(3)
    correlation = processed_df['Close'].corr(sec_df['Close'])
    
    col1.metric("當前收盤價", f"${processed_df['Close'].iloc[-1]:,.2f}")
    col2.metric("宏觀相關性 (vs DXY)", f"{correlation:.4f}")
    col3.metric("RSI (14)", f"{processed_df['RSI'].iloc[-1]:.2f}")

    # 6. 呼叫跨市場宏觀對比圖 (獨立視窗位於底部)
    st.subheader(f"宏觀環境深度對比：{main_ticker} vs {sec_ticker}")
    macro_fig = viz.create_macro_chart(processed_df, sec_df, window=corr_window)
    st.plotly_chart(macro_fig, use_container_width=True)
    
    with st.expander("📝 滾動相關性分析邏輯"):
        st.write(f"""
        - **滾動窗口 ({corr_window})**：使用皮爾森相關係數計算過去 {corr_window} 個時段的動態關聯。
        - **負相關 (0 到 -1)**：表示標的與美元呈現對沖關係（美元強則金價弱），這是正常宏觀邏輯。
        - **正相關 (0 到 +1)**：當曲線進入正值區間，代表兩者同漲同跌。這通常發生在**極端避險環境**或美元失去信用錨定時，是重要的警示訊號。
        - **零軸突破**：相關性穿越零軸往往代表市場交易邏輯的切換（從貨幣屬性切換至避險屬性）。
        """)

if __name__ == "__main__":
    main()
import pandas as pd
import numpy as np

class StrategyEngine:
    """
    策略邏輯層：負責根據計算出的指標產生買賣訊號。
    優化方向：加入趨勢過濾（Trend Filter）與出場訊號，提升訊號的實戰參考價值。
    """
    
    @staticmethod
    def detect_signals(df: pd.DataFrame):
        """
        進階策略示例：趨勢跟蹤 + 震盪指標複合系統。
        """
        signals = pd.DataFrame(index=df.index)
        
        # --- 1. 趨勢濾網 (Trend Filter) ---
        # 只有當價格在 MA50 之上時，才考慮做多（確保大趨勢向上）
        signals['Trend_Up'] = df['Close'] > df['MA50']
        
        # --- 2. 進場訊號 (Entry Signals) ---
        # RSI 低位超賣 (RSI < 30)
        signals['RSI_Oversold'] = df['RSI'] < 30
        
        # MACD 金叉 (DIF 向上突破 Signal)
        signals['MACD_Gold_Cross'] = (df['MACD_DIF'] > df['MACD_Signal']) & \
                                     (df['MACD_DIF'].shift(1) <= df['MACD_Signal'].shift(1))
        
        # 綜合買入訊號：趨勢向上且（RSI超賣 或 MACD金叉）
        signals['Buy_Signal'] = signals['Trend_Up'] & (signals['RSI_Oversold'] | signals['MACD_Gold_Cross'])
        
        # --- 3. 出場訊號 (Exit Signals) ---
        # RSI 高位超買 (RSI > 70)
        signals['RSI_Overbought'] = df['RSI'] > 70
        
        # MACD 死叉 (DIF 向下跌破 Signal)
        signals['MACD_Death_Cross'] = (df['MACD_DIF'] < df['MACD_Signal']) & \
                                      (df['MACD_DIF'].shift(1) >= df['MACD_Signal'].shift(1))
        
        # 綜合賣出訊號：超買或趨勢反轉
        signals['Sell_Signal'] = signals['RSI_Overbought'] | signals['MACD_Death_Cross']
        
        return signals

    @staticmethod
    def get_signal_summary(df: pd.DataFrame, signals: pd.DataFrame):
        """
        將訊號轉換為易於閱讀的文字摘要。
        """
        last_date = df.index[-1]
        last_price = df['Close'].iloc[-1]
        
        status = "觀望"
        if signals['Buy_Signal'].iloc[-1]:
            status = "🔥 買入訊號觸發"
        elif signals['Sell_Signal'].iloc[-1]:
            status = "❄️ 賣出/避險訊號觸發"
            
        return {
            "日期": last_date.strftime('%Y-%m-%d'),
            "收盤價": f"{last_price:.2f}",
            "當前建議": status,
            "RSI": f"{df['RSI'].iloc[-1]:.2f}",
            "趨勢狀態": "偏多" if signals['Trend_Up'].iloc[-1] else "偏空"
        }
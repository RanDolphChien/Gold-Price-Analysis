import pandas as pd
import numpy as np

class GoldAnalysisEngine:
    """
    資深分析師級別的數據處理引擎。
    專注於時間序列數據的技術指標向量化計算與跨標的關聯分析。
    """
    
    def __init__(self, data: pd.DataFrame):
        # 深度拷貝避免原始數據汙染
        self.df = data.copy()
        # 確保索引為 DatetimeIndex 並移除時區資訊以利對齊
        if self.df.index.tz is not None:
            self.df.index = self.df.index.tz_localize(None)

    def calculate_indicators(self):
        """
        封裝所有技術指標計算邏輯，確保計算鏈的完整性。
        """
        self._calculate_ma()
        self._calculate_bollinger_bands()
        self._calculate_rsi()
        self._calculate_macd()
        return self.df

    def _calculate_ma(self, windows=[20, 50]):
        for window in windows:
            self.df[f'MA{window}'] = self.df['Close'].rolling(window=window).mean()

    def _calculate_bollinger_bands(self, window=20, num_std=2):
        ma = self.df['Close'].rolling(window=window).mean()
        std = self.df['Close'].rolling(window=window).std()
        self.df['Upper_Band'] = ma + (std * num_std)
        self.df['Lower_Band'] = ma - (std * num_std)

    def _calculate_rsi(self, window=14):
        """
        修正版 RSI：採用 Wilder's Smoothing (EMA) 以符合國際標準。
        """
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        
        # 使用 alpha = 1/window 的 EWM 計算，這才是標準的 RSI
        avg_gain = gain.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        self.df['RSI'] = 100 - (100 / (1 + rs))

    def _calculate_macd(self, fast=12, slow=26, signal=9):
        """
        利用 pandas ewm 實現 MACD 的向量化計算，確保與國際標準公式一致。
        DIF = EMA(fast) - EMA(slow)
        DEM (Signal Line) = EMA(DIF, signal)
        OSC (Histogram) = DIF - DEM
        """
        exp1 = self.df['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = self.df['Close'].ewm(span=slow, adjust=False).mean()
        self.df['MACD_DIF'] = exp1 - exp2
        self.df['MACD_Signal'] = self.df['MACD_DIF'].ewm(span=signal, adjust=False).mean()
        self.df['MACD_Hist'] = self.df['MACD_DIF'] - self.df['MACD_Signal']

    @staticmethod
    def normalize_series(df: pd.DataFrame, columns: list):
        """
        將不同規模的序列標準化至基數 100，以便在同一基準下比較報酬率。
        Formula: (Value / Initial Value) * 100
        """
        norm_df = df[columns].copy()
        for col in columns:
            first_val = norm_df[col].dropna().iloc[0]
            norm_df[col] = (norm_df[col] / first_val) * 100
        return norm_df

    @property
    def clean_data(self):
        # 移除因指標計算產生的初始 NaN 值，確保視覺化時圖表平滑
        return self.df.dropna()
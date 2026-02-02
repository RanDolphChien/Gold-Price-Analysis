import pandas as pd
import yfinance as yf

class CatchDataEngine:
    
    def __init__(self, ticker: str = "GC=F"):
        self.ticker = ticker
        self.data: Optional[pd.DataFrame] = None

    def fetch_data(self, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        self.data: Optional[pd.DataFrame] = None
        """
        獲取歷史數據。
        註：在生產環境中，建議實作請求頻率控制（Rate Limiting）以符合財經網站之 robots.txt 規範。
        """
        try:
            df = yf.download(self.ticker, period=period, interval=interval)
            if df.empty:
                raise ValueError(f"無法獲取標的 {self.ticker} 的數據。")
            
            # 確保列名一致性，處理 MultiIndex（若 yfinance 版本較新）
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            self.data = df
            return self.data
        except Exception as e:
            print(f"數據獲取異常: {e}")
            return pd.DataFrame()

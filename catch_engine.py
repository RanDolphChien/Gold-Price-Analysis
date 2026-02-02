import pandas as pd
import yfinance as yf
from typing import Optional, Tuple

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

    @staticmethod
    def align_datasets(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        對齊兩個 DataFrame 的時間索引。
        透過 Inner Join 移除任一標的未交易日的數據，確保向量化運算時長度一致。
        """
        if df1.empty or df2.empty:
            return df1, df2
            
        # 取得交集的索引
        common_index = df1.index.intersection(df2.index)
        
        # 重新取樣並排序索引，確保時間序列連續性
        aligned_df1 = df1.loc[common_index].sort_index()
        aligned_df2 = df2.loc[common_index].sort_index()
        
        return aligned_df1, aligned_df2

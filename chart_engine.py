import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class FinancialVisualizer:
    """
    專業金融數據視覺化模組。
    封裝了四層級圖表的繪製邏輯（Price, Volume, MACD, RSI）。
    色彩配置：上漲=紅色 (#EF5350), 下跌=綠色 (#26A69A)。
    """
    
    def __init__(self, theme='plotly_dark'):
        self.theme = theme
        # 定義配色方案
        self.colors = {
            'main_up': '#EF5350',     # 紅色 (漲)
            'main_down': '#26A69A',   # 綠色 (跌)
            'ma20': '#FFA500',        # 橘色
            'ma50': '#00BFFF',        # 藍色
            'macd_dif': '#FFD700',    # 金黃色
            'macd_signal': '#00CED1', # 青色
            'rsi_line': '#AB47BC',    # 紫色
            'dxy_line': '#F48FB1',    # 粉紅 (DXY 指數)
            'corr_line': '#64B5F6',   # 天藍色 (相關性)
            'volume_bars': 'rgba(128, 128, 128, 0.5)', # 預設色，後續會動態變色
            'bb_fill': 'rgba(128, 128, 128, 0.1)',
            'bb_line': 'rgba(255, 255, 255, 0.2)'
        }

    def create_main_chart(self, df: pd.DataFrame):
        """
        主進入點：建立四層結構金融圖表（Price, Volume, MACD, RSI）。
        """
        fig = make_subplots(
            rows=4, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03, # 縮小間距使圖表更緊湊
            subplot_titles=('Price Action & Volatility', 'Volume', 'Momentum (MACD)', 'Strength (RSI)'),
            row_width=[0.15, 0.15, 0.25, 0.45] # 調整比例，給予主圖最大空間
        )

        # 1. 計算全局動態範圍
        ranges = self._calculate_dynamic_ranges(df)

        # 2. 繪製各層視窗
        self._plot_main_chart(fig, df, row=1)
        self._plot_volume(fig, df, row=2)
        self._plot_macd(fig, df, row=3)
        self._plot_rsi(fig, df, row=4)

        # 3. 更新軸屬性與佈局
        self._apply_layout(fig, ranges)

        return fig

    def create_macro_chart(self, df: pd.DataFrame, dxy_df: pd.DataFrame, window: int = 20):
        """
        建立宏觀對比圖：
        Row 1: 資產 vs 美元指數 (標準化 Base 100)
        Row 2: 滾動相關性 (Rolling Correlation)
        """
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_width=[0.4, 0.6],
            subplot_titles=("Normalized Price Comparison", f"Rolling {window}-Period Correlation"),
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
        )

        # 數據對齊處理：確保計算相關性時索引一致
        combined = pd.concat([df['Close'], dxy_df['Close']], axis=1, join='inner').dropna()
        combined.columns = ['Asset', 'DXY']
        
        # 1. 標準化價格計算
        asset_norm = (combined['Asset'] / combined['Asset'].iloc[0]) * 100
        dxy_norm = (combined['DXY'] / combined['DXY'].iloc[0]) * 100

        # Row 1: 主軸 - 資產價格
        fig.add_trace(
            go.Scatter(x=combined.index, y=asset_norm, name="Asset (Base 100)", 
                       line=dict(color=self.colors['macd_dif'], width=2.5)),
            row=1, col=1, secondary_y=False
        )
        # Row 1: 副軸 - DXY
        fig.add_trace(
            go.Scatter(x=combined.index, y=dxy_norm, name="DXY Index (Base 100)", 
                       line=dict(color=self.colors['dxy_line'], width=2, dash='dot')),
            row=1, col=1, secondary_y=True
        )

        # 2. 滾動相關性計算 (Pearson)
        rolling_corr = combined['Asset'].rolling(window=window).corr(combined['DXY'])

        # Row 2: 相關係數線
        fig.add_trace(
            go.Scatter(x=rolling_corr.index, y=rolling_corr, name="Rolling Correlation",
                       line=dict(color=self.colors['corr_line'], width=2),
                       fill='tozeroy', fillcolor='rgba(100, 181, 246, 0.1)'),
            row=2, col=1
        )

        # 裝飾：在相關性圖中加入 0, 0.5, -0.5 的參考線
        fig.add_hline(y=0, line_dash="solid", line_color="white", line_width=1, row=2, col=1)
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray", line_width=0.5, row=2, col=1)
        fig.add_hline(y=-0.5, line_dash="dash", line_color="gray", line_width=0.5, row=2, col=1)

        fig.update_layout(
            height=700,
            template=self.theme,
            hovermode='x unified',
            plot_bgcolor='black',
            paper_bgcolor='black',
            margin=dict(t=100, b=50),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig.update_yaxes(title_text="Price Ratio", row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="DXY Ratio", row=1, col=1, secondary_y=True)
        fig.update_yaxes(title_text="Correlation", range=[-1.1, 1.1], row=2, col=1)
        
        return fig

    def _calculate_dynamic_ranges(self, df):
        """內部方法：計算各指標的顯示邊界"""
        main_max = max(df['High'].max(), df['Upper_Band'].max())
        main_min = min(df['Low'].min(), df['Lower_Band'].min())
        
        macd_abs_max = max(
            df['MACD_DIF'].abs().max(), 
            df['MACD_Signal'].abs().max(), 
            df['MACD_Hist'].abs().max()
        ) * 1.15

        return {
            'main': [main_min * 0.995, main_max * 1.005],
            'volume': [0, df['Volume'].max() * 1.1], # 成交量從 0 開始
            'macd': [-macd_abs_max, macd_abs_max],
            'rsi': [min(df['RSI'].min(), 25) - 5, max(df['RSI'].max(), 75) + 5]
        }

    def _plot_main_chart(self, fig, df, row):
        # Candlestick (紅漲綠跌)
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Market Price',
            increasing_line_color=self.colors['main_up'],
            increasing_fillcolor=self.colors['main_up'],
            decreasing_line_color=self.colors['main_down'],
            decreasing_fillcolor=self.colors['main_down']
        ), row=row, col=1)
        
        # Bollinger Bands
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Upper_Band'], 
            line=dict(color=self.colors['bb_line'], width=1, dash='dot'), 
            name='Upper Band'
        ), row=row, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Lower_Band'], 
            line=dict(color=self.colors['bb_line'], width=1, dash='dot'), 
            name='Lower Band', fill='tonexty', fillcolor=self.colors['bb_fill']
        ), row=row, col=1)

        # Moving Averages
        for col in [c for c in df.columns if c.startswith('MA')]:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col], 
                line=dict(width=1.5, color=self.colors.get(col.lower())), 
                name=col
            ), row=row, col=1)

    def _plot_volume(self, fig, df, row):
        """繪製成交量，顏色與當日收盤關係掛鉤"""
        # 若收盤 >= 開盤，則量柱為紅；反之為綠
        colors = [
            self.colors['main_up'] if row['Close'] >= row['Open'] 
            else self.colors['main_down'] 
            for _, row in df.iterrows()
        ]
        
        fig.add_trace(go.Bar(
            x=df.index, 
            y=df['Volume'], 
            marker_color=colors, 
            name='Volume',
            opacity=0.8
        ), row=row, col=1)

    def _plot_macd(self, fig, df, row):
        # MACD Histogram 也遵循紅漲綠跌邏輯
        colors = [self.colors['main_up'] if val >= 0 else self.colors['main_down'] for val in df['MACD_Hist']]
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors, name='MACD Hist'), row=row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_DIF'], line=dict(color=self.colors['macd_dif'], width=1.2), name='DIF'), row=row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color=self.colors['macd_signal'], width=1.2), name='Signal'), row=row, col=1)

    def _plot_rsi(self, fig, df, row):
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color=self.colors['rsi_line'], width=2), name='RSI'), row=row, col=1)
        fig.add_hline(y=70, line_dash="dash", row=row, col=1, line_color=self.colors['main_up'])
        fig.add_hline(y=30, line_dash="dash", row=row, col=1, line_color=self.colors['main_down'])

    def _apply_layout(self, fig, ranges):
        fig.update_yaxes(range=ranges['main'], row=1, col=1, title="Price")
        fig.update_yaxes(range=ranges['volume'], row=2, col=1, title="Volume")
        fig.update_yaxes(range=ranges['macd'], row=3, col=1, title="MACD")
        fig.update_yaxes(range=ranges['rsi'], row=4, col=1, title="RSI")
        
        fig.update_layout(
            height=1100, # 增加總高度以容納四層
            xaxis_rangeslider_visible=False,
            template=self.theme,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=60, r=40, t=80, b=50),
            plot_bgcolor='black',
            paper_bgcolor='black'
        )
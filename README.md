# Gold-Price-Analysis
分析黃金期貨價格與其他黃金ETF

1. 建立並啟用虛擬環境
在專案根目錄開啟終端機（Terminal），執行以下指令：

Bash

# 建立虛擬環境
python -m venv .venv

# 啟用環境 (Windows)
.venv\Scripts\activate

# 啟用環境 (macOS/Linux)
source .venv/bin/activate

2. 安裝必要的相依套件
根據你的程式碼內容，此系統依賴於 pandas、numpy、yfinance、plotly 以及 streamlit。請直接在終端機執行：

Bash

pip install pandas numpy yfinance plotly streamlit

# 建立一個 requirements.txt 檔案，方便未來部署。內容如下：

Plaintext

pandas
numpy
yfinance
plotly
streamlit
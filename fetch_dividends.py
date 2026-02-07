"""
S&P 500 Top Dividend Stocks Fetcher
Fetches dividend data from yfinance (free, no API key needed)
Outputs: dividend_data.json
Schedule: GitHub Actions daily at 7 AM KST
"""

import json
import datetime
import os

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    os.system("pip install yfinance")
    import yfinance as yf

# S&P 500 top dividend-paying stocks (curated high-yield universe)
# Full S&P 500 scan takes too long; these are the top ~80 known dividend payers
DIVIDEND_TICKERS = [
    # Energy
    "XOM", "CVX", "COP", "EOG", "PSX", "VLO", "MPC", "OKE", "WMB", "KMI",
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "ED", "WEC",
    # REITs
    "O", "AMT", "PLD", "CCI", "SPG", "PSA", "WELL", "DLR", "VICI", "AVB",
    # Consumer Staples
    "PG", "KO", "PEP", "PM", "MO", "CL", "KMB", "GIS", "K", "SJM",
    # Financials
    "JPM", "BAC", "WFC", "USB", "PNC", "TFC", "CFG", "FITB", "KEY", "RF",
    # Healthcare
    "JNJ", "PFE", "ABBV", "MRK", "BMY", "AMGN", "GILD", "MDT",
    # Industrials
    "MMM", "CAT", "EMR", "ITW", "SWK", "GD", "LMT", "RTX",
    # Telecom
    "VZ", "T", "TMUS",
    # Tech (dividend payers)
    "AAPL", "MSFT", "AVGO", "TXN", "IBM", "CSCO", "INTC", "QCOM",
    # Materials
    "LIN", "APD", "NUE", "DOW",
]

def fetch_dividend_data():
    results = []
    total = len(DIVIDEND_TICKERS)
    
    print(f"Fetching data for {total} tickers...")
    
    for i, ticker in enumerate(DIVIDEND_TICKERS):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            dividend_yield = info.get("dividendYield", 0) or 0
            if dividend_yield == 0:
                continue
                
            dividend_rate = info.get("dividendRate", 0) or 0
            payout_ratio = info.get("payoutRatio", 0) or 0
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0) or 0
            market_cap = info.get("marketCap", 0) or 0
            sector = info.get("sector", "N/A")
            name = info.get("shortName", ticker)
            
            # 52-week price change
            week52_high = info.get("fiftyTwoWeekHigh", 0) or 0
            week52_low = info.get("fiftyTwoWeekLow", 0) or 0
            
            # Calculate approximate 52-week return using price vs 52w low
            # (rough proxy - actual calculation would need historical data)
            year_return = None
            try:
                hist = stock.history(period="1y")
                if len(hist) > 0:
                    start_price = hist["Close"].iloc[0]
                    end_price = hist["Close"].iloc[-1]
                    year_return = round(((end_price - start_price) / start_price) * 100, 2)
            except:
                pass
            
            results.append({
                "ticker": ticker,
                "name": name,
                "price": round(price, 2),
                "dividendYield": round(dividend_yield * 100, 2),  # Convert to %
                "dividendRate": round(dividend_rate, 2),
                "payoutRatio": round(payout_ratio * 100, 1) if payout_ratio else None,
                "marketCap": market_cap,
                "sector": sector,
                "week52High": round(week52_high, 2),
                "week52Low": round(week52_low, 2),
                "yearReturn": year_return,
            })
            
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{total}")
                
        except Exception as e:
            print(f"  Error fetching {ticker}: {e}")
            continue
    
    # Sort by dividend yield (highest first)
    results.sort(key=lambda x: x["dividendYield"], reverse=True)
    
    # Take top 30
    top_results = results[:30]
    
    output = {
        "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(top_results),
        "totalScanned": total,
        "stocks": top_results,
    }
    
    # Save JSON
    with open("dividend_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone! Top {len(top_results)} dividend stocks saved to dividend_data.json")
    print(f"Highest yield: {top_results[0]['ticker']} at {top_results[0]['dividendYield']}%")
    
    return output

if __name__ == "__main__":
    fetch_dividend_data()

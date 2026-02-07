"""
S&P 500 Dividend Dashboard Suite - Data Fetcher
Generates JSON data for 4 dashboards:
1. Scatter Plot (배당+주가 매트릭스)
2. Total Return Rankings (총 수익률 랭킹)
3. $10K Investment Simulator (투자 시뮬레이터)
4. Monthly Dividend Calendar (월배당 캘린더)

Uses yfinance (free, no API key)
Schedule: GitHub Actions daily at 7 AM KST
"""

import json
import datetime
import os
import time

try:
    import yfinance as yf
except ImportError:
    os.system("pip install yfinance")
    import yfinance as yf

DIVIDEND_TICKERS = [
    "XOM", "CVX", "COP", "EOG", "PSX", "VLO", "MPC", "OKE", "WMB", "KMI",
    "NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "ED", "WEC",
    "O", "AMT", "PLD", "CCI", "SPG", "PSA", "WELL", "DLR", "VICI", "AVB",
    "PG", "KO", "PEP", "PM", "MO", "CL", "KMB", "GIS", "K", "SJM",
    "JPM", "BAC", "WFC", "USB", "PNC", "TFC", "CFG", "FITB", "KEY", "RF",
    "JNJ", "PFE", "ABBV", "MRK", "BMY", "AMGN", "GILD", "MDT",
    "MMM", "CAT", "EMR", "ITW", "SWK", "GD", "LMT", "RTX",
    "VZ", "T", "TMUS",
    "AAPL", "MSFT", "AVGO", "TXN", "IBM", "CSCO", "INTC", "QCOM",
    "LIN", "APD", "NUE", "DOW",
]

def fetch_all_data():
    stocks_basic = []
    stocks_history = {}
    total = len(DIVIDEND_TICKERS)
    
    print(f"Fetching data for {total} tickers...")
    
    for i, ticker in enumerate(DIVIDEND_TICKERS):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            dividend_yield = info.get("dividendYield", 0) or 0
            dividend_rate = info.get("dividendRate", 0) or 0
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0) or 0
            
            # yfinance dividendYield is unreliable — calculate from rate/price
            if dividend_rate > 0 and price > 0:
                dividend_yield = dividend_rate / price  # decimal form (e.g. 0.0648)
            elif dividend_yield > 0.20:
                # Fallback: if yield looks like percentage, convert to decimal
                dividend_yield = dividend_yield / 100
            
            if dividend_yield <= 0:
                continue
            
            payout_ratio = info.get("payoutRatio", 0) or 0
            market_cap = info.get("marketCap", 0) or 0
            sector = info.get("sector", "N/A")
            name = info.get("shortName", ticker)
            
            # 1-year history
            hist_1y = stock.history(period="1y")
            year_return = None
            if len(hist_1y) > 1:
                start_p = hist_1y["Close"].iloc[0]
                end_p = hist_1y["Close"].iloc[-1]
                year_return = round(((end_p - start_p) / start_p) * 100, 2)
            
            # 5-year monthly prices for simulator
            hist_5y = stock.history(period="5y")
            monthly_prices = []
            if len(hist_5y) > 0:
                monthly = hist_5y["Close"].resample("ME").last().dropna()
                for date, close in monthly.items():
                    monthly_prices.append({
                        "date": date.strftime("%Y-%m"),
                        "price": round(float(close), 2)
                    })
            
            # Dividend history
            divs = stock.dividends
            div_history = []
            div_months = set()
            annual_divs = {}
            
            if len(divs) > 0:
                for date, amount in divs.items():
                    d = date.tz_localize(None) if date.tzinfo else date
                    div_history.append({
                        "date": d.strftime("%Y-%m-%d"),
                        "amount": round(float(amount), 4)
                    })
                    div_months.add(d.month)
                    year = d.year
                    annual_divs[year] = annual_divs.get(year, 0) + float(amount)
            
            # Consecutive dividend increases
            sorted_years = sorted(annual_divs.keys())
            consec_increases = 0
            if len(sorted_years) >= 2:
                for j in range(len(sorted_years) - 1, 0, -1):
                    if annual_divs[sorted_years[j]] > annual_divs[sorted_years[j-1]]:
                        consec_increases += 1
                    else:
                        break
            
            # Total returns (1y, 3y, 5y)
            total_returns = {}
            for period_name, period_str in [("1y", "1y"), ("3y", "3y"), ("5y", "5y")]:
                try:
                    h = stock.history(period=period_str)
                    if len(h) > 1:
                        start = float(h["Close"].iloc[0])
                        end = float(h["Close"].iloc[-1])
                        price_return = ((end - start) / start) * 100
                        period_divs = divs[h.index[0]:h.index[-1]]
                        div_sum = float(period_divs.sum()) if len(period_divs) > 0 else 0
                        div_return = (div_sum / start) * 100
                        total_returns[period_name] = {
                            "priceReturn": round(price_return, 2),
                            "divReturn": round(div_return, 2),
                            "totalReturn": round(price_return + div_return, 2)
                        }
                except:
                    pass
            
            stocks_basic.append({
                "ticker": ticker, "name": name, "price": round(price, 2),
                "dividendYield": round(dividend_yield * 100, 2),
                "dividendRate": round(dividend_rate, 2),
                "payoutRatio": round(payout_ratio * 100, 1) if payout_ratio else None,
                "marketCap": market_cap, "sector": sector,
                "yearReturn": year_return,
                "divMonths": sorted(list(div_months)),
                "consecIncreases": consec_increases,
                "totalReturns": total_returns,
            })
            
            stocks_history[ticker] = {
                "monthlyPrices": monthly_prices,
                "dividends": div_history[-60:],
            }
            
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{total}")
            time.sleep(0.2)
                
        except Exception as e:
            print(f"  Error {ticker}: {e}")
            continue
    
    stocks_basic.sort(key=lambda x: x["dividendYield"], reverse=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Main dividend data
    with open("dividend_data.json", "w", encoding="utf-8") as f:
        json.dump({"updated": now, "count": min(30, len(stocks_basic)), "stocks": stocks_basic[:30]}, f, ensure_ascii=False, indent=2)
    
    # Scatter plot data
    scatter = [s for s in stocks_basic if s["yearReturn"] is not None]
    with open("scatter_data.json", "w", encoding="utf-8") as f:
        json.dump({"updated": now, "stocks": scatter}, f, ensure_ascii=False, indent=2)
    
    # Total return data
    ret_stocks = sorted([s for s in stocks_basic if s.get("totalReturns")],
                        key=lambda x: x["totalReturns"].get("1y", {}).get("totalReturn", -999), reverse=True)
    with open("total_return_data.json", "w", encoding="utf-8") as f:
        json.dump({"updated": now, "stocks": ret_stocks}, f, ensure_ascii=False, indent=2)
    
    # Simulator data
    with open("simulator_data.json", "w", encoding="utf-8") as f:
        json.dump({"updated": now, "histories": stocks_history,
                    "tickers": [s["ticker"] for s in stocks_basic],
                    "names": {s["ticker"]: s["name"] for s in stocks_basic}}, f, ensure_ascii=False, indent=2)
    
    # Calendar data
    cal = [s for s in stocks_basic if len(s["divMonths"]) > 0]
    with open("calendar_data.json", "w", encoding="utf-8") as f:
        json.dump({"updated": now, "stocks": cal}, f, ensure_ascii=False, indent=2)
    
    print(f"\n Done! {len(stocks_basic)} stocks processed, 5 JSON files generated.")

if __name__ == "__main__":
    fetch_all_data()

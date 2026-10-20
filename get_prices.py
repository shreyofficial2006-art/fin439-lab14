"""get_prices.py - build prices.csv for my Project 2 universe (Lab 14, before Thursday).

Five years of MONTHLY Adj Close prices from Yahoo Finance, oldest month first,
date column first, one column per ticker. Also writes prices_source.txt with
the source and download date.

Setup once:   pip install yfinance
Run:          python get_prices.py
"""

import csv
import datetime as dt

import yfinance as yf

TICKERS = ["BIL", "IEF", "LQD", "TIP", "VT"]
PERIOD = "5y"
OUT_FILE = "prices.csv"


def download_adj_close(tickers, period):
    data = yf.download(tickers, period=period, interval="1mo",
                       auto_adjust=False, progress=False)
    adj = data["Adj Close"][tickers].dropna(how="any")
    return adj.sort_index()  # oldest month first


def write_csv(adj, path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date"] + list(adj.columns))
        for date, row in adj.iterrows():
            writer.writerow([date.strftime("%Y-%m-%d")] + [f"{x:.4f}" for x in row])


def main():
    adj = download_adj_close(TICKERS, PERIOD)
    write_csv(adj, OUT_FILE)
    today = dt.date.today().isoformat()
    with open("prices_source.txt", "w") as f:
        f.write(f"Source: Yahoo Finance via yfinance, monthly Adj Close, period {PERIOD}\n")
        f.write(f"Tickers: {', '.join(TICKERS)}\n")
        f.write(f"Download date: {today}\n")
        f.write(f"Rows: {len(adj)} months, {adj.index[0]:%Y-%m} to {adj.index[-1]:%Y-%m}\n")
    print(f"Wrote {OUT_FILE}: {len(adj)} months x {len(TICKERS)} tickers "
          f"({adj.index[0]:%Y-%m} to {adj.index[-1]:%Y-%m}); download date {today}")


if __name__ == "__main__":
    main()

import pandas as pd
import yfinance as yf


class DataFetcher:
    """Fetches live market data for stocks, crypto, and FX rates."""

    def __init__(self):
        self._fx_cache = {}

    def get_prices(self, tickers: list[str]) -> dict:
        """Fetch current price and currency for a batch of tickers."""
        results = {}
        if not tickers:
            return results

        data = yf.Tickers(" ".join(tickers))
        for ticker in tickers:
            try:
                info = data.tickers[ticker].fast_info
                price = info.get("lastPrice", 0.0) or info.get("previousClose", 0.0)
                currency = info.get("currency", "USD")

                if currency == "GBp":
                    price /= 100.0
                    currency = "GBP"

                results[ticker] = {
                    "price": price,
                    "currency": currency,
                    "change_pct": info.get("lastPrice", 0) / info.get("previousClose", 1) * 100 - 100
                    if info.get("previousClose")
                    else 0.0,
                }
            except Exception:
                results[ticker] = {"price": 0.0, "currency": "USD", "change_pct": 0.0}

        return results

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """Fetch historical OHLCV data for a ticker.

        Args:
            ticker: Stock/ETF/commodity symbol.
            period: yfinance period string (default "1y").
            interval: Data interval (default "1d").

        Returns:
            DataFrame with Open, High, Low, Close, Volume columns.
            Empty DataFrame on error.
        """
        try:
            t = yf.Ticker(ticker)
            df = t.history(period=period, interval=interval)
            if df.empty:
                return df

            # LSE ETFs quote in GBp (pence) — convert OHLC to GBP
            currency = t.fast_info.get("currency", "")
            if currency == "GBp":
                for col in ["Open", "High", "Low", "Close"]:
                    if col in df.columns:
                        df[col] = df[col] / 100.0

            return df
        except Exception:
            return pd.DataFrame()

    def get_fx_rate(self, from_currency: str, to_currency: str) -> float:
        """Return the exchange rate between two currencies."""
        if from_currency == to_currency:
            return 1.0

        key = f"{from_currency}{to_currency}"
        if key in self._fx_cache:
            return self._fx_cache[key]

        try:
            pair = f"{from_currency}{to_currency}=X"
            t = yf.Ticker(pair)
            rate = t.fast_info.get("lastPrice", 0.0)
            if rate:
                self._fx_cache[key] = rate
                return rate
        except Exception:
            pass

        return 0.0

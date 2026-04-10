class DataFetcher:
    """Fetches live market data for stocks, crypto, and FX rates."""

    def get_stock_price(self, ticker: str) -> dict:
        """Return the current price and metadata for a stock ticker.

        Args:
            ticker: Stock symbol (e.g. "AAPL", "TSLA", "VUSA.L").

        Returns:
            dict with keys: price, currency, name, change_pct.
        """
        # TODO: integrate yfinance
        return {
            "price": 0.0,
            "currency": "USD",
            "name": ticker,
            "change_pct": 0.0,
        }

    def get_crypto_price(self, symbol: str) -> dict:
        """Return the current price for a cryptocurrency.

        Args:
            symbol: Crypto symbol (e.g. "BTC", "ETH").

        Returns:
            dict with keys: price, currency, change_pct.
        """
        # TODO: integrate crypto API
        return {
            "price": 0.0,
            "currency": "USD",
            "change_pct": 0.0,
        }

    def get_fx_rate(self, from_currency: str, to_currency: str) -> float:
        """Return the exchange rate between two currencies.

        Args:
            from_currency: Source currency code (e.g. "USD").
            to_currency: Target currency code (e.g. "GBP").

        Returns:
            Exchange rate as a float.
        """
        # TODO: integrate FX API
        if from_currency == to_currency:
            return 1.0
        return 0.0

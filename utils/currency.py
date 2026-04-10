from data.fetcher import DataFetcher

_fetcher = DataFetcher()


def convert_to_gbp(amount: float, from_currency: str) -> float:
    """Convert an amount from the given currency to GBP.

    Args:
        amount: The monetary amount to convert.
        from_currency: ISO currency code (e.g. "USD", "EUR").

    Returns:
        The equivalent amount in GBP.
    """
    if from_currency == "GBP":
        return amount
    rate = _fetcher.get_fx_rate(from_currency, "GBP")
    return amount * rate

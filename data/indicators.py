"""Technical indicator calculations for the signal engine."""

import pandas as pd
import pandas_ta as ta


class TechnicalIndicators:
    """Computes technical indicators on OHLCV data and generates trade signals."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._calculate()

    def _calculate(self):
        close = self.df["Close"]

        # Moving averages
        self.df["SMA_20"] = ta.sma(close, length=20)
        self.df["SMA_50"] = ta.sma(close, length=50)
        self.df["SMA_200"] = ta.sma(close, length=200)

        # RSI
        self.df["RSI"] = ta.rsi(close, length=14)

        # MACD — returns DataFrame with MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        macd = ta.macd(close, fast=12, slow=26, signal=9)
        if macd is not None:
            self.df = pd.concat([self.df, macd], axis=1)

    def get_signal(self) -> str:
        """Return 'BUY', 'SELL', or 'HOLD' based on RSI + MACD crossover."""
        if len(self.df) < 2:
            return "HOLD"

        try:
            curr = self.df.iloc[-1]
            prev = self.df.iloc[-2]

            rsi = curr.get("RSI", 50)
            macd_line = curr.get("MACD_12_26_9", 0)
            macd_signal = curr.get("MACDs_12_26_9", 0)
            prev_macd_line = prev.get("MACD_12_26_9", 0)
            prev_macd_signal = prev.get("MACDs_12_26_9", 0)

            if pd.isna(rsi) or pd.isna(macd_line):
                return "HOLD"

            # MACD crossover detection (within last bar)
            macd_cross_up = macd_line > macd_signal and prev_macd_line <= prev_macd_signal
            macd_cross_down = macd_line < macd_signal and prev_macd_line >= prev_macd_signal

            # BUY: RSI oversold + bullish MACD crossover
            if rsi < 35 and macd_cross_up:
                return "BUY"
            if rsi < 30:
                return "BUY"

            # SELL: RSI overbought + bearish MACD crossover
            if rsi > 65 and macd_cross_down:
                return "SELL"
            if rsi > 70:
                return "SELL"

            return "HOLD"
        except Exception:
            return "HOLD"

    def get_latest_values(self) -> dict:
        """Return the most recent indicator values for display."""
        if self.df.empty:
            return {}

        last = self.df.iloc[-1]
        result = {}
        for key in ["RSI", "MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9", "SMA_20", "SMA_50", "SMA_200"]:
            val = last.get(key, None)
            if val is not None and not pd.isna(val):
                result[key] = round(float(val), 2)
        return result

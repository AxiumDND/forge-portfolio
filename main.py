import sys
import json
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSplitter,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ui.holdings_table import HoldingsTable
from ui.chart_panel import ChartPanel
from data.fetcher import DataFetcher
from data.indicators import TechnicalIndicators


def exception_hook(exctype, value, tb):
    traceback.print_exception(exctype, value, tb)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = exception_hook


class PriceFetchWorker(QThread):
    """Background thread that fetches live prices."""
    finished = pyqtSignal(dict, dict)

    def __init__(self, tickers, currencies):
        super().__init__()
        self.tickers = tickers
        self.currencies = currencies

    def run(self):
        fetcher = DataFetcher()
        prices = fetcher.get_prices(self.tickers)
        fx_rates = {"GBP": 1.0}
        for cur in self.currencies:
            if cur not in fx_rates:
                fx_rates[cur] = fetcher.get_fx_rate(cur, "GBP")
        self.finished.emit(prices, fx_rates)


class HistoryFetchWorker(QThread):
    """Background thread that fetches history + computes indicators for one ticker."""
    finished = pyqtSignal(str, object, object)  # ticker, df, TechnicalIndicators

    def __init__(self, ticker):
        super().__init__()
        self.ticker = ticker

    def run(self):
        fetcher = DataFetcher()
        df = fetcher.get_history(self.ticker)
        indicators = None
        if not df.empty:
            indicators = TechnicalIndicators(df)
        self.finished.emit(self.ticker, df, indicators)


class SignalBatchWorker(QThread):
    """Background thread that computes signals for all tickers."""
    finished = pyqtSignal(dict)  # {ticker: signal_string}

    def __init__(self, tickers):
        super().__init__()
        self.tickers = tickers

    def run(self):
        fetcher = DataFetcher()
        signals = {}
        for ticker in self.tickers:
            try:
                df = fetcher.get_history(ticker)
                if not df.empty:
                    ind = TechnicalIndicators(df)
                    signals[ticker] = ind.get_signal()
                else:
                    signals[ticker] = "--"
            except Exception:
                signals[ticker] = "--"
        self.finished.emit(signals)


class ForgePortfolioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forge Portfolio Tracker")
        self.setMinimumSize(1100, 750)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # Header
        header = QLabel("Forge Portfolio Tracker")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #cba6f7;")
        main_layout.addWidget(header)

        # Summary bar
        self.summary_label = QLabel("Loading portfolio...")
        self.summary_label.setStyleSheet("font-size: 14px; color: #a6adc8;")
        main_layout.addWidget(self.summary_label)

        # Splitter: table (top) + chart (bottom)
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle { background-color: #313244; height: 3px; }
        """)

        self.table = HoldingsTable()
        splitter.addWidget(self.table)

        self.chart_panel = ChartPanel()
        splitter.addWidget(self.chart_panel)

        splitter.setSizes([350, 350])
        main_layout.addWidget(splitter, stretch=1)

        self.setStyleSheet("background-color: #1e1e2e;")

        # State
        self.accounts = {}
        self._current_chart_ticker = None
        self.history_worker = None
        self.signal_worker = None

        # Connect table click to chart
        self.table.cellClicked.connect(self._on_holding_clicked)

        self._load_portfolio()

    def _load_portfolio(self):
        try:
            with open("portfolio.json", "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.summary_label.setText(f"Error loading portfolio: {e}")
            return

        self.accounts = data.get("accounts", {})
        total_holdings = sum(len(h) for h in self.accounts.values())
        self.summary_label.setText(
            f"{total_holdings} holdings across {len(self.accounts)} accounts  |  "
            f"Fetching live prices..."
        )
        self.table.load_holdings(self.accounts)
        self._fetch_prices()

    def _fetch_prices(self):
        tickers = set()
        for holdings in self.accounts.values():
            for h in holdings:
                tickers.add(h["ticker"])

        self.price_worker = PriceFetchWorker(list(tickers), ["USD", "CAD"])
        self.price_worker.finished.connect(self._on_prices_loaded)
        self.price_worker.start()

    def _on_prices_loaded(self, prices, fx_rates):
        self.table.update_prices(self.accounts, prices, fx_rates)

        # Calculate total portfolio value
        total_gbp = 0.0
        for holdings in self.accounts.values():
            for h in holdings:
                ticker = h["ticker"]
                p = prices.get(ticker, {})
                price = p.get("price", 0)
                currency = p.get("currency", "USD")
                rate = fx_rates.get(currency, 0)
                total_gbp += h["quantity"] * price * rate

        self.summary_label.setText(
            f"{sum(len(h) for h in self.accounts.values())} holdings across "
            f"{len(self.accounts)} accounts  |  "
            f"Total: \u00a3{total_gbp:,.2f} GBP  |  Computing signals..."
        )

        # Now compute signals for all tickers in background
        tickers = list({h["ticker"] for hl in self.accounts.values() for h in hl})
        self.signal_worker = SignalBatchWorker(tickers)
        self.signal_worker.finished.connect(self._on_signals_loaded)
        self.signal_worker.start()

    def _on_signals_loaded(self, signals):
        self.table.update_signals(signals)
        # Update summary to remove "Computing signals..."
        current = self.summary_label.text()
        self.summary_label.setText(current.replace("  |  Computing signals...", ""))

    def _on_holding_clicked(self, row, col):
        ticker_item = self.table.item(row, 1)
        if not ticker_item:
            return
        ticker = ticker_item.text()
        if ticker == self._current_chart_ticker:
            return

        self._current_chart_ticker = ticker
        self.chart_panel.ticker_label.setText(f"{ticker} — Loading chart...")
        self.chart_panel.signal_badge.hide()
        self.chart_panel.info_label.setText("")

        self.history_worker = HistoryFetchWorker(ticker)
        self.history_worker.finished.connect(self._on_history_loaded)
        self.history_worker.start()

    def _on_history_loaded(self, ticker, df, indicators):
        if ticker != self._current_chart_ticker:
            return  # User clicked a different ticker while loading
        if df.empty:
            self.chart_panel.ticker_label.setText(f"{ticker} — No data available")
            return
        self.chart_panel.update_chart(ticker, df, indicators)


def main():
    app = QApplication(sys.argv)
    window = ForgePortfolioWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

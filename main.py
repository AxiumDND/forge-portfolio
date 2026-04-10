import sys
import json
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSplitter,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from ui.holdings_table import HoldingsTable
from ui.chart_panel import ChartPanel
from ui.fear_greed_widget import FearGreedWidget
from data.fetcher import DataFetcher
from data.indicators import TechnicalIndicators
from data.fear_greed import fetch_fear_greed


def exception_hook(exctype, value, tb):
    traceback.print_exception(exctype, value, tb)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = exception_hook


# ---------------------------------------------------------------------------
# Worker threads
# ---------------------------------------------------------------------------

class PriceFetchWorker(QThread):
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
    finished = pyqtSignal(str, object, object)

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
    finished = pyqtSignal(dict)

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


class FearGreedWorker(QThread):
    finished = pyqtSignal(object, str)  # score (float or None), rating

    def run(self):
        result = fetch_fear_greed()
        self.finished.emit(result["score"], result["rating"])


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

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

        # Header row: title (left) + Fear & Greed gauge (right)
        header_row = QHBoxLayout()
        header_label = QLabel("Forge Portfolio Tracker")
        header_label.setStyleSheet("font-size: 34px; font-weight: bold; color: #cba6f7;")
        header_row.addWidget(header_label)
        header_row.addStretch()

        self.fear_greed_widget = FearGreedWidget()
        header_row.addWidget(self.fear_greed_widget)
        main_layout.addLayout(header_row)

        # Summary bar
        self.summary_label = QLabel("Loading portfolio...")
        self.summary_label.setStyleSheet("font-size: 18px; color: #a6adc8;")
        main_layout.addWidget(self.summary_label)

        # Splitter: table (top) + chart (bottom)
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: #313244; height: 3px; }")

        self.table = HoldingsTable()
        splitter.addWidget(self.table)

        self.chart_panel = ChartPanel()
        splitter.addWidget(self.chart_panel)

        splitter.setSizes([350, 350])
        main_layout.addWidget(splitter, stretch=1)

        self.setStyleSheet("background-color: #1e1e2e;")

        # Status bar
        self.statusBar().setStyleSheet(
            "color: #a6adc8; background-color: #181825; font-size: 15px; padding: 4px 8px;"
        )
        self._status_label = QLabel("Starting up...")
        self.statusBar().addPermanentWidget(self._status_label)

        # State
        self.accounts = {}
        self._current_chart_ticker = None
        self._last_refresh_time = None
        self._refresh_interval = 300
        self.price_worker = None
        self.history_worker = None
        self.signal_worker = None
        self.fg_worker = None

        # Connect table click to chart
        self.table.cellClicked.connect(self._on_holding_clicked)

        # Load config
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            self._refresh_interval = config.get("refresh_interval", 300)
        except Exception:
            pass

        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.start(self._refresh_interval * 1000)

        # Countdown timer (updates status bar every second)
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._update_status_bar)
        self._countdown_timer.start(1000)

        self._load_portfolio()

    # --- Data loading ---

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
        self._fetch_fear_greed()

    def _fetch_prices(self):
        if self.price_worker and self.price_worker.isRunning():
            return
        tickers = list({h["ticker"] for hl in self.accounts.values() for h in hl})
        self.price_worker = PriceFetchWorker(tickers, ["USD", "CAD"])
        self.price_worker.finished.connect(self._on_prices_loaded)
        self.price_worker.start()

    def _fetch_fear_greed(self):
        if self.fg_worker and self.fg_worker.isRunning():
            return
        self.fg_worker = FearGreedWorker()
        self.fg_worker.finished.connect(self._on_fear_greed_loaded)
        self.fg_worker.start()

    def _auto_refresh(self):
        self._fetch_prices()
        self._fetch_fear_greed()

    # --- Callbacks ---

    def _on_prices_loaded(self, prices, fx_rates):
        self.table.update_prices(self.accounts, prices, fx_rates)
        self._last_refresh_time = datetime.now()

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
            f"Total: \u00a3{total_gbp:,.2f} GBP"
        )

        # Compute signals in background
        tickers = list({h["ticker"] for hl in self.accounts.values() for h in hl})
        self.signal_worker = SignalBatchWorker(tickers)
        self.signal_worker.finished.connect(self._on_signals_loaded)
        self.signal_worker.start()

    def _on_signals_loaded(self, signals):
        self.table.update_signals(signals)

    def _on_fear_greed_loaded(self, score, rating):
        self.fear_greed_widget.set_data(score, rating)

    def _on_holding_clicked(self, row, col):
        ticker_item = self.table.item(row, 1)
        if not ticker_item:
            return
        ticker = ticker_item.text()
        if ticker == self._current_chart_ticker:
            return

        self._current_chart_ticker = ticker
        self.chart_panel.ticker_label.setText(f"{ticker} \u2014 Loading chart...")
        self.chart_panel.signal_badge.hide()
        self.chart_panel.info_label.setText("")

        self.history_worker = HistoryFetchWorker(ticker)
        self.history_worker.finished.connect(self._on_history_loaded)
        self.history_worker.start()

    def _on_history_loaded(self, ticker, df, indicators):
        if ticker != self._current_chart_ticker:
            return
        if df.empty:
            self.chart_panel.ticker_label.setText(f"{ticker} \u2014 No data available")
            return
        self.chart_panel.update_chart(ticker, df, indicators)

    # --- Status bar ---

    def _update_status_bar(self):
        parts = []
        if self._last_refresh_time:
            parts.append(f"Last refreshed: {self._last_refresh_time.strftime('%H:%M:%S')}")
            elapsed = (datetime.now() - self._last_refresh_time).total_seconds()
            remaining = max(0, self._refresh_interval - int(elapsed))
            mins, secs = divmod(remaining, 60)
            parts.append(f"Next refresh in {mins}:{secs:02d}")
        else:
            parts.append("Fetching data...")

        total = sum(len(h) for h in self.accounts.values())
        parts.append(f"{total} holdings")
        self._status_label.setText("   |   ".join(parts))


def main():
    app = QApplication(sys.argv)
    window = ForgePortfolioWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

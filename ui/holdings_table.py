from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


COLUMNS = [
    "Account",
    "Ticker",
    "Name",
    "Type",
    "Qty",
    "Price",
    "Currency",
    "Value (GBP)",
    "Day %",
    "Signal",
]

SIGNAL_COLOURS = {
    "BUY": "#a6e3a1",
    "SELL": "#f38ba8",
    "HOLD": "#f9e2af",
}


class NumericTableItem(QTableWidgetItem):
    """Table item that sorts numerically when a sort value is stored."""

    def __lt__(self, other):
        self_val = self.data(Qt.UserRole)
        other_val = other.data(Qt.UserRole)
        if self_val is not None and other_val is not None:
            try:
                return float(self_val) < float(other_val)
            except (ValueError, TypeError):
                pass
        return super().__lt__(other)


class HoldingsTable(QTableWidget):
    """Table widget that displays portfolio holdings with live data."""

    def __init__(self, parent=None):
        super().__init__(0, len(COLUMNS), parent)
        self.setHorizontalHeaderLabels(COLUMNS)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)

        self.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                gridline-color: #313244;
                border: none;
                font-size: 17px;
            }
            QTableWidget::item { padding: 10px; }
            QTableWidget::item:selected { background-color: #45475a; }
            QHeaderView::section {
                background-color: #181825;
                color: #a6adc8;
                border: 1px solid #313244;
                padding: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QTableWidget::item:alternate { background-color: #181825; }
        """)

    def load_holdings(self, accounts: dict) -> None:
        """Populate the table from the accounts dict (before prices arrive)."""
        self.setSortingEnabled(False)

        rows = []
        for account, holdings in accounts.items():
            for h in holdings:
                rows.append((account, h))

        self.setRowCount(len(rows))
        for row, (account, h) in enumerate(rows):
            qty = h.get("quantity", 0)
            self._set_cell(row, 0, account)
            self._set_cell(row, 1, h.get("ticker", ""))
            self._set_cell(row, 2, h.get("name", ""))
            self._set_cell(row, 3, h.get("type", "").upper())
            self._set_cell(row, 4, self._fmt_qty(qty), align_right=True, sort_value=qty)
            self._set_cell(row, 5, "...", align_right=True, sort_value=0)
            self._set_cell(row, 6, "")
            self._set_cell(row, 7, "...", align_right=True, sort_value=0)
            self._set_cell(row, 8, "...", align_right=True, sort_value=0)
            self._set_cell(row, 9, "...")

        self.setSortingEnabled(True)

    def update_prices(self, accounts: dict, prices: dict, fx_rates: dict) -> None:
        """Update table cells with live price data."""
        self.setSortingEnabled(False)

        # Build a lookup from ticker+account to find the correct row
        # (table may have been re-sorted by user)
        for row in range(self.rowCount()):
            ticker_item = self.item(row, 1)
            if not ticker_item:
                continue
            ticker = ticker_item.text()
            account = self.item(row, 0).text() if self.item(row, 0) else ""

            # Find matching holding
            qty = 0
            for acc_name, holdings in accounts.items():
                if acc_name == account:
                    for h in holdings:
                        if h["ticker"] == ticker:
                            qty = h.get("quantity", 0)
                            break

            p = prices.get(ticker, {})
            price = p.get("price", 0)
            currency = p.get("currency", "USD")
            change = p.get("change_pct", 0)
            rate = fx_rates.get(currency, 0)
            value_gbp = qty * price * rate

            self._set_cell(row, 5, f"{price:,.4f}" if price else "--", align_right=True, sort_value=price)
            self._set_cell(row, 6, currency)
            self._set_cell(row, 7, f"\u00a3{value_gbp:,.2f}", align_right=True, sort_value=value_gbp)

            change_text = f"{change:+.2f}%"
            if change > 0:
                self._set_cell(row, 8, change_text, align_right=True, color="#a6e3a1", sort_value=change)
            elif change < 0:
                self._set_cell(row, 8, change_text, align_right=True, color="#f38ba8", sort_value=change)
            else:
                self._set_cell(row, 8, change_text, align_right=True, sort_value=change)

        self.setSortingEnabled(True)

    def update_signals(self, signals: dict) -> None:
        """Update the Signal column with BUY/HOLD/SELL for each ticker."""
        for row in range(self.rowCount()):
            ticker_item = self.item(row, 1)
            if not ticker_item:
                continue
            ticker = ticker_item.text()
            signal = signals.get(ticker, "...")
            colour = SIGNAL_COLOURS.get(signal, "#a6adc8")
            self._set_cell(row, 9, signal, color=colour)

    def _fmt_qty(self, qty):
        if qty < 1:
            return f"{qty:,.6f}"
        if qty < 100:
            return f"{qty:,.4f}"
        return f"{qty:,.2f}"

    def _set_cell(self, row, col, text, align_right=False, color=None, sort_value=None):
        if sort_value is not None:
            item = NumericTableItem(str(text))
            item.setData(Qt.UserRole, sort_value)
        else:
            item = QTableWidgetItem(str(text))
        if align_right:
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if color:
            item.setForeground(QColor(color))
        self.setItem(row, col, item)

"""Embedded candlestick chart panel using mplfinance + matplotlib Qt5 backend."""

import mplfinance as mpf
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt


# Catppuccin-themed mplfinance style
CATPPUCCIN_STYLE = mpf.make_mpf_style(
    base_mpf_style="nightclouds",
    marketcolors=mpf.make_marketcolors(
        up="#a6e3a1", down="#f38ba8",
        edge="inherit", wick="inherit",
        volume={"up": "#a6e3a1", "down": "#f38ba8"},
    ),
    facecolor="#1e1e2e",
    edgecolor="#313244",
    figcolor="#1e1e2e",
    gridcolor="#313244",
    gridstyle="--",
    rc={
        "font.size": 9,
        "axes.labelcolor": "#cdd6f4",
        "xtick.color": "#a6adc8",
        "ytick.color": "#a6adc8",
    },
)

SIGNAL_COLOURS = {
    "BUY": ("#a6e3a1", "#1e1e2e"),
    "SELL": ("#f38ba8", "#1e1e2e"),
    "HOLD": ("#f9e2af", "#1e1e2e"),
}

SMA_COLOURS = {
    "SMA_20": "#89b4fa",
    "SMA_50": "#f9e2af",
    "SMA_200": "#cba6f7",
}


class ChartPanel(QWidget):
    """Candlestick chart panel embedded in the main window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(4)

        # Header row: ticker name + signal badge
        header_row = QHBoxLayout()
        self.ticker_label = QLabel("Click a holding to view chart")
        self.ticker_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #cdd6f4;")
        header_row.addWidget(self.ticker_label)

        self.signal_badge = QLabel("")
        self.signal_badge.setFixedHeight(24)
        self.signal_badge.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px 14px; border-radius: 4px;")
        self.signal_badge.hide()
        header_row.addWidget(self.signal_badge)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Matplotlib canvas
        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.figure.set_facecolor("#1e1e2e")
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas, stretch=1)

        # Info bar: RSI, MACD values
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-size: 15px; color: #a6adc8; padding: 4px 0;")
        layout.addWidget(self.info_label)

    def update_chart(self, ticker, df, indicators):
        """Render candlestick chart with SMA overlays for the given ticker."""
        self.ticker_label.setText(f"{ticker}")

        # Signal badge
        signal = indicators.get_signal() if indicators else "HOLD"
        fg, bg = SIGNAL_COLOURS.get(signal, ("#cdd6f4", "#1e1e2e"))
        self.signal_badge.setText(f"  {signal}  ")
        self.signal_badge.setStyleSheet(
            f"font-size: 16px; font-weight: bold; padding: 4px 14px; "
            f"border-radius: 4px; background-color: {fg}; color: {bg};"
        )
        self.signal_badge.show()

        # Info bar
        if indicators:
            vals = indicators.get_latest_values()
            parts = []
            if "RSI" in vals:
                parts.append(f"RSI: {vals['RSI']}")
            if "MACD_12_26_9" in vals:
                parts.append(f"MACD: {vals['MACD_12_26_9']}")
            if "MACDs_12_26_9" in vals:
                parts.append(f"Signal: {vals['MACDs_12_26_9']}")
            for sma in ["SMA_20", "SMA_50", "SMA_200"]:
                if sma in vals:
                    parts.append(f"{sma}: {vals[sma]}")
            self.info_label.setText("   |   ".join(parts))

        # Slice to last 6 months for display
        plot_df = indicators.df.tail(130).copy() if indicators else df.tail(130).copy()

        # Draw chart
        self.figure.clear()
        ax_price = self.figure.add_subplot(2, 1, 1)
        ax_volume = self.figure.add_subplot(2, 1, 2, sharex=ax_price)

        ax_price.set_facecolor("#1e1e2e")
        ax_volume.set_facecolor("#1e1e2e")

        # Build SMA addplots (must pass ax= for external axes mode)
        addplots = []
        for sma_col, colour in SMA_COLOURS.items():
            if sma_col in plot_df.columns and plot_df[sma_col].notna().any():
                addplots.append(mpf.make_addplot(plot_df[sma_col], ax=ax_price, color=colour, width=1.0))

        mpf.plot(
            plot_df,
            type="candle",
            style=CATPPUCCIN_STYLE,
            ax=ax_price,
            volume=ax_volume,
            addplot=addplots if addplots else None,
            datetime_format="%b %d",
            xrotation=0,
        )

        # Add SMA legend
        for sma_col, colour in SMA_COLOURS.items():
            if sma_col in plot_df.columns and plot_df[sma_col].notna().any():
                ax_price.plot([], [], color=colour, label=sma_col, linewidth=1.0)
        if any(sma in plot_df.columns for sma in SMA_COLOURS):
            ax_price.legend(loc="upper left", fontsize=8, facecolor="#181825",
                            edgecolor="#313244", labelcolor="#cdd6f4")

        self.figure.subplots_adjust(left=0.08, right=0.96, top=0.96, bottom=0.08, hspace=0.05)
        self.canvas.draw()

    def clear_chart(self):
        """Reset chart to placeholder state."""
        self.figure.clear()
        self.canvas.draw()
        self.ticker_label.setText("Click a holding to view chart")
        self.signal_badge.hide()
        self.info_label.setText("")

# Forge Portfolio Tracker

A long-term investment portfolio tracker with a built-in buy/hold/sell signal engine. Built with Python and PyQt5.

## Features

- **Multi-asset support** — Track UK stocks, US stocks, ETFs, and crypto in a single dashboard.
- **Signal engine** — Automated buy, hold, and sell signals powered by technical indicators (RSI, MACD, moving averages).
- **Currency conversion** — All holdings normalised to GBP with live FX rates.
- **Portfolio reporting** — Generate PDF reports summarising performance, allocation, and signals.
- **Desktop notifications** — Get alerted when a signal fires on one of your holdings.
- **Dark theme UI** — Clean, modern interface built with PyQt5.

## Getting Started

```bash
# Clone the repo
git clone https://github.com/<your-username>/forge-portfolio.git
cd forge-portfolio

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the app
python main.py
```

## Project Structure

```
forge-portfolio/
├── main.py              # Application entry point
├── config.json          # User settings (currency, refresh interval, theme)
├── portfolio.json       # Holdings data
├── requirements.txt     # Python dependencies
├── data/                # Market data fetching and technical indicators
├── ui/                  # PyQt5 UI components
├── reports/             # PDF report generation
└── utils/               # Currency conversion and logging utilities
```

## Tech Stack

- **UI**: PyQt5
- **Market Data**: yfinance, requests
- **Analysis**: pandas, pandas-ta, mplfinance, matplotlib
- **Reports**: reportlab
- **Notifications**: plyer

## License

This project is for personal use.

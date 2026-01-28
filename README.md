# Commodity ETF iNAV vs Price Scanner

A Streamlit app to scan Indian Gold and Silver ETFs for premium/discount vs their indicative NAV (iNAV).

## What it does

1. **On button click**: Fetches live LTP (Last Traded Price) and iNAV from NSE
2. **Calculates**: Premium/Discount = (LTP - iNAV) / iNAV × 100%
3. **Highlights**: Funds trading significantly above or below fair value
4. **Exports**: Results as CSV

## Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

Then:
1. Open http://localhost:8501 in your browser
2. Upload your funds CSV (or use the default `funds.csv`)
3. Click **"🔍 Scan Now"**
4. View results sorted by premium/discount
5. Download CSV if needed

## CSV Format

Your CSV should have 3 columns (no header required):

```csv
ISIN,Fund Name,NSE URL
INF204KB17I5,Nippon India ETF Gold BeES,https://www.nseindia.com/get-quote/equity/GOLDBEES/...
```

## Understanding the Results

| Column | Description |
|--------|-------------|
| **LTP** | Last Traded Price on NSE |
| **iNAV** | Indicative NAV (fair value reference) |
| **Premium/Discount %** | Positive = premium (overvalued), Negative = discount (undervalued) |
| **Premium/Discount ₹** | Absolute difference in rupees |

### Color coding:
- 🟢 **Green rows**: Trading at a discount (potential buy opportunity)
- 🔴 **Red rows**: Trading at a premium (potential sell opportunity)

## Notes

1. **iNAV availability**: Not all ETFs have iNAV in NSE's API. For those, the field will be empty.

2. **Rate limiting**: The app includes delays between requests to be polite to NSE servers. If you get errors, increase the delay in settings.

3. **Trading implications**: Premium/discount can persist due to:
   - Low liquidity
   - Market sentiment
   - Arbitrage constraints
   
   Large deviations (>2-3%) may be worth investigating, but aren't automatically "free money".

## Troubleshooting

**"Failed to fetch" errors:**
- NSE may be rate limiting you
- Try increasing the delay between requests
- Wait a few minutes and try again

**Missing iNAV values:**
- NSE doesn't expose iNAV for all ETFs via their API
- You may need to check AMC websites for those funds

## License

MIT - Use at your own risk. This is for educational purposes only and not financial advice.

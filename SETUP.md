# Setup Guide

## Step 1: Install Python

Python is required to run this tool. If you don't have Python installed:

1. **Download Python:**
   - Visit https://www.python.org/downloads/
   - Download Python 3.11 or newer for Windows
   - **Important:** During installation, check the box "Add Python to PATH"

2. **Verify Installation:**
   Open a new PowerShell window and run:
   ```powershell
   python --version
   ```
   You should see something like `Python 3.11.x`

## Step 2: Install Dependencies

Once Python is installed, run:
```powershell
python -m pip install -r requirements.txt
```

This will install:
- selenium (for web scraping)
- beautifulsoup4 (for HTML parsing)
- requests (for HTTP requests)
- pandas (for data analysis)
- schedule (for periodic data collection)
- webdriver-manager (for automatic ChromeDriver management)

## Step 3: Install Chrome Browser

The scraper uses Chrome browser. Make sure you have Chrome installed:
- Download from https://www.google.com/chrome/

The `webdriver-manager` package will automatically download the correct ChromeDriver for your Chrome version.

## Step 4: Test the Scraper

Run the test script to verify everything works:
```powershell
python test_scraper.py
```

This will:
- Open a browser window
- Attempt to scrape facility usage data
- Save a test data point to the database

## Step 5: Start Collecting Data

Once the test works, start collecting data:
```powershell
python collect_data.py
```

This will:
- Collect data immediately
- Then collect data every 15 minutes
- Store all data in `facility_data.db`

**Let this run for at least 1-2 days to gather enough data for meaningful analysis.**

## Step 6: Analyze the Data

After collecting data, get recommendations:
```powershell
python analyze.py --facility "CoRec"
```

Or analyze all facilities:
```powershell
python analyze.py --all
```

## Troubleshooting

### "Python was not found"
- Make sure Python is installed and added to PATH
- Try restarting your terminal/PowerShell after installing Python
- Verify with `python --version`

### "ChromeDriver not found"
- The `webdriver-manager` package should handle this automatically
- Make sure Chrome browser is installed
- If issues persist, manually download ChromeDriver from https://chromedriver.chromium.org/

### Scraper finds no data
- The website structure may have changed
- Check `test_scraper.py` output - it will show what the scraper found
- You may need to adjust the parsing logic in `scraper.py` based on the actual page structure

### Database errors
- Make sure you have write permissions in the project directory
- The database file `facility_data.db` will be created automatically

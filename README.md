# CoRec Tracker

A web application to track and analyze Purdue RecWell facility usage data to determine the best times to visit specific facilities.

## Features

- 🌐 **Web Interface**: Beautiful, modern web UI to view analytics
- 🤖 **Automated Data Collection**: Collects facility usage data every 15 minutes
- 📊 **Historical Analysis**: Recommends optimal visit times based on occupancy patterns
- ☁️ **Cloud Deployable**: Deploy to Railway, Render, or Heroku for 24/7 operation
- 📈 **Real-time Analytics**: View current occupancy, best/worst times, and patterns

## Setup

### Quick Setup (Windows)

Run the PowerShell setup script:
```powershell
.\setup.ps1
```

### Manual Setup

1. **Install Python** (if not already installed):
   - Download from https://www.python.org/downloads/
   - **Important:** Check "Add Python to PATH" during installation

2. **Install dependencies:**
```bash
python -m pip install -r requirements.txt
```

3. **Install Chrome Browser** (required for web scraping):
   - Download from https://www.google.com/chrome/
   - ChromeDriver will be downloaded automatically

See [SETUP.md](SETUP.md) for detailed setup instructions.

## Quick Start

### Option 1: Web Application (Recommended)

Run the web app locally:
```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser!

### Option 2: Deploy to Cloud (24/7 Operation)

Deploy to Railway, Render, or Heroku for continuous data collection:

**Railway (Easiest - 5 minutes):**
1. Push code to GitHub
2. Go to https://railway.app
3. Deploy from GitHub repo
4. Done! Your app runs 24/7

See [QUICK_START.md](QUICK_START.md) for detailed deployment instructions.

### Option 3: Command Line Tools

**Test the scraper:**
```bash
python test_scraper.py
```

**Collect data manually:**
```bash
python collect_data.py
```

**Analyze data:**
```bash
python analyze.py --facility "Colby Fitness"
python analyze.py --all --days 7
```

## Web Application Features

- **Dashboard**: View all facilities and their current status
- **Real-time Data**: See current occupancy for each facility
- **Recommendations**: Get best/worst times to visit
- **Patterns**: View daily and hourly occupancy trends
- **Auto-refresh**: Data updates automatically

## Deployment Options

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guides for:
- Railway (Recommended - Free tier available)
- Render (Free tier available)
- Heroku (Paid)
- PythonAnywhere (Free tier available)

## Project Structure

- `scraper.py` - Web scraper to extract facility usage data
- `collect_data.py` - Main script to run periodic data collection
- `analyze.py` - Analysis tool to recommend best visit times
- `database.py` - Database operations for storing and retrieving data
- `facility_data.db` - SQLite database storing historical data

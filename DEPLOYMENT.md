# Deployment Guide

This guide will help you deploy CoRec Tracker to a cloud platform so it can run continuously without your laptop.

## Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)

Railway is the easiest option with a free tier:

1. **Sign up**: Go to https://railway.app and sign up with GitHub
2. **Create new project**: Click "New Project"
3. **Deploy from GitHub**:
   - Select "Deploy from GitHub repo"
   - Choose your repository (or create one and push this code)
   - Railway will automatically detect Python and deploy

4. **Set up environment** (optional):
   - Railway will automatically install dependencies
   - The app will start automatically

5. **Access your app**: Railway provides a URL like `https://your-app.railway.app`

**Cost**: Free tier includes 500 hours/month, $5/month for more

---

### Option 2: Render (Free Tier Available)

1. **Sign up**: Go to https://render.com and sign up
2. **Create new Web Service**:
   - Connect your GitHub repository
   - Select "Web Service"
   - Choose Python environment
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120`

3. **Deploy**: Click "Create Web Service"

**Cost**: Free tier available, but services spin down after 15 minutes of inactivity

---

### Option 3: Heroku (Paid, but reliable)

1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli
2. **Login**: `heroku login`
3. **Create app**: `heroku create your-app-name`
4. **Deploy**: `git push heroku main`
5. **Scale worker**: `heroku ps:scale worker=1` (for background collector)

**Cost**: $7/month minimum (no free tier anymore)

---

### Option 4: PythonAnywhere (Free tier available)

1. **Sign up**: Go to https://www.pythonanywhere.com
2. **Upload files**: Use the Files tab to upload your project
3. **Create Web App**:
   - Go to Web tab
   - Click "Add a new web app"
   - Choose Flask and Python 3.10
   - Set source code path
   - Set WSGI file to point to `app.py`

4. **Set up scheduled task** (for data collection):
   - Go to Tasks tab
   - Create a scheduled task to run `python collect_data.py` every 15 minutes

**Cost**: Free tier available, $5/month for better performance

---

## Pre-Deployment Checklist

Before deploying, make sure:

1. ✅ All dependencies are in `requirements.txt`
2. ✅ Database file (`facility_data.db`) is in `.gitignore` (it will be created on the server)
3. ✅ Environment variables are set (if needed)
4. ✅ The app runs locally: `python app.py`

## Post-Deployment

After deploying:

1. **Access your app**: Visit the URL provided by your hosting service
2. **Verify data collection**: Check the status bar - collector should be running
3. **Monitor**: Let it run for a few hours and check if data is being collected

## Database Persistence

**Important**: Most free hosting services don't persist files between deployments. Consider:

1. **SQLite (current)**: Works but data may be lost on redeploy
2. **Upgrade to PostgreSQL**: For production, use a managed database
   - Railway: Add PostgreSQL service
   - Render: Add PostgreSQL database
   - Heroku: `heroku addons:create heroku-postgresql`

## Updating Database to PostgreSQL (Optional)

If you want persistent data storage:

1. Install: `pip install psycopg2-binary`
2. Update `database.py` to use PostgreSQL connection string from environment
3. Set `DATABASE_URL` environment variable on your hosting platform

## Troubleshooting

### Collector not running
- Check logs on your hosting platform
- Verify Chrome/ChromeDriver is available (may need to install buildpacks)
- Check if background threads are supported

### No data being collected
- Check if Selenium can access the website
- Verify ChromeDriver is installed correctly
- Check application logs for errors

### App crashes
- Check memory limits (Selenium can be memory-intensive)
- Verify all dependencies are installed
- Check Python version compatibility

## Recommended Setup

For best results:
- **Platform**: Railway or Render
- **Database**: Start with SQLite, upgrade to PostgreSQL if needed
- **Monitoring**: Check logs regularly for first few days
- **Backup**: Export database periodically if using SQLite

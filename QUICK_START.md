# Quick Start Guide - Deploy to Railway (5 minutes)

## Step 1: Push to GitHub

1. Create a new repository on GitHub
2. Push your code:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/corec-tracker.git
git push -u origin main
```

## Step 2: Deploy to Railway

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically:
   - Detect Python
   - Install dependencies
   - Start the app

## Step 3: Access Your App

1. Railway will provide a URL like `https://your-app.up.railway.app`
2. Click on it to open your web app
3. The data collector starts automatically!

## That's It! 🎉

Your app is now running 24/7 in the cloud, collecting data every 15 minutes.

---

## Testing Locally First

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Open http://localhost:5000 in your browser
```

## Troubleshooting

**If the collector doesn't start:**
- Check Railway logs
- Make sure Chrome/ChromeDriver is available (Railway handles this automatically)

**If you see errors:**
- Check that all files are pushed to GitHub
- Verify `requirements.txt` includes Flask and gunicorn
- Check Railway logs for specific errors

## Next Steps

- Monitor the app for a few hours to ensure data collection works
- Share the URL with friends!
- Consider upgrading to PostgreSQL for persistent storage (see DEPLOYMENT.md)

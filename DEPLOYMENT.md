# 🚀 Free Hosting Deployment Guide

This guide will help you deploy your Stock Market Price Prediction application on free hosting platforms.

## 📋 Table of Contents
1. [Render.com (Recommended)](#rendercom)
2. [Railway.app](#railwayapp)
3. [Fly.io](#flyio)
4. [PythonAnywhere](#pythonanywhere)
5. [Troubleshooting](#troubleshooting)

---

## 🌟 Render.com (Recommended)

**Free Tier:** 750 hours/month, free SSL, custom domains

### Step 1: Prepare Your Repository
1. Push your code to GitHub/GitLab/Bitbucket
2. Make sure all files are committed

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com) and sign up (free)
2. Click "New +" → "Web Service"
3. Connect your repository
4. Configure the service:
   - **Name:** stock-market-prediction (or your choice)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

### Step 3: Environment Variables
Add these in Render dashboard → Environment:
- `SECRET_KEY`: Generate a random secret key (you can use: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `FLASK_ENV`: `production`
- `PORT`: `10000` (Render uses port 10000)

### Step 4: Deploy
Click "Create Web Service" and wait for deployment (5-10 minutes)

**Your app will be live at:** `https://your-app-name.onrender.com`

---

## 🚂 Railway.app

**Free Tier:** $5 credit/month (enough for small apps)

### Step 1: Deploy on Railway
1. Go to [railway.app](https://railway.app) and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository

### Step 2: Configure
Railway auto-detects Python apps. If needed, add:
- **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`

### Step 3: Environment Variables
Add in Railway dashboard → Variables:
- `SECRET_KEY`: Generate a random secret key
- `FLASK_ENV`: `production`
- `PORT`: Railway sets this automatically

### Step 4: Deploy
Railway will automatically deploy. Get your URL from the dashboard.

---

## ✈️ Fly.io

**Free Tier:** 3 shared-cpu VMs, 3GB persistent volumes

### Step 1: Install Fly CLI
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Mac/Linux
curl -L https://fly.io/install.sh | sh
```

### Step 2: Login
```bash
fly auth login
```

### Step 3: Initialize
```bash
fly launch
```
Follow the prompts. Fly will detect your Python app.

### Step 4: Deploy
```bash
fly deploy
```

**Your app will be live at:** `https://your-app-name.fly.dev`

---

## 🐍 PythonAnywhere

**Free Tier:** Limited to 1 web app, subdomain only

### Step 1: Sign Up
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com) and create a free account
2. Verify your email

### Step 2: Upload Files
1. Go to "Files" tab
2. Upload your project files (or use Git)
3. Or use Bash console:
```bash
git clone https://github.com/yourusername/your-repo.git
```

### Step 3: Install Dependencies
In Bash console:
```bash
cd your-repo
pip3.10 install --user -r requirements.txt
```

### Step 4: Configure Web App
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Flask"
4. Select Python 3.10
5. Set path: `/home/yourusername/your-repo/app.py`

### Step 5: Set Environment Variables
In Web tab → "Static files" section, add:
- `SECRET_KEY`: Your secret key
- `FLASK_ENV`: `production`

### Step 6: Reload
Click the green "Reload" button

**Your app will be live at:** `https://yourusername.pythonanywhere.com`

---

## 🔧 Additional Setup for All Platforms

### Install Gunicorn
✅ `gunicorn` has been added to `requirements.txt`

### Lightweight Production Build (Optional)
If you encounter build timeouts or memory issues, use `requirements-production.txt` instead:
- This file excludes heavy unused dependencies (TensorFlow, PyTorch)
- Faster builds and smaller deployment size
- To use: Change build command to `pip install -r requirements-production.txt`

**Note:** The main `requirements.txt` includes all dependencies. Use `requirements-production.txt` only if you face deployment issues.

---

## 🐛 Troubleshooting

### Issue: Build fails due to large dependencies
**Solution:** Remove unused heavy dependencies from `requirements.txt` (TensorFlow, PyTorch if not used)

### Issue: Database not working
**Solution:** 
- For SQLite: Make sure the instance folder has write permissions
- Consider upgrading to PostgreSQL (free on Render/Railway)

### Issue: App crashes on startup
**Solution:**
1. Check logs in hosting dashboard
2. Verify all environment variables are set
3. Ensure `gunicorn` is installed
4. Check that `SECRET_KEY` is set

### Issue: Static files not loading
**Solution:**
- Make sure all static files are in the repository
- Check file paths in templates

### Issue: Port binding errors
**Solution:**
- Use `0.0.0.0` as host
- Use `$PORT` environment variable (platforms set this automatically)

---

## 📝 Quick Checklist

Before deploying, ensure:
- [ ] All code is pushed to Git repository
- [ ] `requirements.txt` is up to date
- [ ] `Procfile` exists (for Render/Railway)
- [ ] `runtime.txt` exists (for Render)
- [ ] `SECRET_KEY` is set in environment variables
- [ ] `gunicorn` is in `requirements.txt`
- [ ] Database path is configured correctly
- [ ] All static files are included

---

## 🎯 Recommended Platform

**For beginners:** **Render.com** - Easiest setup, good free tier
**For more control:** **Railway.app** - More flexible, $5 credit
**For advanced users:** **Fly.io** - More control, Docker-based

---

## 🔗 Useful Links

- [Render Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Fly.io Documentation](https://fly.io/docs)
- [PythonAnywhere Help](https://help.pythonanywhere.com)

---

**Need help?** Check the logs in your hosting platform's dashboard for detailed error messages.


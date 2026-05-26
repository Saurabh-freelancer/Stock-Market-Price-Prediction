# ⚡ Quick Deploy Guide

## Fastest Way: Render.com (5 minutes)

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com) → Sign up (free)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free
5. Add Environment Variables:
   - `SECRET_KEY`: Run `python -c "import secrets; print(secrets.token_hex(32))"` to generate
   - `FLASK_ENV`: `production`
6. Click "Create Web Service"

**Done!** Your app will be live in 5-10 minutes at `https://your-app-name.onrender.com`

---

## Alternative: Railway.app (3 minutes)

1. Go to [railway.app](https://railway.app) → Sign up
2. "New Project" → "Deploy from GitHub"
3. Select your repo
4. Add environment variable: `SECRET_KEY` (generate one)
5. Deploy automatically!

---

## Environment Variables Needed

All platforms need:
- `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
- `FLASK_ENV`: Set to `production`

---

## Files Already Created ✅

- ✅ `Procfile` - For Render/Railway
- ✅ `runtime.txt` - Python version
- ✅ `render.yaml` - Render configuration
- ✅ `railway.json` - Railway configuration
- ✅ `fly.toml` - Fly.io configuration
- ✅ `requirements.txt` - Updated with gunicorn
- ✅ `app.py` - Updated for production

**You're all set! Just push to GitHub and deploy!**


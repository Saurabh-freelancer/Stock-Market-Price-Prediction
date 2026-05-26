# Quick Setup Guide - Stock Market Price Prediction Website

## 🚀 How to Run the Website

### Option 1: Simplified Version (Recommended)
This version avoids compatibility issues and runs smoothly:

```bash
# Install only essential packages
pip install -r requirements_simple.txt

# Run the simplified version
python run_simple.py
```

### Option 2: Full Version (If you have compatible packages)
This version includes advanced ML features:

```bash
# Install all packages (may have compatibility issues)
pip install -r requirements.txt

# Run the full version
python run.py
```

## 🌐 Access the Website

Once running, open your browser and go to:
**http://localhost:5000**

## 📱 Features Available

### ✅ Working Features:
- **User Registration & Login** - Create accounts and sign in
- **Dashboard** - View your prediction history and statistics
- **Stock Predictions** - Make AI-powered stock price predictions
- **Real-time Market Data** - View current stock prices and trends
- **Interactive Charts** - Visualize stock data and predictions
- **Responsive Design** - Works on desktop and mobile

### 📊 Stock Data:
- **Mock Data**: The simplified version uses realistic mock data
- **Real API**: Can be configured to use Alpha Vantage API for real data
- **Popular Stocks**: AAPL, GOOGL, MSFT, AMZN, TSLA, META, NVDA, NFLX

## 🔧 Configuration

### For Real Stock Data:
1. Get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Replace `"demo"` with your API key in `app_simple.py` line 47
3. Restart the application

### Database:
- SQLite database is created automatically
- No additional setup required

## 🎯 How to Use

1. **Register**: Create a new account
2. **Login**: Sign in with your credentials
3. **Make Predictions**: 
   - Go to "Predict" page
   - Enter stock symbol (e.g., AAPL)
   - Select timeframe (1 week to 1 year)
   - Click "Generate Prediction"
4. **View Dashboard**: Check your prediction history and performance

## 🛠️ Troubleshooting

### If you get import errors:
- Use the simplified version (`run_simple.py`)
- Install only essential packages (`requirements_simple.txt`)

### If the website doesn't load:
- Check if port 5000 is available
- Try a different port by editing the port number in the run script

### If predictions don't work:
- The simplified version uses mock data for demonstration
- For real predictions, configure the Alpha Vantage API key

## 📝 Notes

- **Demo Mode**: The simplified version uses realistic mock data
- **No Real Money**: This is for educational purposes only
- **Predictions**: Based on simplified algorithms for demonstration
- **Security**: Passwords are hashed and stored securely

## 🎉 Success!

Your Stock Market Price Prediction website is now running! 
Access it at **http://localhost:5000** and start making predictions. 
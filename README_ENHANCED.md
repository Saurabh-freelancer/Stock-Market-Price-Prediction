# 🚀 Enhanced Stock Market Price Prediction Application

A comprehensive, AI-powered stock market prediction platform with advanced features including sentiment analysis, technical indicators, market overview, and user personalization.

## ✨ Key Features

### 🔮 Advanced Prediction Models
- **Enhanced AI Model**: Uses multiple machine learning algorithms with technical indicators and sentiment analysis
- **Simple Linear Regression**: Basic prediction model for quick analysis
- **Confidence Scoring**: Each prediction includes a confidence percentage
- **Multiple Timeframes**: Predict from 1 week to 1 year ahead

### 📊 Technical Analysis
- **Comprehensive Indicators**: RSI, MACD, Bollinger Bands, Stochastic Oscillator, Williams %R
- **Moving Averages**: SMA (5, 20, 50), EMA (12, 26)
- **Volume Analysis**: Volume ratios and trends
- **Volatility Metrics**: Price volatility and risk assessment
- **Interactive Charts**: Plotly-powered charts with technical overlays

### 🧠 Sentiment Analysis
- **News Sentiment**: Analyzes market news using NLP
- **Social Media**: Twitter and Reddit sentiment analysis
- **Sentiment Scoring**: Positive, negative, or neutral sentiment with confidence scores
- **Market Impact**: How sentiment affects price predictions

### 🌍 Market Overview
- **Real-time Data**: Live market data from Yahoo Finance
- **Market Indices**: S&P 500, Dow Jones, NASDAQ, Russell 2000
- **Sector Performance**: 11 major sectors with performance tracking
- **Top Stocks**: Popular stocks with real-time price updates
- **Market News**: Latest financial news with sentiment analysis

### 👤 User Personalization
- **Watchlists**: Track your favorite stocks
- **Custom Settings**: Theme, notifications, and preferences
- **Prediction History**: View and analyze past predictions
- **Personal Dashboard**: Customized overview of your activity
- **Export Data**: Download your prediction data

### 🎨 Modern UI/UX
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Interactive Charts**: Plotly charts with zoom, pan, and hover
- **Real-time Updates**: Auto-refreshing market data
- **Dark/Light Theme**: Customizable appearance
- **3D Animations**: Smooth transitions and hover effects

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd stock-market-price-prediction
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python run_enhanced.py
```

### Step 4: Access the Application
Open your web browser and navigate to:
- **Local**: http://127.0.0.1:5000
- **Network**: http://0.0.0.0:5000

## 📋 Requirements

The application requires the following Python packages:

```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-WTF==1.1.1
Werkzeug==2.3.7
requests==2.31.0
pandas==2.1.4
numpy==1.26.2
scikit-learn==1.3.2
yfinance==0.2.28
plotly==5.17.0
python-dotenv==1.0.0
bcrypt==4.1.2
textblob==0.17.1
nltk==3.8.1
ta==0.10.2
beautifulsoup4==4.12.2
lxml==4.9.3
newsapi-python==0.2.6
alpha-vantage==2.3.1
tensorflow==2.13.0
keras==2.13.1
transformers==4.33.2
torch==2.0.1
sentence-transformers==2.2.2
```

## 🚀 Quick Start Guide

### 1. Registration and Login
- Create an account or login with existing credentials
- Access your personalized dashboard

### 2. Making Predictions
- Navigate to "Price Prediction"
- Enter a stock symbol (e.g., AAPL, GOOGL, MSFT)
- Select prediction timeframe (1 week to 1 year)
- Choose prediction model (Enhanced AI recommended)
- Click "Generate Prediction"

### 3. Market Overview
- View real-time market data
- Check sector performance
- Read latest market news
- Monitor market indices

### 4. Watchlist Management
- Add stocks to your watchlist
- Track price changes
- Set up alerts
- View detailed analysis

### 5. Stock Analysis
- Comprehensive technical analysis
- Sentiment analysis
- Trading signals
- Risk assessment

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
NEWS_API_KEY=your-news-api-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
```

### Database
The application uses SQLite by default. The database file is created automatically at `instance/stock_prediction.db`.

## 📊 API Endpoints

### Public Endpoints
- `GET /` - Home page with market overview
- `GET /register` - User registration
- `GET /login` - User login
- `GET /market_overview` - Market overview page

### Authenticated Endpoints
- `GET /dashboard` - User dashboard
- `GET /predict` - Prediction form
- `POST /predict` - Generate prediction
- `GET /watchlist` - Watchlist management
- `GET /stock_analysis/<symbol>` - Stock analysis
- `GET /settings` - User settings

### API Endpoints
- `GET /api/stock/<symbol>` - Stock information
- `GET /api/market-data` - Market data
- `GET /api/sentiment/<symbol>` - Sentiment analysis
- `GET /api/technical-indicators/<symbol>` - Technical indicators

## 🧪 Testing

### Manual Testing
1. **User Registration/Login**: Test account creation and authentication
2. **Stock Prediction**: Try different symbols and timeframes
3. **Market Overview**: Verify real-time data updates
4. **Watchlist**: Add/remove stocks and check functionality
5. **Settings**: Test user preferences and customization

### Sample Test Cases
```python
# Test prediction for popular stocks
symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
timeframes = [7, 30, 90, 365]

# Test technical indicators
indicators = ['RSI', 'MACD', 'SMA_20', 'Bollinger_Bands']

# Test sentiment analysis
sentiment_symbols = ['AAPL', 'TSLA', 'NVDA']
```

## 🔒 Security Features

- **Password Hashing**: Secure password storage using bcrypt
- **Session Management**: Flask-Login for user sessions
- **Input Validation**: Form validation and sanitization
- **SQL Injection Protection**: SQLAlchemy ORM protection
- **XSS Protection**: Template escaping and validation

## 📈 Performance Optimization

- **Caching**: Redis caching for frequently accessed data
- **Database Indexing**: Optimized database queries
- **Lazy Loading**: Efficient data loading
- **Compression**: Gzip compression for static assets
- **CDN**: Content delivery network for assets

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Database Issues**
   ```bash
   rm instance/stock_prediction.db
   python run_enhanced.py
   ```

3. **Port Already in Use**
   ```bash
   lsof -ti:5000 | xargs kill -9
   ```

4. **Memory Issues**
   - Reduce batch size for predictions
   - Clear browser cache
   - Restart the application

### Debug Mode
Enable debug mode for detailed error messages:
```python
app.run(debug=True)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black app_enhanced.py
flake8 app_enhanced.py
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Yahoo Finance**: For providing free stock market data
- **Plotly**: For interactive charting capabilities
- **Flask**: For the web framework
- **scikit-learn**: For machine learning algorithms
- **NLTK**: For natural language processing
- **TA-Lib**: For technical analysis indicators

## 📞 Support

For support and questions:
- **Email**: support@stockpredict.com
- **Documentation**: [Link to documentation]
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)

## 🔮 Future Enhancements

- **Real-time Trading**: Integration with brokerage APIs
- **Advanced ML Models**: LSTM, GRU, and Transformer models
- **Portfolio Optimization**: Modern portfolio theory implementation
- **Social Trading**: Copy trading and social features
- **Mobile App**: Native iOS and Android applications
- **API Rate Limiting**: Implement proper rate limiting
- **Backtesting**: Historical strategy testing
- **Options Analysis**: Options pricing and strategies

---

**⚠️ Disclaimer**: This application is for educational and research purposes only. Stock market predictions are inherently uncertain and should not be used as the sole basis for investment decisions. Always consult with financial advisors before making investment decisions.

**📊 Data Sources**: Market data provided by Yahoo Finance. News and sentiment data from various sources. All data is for informational purposes only.

**🔒 Privacy**: User data is stored securely and never shared with third parties. All predictions and personal information remain confidential.


# Stock Market Price Prediction Website

A modern, AI-powered stock market price prediction website built with Python Flask, featuring real-time market data, user authentication, and machine learning predictions.

## 🚀 Features

### Core Features
- **AI-Powered Predictions**: Machine learning algorithms analyze historical data to predict future stock prices
- **Real-Time Market Data**: Live stock prices and market information from Yahoo Finance API
- **User Authentication**: Secure login/signup system with session management
- **Personal Dashboard**: Track prediction history and performance metrics
- **Interactive Charts**: Visual representation of stock data and predictions
- **Responsive Design**: Modern, mobile-friendly interface

### Technical Features
- **Python Flask Backend**: Robust web framework with SQLAlchemy ORM
- **Machine Learning**: Linear regression model with technical indicators
- **Real-Time APIs**: Integration with Yahoo Finance for live market data
- **Database Storage**: SQLite database for user data and prediction history
- **Modern UI**: Bootstrap 5 with custom CSS and JavaScript

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stock-market-prediction
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the website**
   Open your browser and go to `http://localhost:5000`

## 📁 Project Structure

```
stock-market-prediction/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── templates/            # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Home page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # User dashboard
│   └── predict.html      # Prediction page
└── stock_prediction.db   # SQLite database (created automatically)
```

## 🎯 Usage Guide

### Getting Started
1. **Register an Account**: Click "Register" and create a new account
2. **Login**: Sign in with your credentials
3. **Make Predictions**: Navigate to the "Predict" page
4. **View Dashboard**: Check your prediction history and performance

### Making Predictions
1. Enter a stock symbol (e.g., AAPL, GOOGL, MSFT)
2. Select a prediction timeframe (1 week to 1 year)
3. Click "Generate Prediction"
4. View detailed results with confidence scores

### Dashboard Features
- **Statistics Overview**: Total predictions, active predictions, completion rate
- **Prediction History**: Detailed table of all your predictions
- **Performance Charts**: Visual representation of prediction accuracy
- **Quick Actions**: Easy access to common features

## 🔧 API Endpoints

### Public APIs
- `GET /api/market-data` - Get real-time market data for popular stocks
- `GET /api/stock/<symbol>` - Get detailed information for a specific stock

### Protected APIs (Require Login)
- `POST /predict` - Generate stock price predictions
- `GET /dashboard` - User dashboard with prediction history

## 🤖 Machine Learning Model

The prediction model uses:
- **Linear Regression**: Base prediction algorithm
- **Technical Indicators**: RSI, Moving Averages, Price/Volume changes
- **Historical Data**: 2 years of historical price data
- **Feature Engineering**: Multiple technical indicators as features

### Model Features
- Open, High, Low, Close prices
- Volume data
- 5-day and 20-day Simple Moving Averages
- Relative Strength Index (RSI)
- Price and volume change percentages

## 🎨 UI/UX Features

### Design Elements
- **Modern Gradient Backgrounds**: Eye-catching visual design
- **Responsive Cards**: Clean, organized information display
- **Interactive Charts**: Chart.js integration for data visualization
- **Loading States**: Smooth user experience during data processing
- **Error Handling**: User-friendly error messages

### Color Scheme
- Primary: #3498db (Blue)
- Secondary: #2c3e50 (Dark Blue)
- Success: #27ae60 (Green)
- Warning: #f39c12 (Orange)
- Danger: #e74c3c (Red)

## 🔒 Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **Session Management**: Flask-Login for user sessions
- **Form Validation**: Client and server-side validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CSRF Protection**: Built-in Flask security features

## 📊 Data Sources

- **Yahoo Finance API**: Real-time stock data and historical prices
- **Technical Indicators**: Calculated from historical price data
- **Market Information**: Company details, market cap, volume data

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. Set environment variables for production
2. Use a production WSGI server (Gunicorn)
3. Configure a reverse proxy (Nginx)
4. Set up SSL certificates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This application is for educational and research purposes only. Stock market predictions are inherently uncertain and should not be used as the sole basis for investment decisions. Always consult with financial advisors before making investment decisions.

## 🆘 Support

If you encounter any issues or have questions:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information

## 🔄 Updates

### Version 1.0.0
- Initial release with core prediction functionality
- User authentication system
- Real-time market data integration
- Responsive web interface
- Machine learning prediction model

---

**Built with ❤️ using Python Flask and modern web technologies** 
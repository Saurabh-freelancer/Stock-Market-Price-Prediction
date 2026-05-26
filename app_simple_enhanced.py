from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import json
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_prediction.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    preferences = db.Column(db.Text)  # JSON string for user preferences
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    watchlists = db.relationship('Watchlist', backref='user', lazy=True)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    predicted_price = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    prediction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    target_date = db.Column(db.Date, nullable=False)
    prediction_type = db.Column(db.String(20), default='linear_regression')
    technical_indicators = db.Column(db.Text)  # JSON string for technical indicators
    sentiment_score = db.Column(db.Float, default=0.0)

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Simple Technical Indicators
def calculate_sma(prices, window):
    """Calculate Simple Moving Average"""
    return prices.rolling(window=window).mean()

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_histogram = macd - macd_signal
    return macd, macd_signal, macd_histogram

def calculate_bollinger_bands(prices, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band

def get_stock_data(symbol, period='1y'):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        info = stock.info
        return data, info
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None, None

def add_technical_indicators(data):
    """Add technical indicators to stock data"""
    try:
        # Moving Averages
        data['SMA_5'] = calculate_sma(data['Close'], 5)
        data['SMA_20'] = calculate_sma(data['Close'], 20)
        data['SMA_50'] = calculate_sma(data['Close'], 50)
        
        # RSI
        data['RSI'] = calculate_rsi(data['Close'])
        
        # MACD
        macd, macd_signal, macd_hist = calculate_macd(data['Close'])
        data['MACD'] = macd
        data['MACD_signal'] = macd_signal
        data['MACD_histogram'] = macd_hist
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(data['Close'])
        data['BB_upper'] = bb_upper
        data['BB_middle'] = bb_middle
        data['BB_lower'] = bb_lower
        
        # Price change indicators
        data['Price_Change'] = data['Close'].pct_change()
        data['Volume_Change'] = data['Volume'].pct_change()
        
        # Volume indicators
        data['Volume_SMA'] = calculate_sma(data['Volume'], 20)
        data['Volume_ratio'] = data['Volume'] / data['Volume_SMA']
        
        return data
    except Exception as e:
        print(f"Error adding technical indicators: {e}")
        return data

def get_market_sentiment(symbol):
    """Get market sentiment for a stock symbol"""
    try:
        # Simple sentiment based on price movement
        data, info = get_stock_data(symbol, '1mo')
        if data is None or len(data) < 2:
            return 0.0
        
        # Calculate recent price trend
        recent_change = (data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]
        
        # Simple sentiment scoring based on price movement
        if recent_change > 0.02:  # > 2% increase
            return 0.3
        elif recent_change > 0.01:  # > 1% increase
            return 0.1
        elif recent_change < -0.02:  # < -2% decrease
            return -0.3
        elif recent_change < -0.01:  # < -1% decrease
            return -0.1
        else:
            return 0.0
    except Exception as e:
        print(f"Error getting sentiment for {symbol}: {e}")
        return 0.0

def predict_stock_price(symbol, days_ahead=30):
    """Enhanced prediction using technical indicators"""
    try:
        # Get comprehensive data
        data, info = get_stock_data(symbol, '2y')
        if data is None or len(data) < 30:
            return None, None, None, None
        
        # Add technical indicators
        data = add_technical_indicators(data)
        
        # Remove NaN values
        data = data.dropna()
        
        if len(data) < 30:
            return None, None, None, None
        
        # Get market sentiment
        sentiment_score = get_market_sentiment(symbol)
        
        # Simple prediction using moving averages and trend
        current_price = data['Close'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]
        
        # Trend analysis
        recent_trend = (data['Close'].iloc[-5:].mean() - data['Close'].iloc[-10:-5].mean()) / data['Close'].iloc[-10:-5].mean()
        
        # RSI analysis
        rsi = data['RSI'].iloc[-1]
        
        # Simple prediction logic
        if sma_20 > sma_50 and rsi < 70:  # Uptrend, not overbought
            trend_multiplier = 1 + (recent_trend * 0.5)
        elif sma_20 < sma_50 and rsi > 30:  # Downtrend, not oversold
            trend_multiplier = 1 + (recent_trend * 0.5)
        else:
            trend_multiplier = 1 + (recent_trend * 0.3)
        
        # Apply sentiment adjustment
        sentiment_multiplier = 1 + (sentiment_score * 0.1)
        
        # Calculate prediction
        predicted_price = current_price * trend_multiplier * sentiment_multiplier
        
        # Adjust for time horizon
        daily_change = (predicted_price - current_price) / days_ahead
        predicted_price = current_price + (daily_change * days_ahead)
        
        # Calculate confidence based on trend strength and RSI
        confidence = 0.5
        if abs(recent_trend) > 0.02:
            confidence += 0.2
        if 30 < rsi < 70:
            confidence += 0.2
        if abs(sentiment_score) > 0.1:
            confidence += 0.1
        
        confidence = min(confidence, 0.9)  # Cap at 90%
        
        # Get latest technical indicators
        latest_indicators = {
            'SMA_20': float(sma_20),
            'SMA_50': float(sma_50),
            'RSI': float(rsi),
            'MACD': float(data['MACD'].iloc[-1]),
            'BB_upper': float(data['BB_upper'].iloc[-1]),
            'BB_lower': float(data['BB_lower'].iloc[-1])
        }
        
        return current_price, predicted_price, confidence, latest_indicators
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None, None, None, None

def get_market_overview():
    """Get comprehensive market overview with indices and sectors"""
    try:
        # Major indices
        indices = ['^GSPC', '^DJI', '^IXIC']  # S&P 500, Dow Jones, NASDAQ
        index_data = []
        
        for index in indices:
            try:
                ticker = yf.Ticker(index)
                info = ticker.info
                hist = ticker.history(period='2d')
                
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = current - previous
                    change_percent = (change / previous * 100) if previous else 0
                    
                    index_data.append({
                        'symbol': index,
                        'name': info.get('longName', index),
                        'price': current,
                        'change': change,
                        'change_percent': change_percent
                    })
            except:
                continue
        
        # Popular stocks
        popular_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
        stock_data = []
        
        for symbol in popular_stocks:
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                hist = stock.history(period='2d')
                
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = current - previous
                    change_percent = (change / previous * 100) if previous else 0
                    
                    stock_data.append({
                        'symbol': symbol,
                        'name': info.get('longName', symbol),
                        'price': current,
                        'change': change,
                        'change_percent': change_percent,
                        'volume': info.get('volume', 0),
                        'market_cap': info.get('marketCap', 0),
                        'sector': info.get('sector', 'Unknown')
                    })
            except:
                continue
        
        return {
            'indices': index_data,
            'stocks': stock_data
        }
    except Exception as e:
        print(f"Error getting market overview: {e}")
        return {'indices': [], 'stocks': []}

def get_sector_performance():
    """Get sector performance data"""
    try:
        # Sector ETFs
        sector_etfs = {
            'XLK': 'Technology',
            'XLF': 'Financial',
            'XLV': 'Healthcare',
            'XLE': 'Energy',
            'XLI': 'Industrial',
            'XLY': 'Consumer Discretionary',
            'XLP': 'Consumer Staples',
            'XLU': 'Utilities',
            'XLB': 'Materials',
            'XLRE': 'Real Estate'
        }
        
        sector_data = []
        for etf, sector_name in sector_etfs.items():
            try:
                ticker = yf.Ticker(etf)
                hist = ticker.history(period='2d')
                
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = current - previous
                    change_percent = (change / previous * 100) if previous else 0
                    
                    sector_data.append({
                        'sector': sector_name,
                        'etf': etf,
                        'price': current,
                        'change': change,
                        'change_percent': change_percent
                    })
            except:
                continue
        
        return sorted(sector_data, key=lambda x: x['change_percent'], reverse=True)
    except Exception as e:
        print(f"Error getting sector performance: {e}")
        return []

def get_market_news():
    """Get market news with sentiment analysis"""
    try:
        # Simulated news items
        news_items = [
            {
                'title': 'Federal Reserve Signals Potential Rate Cuts',
                'summary': 'The Federal Reserve indicated potential interest rate cuts in the coming months, boosting market sentiment.',
                'sentiment': 0.3,
                'published_date': datetime.now() - timedelta(hours=2),
                'source': 'Financial Times',
                'impact': 'High'
            },
            {
                'title': 'Tech Earnings Beat Expectations',
                'summary': 'Major technology companies report stronger-than-expected quarterly earnings, driving market gains.',
                'sentiment': 0.6,
                'published_date': datetime.now() - timedelta(hours=4),
                'source': 'Reuters',
                'impact': 'Medium'
            },
            {
                'title': 'Oil Prices Show Increased Volatility',
                'summary': 'Crude oil prices show increased volatility due to geopolitical tensions in the Middle East.',
                'sentiment': -0.2,
                'published_date': datetime.now() - timedelta(hours=6),
                'source': 'Bloomberg',
                'impact': 'Medium'
            }
        ]
        
        return news_items
    except Exception as e:
        print(f"Error getting market news: {e}")
        return []

# Routes
@app.route('/')
def index():
    market_overview = get_market_overview()
    sector_performance = get_sector_performance()
    market_news = get_market_news()
    return render_template('index.html', 
                         market_overview=market_overview,
                         sector_performance=sector_performance,
                         market_news=market_news)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.prediction_date.desc()).limit(10).all()
    watchlist = Watchlist.query.filter_by(user_id=current_user.id).all()
    today = datetime.now().date()
    
    # Get user preferences
    preferences = {}
    if current_user.preferences:
        try:
            preferences = json.loads(current_user.preferences)
        except:
            preferences = {}
    
    return render_template('dashboard.html', 
                         predictions=predictions, 
                         watchlist=watchlist,
                         today=today,
                         preferences=preferences)

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        days_ahead = int(request.form['days_ahead'])
        prediction_type = request.form.get('prediction_type', 'enhanced')
        
        current_price, predicted_price, confidence, indicators = predict_stock_price(symbol, days_ahead)
        
        if current_price is not None:
            target_date = datetime.now().date() + timedelta(days=days_ahead)
            
            prediction = Prediction(
                user_id=current_user.id,
                symbol=symbol,
                current_price=current_price,
                predicted_price=predicted_price,
                confidence=confidence,
                target_date=target_date,
                prediction_type=prediction_type,
                technical_indicators=json.dumps(indicators) if indicators else None
            )
            db.session.add(prediction)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2),
                'confidence': round(confidence * 100, 2),
                'target_date': target_date.strftime('%Y-%m-%d'),
                'indicators': indicators
            })
        else:
            return jsonify({'success': False, 'error': 'Unable to predict price for this symbol'})
    
    return render_template('predict.html')

@app.route('/watchlist', methods=['GET', 'POST'])
@login_required
def watchlist():
    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        notes = request.form.get('notes', '')
        
        # Check if already in watchlist
        existing = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()
        if existing:
            flash('Stock already in watchlist')
        else:
            watchlist_item = Watchlist(user_id=current_user.id, symbol=symbol, notes=notes)
            db.session.add(watchlist_item)
            db.session.commit()
            flash(f'{symbol} added to watchlist')
        
        return redirect(url_for('watchlist'))
    
    watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
    return render_template('watchlist.html', watchlist_items=watchlist_items)

@app.route('/remove_from_watchlist/<int:item_id>')
@login_required
def remove_from_watchlist(item_id):
    item = Watchlist.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Removed from watchlist')
    return redirect(url_for('watchlist'))

@app.route('/market_overview')
def market_overview():
    market_overview = get_market_overview()
    sector_performance = get_sector_performance()
    market_news = get_market_news()
    return render_template('market_overview.html',
                         market_overview=market_overview,
                         sector_performance=sector_performance,
                         market_news=market_news)

@app.route('/stock_analysis/<symbol>')
@login_required
def stock_analysis(symbol):
    data, info = get_stock_data(symbol, '1y')
    if data is None:
        flash('Unable to fetch data for this symbol')
        return redirect(url_for('dashboard'))
    
    # Add technical indicators
    data = add_technical_indicators(data)
    
    # Get latest technical indicators
    latest_indicators = {}
    for col in ['SMA_20', 'SMA_50', 'RSI', 'MACD', 'BB_upper', 'BB_lower']:
        if col in data.columns:
            latest_indicators[col] = float(data[col].iloc[-1])
    
    # Get sentiment
    sentiment_score = get_market_sentiment(symbol)
    
    return render_template('stock_analysis.html',
                         symbol=symbol,
                         info=info,
                         indicators=latest_indicators,
                         sentiment_score=sentiment_score)

@app.route('/api/stock/<symbol>')
def get_stock_info(symbol):
    """Enhanced API endpoint to get stock information"""
    try:
        data, info = get_stock_data(symbol, '1mo')
        if data is None:
            return jsonify({'error': 'Unable to fetch data'}), 400
        
        # Add technical indicators
        data = add_technical_indicators(data)
        
        # Get latest indicators
        latest_indicators = {}
        for col in ['SMA_20', 'RSI', 'MACD']:
            if col in data.columns:
                latest_indicators[col] = float(data[col].iloc[-1])
        
        # Get sentiment
        sentiment_score = get_market_sentiment(symbol)
        
        return jsonify({
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'current_price': info.get('currentPrice', data['Close'].iloc[-1]),
            'previous_close': info.get('previousClose', 0),
            'market_cap': info.get('marketCap', 0),
            'volume': info.get('volume', 0),
            'sector': info.get('sector', 'Unknown'),
            'indicators': latest_indicators,
            'sentiment_score': sentiment_score,
            'history': data['Close'].tolist()[-30:] if len(data) > 0 else []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/market-data')
def api_market_data():
    """Enhanced API endpoint for real-time market data"""
    market_overview = get_market_overview()
    return jsonify(market_overview)

@app.route('/api/sentiment/<symbol>')
def api_sentiment(symbol):
    """API endpoint for sentiment analysis"""
    try:
        sentiment_score = get_market_sentiment(symbol)
        return jsonify({
            'symbol': symbol,
            'sentiment_score': sentiment_score,
            'sentiment_label': 'Positive' if sentiment_score > 0.1 else 'Negative' if sentiment_score < -0.1 else 'Neutral'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        preferences = {
            'theme': request.form.get('theme', 'light'),
            'default_prediction_days': int(request.form.get('default_prediction_days', 30)),
            'auto_refresh': request.form.get('auto_refresh') == 'on',
            'email_notifications': request.form.get('email_notifications') == 'on',
            'watchlist_alerts': request.form.get('watchlist_alerts') == 'on'
        }
        
        current_user.preferences = json.dumps(preferences)
        db.session.commit()
        flash('Settings updated successfully')
        return redirect(url_for('settings'))
    
    preferences = {}
    if current_user.preferences:
        try:
            preferences = json.loads(current_user.preferences)
        except:
            preferences = {}
    
    return render_template('settings.html', preferences=preferences)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

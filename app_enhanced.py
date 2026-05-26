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
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import json
import ta
from textblob import TextBlob
import nltk
from bs4 import BeautifulSoup
import plotly.graph_objs as go
import plotly.utils
from newsapi import NewsApiClient
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
try:
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
except:
    SentimentIntensityAnalyzer = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_prediction.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer() if SentimentIntensityAnalyzer else None

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

class MarketNews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10))
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text)
    sentiment_score = db.Column(db.Float)
    published_date = db.Column(db.DateTime)
    source = db.Column(db.String(100))
    url = db.Column(db.String(500))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Enhanced Stock Data Functions
def get_comprehensive_stock_data(symbol, period='1y'):
    """Fetch comprehensive stock data using yfinance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        info = stock.info
        
        if data.empty:
            return None, None
            
        # Add technical indicators
        data = add_technical_indicators(data)
        
        return data, info
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None, None

def add_technical_indicators(data):
    """Add comprehensive technical indicators to stock data"""
    try:
        # Moving Averages
        data['SMA_5'] = ta.trend.sma_indicator(data['Close'], window=5)
        data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
        data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
        data['EMA_12'] = ta.trend.ema_indicator(data['Close'], window=12)
        data['EMA_26'] = ta.trend.ema_indicator(data['Close'], window=26)
        
        # MACD
        data['MACD'] = ta.trend.macd(data['Close'])
        data['MACD_signal'] = ta.trend.macd_signal(data['Close'])
        data['MACD_histogram'] = ta.trend.macd_diff(data['Close'])
        
        # RSI
        data['RSI'] = ta.momentum.rsi(data['Close'])
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(data['Close'])
        data['BB_upper'] = bollinger.bollinger_hband()
        data['BB_middle'] = bollinger.bollinger_mavg()
        data['BB_lower'] = bollinger.bollinger_lband()
        data['BB_width'] = bollinger.bollinger_wband()
        
        # Stochastic Oscillator
        data['Stoch_K'] = ta.momentum.stoch(data['High'], data['Low'], data['Close'])
        data['Stoch_D'] = ta.momentum.stoch_signal(data['High'], data['Low'], data['Close'])
        
        # Williams %R
        data['Williams_R'] = ta.momentum.williams_r(data['High'], data['Low'], data['Close'])
        
        # Volume indicators
        data['Volume_SMA'] = ta.volume.volume_sma(data['Close'], data['Volume'])
        data['Volume_ratio'] = data['Volume'] / data['Volume_SMA']
        
        # Price change indicators
        data['Price_Change'] = data['Close'].pct_change()
        data['Volume_Change'] = data['Volume'].pct_change()
        
        # Volatility
        data['Volatility'] = data['Close'].rolling(window=20).std()
        
        return data
    except Exception as e:
        print(f"Error adding technical indicators: {e}")
        return data

def get_market_sentiment(symbol):
    """Get market sentiment for a stock symbol"""
    try:
        # Get news from Yahoo Finance
        stock = yf.Ticker(symbol)
        news = stock.news
        
        if not news:
            return 0.0
        
        sentiment_scores = []
        for article in news[:10]:  # Analyze top 10 news articles
            title = article.get('title', '')
            summary = article.get('summary', '')
            text = f"{title} {summary}"
            
            if sia:
                scores = sia.polarity_scores(text)
                sentiment_scores.append(scores['compound'])
            else:
                blob = TextBlob(text)
                sentiment_scores.append(blob.sentiment.polarity)
        
        return np.mean(sentiment_scores) if sentiment_scores else 0.0
    except Exception as e:
        print(f"Error getting sentiment for {symbol}: {e}")
        return 0.0

def enhanced_predict_stock_price(symbol, days_ahead=30):
    """Enhanced prediction using multiple models and features"""
    try:
        # Get comprehensive data
        data, info = get_comprehensive_stock_data(symbol, '2y')
        if data is None or len(data) < 30:
            return None, None, None, None
        
        # Remove NaN values
        data = data.dropna()
        
        if len(data) < 30:
            return None, None, None, None
        
        # Get market sentiment
        sentiment_score = get_market_sentiment(symbol)
        
        # Prepare features for prediction
        feature_columns = [
            'Open', 'High', 'Low', 'Volume', 'SMA_5', 'SMA_20', 'SMA_50',
            'EMA_12', 'EMA_26', 'MACD', 'MACD_signal', 'RSI', 'Stoch_K',
            'Williams_R', 'BB_width', 'Volume_ratio', 'Price_Change',
            'Volume_Change', 'Volatility'
        ]
        
        # Ensure all feature columns exist
        available_features = [col for col in feature_columns if col in data.columns]
        X = data[available_features].values[:-1]
        y = data['Close'].values[1:]
        
        if len(X) == 0:
            return None, None, None, None
        
        # Train multiple models
        models = {
            'linear_regression': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        
        predictions = {}
        confidences = {}
        
        for model_name, model in models.items():
            try:
                model.fit(X, y)
                last_features = data[available_features].values[-1:]
                predicted_price = model.predict(last_features)[0]
                confidence = model.score(X, y)
                
                predictions[model_name] = predicted_price
                confidences[model_name] = confidence
            except Exception as e:
                print(f"Error with {model_name}: {e}")
                continue
        
        if not predictions:
            return None, None, None, None
        
        # Use ensemble prediction (weighted average)
        total_confidence = sum(confidences.values())
        if total_confidence > 0:
            weighted_prediction = sum(
                predictions[model] * confidences[model] 
                for model in predictions
            ) / total_confidence
            avg_confidence = total_confidence / len(confidences)
        else:
            weighted_prediction = sum(predictions.values()) / len(predictions)
            avg_confidence = 0.5
        
        # Adjust prediction based on sentiment
        sentiment_adjustment = sentiment_score * 0.02  # 2% adjustment based on sentiment
        final_prediction = weighted_prediction * (1 + sentiment_adjustment)
        
        current_price = data['Close'].iloc[-1]
        
        # For multiple days ahead, use recursive prediction with sentiment
        if days_ahead > 1:
            daily_change = (final_prediction - current_price) / 1
            sentiment_daily_impact = sentiment_score * 0.001  # 0.1% daily impact
            final_prediction = current_price + (daily_change + sentiment_daily_impact) * days_ahead
        
        # Get technical indicators for the latest data point
        latest_indicators = {}
        for col in available_features:
            if col in data.columns:
                latest_indicators[col] = float(data[col].iloc[-1])
        
        return current_price, final_prediction, avg_confidence, latest_indicators
        
    except Exception as e:
        print(f"Error in enhanced prediction: {e}")
        return None, None, None, None

def get_market_overview():
    """Get comprehensive market overview with indices and sectors"""
    try:
        # Major indices
        indices = ['^GSPC', '^DJI', '^IXIC', '^RUT']  # S&P 500, Dow Jones, NASDAQ, Russell 2000
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
        popular_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'JPM', 'JNJ']
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
            'XLRE': 'Real Estate',
            'XLC': 'Communication'
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
        # This would typically use a news API, but for demo purposes, we'll simulate
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

def create_stock_chart(symbol, period='6mo'):
    """Create interactive stock chart with technical indicators"""
    try:
        data, info = get_comprehensive_stock_data(symbol, period)
        if data is None or data.empty:
            return None
        
        # Create candlestick chart
        fig = go.Figure()
        
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=symbol
        ))
        
        # Moving averages
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['SMA_20'],
            mode='lines',
            name='SMA 20',
            line=dict(color='orange', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['SMA_50'],
            mode='lines',
            name='SMA 50',
            line=dict(color='blue', width=1)
        ))
        
        # Bollinger Bands
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['BB_upper'],
            mode='lines',
            name='BB Upper',
            line=dict(color='gray', width=1, dash='dash'),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['BB_lower'],
            mode='lines',
            name='BB Lower',
            line=dict(color='gray', width=1, dash='dash'),
            fill='tonexty',
            fillcolor='rgba(128,128,128,0.1)'
        ))
        
        fig.update_layout(
            title=f'{symbol} Stock Price with Technical Indicators',
            xaxis_title='Date',
            yaxis_title='Price',
            template='plotly_white',
            height=500
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        print(f"Error creating chart for {symbol}: {e}")
        return None

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
        
        if prediction_type == 'enhanced':
            current_price, predicted_price, confidence, indicators = enhanced_predict_stock_price(symbol, days_ahead)
        else:
            current_price, predicted_price, confidence = predict_stock_price_simple(symbol, days_ahead)
            indicators = {}
        
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
            
            # Get stock chart
            chart_json = create_stock_chart(symbol)
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2),
                'confidence': round(confidence * 100, 2),
                'target_date': target_date.strftime('%Y-%m-%d'),
                'indicators': indicators,
                'chart': chart_json
            })
        else:
            return jsonify({'success': False, 'error': 'Unable to predict price for this symbol'})
    
    return render_template('predict.html')

def predict_stock_price_simple(symbol, days_ahead=30):
    """Simple linear regression model for stock price prediction"""
    try:
        data, info = get_comprehensive_stock_data(symbol, '2y')
        if data is None or len(data) < 30:
            return None, None, None
        
        # Prepare features
        data['SMA_5'] = data['Close'].rolling(window=5).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['RSI'] = ta.momentum.rsi(data['Close'])
        data['Price_Change'] = data['Close'].pct_change()
        data['Volume_Change'] = data['Volume'].pct_change()
        
        # Remove NaN values
        data = data.dropna()
        
        if len(data) < 30:
            return None, None, None
        
        # Features for prediction
        features = ['Open', 'High', 'Low', 'Volume', 'SMA_5', 'SMA_20', 'RSI', 'Price_Change', 'Volume_Change']
        X = data[features].values[:-1]
        y = data['Close'].values[1:]
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next day
        last_features = data[features].values[-1:]
        predicted_price = model.predict(last_features)[0]
        
        # Calculate confidence
        confidence = model.score(X, y)
        
        current_price = data['Close'].iloc[-1]
        
        if days_ahead > 1:
            avg_daily_change = (predicted_price - current_price) / 1
            predicted_price = current_price + (avg_daily_change * days_ahead)
        
        return current_price, predicted_price, confidence
        
    except Exception as e:
        print(f"Error in simple prediction: {e}")
        return None, None, None

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
    data, info = get_comprehensive_stock_data(symbol, '1y')
    if data is None:
        flash('Unable to fetch data for this symbol')
        return redirect(url_for('dashboard'))
    
    # Get latest technical indicators
    latest_indicators = {}
    for col in data.columns:
        if col in ['SMA_5', 'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26', 'MACD', 'RSI', 'Stoch_K', 'Williams_R']:
            latest_indicators[col] = float(data[col].iloc[-1])
    
    # Get sentiment
    sentiment_score = get_market_sentiment(symbol)
    
    # Create chart
    chart_json = create_stock_chart(symbol)
    
    return render_template('stock_analysis.html',
                         symbol=symbol,
                         info=info,
                         indicators=latest_indicators,
                         sentiment_score=sentiment_score,
                         chart=chart_json)

@app.route('/api/stock/<symbol>')
def get_stock_info(symbol):
    """Enhanced API endpoint to get stock information"""
    try:
        data, info = get_comprehensive_stock_data(symbol, '1mo')
        if data is None:
            return jsonify({'error': 'Unable to fetch data'}), 400
        
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

@app.route('/api/technical-indicators/<symbol>')
def api_technical_indicators(symbol):
    """API endpoint for technical indicators"""
    try:
        data, info = get_comprehensive_stock_data(symbol, '6mo')
        if data is None:
            return jsonify({'error': 'Unable to fetch data'}), 400
        
        latest_indicators = {}
        for col in data.columns:
            if col not in ['Open', 'High', 'Low', 'Close', 'Volume']:
                latest_indicators[col] = float(data[col].iloc[-1])
        
        return jsonify({
            'symbol': symbol,
            'indicators': latest_indicators
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

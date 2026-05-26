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

def predict_stock_price(symbol, days_ahead=30):
    """Simple prediction using moving averages"""
    try:
        data, info = get_stock_data(symbol, '2y')
        if data is None or len(data) < 30:
            return None, None, None
        
        # Calculate moving averages
        data['SMA_5'] = calculate_sma(data['Close'], 5)
        data['SMA_20'] = calculate_sma(data['Close'], 20)
        data['RSI'] = calculate_rsi(data['Close'])
        data['Price_Change'] = data['Close'].pct_change()
        
        # Remove NaN values
        data = data.dropna()
        
        if len(data) < 30:
            return None, None, None
        
        # Simple prediction logic
        current_price = data['Close'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        recent_trend = (data['Close'].iloc[-5:].mean() - data['Close'].iloc[-10:-5].mean()) / data['Close'].iloc[-10:-5].mean()
        
        # Predict based on trend
        predicted_price = current_price * (1 + recent_trend * 0.5)
        
        # Calculate confidence
        confidence = 0.6 + min(abs(recent_trend) * 10, 0.3)
        
        return current_price, predicted_price, confidence
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None, None, None

def get_market_data():
    """Get real-time market data for popular stocks"""
    popular_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
    market_data = []
    
    for symbol in popular_stocks:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            current_price = info.get('currentPrice', 0)
            previous_close = info.get('previousClose', 0)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            market_data.append({
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'price': current_price,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'volume': info.get('volume', 0)
            })
        except:
            continue
    
    return market_data

# Routes
@app.route('/')
def index():
    market_data = get_market_data()
    return render_template('index.html', market_data=market_data)

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
    today = datetime.now().date()
    return render_template('dashboard.html', predictions=predictions, today=today)

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        days_ahead = int(request.form['days_ahead'])
        
        current_price, predicted_price, confidence = predict_stock_price(symbol, days_ahead)
        
        if current_price is not None:
            target_date = datetime.now().date() + timedelta(days=days_ahead)
            
            prediction = Prediction(
                user_id=current_user.id,
                symbol=symbol,
                current_price=current_price,
                predicted_price=predicted_price,
                confidence=confidence,
                target_date=target_date
            )
            db.session.add(prediction)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2),
                'confidence': round(confidence * 100, 2),
                'target_date': target_date.strftime('%Y-%m-%d')
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

# Enhanced Features
@app.route('/market_overview')
@login_required
def market_overview():
    """Enhanced market overview with sector analysis"""
    try:
        # Get popular stocks for overview
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
        market_data = []
        
        for symbol in symbols:
            try:
                data = get_stock_data(symbol, period='1d')
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
                    change = current_price - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
                    
                    market_data.append({
                        'symbol': symbol,
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2)
                    })
            except:
                continue
        
        return render_template('market_overview.html', market_data=market_data)
    except Exception as e:
        flash('Error loading market data')
        return redirect(url_for('index'))


@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('settings.html')

@app.route('/portfolio')
@login_required
def portfolio():
    """User portfolio tracking"""
    # Get user's predictions as portfolio entries
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).all()
    return render_template('portfolio.html', predictions=predictions)

@app.route('/alerts')
@login_required
def alerts():
    """Price alerts management"""
    return render_template('alerts.html')

@app.route('/news')
def news():
    """Market news section"""
    return render_template('news.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form and information"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        # In a real app, you would save this to database or send email
        flash('Thank you for your message! We will get back to you soon.')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    """User feedback form"""
    if request.method == 'POST':
        rating = request.form['rating']
        feedback_text = request.form['feedback']
        category = request.form['category']
        
        # In a real app, you would save this to database
        flash('Thank you for your feedback! Your input helps us improve.')
        return redirect(url_for('feedback'))
    
    return render_template('feedback.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/help')
def help():
    """Help and support page"""
    return render_template('help.html')

@app.route('/api/portfolio-performance')
@login_required
def portfolio_performance():
    """API endpoint for portfolio performance data"""
    try:
        predictions = Prediction.query.filter_by(user_id=current_user.id).all()
        performance_data = []
        
        for prediction in predictions:
            try:
                current_data = get_stock_data(prediction.symbol, period='1d')
                if not current_data.empty:
                    current_price = current_data['Close'].iloc[-1]
                    predicted_price = prediction.predicted_price
                    accuracy = ((predicted_price - current_price) / current_price) * 100
                    
                    performance_data.append({
                        'symbol': prediction.symbol,
                        'predicted_price': predicted_price,
                        'current_price': current_price,
                        'accuracy': round(abs(accuracy), 2),
                        'direction': 'bullish' if predicted_price > current_price else 'bearish'
                    })
            except:
                continue
        
        return jsonify(performance_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<symbol>')
def get_stock_info(symbol):
    """API endpoint to get stock information"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        history = stock.history(period='1mo')
        
        return jsonify({
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'current_price': info.get('currentPrice', 0),
            'previous_close': info.get('previousClose', 0),
            'market_cap': info.get('marketCap', 0),
            'volume': info.get('volume', 0),
            'history': history['Close'].tolist()[-30:] if len(history) > 0 else []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/market-data')
def api_market_data():
    """API endpoint for real-time market data"""
    market_data = get_market_data()
    return jsonify(market_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
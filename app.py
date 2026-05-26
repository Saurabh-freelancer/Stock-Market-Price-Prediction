from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///stock_prediction.db')
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
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    theme_preference = db.Column(db.String(20), nullable=False, default='light')
    predictions = db.relationship('Prediction', backref='user', lazy=True)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    predicted_price = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    prediction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    target_date = db.Column(db.Date, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def ensure_user_schema():
    """Add new columns to SQLite `user` table if missing (safe for existing DBs)."""
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if 'user' not in tables:
            return
        cols = {c['name'] for c in inspector.get_columns('user')}
        with db.engine.begin() as conn:
            if 'created_at' not in cols:
                conn.execute(text('ALTER TABLE user ADD COLUMN created_at DATETIME'))
                conn.execute(text("UPDATE user SET created_at = datetime('now') WHERE created_at IS NULL"))
            if 'theme_preference' not in cols:
                conn.execute(text("ALTER TABLE user ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'light'"))
                conn.execute(text("UPDATE user SET theme_preference = 'light' WHERE theme_preference IS NULL"))
    except Exception as e:
        print(f"Schema migration note: {e}")


@app.context_processor
def inject_globals():
    theme = 'light'
    if current_user.is_authenticated:
        theme = getattr(current_user, 'theme_preference', None) or 'light'
    return {'user_theme': theme}


# Stock Data Functions
def get_stock_data(symbol, period='1y'):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def predict_stock_price(symbol, days_ahead=30):
    """Simple linear regression model for stock price prediction"""
    try:
        # Get historical data
        data = get_stock_data(symbol, '2y')
        if data is None or len(data) < 30:
            return None, None, None
        
        # Prepare features
        data['SMA_5'] = data['Close'].rolling(window=5).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['RSI'] = calculate_rsi(data['Close'])
        data['Price_Change'] = data['Close'].pct_change()
        data['Volume_Change'] = data['Volume'].pct_change()
        
        # Remove NaN values
        data = data.dropna()
        
        if len(data) < 30:
            return None, None, None
        
        # Features for prediction
        features = ['Open', 'High', 'Low', 'Volume', 'SMA_5', 'SMA_20', 'RSI', 'Price_Change', 'Volume_Change']
        X = data[features].values[:-1]  # All but last day
        y = data['Close'].values[1:]    # Next day's close price
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next day
        last_features = data[features].values[-1:]
        predicted_price = model.predict(last_features)[0]
        
        # Calculate confidence (R-squared score)
        confidence = model.score(X, y)
        
        # For multiple days ahead, use recursive prediction
        current_price = data['Close'].iloc[-1]
        future_price = predicted_price
        
        # Simple extrapolation for multiple days
        if days_ahead > 1:
            avg_daily_change = (predicted_price - current_price) / 1
            future_price = current_price + (avg_daily_change * days_ahead)
        
        return current_price, future_price, confidence
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None, None, None

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

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
    total_predictions = Prediction.query.filter_by(user_id=current_user.id).count()
    today = datetime.now().date()
    return render_template(
        'dashboard.html',
        predictions=predictions,
        today=today,
        total_predictions=total_predictions,
    )


@app.route('/history')
@login_required
def prediction_history():
    """Full prediction history for the logged-in user (paginated)."""
    page = request.args.get('page', 1, type=int)
    per_page = min(max(request.args.get('per_page', 25, type=int), 5), 100)
    pagination = (
        Prediction.query.filter_by(user_id=current_user.id)
        .order_by(Prediction.prediction_date.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    today = datetime.now().date()
    return render_template('history.html', pagination=pagination, today=today)

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


@app.route('/api/predictions/<int:pred_id>/delete', methods=['DELETE', 'POST'])
@login_required
def api_delete_prediction(pred_id):
    """Delete a prediction (must belong to current user)."""
    pred = Prediction.query.filter_by(id=pred_id, user_id=current_user.id).first()
    if not pred:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    db.session.delete(pred)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/predictions/export')
@login_required
def api_export_predictions():
    """Export user's predictions as CSV."""
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.prediction_date.desc()).all()
    lines = ['Symbol,Current Price,Predicted Price,Confidence %,Prediction Date,Target Date']
    for p in predictions:
        lines.append(f'{p.symbol},{p.current_price},{p.predicted_price},{p.confidence * 100},{p.prediction_date.strftime("%Y-%m-%d %H:%M")},{p.target_date}')
    from flask import Response
    return Response('\n'.join(lines), mimetype='text/csv', headers={
        'Content-Disposition': f'attachment; filename=predictions_{current_user.username}.csv'
    })


@app.route('/api/user/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change user password."""
    data = request.get_json(silent=True) or {}
    current = data.get('current') or ''
    new_pw = data.get('new') or ''
    if not current or not new_pw:
        return jsonify({'success': False, 'error': 'Missing fields'})
    if len(new_pw) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'})
    if not check_password_hash(current_user.password_hash, current):
        return jsonify({'success': False, 'error': 'Current password is incorrect'})
    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/user/theme', methods=['POST'])
@login_required
def api_save_user_theme():
    """Persist theme choice (light / dark / system) for logged-in users."""
    data = request.get_json(silent=True) or {}
    theme = (data.get('theme') or 'light').lower()
    if theme not in ('light', 'dark', 'system'):
        theme = 'light'
    current_user.theme_preference = theme
    db.session.commit()
    return jsonify({'success': True, 'theme': theme})


@app.route('/market-overview')
def market_overview():
    stocks = get_market_data()
    indices = [
        {'symbol': '^GSPC', 'name': 'S&P 500', 'price': 0, 'change': 0, 'change_percent': 0},
        {'symbol': '^DJI', 'name': 'Dow Jones', 'price': 0, 'change': 0, 'change_percent': 0},
        {'symbol': '^IXIC', 'name': 'NASDAQ', 'price': 0, 'change': 0, 'change_percent': 0},
        {'symbol': '^RUT', 'name': 'Russell 2000', 'price': 0, 'change': 0, 'change_percent': 0},
    ]

    # Try to fetch live index data; keep safe defaults if unavailable.
    for index in indices:
        try:
            info = yf.Ticker(index['symbol']).info
            price = info.get('regularMarketPrice') or info.get('currentPrice') or 0
            previous = info.get('regularMarketPreviousClose') or info.get('previousClose') or 0
            change = (price - previous) if previous else 0
            change_percent = ((change / previous) * 100) if previous else 0
            index['price'] = float(price or 0)
            index['change'] = round(change, 2)
            index['change_percent'] = round(change_percent, 2)
        except Exception:
            continue

    for stock in stocks:
        stock.setdefault('market_cap', 0)
        stock.setdefault('sector', 'Technology')

    sector_performance = [
        {'sector': 'Technology', 'etf': 'XLK', 'price': 0, 'change': 0, 'change_percent': 0},
        {'sector': 'Financials', 'etf': 'XLF', 'price': 0, 'change': 0, 'change_percent': 0},
        {'sector': 'Healthcare', 'etf': 'XLV', 'price': 0, 'change': 0, 'change_percent': 0},
    ]

    market_news = [
        {
            'title': 'US markets remain active amid mixed sentiment',
            'summary': 'Major indices are seeing moderate volatility as investors track earnings and macro data.',
            'source': 'Market Desk',
            'impact': 'Medium',
            'sentiment': 0.1,
            'published_date': datetime.now(),
        },
        {
            'title': 'Technology stocks continue to attract volume',
            'summary': 'Large-cap tech names lead intraday activity with strong participation.',
            'source': 'Finance Wire',
            'impact': 'High',
            'sentiment': 0.25,
            'published_date': datetime.now(),
        },
    ]

    return render_template(
        'market_overview.html',
        market_overview={'indices': indices, 'stocks': stocks},
        sector_performance=sector_performance,
        market_news=market_news,
    )


@app.route('/news')
def news():
    return render_template('news.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Thank you! Your message has been received.')
        return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        flash('Thank you for your feedback!')
        return redirect(url_for('feedback'))
    return render_template('feedback.html')


@app.route('/alerts')
def alerts():
    return render_template('alerts.html')


@app.route('/watchlist', methods=['GET', 'POST'])
def watchlist():
    if request.method == 'POST':
        return jsonify({'success': True, 'message': 'Added to watchlist'})
    return render_template('watchlist.html')


@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        theme = request.form.get('theme', 'light')
        if theme not in ('light', 'dark', 'system'):
            theme = 'light'
        current_user.theme_preference = theme
        db.session.commit()
        flash('Settings saved successfully.')
        return redirect(url_for('settings'))

    # Backfill optional fields expected by the template.
    if not hasattr(current_user, 'watchlists'):
        current_user.watchlists = []
    if not hasattr(current_user, 'created_at'):
        current_user.created_at = datetime.utcnow()

    preferences = {
        'theme': getattr(current_user, 'theme_preference', None) or 'light',
        'default_prediction_days': 30,
        'auto_refresh': True,
        'email_notifications': True,
        'watchlist_alerts': True,
        'prediction_alerts': True,
        'risk_tolerance': 'moderate',
        'investment_style': 'mixed',
        'chart_type': 'candlestick',
        'timeframe': '1mo',
    }
    return render_template('settings.html', preferences=preferences)


@app.route('/owner')
def owner():
    return render_template('owner.html')

# Initialize database tables
with app.app_context():
    db.create_all()
    ensure_user_schema()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
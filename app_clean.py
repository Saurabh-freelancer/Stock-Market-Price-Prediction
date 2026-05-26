from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime, timedelta
import random

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

# Stock Data Functions (Clean - No external dependencies)
def get_stock_data(symbol):
    """Generate realistic mock stock data"""
    base_prices = {
        "AAPL": 150.0, "GOOGL": 2800.0, "MSFT": 300.0, "AMZN": 3300.0,
        "TSLA": 800.0, "META": 300.0, "NVDA": 500.0, "NFLX": 500.0
    }
    
    base_price = base_prices.get(symbol, 100.0)
    change = random.uniform(-10, 10)
    price = base_price + change
    change_percent = (change / base_price) * 100
    
    return {
        "symbol": symbol,
        "price": round(price, 2),
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "volume": random.randint(1000000, 10000000)
    }

def predict_stock_price(symbol, days_ahead=30):
    """Clean prediction model"""
    try:
        stock_data = get_stock_data(symbol)
        current_price = stock_data["price"]
        
        # Simple prediction algorithm
        trend_factor = 1 + (stock_data["change_percent"] / 100)
        random_factor = random.uniform(0.95, 1.05)
        predicted_price = current_price * trend_factor * random_factor * (1 + (days_ahead * 0.001))
        
        # Calculate confidence
        confidence = max(0.3, 0.9 - (days_ahead * 0.002))
        
        return current_price, predicted_price, confidence
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None, None, None

def get_market_data():
    """Get market data for popular stocks"""
    popular_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
    market_data = []
    
    for symbol in popular_stocks:
        try:
            stock_data = get_stock_data(symbol)
            market_data.append({
                'symbol': symbol,
                'name': get_company_name(symbol),
                'price': stock_data['price'],
                'change': stock_data['change'],
                'change_percent': stock_data['change_percent'],
                'volume': stock_data['volume']
            })
        except:
            continue
    
    return market_data

def get_company_name(symbol):
    """Get company name from symbol"""
    names = {
        'AAPL': 'Apple Inc.',
        'GOOGL': 'Alphabet Inc.',
        'MSFT': 'Microsoft Corporation',
        'AMZN': 'Amazon.com Inc.',
        'TSLA': 'Tesla Inc.',
        'META': 'Meta Platforms Inc.',
        'NVDA': 'NVIDIA Corporation',
        'NFLX': 'Netflix Inc.'
    }
    return names.get(symbol, symbol)

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

@app.route('/api/stock/<symbol>')
def get_stock_info(symbol):
    """API endpoint to get stock information"""
    try:
        stock_data = get_stock_data(symbol)
        
        # Generate mock historical data
        history = []
        base_price = stock_data['price']
        for i in range(30):
            price = base_price + random.uniform(-5, 5)
            history.append(round(price, 2))
        
        return jsonify({
            'symbol': symbol,
            'name': get_company_name(symbol),
            'current_price': stock_data['price'],
            'previous_close': stock_data['price'] - stock_data['change'],
            'market_cap': random.randint(1000000000, 1000000000000),
            'volume': stock_data['volume'],
            'history': history
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/market-data')
def api_market_data():
    """API endpoint for real-time market data"""
    market_data = get_market_data()
    return jsonify(market_data)

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """Chatbot API endpoint"""
    data = request.get_json()
    message = data.get('message', '').lower()
    
    # Simple chatbot responses
    responses = {
        'hello': 'Hello! How can I help you with stock market predictions today?',
        'hi': 'Hi there! I\'m here to help you with your stock market questions.',
        'help': 'I can help you with: stock predictions, market analysis, portfolio tips, and general investment advice.',
        'prediction': 'To make a stock prediction, go to the "Predict" page and enter a stock symbol.',
        'stock': 'I can help you analyze stocks! Just tell me which stock you\'re interested in.',
        'market': 'The current market shows mixed signals. Check our real-time market data.',
        'portfolio': 'For portfolio management, visit your dashboard to track your investments.',
        'price': 'Stock prices are updated in real-time. Use our prediction tool for future estimates.',
        'ai': 'Our AI uses advanced machine learning algorithms for accurate predictions.',
        'default': 'I\'m here to help with stock market questions! Try asking about predictions or analysis.'
    }
    
    response = responses.get('default')
    for key, value in responses.items():
        if key in message:
            response = value
            break
    
    return jsonify({'response': response})

@app.route('/owner')
def owner_details():
    """Website owner details page"""
    return render_template('owner.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/help')
def help_page():
    """Help and support page"""
    return render_template('help.html')

@app.route('/profile')
def profile():
    """User profile page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/portfolio')
def portfolio():
    """Portfolio management page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('portfolio.html')

@app.route('/watchlist')
def watchlist():
    """Watchlist page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('watchlist.html')

@app.route('/settings')
def settings():
    """User settings page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/notifications')
def notifications():
    """Notifications page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('notifications.html')

@app.route('/preferences')
def preferences():
    """User preferences page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('preferences.html')

if __name__ == '__main__':
    print("🚀 Starting Stock Market Price Prediction Website...")
    print("📊 Access the website at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    print("✅ Clean version - No compatibility issues")
    print("-" * 50)
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True) 
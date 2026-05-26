#!/usr/bin/env python3
"""
Stock Market Price Prediction Website (Simplified Version)
Startup script for the Flask application
"""

from app_simple import app, db

if __name__ == '__main__':
    print("🚀 Starting Stock Market Price Prediction Website (Simplified)...")
    print("📊 Access the website at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    print("📝 Note: This version uses mock data for demonstration")
    print("-" * 50)
    
    # Ensure database tables exist before starting
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=5000)
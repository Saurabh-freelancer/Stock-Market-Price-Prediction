#!/usr/bin/env python3
"""
Stock Market Price Prediction Website
Startup script for the Flask application
"""

from app import app

if __name__ == '__main__':
    print("🚀 Starting Stock Market Price Prediction Website...")
    print("📊 Access the website at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
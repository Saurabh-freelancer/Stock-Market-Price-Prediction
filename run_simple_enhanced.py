#!/usr/bin/env python3
"""
Simple Enhanced Stock Market Price Prediction Application
Run this script to start the application with core features.
"""

import os
import sys
from app_simple_enhanced import app, db

def main():
    """Main function to run the simple enhanced application"""
    print("🚀 Starting Simple Enhanced Stock Market Price Prediction Application...")
    print("=" * 70)
    
    # Check if database exists, if not create it
    if not os.path.exists('instance/stock_prediction.db'):
        print("📊 Creating database...")
        with app.app_context():
            db.create_all()
        print("✅ Database created successfully!")
    
    print("🔧 Features Available:")
    print("   • Yahoo Finance API integration")
    print("   • Technical indicators (RSI, MACD, Bollinger Bands)")
    print("   • Market sentiment analysis")
    print("   • Market overview with sector analysis")
    print("   • User personalization (watchlists, settings)")
    print("   • Interactive charts and modern UI")
    print("   • Stock price predictions")
    print("")
    
    print("🌐 Starting server...")
    print("   • Local: http://127.0.0.1:5000")
    print("   • Network: http://0.0.0.0:5000")
    print("")
    print("💡 Tips:")
    print("   • Register an account to access all features")
    print("   • Check market overview for real-time data")
    print("   • Add stocks to your watchlist for tracking")
    print("   • Explore technical indicators in stock analysis")
    print("")
    print("⚠️  Press Ctrl+C to stop the server")
    print("=" * 70)
    
    try:
        # Run the application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        print("👋 Thank you for using Stock Market Price Prediction!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements_simple.txt")
        sys.exit(1)

if __name__ == '__main__':
    main()

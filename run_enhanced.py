#!/usr/bin/env python3
"""
Enhanced Stock Market Price Prediction Application
Run this script to start the enhanced application with all new features.
"""

import os
import sys
from app_enhanced import app, db

def main():
    """Main function to run the enhanced application"""
    print("🚀 Starting Enhanced Stock Market Price Prediction Application...")
    print("=" * 60)
    
    # Check if database exists, if not create it
    if not os.path.exists('instance/stock_prediction.db'):
        print("📊 Creating database...")
        with app.app_context():
            db.create_all()
        print("✅ Database created successfully!")
    
    print("🔧 Features Available:")
    print("   • Enhanced Yahoo Finance API integration")
    print("   • Advanced technical indicators (MACD, RSI, Bollinger Bands)")
    print("   • News sentiment analysis")
    print("   • Market overview with sector analysis")
    print("   • User personalization (watchlists, settings)")
    print("   • Interactive charts and modern UI")
    print("   • Multiple prediction models")
    print("")
    
    print("🌐 Starting server...")
    print("   • Local: http://127.0.0.1:5000")
    print("   • Network: http://0.0.0.0:5000")
    print("")
    print("💡 Tips:")
    print("   • Use 'enhanced' prediction model for best results")
    print("   • Check market overview for real-time data")
    print("   • Add stocks to your watchlist for tracking")
    print("   • Explore technical indicators in stock analysis")
    print("")
    print("⚠️  Press Ctrl+C to stop the server")
    print("=" * 60)
    
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
        print("   pip install -r requirements.txt")
        sys.exit(1)

if __name__ == '__main__':
    main()

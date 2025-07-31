import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
COINGECKO_API = "https://api.coingecko.com/api/v3"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Crypto Analysis Bot Ready!\n"
        "Use /analyze <pair> (e.g. /analyze eth-usd) to get trend analysis"
    )

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("⚠️ Please specify a pair (e.g. /analyze btc-usd)")
            return
        
        pair = context.args[0].lower()
        # Handle pairs with or without dash
        if '-' in pair:
            symbol, currency = pair.split('-')
        else:
            symbol, currency = pair, 'usd'
        
        data = get_crypto_data(symbol, currency)
        if not data:
            await update.message.reply_text(f"❌ Failed to fetch market data for {symbol.upper()}/{currency.upper()}")
            return
        
        # Generate analysis prompt
        prompt = f"""
        As a professional crypto trading analyst, provide technical analysis for {symbol.upper()}/{currency.upper()} using:
        - Current price: ${data['current_price']}
        - 24h Change: {data['price_change_percentage_24h']}%
        - Market Cap: ${data['market_cap']/1e9:.2f}B
        - 24h Volume: ${data['total_volume']/1e6:.2f}M
        - 7-Day Price Movement: {data['price_change_percentage_7d_in_currency']}%
        
        Provide concise analysis covering:
        1. Current trend direction
        2. Key support/resistance levels
        3. Entry/exit strategy
        4. Risk management suggestions
        """
        
        analysis = get_deepseek_analysis(prompt)
        await update.message.reply_text(f"🔍 {symbol.upper()}/{currency.upper()} Analysis:\n\n{analysis}")
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

def get_crypto_data(symbol: str, currency: str):
    """Fetch market data from CoinGecko"""
    try:
        url = f"{COINGECKO_API}/coins/markets"
        params = {
            'vs_currency': currency,
            'ids': symbol,
            'price_change_percentage': '7d'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None
    except Exception as e:
        print(f"CoinGecko API error: {str(e)}")
        return None

def get_deepseek_analysis(prompt: str):
    """Get analysis from DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 600
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"DeepSeek API error: {str(e)}")
        return "⚠️ Analysis service is currently unavailable. Please try again later."

if __name__ == '__main__':
    # Create Bot Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    
    print("🤖 Starting bot with polling method...")
    app.run_polling()

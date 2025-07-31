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
        pair = context.args[0].lower() if context.args else None
        if not pair:
            await update.message.reply_text("⚠️ Please specify a pair (e.g. /analyze btc-usd)")
            return
        
        # Get crypto data
        symbol, currency = pair.split('-') if '-' in pair else (pair, 'usd')
        data = get_crypto_data(symbol, currency)
        
        if not data:
            await update.message.reply_text("❌ Failed to fetch market data")
            return
        
        # Generate analysis
        prompt = f"""
        Analyze the cryptocurrency trend for {symbol.upper()}/{currency.upper()} using this data:
        - Current price: ${data['current_price']}
        - 24h Change: {data['price_change_percentage_24h']}%
        - Market Cap: ${data['market_cap']/1e9:.2f}B
        - 24h Volume: ${data['total_volume']/1e6:.2f}M
        - 7-Day Price Movement: {data['7d_price_change']}%
        
        Provide:
        1. Trend analysis (1-2 sentences)
        2. Key support/resistance levels
        3. Entry/exit strategy suggestions
        4. Risk assessment
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
        response = requests.get(url, params=params)
        data = response.json()
        return data[0] if data else None
    except:
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
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.ai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        return response.json()['choices'][0]['message']['content']
    except:
        return "DeepSeek API currently unavailable. Please try later."

if __name__ == '__main__':
    # Create Bot Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    
    # Start Polling
    print("🤖 Bot is running...")
    app.run_polling()
"""
Test script to check Telegram bot connection
"""
import sys
import io

# Fix encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from bot.config import TELEGRAM_BOT_TOKEN
from telegram import Bot
from telegram.request import HTTPXRequest
from bot.config import PROXY_URL
import asyncio

async def test_connection():
    """Test if bot can connect to Telegram"""
    try:
        print("[TEST] Testing Telegram connection...")
        print(f"[TEST] Token: {TELEGRAM_BOT_TOKEN[:10]}...")
        
        # Create bot instance
        request = None
        if PROXY_URL:
            print(f"[TEST] Using proxy: {PROXY_URL}")
            request = HTTPXRequest(proxy=PROXY_URL, connect_timeout=10.0, read_timeout=10.0)
        else:
            print("[TEST] No proxy configured")
            request = HTTPXRequest(connect_timeout=10.0, read_timeout=10.0)
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN, request=request)
        
        # Try to get bot info
        print("[TEST] Getting bot information...")
        bot_info = await bot.get_me()
        
        print(f"[SUCCESS] Bot connected successfully!")
        print(f"[INFO] Bot username: @{bot_info.username}")
        print(f"[INFO] Bot name: {bot_info.first_name}")
        print(f"[INFO] Bot ID: {bot_info.id}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Connection failed: {str(e)}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)


"""
Main entry point for Telegram Bot
This is the main file that starts the bot
"""

import sys
import io

# Fix encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from bot.telegram_bot import TelegramBot


def main():
    """Main function to start the bot"""
    try:
        print("[START] Starting Telegram bot...")
        bot = TelegramBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n[STOP] Bot stopped by user.")
    except Exception as e:
        print(f"[ERROR] Bot error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

"""
Telegram Bot Module
Handles Telegram bot interactions and message processing
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from .config import TELEGRAM_BOT_TOKEN, MAX_MESSAGE_LENGTH, PROXY_URL
from .interview import InterviewAgent


class TelegramBot:
    """Telegram Bot Handler"""
    
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.interview_agent = InterviewAgent()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - Start interview"""
        user_id = update.effective_user.id
        
        # Reset any existing interview
        self.interview_agent.reset_interview(user_id)
        
        # Start new interview
        welcome_message = self.interview_agent.start_interview(user_id)
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "📚 راهنمای استفاده:\n\n"
            "/start - شروع مجدد ربات 😊\n"
            "/help - نمایش این راهنما 📖\n"
            "/clear - پاک کردن تاریخچه گفتگو 🗑️\n\n"
            "فقط پیامت رو بفرست تا من جواب بدم! همیشه اینجام! 😄✨"
        )
        await update.message.reply_text(help_message)
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command to reset conversation history"""
        user_id = update.effective_user.id
        # Reset interview for the user
        self.interview_agent.reset_interview(user_id)
        await update.message.reply_text("✅ عالی! تاریخچه گفتگو پاک شد! 😊\n\nاگه می‌خوای دوباره شروع کنیم، /start رو بزن! 🎉")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages - Interview flow"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        try:
            # Show typing indicator
            try:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action="typing"
                )
            except Exception as e:
                # If typing indicator fails, continue anyway
                print(f"[WARNING] Could not send typing indicator: {str(e)}")
            
            # Process with interview agent
            result = self.interview_agent.process_response(user_id, user_message)
            
            # Send response
            bot_message = result["message"]
            
            # Split long messages if necessary
            if len(bot_message) > MAX_MESSAGE_LENGTH:
                chunks = [
                    bot_message[i:i + MAX_MESSAGE_LENGTH]
                    for i in range(0, len(bot_message), MAX_MESSAGE_LENGTH)
                ]
                for chunk in chunks:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(bot_message)
            
            # If interview is complete, save result (optional - you can add logging/saving here)
            if result["is_complete"] and result["result"]:
                # You can save the result to a file or database here
                import json
                result_json = json.dumps(result["result"], ensure_ascii=False, indent=2)
                print(f"\n[INTERVIEW COMPLETE] User {user_id}:")
                print(result_json)
        
        except Exception as e:
            # Handle errors gracefully
            error_msg = f"⚠️ اووه! متاسفم، یه مشکلی پیش اومد! 😅\n\nنگران نباش! لطفاً دوباره تلاش کن! من اینجام تا کمکت کنم! 😊✨"
            try:
                await update.message.reply_text(error_msg)
            except:
                pass
            print(f"[ERROR] Error handling message: {str(e)}")
    
    def run(self):
        """Start the Telegram bot"""
        try:
            # Create application with optional proxy
            print("[BOT] Initializing bot...")
            
            # Configure request with optional proxy
            request = None
            if PROXY_URL:
                print(f"[BOT] Using proxy: {PROXY_URL}")
                request = HTTPXRequest(proxy=PROXY_URL, connect_timeout=30.0, read_timeout=30.0)
            else:
                request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
            
            application = Application.builder().token(self.token).request(request).build()
            
            # Add command handlers
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("clear", self.clear_command))
            
            # Add message handler (must be last)
            application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            )
            
            # Add error handler
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                """Handle errors"""
                error = context.error
                print(f"[ERROR] Update {update} caused error {error}")
                
                # Check if it's a network error
                from telegram.error import NetworkError
                if isinstance(error, NetworkError):
                    print("[ERROR] Network error - Check VPN/Internet connection")
                    print("[ERROR] If VPN is disconnected, please reconnect and restart the bot")
            
            application.add_error_handler(error_handler)
            
            # Start the bot
            print("[BOT] Bot is running...")
            print("[BOT] Waiting for messages...")
            print("[BOT] You can send /start to the bot now!")
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False,
                stop_signals=None  # Prevent signal handling issues
            )
        except Exception as e:
            print(f"[ERROR] Failed to start bot: {str(e)}")
            print(f"[ERROR] Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise


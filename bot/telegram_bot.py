"""
Telegram Bot Module
Handles Telegram bot interactions and message processing
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from .config import TELEGRAM_BOT_TOKEN, MAX_MESSAGE_LENGTH, PROXY_URL
from .interview import InterviewAgent, LearningAnalyst


class TelegramBot:
    """Telegram Bot Handler"""
    
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.interview_agent = InterviewAgent()
        self.learning_analyst = LearningAnalyst()
        self.admin_id = 5184305178  # Admin Telegram ID
    
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
            
            # If interview is complete, analyze and send report to admin
            if result["is_complete"] and result["result"]:
                # Save result for logging
                import json
                result_json = json.dumps(result["result"], ensure_ascii=False, indent=2)
                print(f"\n[INTERVIEW COMPLETE] User {user_id}:")
                print(result_json)
                
                # Analyze with Learning Analyst Agent
                try:
                    await context.bot.send_chat_action(
                        chat_id=update.effective_chat.id,
                        action="typing"
                    )
                    
                    # Save interview file
                    filepath = self.learning_analyst.save_interview_file(result["result"], user_id)
                    
                    # Generate comprehensive report
                    report = self.learning_analyst.analyze_interview(result["result"])
                    
                    # Send report to admin with download button
                    await self._send_report_to_admin(context, result["result"], report, user_id, filepath)
                    
                except Exception as e:
                    print(f"[ERROR] Failed to analyze interview or send report: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
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
            
            # Add callback query handler for download button
            application.add_handler(CallbackQueryHandler(self.handle_download_callback))
            
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
    
    async def _send_report_to_admin(self, context: ContextTypes.DEFAULT_TYPE, interview_data: dict, report: str, user_id: int, filepath: str):
        """Send analysis report to admin with download button"""
        try:
            # Prepare admin message
            admin_message = f"""📊 گزارش جدید مصاحبه

👤 کاربر: {user_id}
📅 زمان: {self._get_current_time()}

{report}"""
            
            # Create inline keyboard with download button
            # Store filepath in a simple format (just filename to avoid callback data length limit)
            filename = os.path.basename(filepath)
            keyboard = [
                [InlineKeyboardButton("📥 دانلود فایل کامل چت", callback_data=f"dl_{user_id}_{filename}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Split long messages
            if len(admin_message) > MAX_MESSAGE_LENGTH:
                chunks = [
                    admin_message[i:i + MAX_MESSAGE_LENGTH]
                    for i in range(0, len(admin_message), MAX_MESSAGE_LENGTH)
                ]
                # Send all chunks except last one
                for chunk in chunks[:-1]:
                    await context.bot.send_message(
                        chat_id=self.admin_id,
                        text=chunk
                    )
                # Send last chunk with download button
                await context.bot.send_message(
                    chat_id=self.admin_id,
                    text=chunks[-1],
                    reply_markup=reply_markup
                )
            else:
                await context.bot.send_message(
                    chat_id=self.admin_id,
                    text=admin_message,
                    reply_markup=reply_markup
                )
            
            print(f"[REPORT SENT] Report sent to admin for user {user_id}")
            
        except Exception as e:
            print(f"[ERROR] Failed to send report to admin: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def handle_download_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download button callback"""
        query = update.callback_query
        await query.answer("در حال ارسال فایل...")
        
        try:
            # Extract filename from callback data
            callback_data = query.data
            if callback_data.startswith("dl_"):
                # Format: dl_userid_filename
                parts = callback_data.split("_", 2)
                if len(parts) >= 3:
                    user_id = parts[1]
                    filename = parts[2]
                    
                    # Reconstruct filepath
                    filepath = os.path.join("interviews", filename)
                    
                    # Send file to admin
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            await context.bot.send_document(
                                chat_id=self.admin_id,
                                document=f,
                                filename=filename,
                                caption="📄 فایل کامل مصاحبه (سوال و جواب‌ها)"
                            )
                        await query.edit_message_text(
                            query.message.text + "\n\n✅ فایل با موفقیت ارسال شد!",
                            reply_markup=None
                        )
                    else:
                        await query.edit_message_text(
                            query.message.text + "\n\n❌ فایل پیدا نشد!",
                            reply_markup=None
                        )
                else:
                    await query.edit_message_text("❌ خطا در پردازش درخواست!")
            else:
                await query.edit_message_text("❌ خطا در پردازش درخواست!")
        except Exception as e:
            print(f"[ERROR] Failed to handle download callback: {str(e)}")
            import traceback
            traceback.print_exc()
            try:
                await query.edit_message_text(
                    query.message.text + "\n\n❌ خطا در ارسال فایل!",
                    reply_markup=None
                )
            except:
                pass
    
    def _get_current_time(self) -> str:
        """Get current time as formatted string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


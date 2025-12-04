"""
Configuration module for Telegram bot
Contains all API keys and configuration settings
"""

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8277682636:AAECGOsy9rhJHLTaPlQIgX2gdJbZZxrSGic"

# OpenRouter API Configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "google/gemini-2.0-flash-lite-001"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Bot Settings
MAX_MESSAGE_LENGTH = 4096  # Telegram's maximum message length
REQUEST_TIMEOUT = 30  # Timeout for API requests in seconds

# Proxy Settings (optional - set if needed)
# For example in Iran where Telegram might be blocked
# PROXY_URL = "http://proxy.example.com:8080"  # Uncomment and set if needed
PROXY_URL = None  # Set to None if no proxy needed


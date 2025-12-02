"""
OpenRouter API Client Module
Handles communication with OpenRouter API for AI model requests
"""

import requests
import time
from ..config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_API_URL, REQUEST_TIMEOUT


class OpenRouterClient:
    """Client for interacting with OpenRouter API"""
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL
        self.api_url = OPENROUTER_API_URL
        self.timeout = REQUEST_TIMEOUT
        self.last_request_time = 0
        self.min_request_interval = 2.0  # Minimum 2 seconds between requests to avoid rate limiting
    
    def get_response(self, user_message: str, conversation_history: list = None) -> str:
        """
        Get AI response from OpenRouter API
        
        Args:
            user_message: The user's message
            conversation_history: Optional list of previous messages for context
            
        Returns:
            AI response as string
        """
        # Prepare messages for the API
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Optional: your app URL
            "X-Title": "Telegram Bot"  # Optional: your app name
        }
        
        # Prepare payload
        payload = {
            "model": self.model,
            "messages": messages
        }
        
        # Rate limiting: ensure minimum time between requests
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_request
            time.sleep(wait_time)
        
        # Retry logic for rate limiting
        max_retries = 3
        retry_delay = 2  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                # Make API request
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        # Extract retry-after from headers if available
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            wait_time = int(retry_after)
                        else:
                            wait_time = retry_delay * (attempt + 1)  # Exponential backoff
                        
                        # Wait before retry
                        time.sleep(wait_time)
                        continue
                    else:
                        return "⏳ متاسفم، در حال حاضر تعداد درخواست‌های زیادی ارسال شده است. لطفاً چند لحظه صبر کنید و دوباره تلاش کنید."
                
                # Check if request was successful
                response.raise_for_status()
                
                # Extract and return the AI response
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]
                
                # Update last request time
                self.last_request_time = time.time()
                
                return ai_response
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    return "⏱️ درخواست شما بیش از حد طول کشید. لطفاً دوباره تلاش کنید."
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        return "⏳ در حال حاضر تعداد درخواست‌های زیادی ارسال شده است. لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید."
                elif e.response.status_code == 401:
                    return "❌ خطا در احراز هویت API. لطفاً کلید API را بررسی کنید."
                elif e.response.status_code == 402:
                    return "💰 موجودی حساب شما کافی نیست. لطفاً حساب OpenRouter خود را بررسی کنید."
                else:
                    return f"⚠️ خطای HTTP {e.response.status_code}: {str(e)}"
            
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    return f"🔌 خطا در ارتباط با API: {str(e)}"
            
            except KeyError as e:
                return f"⚠️ خطا در پردازش پاسخ API: {str(e)}"
            
            except Exception as e:
                return f"❌ خطای غیرمنتظره: {str(e)}"
        
        # If all retries failed
        return "⏳ متاسفم، بعد از چندین تلاش موفق به دریافت پاسخ نشد. لطفاً چند لحظه صبر کنید و دوباره تلاش کنید."


"""
Question Analyzer Module
Analyzes user responses to determine if they contain enough information
"""

from ..conversation.openrouter_client import OpenRouterClient


class QuestionAnalyzer:
    """Analyzes user responses to interview questions"""
    
    def __init__(self):
        self.client = OpenRouterClient()
    
    def analyze_response(self, question_id: str, question_text: str, user_response: str, required_elements: list, previous_responses: list = None, conversation_history: list = None) -> dict:
        """
        Analyze if user response contains enough information
        
        Args:
            question_id: ID of the question (q1, q2, etc.)
            question_text: The question text
            user_response: User's response
            required_elements: List of required elements to check
            previous_responses: List of previous responses for this question (to avoid repetition)
        
        Returns:
            dict with keys:
                - is_complete: bool
                - missing_elements: list
                - feedback: str
                - mentioned_topics: list (topics already mentioned)
        """
        # Build context of what was already mentioned
        previous_context = ""
        if previous_responses:
            previous_context = f"\n\nپاسخ‌های قبلی کاربر برای همین سوال:\n" + "\n".join([f"- {resp}" for resp in previous_responses])
            previous_context += "\n\nمهم: چیزهایی که در پاسخ‌های قبلی گفته شده را دوباره نپرس. فقط چیزهایی که هنوز گفته نشده را بپرس."
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            # Format conversation history for context
            conv_text = "\n".join([f"{'کاربر' if msg.get('role') == 'user' else 'بات'}: {msg.get('content', '')[:200]}" for msg in conversation_history[-10:]])  # Last 10 messages
            conversation_context = f"\n\nتاریخچه گفتگو (برای درک بهتر):\n{conv_text}\n\nمهم: از این تاریخچه استفاده کن تا بفهمی کاربر چه گفته و چه چیزهایی را قبلاً توضیح داده. چیزهایی که قبلاً گفته شده را دوباره نپرس."
        
        # Create analysis prompt
        analysis_prompt = f"""شما یک تحلیل‌گر دقیق و هوشمند هستید که باید تشخیص دهید آیا پاسخ کاربر برای سوال کافی است یا نه.

🎯 هدف: فقط چیزهایی که واقعاً گفته نشده را بپرسید. اگر پاسخ کافی است، سریع به سوال بعدی بروید.

سوال اصلی:
{question_text}

پاسخ فعلی کاربر:
{user_response}
{previous_context}
{conversation_context}

عناصر مورد نیاز برای این سوال:
{', '.join(required_elements)}

⚠️ قوانین بسیار مهم:

1. **تحلیل دقیق**: بررسی کنید که آیا کاربر به تمام عناصر مورد نیاز پاسخ داده است یا نه
   - اگر پاسخ داده: is_complete = true
   - اگر پاسخ نداده: is_complete = false و فقط عناصر مفقوده را لیست کنید

2. **هوشمندی در تشخیص**: 
   - اگر کاربر به سوال پاسخ داده و اطلاعات کافی داده، حتی اگر کوتاه باشد، is_complete = true
   - فقط اگر واقعاً چیزی کم است، is_complete = false
   - از سوالات اضافی و غیرضروری خودداری کنید

3. **فقط چیزهای مفقوده**: 
   - در missing_elements فقط چیزهایی را بگذارید که واقعاً گفته نشده
   - اگر کاربر چیزی گفته، حتی به صورت غیرمستقیم، آن را در missing_elements نگذارید

4. **سوالات هوشمند**: 
   - در feedback فقط یک سوال کوتاه و مستقیم بپرسید که دقیقاً همان چیز مفقوده را می‌خواهد
   - از سوالات کلی و مسخره خودداری کنید
   - اگر چیزی گفته شده، آن را دوباره نپرسید

5. **سرعت در پیشرفت**: 
   - اگر پاسخ کافی است، سریع is_complete = true کنید
   - هدف گرفتن دیتای مورد نیاز است، نه پرسیدن سوالات اضافی

لطفاً تحلیل کنید و به این فرمت JSON پاسخ دهید:
{{
    "is_complete": true/false,
    "missing_elements": ["فقط عناصری که واقعاً گفته نشده"],
    "mentioned_topics": ["چیزهایی که کاربر گفته"],
    "feedback": "اگر is_complete=false، فقط یک سوال کوتاه و مستقیم برای چیز مفقوده. اگر is_complete=true، خالی بگذارید یا 'عالی'"
}}

مثال:
- اگر کاربر گفت: "من ماینکرفت بازی می‌کنم و وقتی دارم ساختم خیلی باحاله"
  → is_complete = true (موضوع، فعالیت، و لحظه خاص را گفته)
  
- اگر کاربر گفت: "یه بازی بود"
  → is_complete = false, missing_elements = ["لحظه خاص", "محرک دقیق"], feedback = "کدوم لحظه بازی برات باحال‌تر بود؟"

فقط JSON را برگردانید، هیچ متن اضافی نباشد."""

        try:
            # Get AI analysis
            analysis_text = self.client.get_response(analysis_prompt)
            
            # Try to extract JSON from response
            import json
            import re
            
            # Try to find JSON in response (support for nested JSON)
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                try:
                    analysis_json = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # Try to fix common JSON issues
                    json_str = json_match.group()
                    # Remove trailing commas
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*]', ']', json_str)
                    try:
                        analysis_json = json.loads(json_str)
                    except:
                        return self._basic_analysis(user_response, required_elements, previous_responses, conversation_history)
            else:
                # Fallback: basic analysis
                return self._basic_analysis(user_response, required_elements, previous_responses, conversation_history)
            
            is_complete = analysis_json.get("is_complete", False)
            missing_elements = analysis_json.get("missing_elements", [])
            feedback = analysis_json.get("feedback", "")
            
            # اگر پاسخ کامل است، feedback را خالی یا مثبت کنیم
            if is_complete:
                if not feedback or feedback.strip() == "":
                    feedback = "عالی! جوابت کامل بود! 😊✨"
            
            # اگر missing_elements خالی است اما is_complete false است، احتمالاً پاسخ کافی است
            if not is_complete and len(missing_elements) == 0:
                # احتمالاً AI فکر کرده پاسخ کافی است
                is_complete = True
                feedback = "عالی! جوابت کامل بود! 😊✨"
            
            return {
                "is_complete": is_complete,
                "missing_elements": missing_elements,
                "mentioned_topics": analysis_json.get("mentioned_topics", []),
                "feedback": feedback
            }
            
        except Exception as e:
            print(f"[ANALYZER ERROR] {str(e)}")
            # Fallback to basic analysis if AI fails
            return self._basic_analysis(user_response, required_elements, previous_responses, conversation_history)
    
    def _basic_analysis(self, user_response: str, required_elements: list, previous_responses: list = None, conversation_history: list = None) -> dict:
        """
        Basic analysis fallback when AI is not available
        Checks response length and basic keywords
        """
        response_lower = user_response.lower()
        missing = []
        
        # Simple length check
        if len(user_response.strip()) < 30:
            return {
                "is_complete": False,
                "missing_elements": required_elements,
                "mentioned_topics": [],
                "feedback": "اوه! جوابت خیلی کوتاه بود! 😊\n\nمی‌خوام بیشتر بفهمم! لطفاً بیشتر برام توضیح بده تا بهتر بفهمم چی می‌گی! 🤔"
            }
        
        # Check for question marks (might indicate user is confused)
        if user_response.count('?') > 2:
            return {
                "is_complete": False,
                "missing_elements": ["اطلاعات بیشتر"],
                "mentioned_topics": [],
                "feedback": "اوه! به نظر می‌رسه سوال داری! 😊\n\nاگه چیزی واضح نیست یا سوالی داری، حتماً بپرس! من اینجام تا کمکت کنم! بعدش جوابت رو کامل کن تا بهتر بفهمم! 🤔✨"
            }
        
        # If response is reasonably long and contains some keywords, assume it's complete
        # Check if response mentions at least some relevant keywords
        if len(user_response.strip()) > 40:
            # Check for common keywords that indicate a complete answer
            keywords_found = 0
            for element in required_elements:
                # Simple keyword matching
                if any(keyword in response_lower for keyword in ["بود", "هست", "دارم", "می‌کنم", "داشتم", "کردم"]):
                    keywords_found += 1
            
            # If at least some keywords found, assume complete
            if keywords_found > 0 or len(user_response.strip()) > 80:
                return {
                    "is_complete": True,
                    "missing_elements": [],
                    "mentioned_topics": [],
                    "feedback": "عالی! جوابت کامل بود! 😊✨"
                }
        
        return {
            "is_complete": False,
            "missing_elements": required_elements[:1],
            "mentioned_topics": [],
            "feedback": "اوه! می‌خوام بیشتر بفهمم! 😊\n\nلطفاً بیشتر برام توضیح بده تا بهتر بفهمم چی می‌گی! 🤔"
        }


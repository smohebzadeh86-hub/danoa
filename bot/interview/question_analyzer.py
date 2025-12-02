"""
Question Analyzer Module
Analyzes user responses to determine if they contain enough information
"""

from ..conversation.openrouter_client import OpenRouterClient


class QuestionAnalyzer:
    """Analyzes user responses to interview questions"""
    
    def __init__(self):
        self.client = OpenRouterClient()
    
    def analyze_response(self, question_id: str, question_text: str, user_response: str, required_elements: list) -> dict:
        """
        Analyze if user response contains enough information
        
        Args:
            question_id: ID of the question (q1, q2, etc.)
            question_text: The question text
            user_response: User's response
            required_elements: List of required elements to check
        
        Returns:
            dict with keys:
                - is_complete: bool
                - missing_elements: list
                - feedback: str
        """
        # Create analysis prompt
        analysis_prompt = f"""شما یک تحلیل‌گر پاسخ‌های مصاحبه هستید. 

سوال:
{question_text}

پاسخ کاربر:
{user_response}

عناصر مورد نیاز در پاسخ:
{', '.join(required_elements)}

لطفاً تحلیل کنید و به این فرمت JSON پاسخ دهید:
{{
    "is_complete": true/false,
    "missing_elements": ["عنصر1", "عنصر2"],
    "feedback": "توضیح کوتاه"
}}

اگر پاسخ کامل است، is_complete را true قرار دهید و missing_elements را خالی بگذارید.
اگر پاسخ ناقص است، is_complete را false قرار دهید و عناصر مفقوده را لیست کنید.

فقط JSON را برگردانید، هیچ متن اضافی نباشد."""

        try:
            # Get AI analysis
            analysis_text = self.client.get_response(analysis_prompt)
            
            # Try to extract JSON from response
            import json
            import re
            
            # Try to find JSON in response
            json_match = re.search(r'\{[^}]+\}', analysis_text, re.DOTALL)
            if json_match:
                analysis_json = json.loads(json_match.group())
            else:
                # Fallback: basic analysis
                return self._basic_analysis(user_response, required_elements)
            
            return {
                "is_complete": analysis_json.get("is_complete", False),
                "missing_elements": analysis_json.get("missing_elements", []),
                "feedback": analysis_json.get("feedback", "")
            }
            
        except Exception as e:
            # Fallback to basic analysis if AI fails
            return self._basic_analysis(user_response, required_elements)
    
    def _basic_analysis(self, user_response: str, required_elements: list) -> dict:
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
                "feedback": "اوه! جوابت خیلی کوتاه بود! 😊\n\nمی‌خوام بیشتر بفهمم! لطفاً بیشتر برام توضیح بده تا بهتر بفهمم چی می‌گی! 🤔"
            }
        
        # Check for question marks (might indicate user is confused)
        if user_response.count('?') > 2:
            return {
                "is_complete": False,
                "missing_elements": ["اطلاعات بیشتر"],
                "feedback": "اوه! به نظر می‌رسه سوال داری! 😊\n\nاگه چیزی واضح نیست یا سوالی داری، حتماً بپرس! من اینجام تا کمکت کنم! بعدش جوابت رو کامل کن تا بهتر بفهمم! 🤔✨"
            }
        
        # If response is reasonably long, assume it's complete
        if len(user_response.strip()) > 50:
            return {
                "is_complete": True,
                "missing_elements": [],
                "feedback": "عالی! جوابت کامل بود! 😊✨"
            }
        
        return {
            "is_complete": False,
            "missing_elements": required_elements[:1],
                "feedback": "اوه! می‌خوام بیشتر بفهمم! 😊\n\nلطفاً بیشتر برام توضیح بده تا بهتر بفهمم چی می‌گی! 🤔"
        }


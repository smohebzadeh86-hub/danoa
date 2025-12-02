"""
Interview Agent Module
Manages the interview flow and state
"""

from enum import Enum
import json
from .interview_questions import INTRODUCTION, QUESTIONS, COMPLETION_MESSAGE
from .question_analyzer import QuestionAnalyzer


class InterviewState(Enum):
    """Interview states"""
    WAITING_FOR_START = "waiting_for_start"
    GETTING_NAME_AGE = "getting_name_age"
    ASKING_QUESTION = "asking_question"
    FOLLOWING_UP = "following_up"
    COMPLETED = "completed"


class InterviewAgent:
    """Manages interview flow"""
    
    def __init__(self):
        self.analyzer = QuestionAnalyzer()
        self.interviews = {}  # user_id -> interview_data
        from ..conversation.openrouter_client import OpenRouterClient
        self.ai_client = OpenRouterClient()
    
    def start_interview(self, user_id: int):
        """Start a new interview for a user"""
        self.interviews[user_id] = {
            "state": InterviewState.GETTING_NAME_AGE,
            "current_question_index": 0,
            "name": None,
            "age": None,
            "answers": {}
        }
        return INTRODUCTION
    
    def _is_question(self, message: str) -> bool:
        """Check if user message is a question"""
        question_indicators = ['؟', '?', 'چیه', 'چیه؟', 'چی', 'چی؟', 'چطور', 'چطور؟', 
                             'چرا', 'چرا؟', 'کیه', 'کیه؟', 'کی', 'کی؟', 'کجا', 'کجا؟',
                             'چند', 'چند؟', 'چه', 'چه؟', 'میشه', 'میشه؟', 'می‌شه', 'می‌شه؟']
        message_lower = message.lower().strip()
        
        # Check if ends with question mark
        if message_lower.endswith('؟') or message_lower.endswith('?'):
            return True
        
        # Check for question indicators
        for indicator in question_indicators:
            if indicator in message_lower:
                return True
        
        # Check if message is very short (likely a question)
        if len(message.strip()) < 20 and any(word in message_lower for word in ['چیه', 'چی', 'چطور', 'چرا']):
            return True
        
        return False
    
    def _answer_user_question(self, user_question: str, current_question: str) -> str:
        """Answer user's question briefly and return to interview"""
        prompt = f"""تو دانوا هستی، یک دوست صمیمی که با بچه‌ها مصاحبه می‌کنی.

در حال حاضر این سوال مصاحبه رو می‌پرسی:
{current_question}

کاربر این سوال رو ازت پرسیده:
{user_question}

لطفاً یک جواب کوتاه و صمیمی (حداکثر 2-3 جمله) به سوال کاربر بده. بعد یادآوری کن که باید به سوال مصاحبه جواب بده.

لحن تو باید:
- صمیمی و دوستانه باشه
- برای بچه‌ها قابل فهم باشه
- کوتاه و مختصر باشه
- بعد یادآوری کن که باید به سوال مصاحبه برگرده

فقط جواب رو بده، بدون توضیح اضافی."""
        
        try:
            answer = self.ai_client.get_response(prompt)
            # Add reminder to return to interview
            return f"{answer}\n\nحالا بذار برگردیم به سوال مصاحبه! 😊"
        except:
            return "اوه! متاسفم، الان نمی‌تونم جواب بدم! 😅\n\nولی بذار برگردیم به سوال مصاحبه! 😊"
    
    def process_response(self, user_id: int, user_message: str) -> dict:
        """
        Process user response and return next message
        
        Returns:
            dict with keys:
                - message: str - Message to send to user
                - state: InterviewState - Current state
                - is_complete: bool - Whether interview is complete
                - result: dict - Final result if complete
        """
        if user_id not in self.interviews:
            # Start interview if not started
            return {
                "message": self.start_interview(user_id),
                "state": InterviewState.GETTING_NAME_AGE,
                "is_complete": False,
                "result": None
            }
        
        interview = self.interviews[user_id]
        
        # Check if user is asking a question (not during name/age collection)
        if interview["state"] != InterviewState.GETTING_NAME_AGE:
            if self._is_question(user_message):
                # Get current question context
                if interview["state"] == InterviewState.ASKING_QUESTION:
                    question_index = interview["current_question_index"]
                    current_question = QUESTIONS[question_index]["question"]
                elif interview["state"] == InterviewState.FOLLOWING_UP:
                    question_index = interview["current_question_index"]
                    current_question = QUESTIONS[question_index]["question"]
                else:
                    current_question = "مصاحبه"
                
                # Answer the question and remind about interview
                answer = self._answer_user_question(user_message, current_question)
                
                # Return to current interview state
                if interview["state"] == InterviewState.ASKING_QUESTION:
                    question_index = interview["current_question_index"]
                    question_data = QUESTIONS[question_index]
                    return {
                        "message": f"{answer}\n\n{question_data['question']}",
                        "state": InterviewState.ASKING_QUESTION,
                        "is_complete": False,
                        "result": None
                    }
                elif interview["state"] == InterviewState.FOLLOWING_UP:
                    question_index = interview["current_question_index"]
                    question_data = QUESTIONS[question_index]
                    return {
                        "message": f"{answer}\n\n{question_data['follow_up']}",
                        "state": InterviewState.FOLLOWING_UP,
                        "is_complete": False,
                        "result": None
                    }
        
        # Handle different states
        if interview["state"] == InterviewState.GETTING_NAME_AGE:
            return self._handle_name_age(user_id, user_message)
        
        elif interview["state"] == InterviewState.ASKING_QUESTION:
            return self._handle_question_response(user_id, user_message)
        
        elif interview["state"] == InterviewState.FOLLOWING_UP:
            return self._handle_follow_up(user_id, user_message)
        
        elif interview["state"] == InterviewState.COMPLETED:
            return {
                "message": "اوه! مصاحبه قبلاً تموم شده بود! 😊\n\nاگه می‌خوای دوباره شروع کنیم، /start رو بزن تا یه مصاحبه جدید شروع کنیم! 🎉",
                "state": InterviewState.COMPLETED,
                "is_complete": True,
                "result": self._get_result(user_id)
            }
    
    def _handle_name_age(self, user_id: int, user_message: str) -> dict:
        """Extract name and age from user message"""
        interview = self.interviews[user_id]
        
        # Check if user is asking a question
        if self._is_question(user_message):
            answer = self._answer_user_question(user_message, "لطفاً نام و سن خودتون رو بهم بدید")
            return {
                "message": f"{answer}\n\n{INTRODUCTION}",
                "state": InterviewState.GETTING_NAME_AGE,
                "is_complete": False,
                "result": None
            }
        
        # Try to extract name and age
        message_lower = user_message.lower()
        
        # Look for patterns
        name = None
        age = None
        
        # Try to find name and age patterns
        lines = user_message.split('\n')
        for line in lines:
            if 'نام' in line or 'اسم' in line:
                parts = line.split(':')
                if len(parts) > 1:
                    name = parts[1].strip()
            elif 'سن' in line:
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        age = int(parts[1].strip())
                    except:
                        pass
        
        # If not found in structured format, try to extract from natural text
        if not name or not age:
            words = user_message.split()
            for i, word in enumerate(words):
                if word.isdigit() and 3 <= int(word) <= 20:  # Reasonable age range
                    age = int(word)
                    # Name might be before or after age
                    if i > 0 and len(words[i-1]) > 2:
                        name = words[i-1]
                    elif i < len(words) - 1 and len(words[i+1]) > 2:
                        name = words[i+1]
        
        # If still not found, use AI to extract
        if not name or not age:
            extraction_prompt = f"""این پیام یک کاربر است که می‌خواهد نام و سن خود را بگوید:

{user_message}

لطفاً نام و سن را استخراج کنید و به این فرمت JSON پاسخ دهید:
{{
    "name": "نام",
    "age": عدد
}}

اگر پیدا نکردید، null بگذارید. فقط JSON را برگردانید."""
            
            try:
                from ..conversation.openrouter_client import OpenRouterClient
                client = OpenRouterClient()
                result_text = client.get_response(extraction_prompt)
                
                import re
                json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
                if json_match:
                    extracted = json.loads(json_match.group())
                    if extracted.get("name"):
                        name = extracted["name"]
                    if extracted.get("age"):
                        age = extracted["age"]
            except:
                pass
        
        # Check if we have both
        if name and age:
            interview["name"] = name
            interview["age"] = age
            interview["state"] = InterviewState.ASKING_QUESTION
            
            question_data = QUESTIONS[0]
            return {
                "message": f"عالی {name}! خوشحالم که باهات دوست شدم! 😊\n\nحالا بذار سوالات باحال رو شروع کنیم! آماده‌ای؟ 🎉\n\n{question_data['question']}",
                "state": InterviewState.ASKING_QUESTION,
                "is_complete": False,
                "result": None
            }
        else:
            missing = []
            if not name:
                missing.append("نام")
            if not age:
                missing.append("سن")
            
            return {
                "message": f"اوه! من هنوز {', '.join(missing)} تو رو نمی‌دونم! 😊\n\nلطفاً بگو تا بهتر باهم دوست بشیم!\nمثلاً می‌تونی بگی: «من [نام] هستم و [سن] سال دارم»\n\nیا می‌تونی جداگانه بگی:\nاسمم: [نام]\nسنم: [سن]",
                "state": InterviewState.GETTING_NAME_AGE,
                "is_complete": False,
                "result": None
            }
    
    def _handle_question_response(self, user_id: int, user_message: str) -> dict:
        """Handle response to a question"""
        interview = self.interviews[user_id]
        question_index = interview["current_question_index"]
        question_data = QUESTIONS[question_index]
        
        # Analyze response
        analysis = self.analyzer.analyze_response(
            question_data["id"],
            question_data["question"],
            user_message,
            question_data["required_elements"]
        )
        
        if analysis["is_complete"]:
            # Save answer and move to next question
            interview["answers"][question_data["id"]] = user_message
            interview["current_question_index"] += 1
            
            # Check if all questions are done
            if interview["current_question_index"] >= len(QUESTIONS):
                interview["state"] = InterviewState.COMPLETED
                return {
                    "message": COMPLETION_MESSAGE,
                    "state": InterviewState.COMPLETED,
                    "is_complete": True,
                    "result": self._get_result(user_id)
                }
            else:
                # Ask next question
                next_question = QUESTIONS[interview["current_question_index"]]
                return {
                    "message": next_question["question"],
                    "state": InterviewState.ASKING_QUESTION,
                    "is_complete": False,
                    "result": None
                }
        else:
            # Need follow-up
            interview["state"] = InterviewState.FOLLOWING_UP
            follow_up_message = f"{analysis['feedback']}\n\n{question_data['follow_up']}"
            return {
                "message": follow_up_message,
                "state": InterviewState.FOLLOWING_UP,
                "is_complete": False,
                "result": None
            }
    
    def _handle_follow_up(self, user_id: int, user_message: str) -> dict:
        """Handle follow-up response"""
        interview = self.interviews[user_id]
        question_index = interview["current_question_index"]
        question_data = QUESTIONS[question_index]
        
        # Combine original answer with follow-up
        original_answer = interview["answers"].get(question_data["id"], "")
        combined_answer = f"{original_answer}\n\n[توضیح بیشتر]: {user_message}"
        
        # Analyze again
        analysis = self.analyzer.analyze_response(
            question_data["id"],
            question_data["question"],
            combined_answer,
            question_data["required_elements"]
        )
        
        if analysis["is_complete"]:
            # Save combined answer and move to next
            interview["answers"][question_data["id"]] = combined_answer
            interview["current_question_index"] += 1
            interview["state"] = InterviewState.ASKING_QUESTION
            
            # Check if done
            if interview["current_question_index"] >= len(QUESTIONS):
                interview["state"] = InterviewState.COMPLETED
                return {
                    "message": COMPLETION_MESSAGE,
                    "state": InterviewState.COMPLETED,
                    "is_complete": True,
                    "result": self._get_result(user_id)
                }
            else:
                next_question = QUESTIONS[interview["current_question_index"]]
                return {
                    "message": next_question["question"],
                    "state": InterviewState.ASKING_QUESTION,
                    "is_complete": False,
                    "result": None
                }
        else:
            # Still need more info
            return {
                "message": f"{analysis['feedback']}\n\n{question_data['follow_up']}",
                "state": InterviewState.FOLLOWING_UP,
                "is_complete": False,
                "result": None
            }
    
    def _get_result(self, user_id: int) -> dict:
        """Get final interview result as JSON"""
        interview = self.interviews[user_id]
        result = {
            "name": interview["name"],
            "age": interview["age"],
            "q1": interview["answers"].get("q1", ""),
            "q2": interview["answers"].get("q2", ""),
            "q3": interview["answers"].get("q3", ""),
            "q4": interview["answers"].get("q4", ""),
            "q5": interview["answers"].get("q5", ""),
            "q6": interview["answers"].get("q6", ""),
            "q7": interview["answers"].get("q7", "")
        }
        return result
    
    def reset_interview(self, user_id: int):
        """Reset interview for a user"""
        if user_id in self.interviews:
            del self.interviews[user_id]
    
    def get_interview_state(self, user_id: int) -> InterviewState:
        """Get current interview state for a user"""
        if user_id not in self.interviews:
            return InterviewState.WAITING_FOR_START
        return self.interviews[user_id]["state"]


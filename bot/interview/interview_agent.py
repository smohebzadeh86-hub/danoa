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
    
    def start_interview(self, user_id: int):
        """Start a new interview for a user"""
        self.interviews[user_id] = {
            "state": InterviewState.GETTING_NAME_AGE,
            "current_question_index": 0,
            "name": None,
            "age": None,
            "answers": {},
            "question_responses": {},  # question_id -> list of responses for this question
            "follow_up_count": {},  # question_id -> number of follow-ups
            "conversation_history": []  # Full conversation history: list of {"role": "user"/"assistant", "content": "..."}
        }
        return INTRODUCTION
    
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
            welcome_msg = f"عالی {name}! خوشحالم که باهات دوست شدم! 😊\n\nحالا بذار سوالات باحال رو شروع کنیم! آماده‌ای؟ 🎉\n\n{question_data['question']}"
            # Add welcome message to conversation history
            interview["conversation_history"].append({
                "role": "assistant",
                "content": welcome_msg
            })
            return {
                "message": welcome_msg,
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
            
            missing_msg = f"اوه! من هنوز {', '.join(missing)} تو رو نمی‌دونم! 😊\n\nلطفاً بگو تا بهتر باهم دوست بشیم!\nمثلاً می‌تونی بگی: «من [نام] هستم و [سن] سال دارم»\n\nیا می‌تونی جداگانه بگی:\nاسمم: [نام]\nسنم: [سن]"
            # Add bot message to conversation history
            interview["conversation_history"].append({
                "role": "assistant",
                "content": missing_msg
            })
            return {
                "message": missing_msg,
                "state": InterviewState.GETTING_NAME_AGE,
                "is_complete": False,
                "result": None
            }
    
    def _handle_question_response(self, user_id: int, user_message: str) -> dict:
        """Handle response to a question"""
        interview = self.interviews[user_id]
        question_index = interview["current_question_index"]
        question_data = QUESTIONS[question_index]
        question_id = question_data["id"]
        
        # Add user message to conversation history
        interview["conversation_history"].append({
            "role": "user",
            "content": user_message
        })
        
        # Store response history for this specific question
        if question_id not in interview["question_responses"]:
            interview["question_responses"][question_id] = []
        interview["question_responses"][question_id].append(user_message)
        
        # Get previous responses for this question
        previous_responses = interview["question_responses"][question_id][:-1]  # All except current
        
        # Get recent conversation history (last 15 messages to avoid token limit)
        recent_history = interview["conversation_history"][-15:] if len(interview["conversation_history"]) > 15 else interview["conversation_history"]
        
        # Analyze response with context of previous responses and conversation history
        analysis = self.analyzer.analyze_response(
            question_id,
            question_data["question"],
            user_message,
            question_data["required_elements"],
            previous_responses=previous_responses if previous_responses else None,
            conversation_history=recent_history[:-1] if len(recent_history) > 1 else None  # Exclude current message
        )
        
        if analysis["is_complete"]:
            # Save answer and move to next question
            # Combine all responses for this question
            all_responses = interview["question_responses"][question_id]
            combined_answer = "\n\n".join(all_responses)
            interview["answers"][question_id] = combined_answer
            
            # Reset follow-up count for this question
            if question_id in interview["follow_up_count"]:
                del interview["follow_up_count"][question_id]
            
            interview["current_question_index"] += 1
            
            # Check if all questions are done
            if interview["current_question_index"] >= len(QUESTIONS):
                interview["state"] = InterviewState.COMPLETED
                completion_msg = COMPLETION_MESSAGE
                # Add completion message to conversation history
                interview["conversation_history"].append({
                    "role": "assistant",
                    "content": completion_msg
                })
                return {
                    "message": completion_msg,
                    "state": InterviewState.COMPLETED,
                    "is_complete": True,
                    "result": self._get_result(user_id)
                }
            else:
                # Ask next question
                next_question = QUESTIONS[interview["current_question_index"]]
                next_question_msg = next_question["question"]
                # Add bot message to conversation history
                interview["conversation_history"].append({
                    "role": "assistant",
                    "content": next_question_msg
                })
                return {
                    "message": next_question_msg,
                    "state": InterviewState.ASKING_QUESTION,
                    "is_complete": False,
                    "result": None
                }
        else:
            # Need follow-up - check if we've exceeded max follow-ups
            max_follow_ups = 1  # Maximum 1 follow-up per question (reduced for faster progress)
            
            if question_id not in interview["follow_up_count"]:
                interview["follow_up_count"][question_id] = 0
            
            interview["follow_up_count"][question_id] += 1
            
            # If too many follow-ups or missing_elements is empty, accept what we have and move on
            if interview["follow_up_count"][question_id] > max_follow_ups or len(analysis.get("missing_elements", [])) == 0:
                # Save what we have and move to next question
                all_responses = interview["question_responses"][question_id]
                combined_answer = "\n\n".join(all_responses)
                interview["answers"][question_id] = combined_answer
                
                # Reset follow-up count
                del interview["follow_up_count"][question_id]
                
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
                        "message": f"باشه! بذار به سوال بعدی بریم! 😊\n\n{next_question['question']}",
                        "state": InterviewState.ASKING_QUESTION,
                        "is_complete": False,
                        "result": None
                    }
            
            # Normal follow-up - only use smart feedback, not the generic follow_up
            interview["state"] = InterviewState.FOLLOWING_UP
            
            # Use smart feedback from analysis - this is more intelligent and specific
            if analysis.get("feedback") and analysis["feedback"].strip():
                follow_up_message = analysis["feedback"]
            else:
                # If no smart feedback, create a simple one based on missing elements
                missing = analysis.get("missing_elements", [])
                if missing:
                    follow_up_message = f"اوه! می‌خوام بیشتر بفهمم! 😊\n\nلطفاً درباره {missing[0]} بیشتر بگو! 🤔"
                else:
                    # If no missing elements but still not complete, just move on
                    follow_up_message = "باشه! بذار به سوال بعدی بریم! 😊"
            
            # Add bot follow-up message to conversation history
            interview["conversation_history"].append({
                "role": "assistant",
                "content": follow_up_message
            })
            
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
        question_id = question_data["id"]
        
        # Add user message to conversation history
        interview["conversation_history"].append({
            "role": "user",
            "content": user_message
        })
        
        # Store this follow-up response
        if question_id not in interview["question_responses"]:
            interview["question_responses"][question_id] = []
        interview["question_responses"][question_id].append(user_message)
        
        # Get all previous responses for this question
        previous_responses = interview["question_responses"][question_id][:-1]  # All except current
        
        # Get recent conversation history (last 15 messages to avoid token limit)
        recent_history = interview["conversation_history"][-15:] if len(interview["conversation_history"]) > 15 else interview["conversation_history"]
        
        # Analyze with context of all previous responses and conversation history
        analysis = self.analyzer.analyze_response(
            question_id,
            question_data["question"],
            user_message,
            question_data["required_elements"],
            previous_responses=previous_responses if previous_responses else None,
            conversation_history=recent_history[:-1] if len(recent_history) > 1 else None  # Exclude current message
        )
        
        if analysis["is_complete"]:
            # Save all responses combined and move to next
            all_responses = interview["question_responses"][question_id]
            combined_answer = "\n\n".join(all_responses)
            interview["answers"][question_id] = combined_answer
            
            # Reset follow-up count
            if question_id in interview["follow_up_count"]:
                del interview["follow_up_count"][question_id]
            
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
            # Still need more info - check follow-up count
            if question_id not in interview["follow_up_count"]:
                interview["follow_up_count"][question_id] = 0
            
            interview["follow_up_count"][question_id] += 1
            
            # If too many follow-ups or no missing elements, accept what we have and move on
            if interview["follow_up_count"][question_id] > 1 or len(analysis.get("missing_elements", [])) == 0:  # Max 1 follow-up
                # Save what we have
                all_responses = interview["question_responses"][question_id]
                combined_answer = "\n\n".join(all_responses)
                interview["answers"][question_id] = combined_answer
                
                # Reset follow-up count
                del interview["follow_up_count"][question_id]
                
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
                    next_question_msg = f"باشه! بذار به سوال بعدی بریم! 😊\n\n{next_question['question']}"
                    # Add bot message to conversation history
                    interview["conversation_history"].append({
                        "role": "assistant",
                        "content": next_question_msg
                    })
                    return {
                        "message": next_question_msg,
                        "state": InterviewState.ASKING_QUESTION,
                        "is_complete": False,
                        "result": None
                    }
            
            # Normal follow-up - use smart feedback only
            if analysis.get("feedback") and analysis["feedback"].strip():
                follow_up_message = analysis["feedback"]
            else:
                # If no smart feedback, create a simple one based on missing elements
                missing = analysis.get("missing_elements", [])
                if missing:
                    follow_up_message = f"اوه! می‌خوام بیشتر بفهمم! 😊\n\nلطفاً درباره {missing[0]} بیشتر بگو! 🤔"
                else:
                    # If no missing elements, just move on
                    follow_up_message = "باشه! بذار به سوال بعدی بریم! 😊"
            
            # Add bot follow-up message to conversation history
            interview["conversation_history"].append({
                "role": "assistant",
                "content": follow_up_message
            })
            
            return {
                "message": follow_up_message,
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


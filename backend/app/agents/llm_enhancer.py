from app.services.llm import generate_completion
from app.utils.logging import get_logger

logger = get_logger(__name__)

class LLMEnhance:
    """
    Enhances schedule with human-like study instructions.
    """
    def enhance(self, schedule: list):
        """Call the LLM for each schedule item to add a practical 1–2 line study instruction."""
        enhanced_schedule = []
        
        for item in schedule:
            topic = item['topic']
            task = item['task']
            
            prompt = f"""
            You are a helpful study assistant.

            Write a short, practical study instruction for the following:

            Topic: {topic}
            Task: {task}

            RULES:
            - Do NOT start with "Task:", "Topic:", or repeat the task/topic name.
            - If task is 'revise'   -> tell the student what specific concepts to revisit.
            - If task is 'practice' -> tell the student what to actively practise or attempt.
            - If task is 'maintain' -> give a light tip to keep knowledge fresh (e.g. skim notes, do 2-3 questions).
            - Start directly with the action verb (e.g. "Revisit...", "Attempt...", "Skim...").
            - Keep it to 1 sentence.
            """
            
            try:
                response = generate_completion(
                    prompt=prompt, 
                    system_prompt="You are a smart study planner helping students revise and practice effectively."
                )
                
                if response:
                    item['instruction'] = response.strip()
                else:
                    item["instruction"] = f"{task.capitalize()} {topic} concepts."
                    
            except Exception as e:
                item["instruction"] = f"{task.capitalize()} {topic} concepts."
                
            enhanced_schedule.append(item)
            
        return enhanced_schedule
                    
from app.services.llm import generate_completion
from app.utils.logging import get_logger

logger = get_logger(__name__)

class LLMEnhance:
    """
    Enhances schedule with human-like study instructions.
    """
    def enhance(self, schedule: list):
        enhanced_schedule = []
        
        for item in schedule:
            topic = item['topic']
            task = item['task']
            
            prompt = f"""
            You are a helpful study assistant.
            
            Generate a short and practical instruction.
            
            Topic: {topic}
            Task: {task}
            
            RULES:
            - If task is 'revise' -> tell what to revise.
            - If task is 'practice' -> tell what to practice.
            - Keep it 1-2 lines
            - No extra explaination
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
                    
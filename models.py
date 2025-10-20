from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
import os
from dotenv import load_dotenv

load_dotenv()

class OpenRouterProvider:
    """
    Provides access to OpenRouter models with specific model mapping
    """
    
    MODEL_MAPPING = {
        'master': 'openai/gpt-3.5-turbo',
        'researcher': 'openai/gpt-4o',
        'backend_dev': 'openai/gpt-4o',
        'frontend_dev': 'openai/gpt-4o',
        'doc_writer': 'openai/gpt-3.5-turbo',
        'tester': 'openai/gpt-4o',
        'devops': 'openai/gpt-4o',
    }
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        
    def get_model(self, agent_type: str):
        """
        Get a model instance for the specified agent type
        """
        model_name = self.MODEL_MAPPING.get(agent_type)
        if not model_name:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        return ChatOpenAI(
            model=model_name,
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1
        )
    
    def call_model(self, agent_type: str, messages: list) -> BaseMessage:
        """
        Call the model with the given messages
        """
        model = self.get_model(agent_type)
        return model.invoke(messages)
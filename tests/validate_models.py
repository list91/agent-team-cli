import os
import sys
from dotenv import load_dotenv
from models import OpenRouterProvider

def validate_models(agent_type: str, prompt: str):
    """
    CLI script to validate OpenRouter models
    """
    load_dotenv()
    
    try:
        provider = OpenRouterProvider()
        model = provider.get_model(agent_type)
        
        # Create a simple message for testing
        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=prompt)]
        
        response = model.invoke(messages)
        print(f"Model response for {agent_type}: {response.content}")
        return True
        
    except Exception as e:
        print(f"Error validating model {agent_type}: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate_models.py --agent_type=<agent_type> --prompt='<prompt>'")
        sys.exit(1)
    
    agent_type = sys.argv[1].split('=')[1] if '=' in sys.argv[1] else sys.argv[1]
    prompt = sys.argv[2].split('=', 1)[1] if '=' in sys.argv[2] else sys.argv[2]
    
    success = validate_models(agent_type, prompt)
    if success:
        print(f"✓ Successfully validated {agent_type} model")
    else:
        print(f"✗ Failed to validate {agent_type} model")
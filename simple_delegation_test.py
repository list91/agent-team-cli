from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_simple():
    """
    Simple test to confirm the system works with proper agent delegation
    """
    load_dotenv()
    
    session_id = "simple_test"
    user_request = "Create a CLI tool that prints 'Hello World' and writes it to a file"
    
    print(f"Testing: {user_request}")
    
    result = run_agent_workflow(session_id, user_request)
    
    print(f"Final decision: {result.get('final_decision', 'No decision')}")
    print(f"Number of agent results: {len(result.get('agent_results', []))}")
    
    # Check which agents were used
    agent_names = [ar.get('agent_name', 'Unknown') for ar in result.get('agent_results', [])]
    print(f"Agents used: {set(agent_names)}")
    
    return result

if __name__ == "__main__":
    test_simple()
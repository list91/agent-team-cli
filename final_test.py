from dotenv import load_dotenv
from workflow import run_agent_workflow

def final_test():
    """
    Final test to ensure the system is working properly
    """
    load_dotenv()
    
    session_id = "final_test"
    user_request = "Create a simple Flask hello world application in Python"
    
    print(f"Starting final test for session: {session_id}")
    print(f"User request: {user_request}")
    print("-" * 50)
    
    result = run_agent_workflow(session_id, user_request)
    
    print("Final result:")
    print(f"Final decision: {result.get('final_decision', 'No decision')}")
    print(f"Number of agent results: {len(result.get('agent_results', []))}")
    
    for i, agent_result in enumerate(result.get('agent_results', [])):
        print(f"  Agent {i+1}: {agent_result.get('agent_name', 'Unknown')}")
        print(f"    Task: {agent_result.get('task', 'No task')[:100]}...")
        print(f"    Result length: {len(agent_result.get('result', 'No result'))} chars")
    
    print(f"\nCheck the workspace directory: ./workspace/{session_id}/ for generated files")
    
    return result

if __name__ == "__main__":
    final_test()
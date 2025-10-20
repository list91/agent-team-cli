import sys
import os
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from it
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow import run_agent_workflow

def run_full_scenario(task: str, session_id: str):
    """
    CLI script to run the full scenario: Master → SAP → Approval
    """
    load_dotenv()
    
    try:
        print(f"Starting full scenario for task: {task}")
        print(f"Session ID: {session_id}")
        print("-" * 50)
        
        result = run_agent_workflow(session_id, task)
        
        print("Final result:")
        print(f"Final decision: {result.get('final_decision', 'No decision')}")
        print(f"Review notes: {result.get('review_notes', 'No review notes')[:300]}...")
        print(f"Number of agent results: {len(result.get('agent_results', []))}")
        
        for i, agent_result in enumerate(result.get('agent_results', [])):
            print(f"  Agent {i+1}: {agent_result.get('agent_name', 'Unknown')}")
            print(f"    Task: {agent_result.get('task', 'No task')[:100]}...")
            print(f"    Result preview: {agent_result.get('result', 'No result')[:100]}...")
        
        return True
            
    except Exception as e:
        print(f"Error running full scenario: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_scenario.py --task='<task>' --session_id=<session_id>")
        sys.exit(1)
    
    task = sys.argv[1].split('=', 1)[1] if '=' in sys.argv[1] else sys.argv[1]
    session_id = sys.argv[2].split('=', 1)[1] if '=' in sys.argv[2] else sys.argv[2]
    
    success = run_full_scenario(task, session_id)
    if success:
        print("✓ Full scenario test completed successfully")
    else:
        print("✗ Full scenario test failed")
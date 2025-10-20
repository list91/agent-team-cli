import sys
import os
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from it
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.master import MasterOrchestrator

def test_master_agent(task: str, session_id: str):
    """
    CLI script to test Master agent
    """
    load_dotenv()
    
    try:
        master = MasterOrchestrator(session_id)
        result = master.execute(task)
        
        print(f"Task: {task}")
        print(f"Session ID: {session_id}")
        print(f"Delegated tasks: {result['delegated_tasks']}")
        print(f"Master decision: {result['master_decision'][:200]}...")  # Truncate for readability
        
        return True
            
    except Exception as e:
        print(f"Error testing Master agent: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_master.py --task='<task>' --session_id=<session_id>")
        sys.exit(1)
    
    task = sys.argv[1].split('=', 1)[1] if '=' in sys.argv[1] else sys.argv[1]
    session_id = sys.argv[2].split('=', 1)[1] if '=' in sys.argv[2] else sys.argv[2]
    
    success = test_master_agent(task, session_id)
    if success:
        print("✓ Master agent test completed successfully")
    else:
        print("✗ Master agent test failed")
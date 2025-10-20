import sys
import os
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from it
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.sap_agents import create_agent

def test_sap_agent(agent: str, task: str, session_id: str):
    """
    CLI script to test SAP agent
    """
    load_dotenv()
    
    try:
        sap_agent = create_agent(agent, session_id)
        result = sap_agent.execute_task(task)
        
        print(f"Agent: {agent}")
        print(f"Task: {task}")
        print(f"Session ID: {session_id}")
        print(f"Result: {result['result'][:200]}...")  # Truncate for readability
        
        return True
            
    except Exception as e:
        print(f"Error testing SAP agent {agent}: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python test_sap.py --agent=<agent_name> --task='<task>' --session_id=<session_id>")
        sys.exit(1)
    
    agent = sys.argv[1].split('=', 1)[1] if '=' in sys.argv[1] else sys.argv[1]
    task = sys.argv[2].split('=', 1)[1] if '=' in sys.argv[2] else sys.argv[2]
    session_id = sys.argv[3].split('=', 1)[1] if '=' in sys.argv[3] else sys.argv[3]
    
    success = test_sap_agent(agent, task, session_id)
    if success:
        print("✓ SAP agent test completed successfully")
    else:
        print("✗ SAP agent test failed")
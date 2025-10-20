import sys
import os
import threading
import time
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from it
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow import run_agent_workflow

def run_session(session_id: str, task: str, results: dict, index: int):
    """
    Function to run a single session in a thread
    """
    load_dotenv()
    
    try:
        print(f"Thread {index}: Starting session {session_id} with task: {task}")
        
        result = run_agent_workflow(session_id, task)
        
        results[index] = {
            'session_id': session_id,
            'success': True,
            'result': result
        }
        
        print(f"Thread {index}: Completed session {session_id}")
    except Exception as e:
        print(f"Thread {index}: Error in session {session_id}: {str(e)}")
        results[index] = {
            'session_id': session_id,
            'success': False,
            'error': str(e)
        }

def test_isolation(session_a: str, session_b: str):
    """
    CLI script to test isolation between parallel sessions
    """
    load_dotenv()
    
    try:
        print(f"Testing isolation between sessions: {session_a} and {session_b}")
        
        # Define different tasks for each session to ensure they're doing different things
        task_a = f"Create a health endpoint for session {session_a}"
        task_b = f"Create a user management system for session {session_b}"
        
        # Dictionary to store results from each thread
        results = {}
        
        # Create threads for each session
        thread_a = threading.Thread(target=run_session, args=(session_a, task_a, results, 0))
        thread_b = threading.Thread(target=run_session, args=(session_b, task_b, results, 1))
        
        # Start both threads
        thread_a.start()
        thread_b.start()
        
        # Wait for both threads to complete
        thread_a.join()
        thread_b.join()
        
        # Check results
        success_a = results[0]['success']
        success_b = results[1]['success']
        
        print(f"Session {session_a} success: {success_a}")
        print(f"Session {session_b} success: {success_b}")
        
        if success_a and success_b:
            print("SUCCESS: Both sessions completed successfully - isolation test passed")
            return True
        else:
            print("FAILURE: One or both sessions failed - isolation test failed")
            if not success_a:
                print(f"  Session {session_a} error: {results[0].get('error', 'Unknown error')}")
            if not success_b:
                print(f"  Session {session_b} error: {results[1].get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"Error testing isolation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_isolation.py --session_a=<session_id> --session_b=<session_id>")
        sys.exit(1)
    
    session_a = sys.argv[1].split('=', 1)[1] if '=' in sys.argv[1] else sys.argv[1]
    session_b = sys.argv[2].split('=', 1)[1] if '=' in sys.argv[2] else sys.argv[2]
    
    success = test_isolation(session_a, session_b)
    if success:
        print("SUCCESS: Isolation test completed successfully")
    else:
        print("FAILURE: Isolation test failed")
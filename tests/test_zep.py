import sys
import os
from dotenv import load_dotenv
from memory.zep_client import ZepMemoryManager

def test_zep_memory(session_id: str, agent: str, msg: str = None, read: bool = False):
    """
    CLI script to test Zep memory
    """
    load_dotenv()
    
    try:
        memory_manager = ZepMemoryManager()
        
        if read:
            # Read messages from the agent's memory
            messages = memory_manager.get_all_agent_messages(session_id, agent)
            print(f"Messages for session {session_id}, agent {agent}:")
            for i, message in enumerate(messages):
                print(f"{i+1}. {message}")
            return True
        else:
            # Add a message to the agent's memory
            memory_manager.add_message(session_id, agent, msg)
            print(f"Added message to session {session_id}, agent {agent}")
            
            # Ensure memory limit
            memory_manager.ensure_memory_limit(session_id, agent)
            print(f"Memory limit enforced for session {session_id}, agent {agent}")
            return True
            
    except Exception as e:
        print(f"Error testing Zep memory: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_zep.py --session_id=<session_id> --agent=<agent_name> [--msg='<message>' or --read]")
        sys.exit(1)
    
    session_id = None
    agent = None
    msg = None
    read = False
    
    for arg in sys.argv[1:]:
        if arg.startswith('--session_id='):
            session_id = arg.split('=', 1)[1]
        elif arg.startswith('--agent='):
            agent = arg.split('=', 1)[1]
        elif arg.startswith('--msg='):
            msg = arg.split('=', 1)[1]
        elif arg == '--read':
            read = True
    
    if not session_id or not agent:
        print("Error: session_id and agent are required")
        sys.exit(1)
    
    if not read and not msg:
        print("Error: Either --msg or --read is required")
        sys.exit(1)
    
    success = test_zep_memory(session_id, agent, msg, read)
    if success:
        print("✓ Zep memory test completed successfully")
    else:
        print("✗ Zep memory test failed")
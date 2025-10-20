from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_devops_task():
    """
    Test to specifically check if devops agent is used
    """
    load_dotenv()
    
    session_id = "test_devops_task"
    user_request = """Create a CI/CD pipeline for a Python project with the following requirements:
    
    1. Use GitHub Actions for continuous integration
    2. Set up automated testing with pytest
    3. Create Docker image and push to Docker Hub
    4. Deploy to staging environment on successful tests
    5. Add security scanning with bandit
    6. Configure pre-commit hooks for code quality
    
    The pipeline should be defined in .github/workflows/ci.yml and include all the above steps.
    Also create Dockerfile and requirements.txt for the project."""
    
    print(f"=== TESTING DEVOPS TASK ===")
    print(f"Session ID: {session_id}")
    print(f"Request: {user_request}")
    print("-" * 60)
    
    result = run_agent_workflow(session_id, user_request)
    
    print(f"\nFINAL DECISION: {result.get('final_decision', 'No decision')}")
    print(f"REVIEW NOTES: {result.get('review_notes', 'No review notes')[:200]}...")
    print(f"NUMBER OF AGENT RESULTS: {len(result.get('agent_results', []))}")
    
    print("\nAGENT RESULTS:")
    agent_names = []
    for i, agent_result in enumerate(result.get('agent_results', [])):
        agent_name = agent_result.get('agent_name', 'Unknown')
        task = agent_result.get('task', 'No task')
        result_content = agent_result.get('result', 'No result')
        agent_names.append(agent_name)
        
        print(f"  {i+1}. Agent: {agent_name}")
        print(f"     Task preview: {task[:100]}...")
        print(f"     Result preview: {result_content[:200]}...")
        print(f"     Result length: {len(result_content)} chars")
        print()
    
    print(f"AGENTS USED: {set(agent_names)}")
    
    # Check workspace artifacts
    import os
    workspace_path = f"./workspace/{session_id}/"
    if os.path.exists(workspace_path):
        files = os.listdir(workspace_path)
        print(f"\nFILES IN WORKSPACE {workspace_path}: {files}")
    else:
        print(f"\nWORKSPACE {workspace_path} DOES NOT EXIST")
    
    return result

if __name__ == "__main__":
    test_devops_task()
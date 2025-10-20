from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_task2_detailed():
    """
    Detailed test for Task 2: Auto dependency update system
    Expected: Master should delegate to Researcher, BackendDev, Tester, DocWriter, DevOps
    """
    load_dotenv()
    
    session_id = "task2_detailed"
    user_request = """Разработай систему автоматического обновления зависимостей с проверкой совместимости и регрессионных тестов.
    Мастер поручает Researcher'у собрать данные о breaking changes в релизах, BackendDev'у — написать скрипт обновления `requirements.txt`, Tester'у — запустить регрессионные тесты до/после обновления, DocWriter'у — отчёт об изменениях, DevOpsAgent'у — GitHub Action для автоматического PR с обновлением."""
    
    print(f"=== TESTING TASK 2: Auto Dependency Update System ===")
    print(f"Session: {session_id}")
    print(f"Request length: {len(user_request)} chars")
    print("-" * 60)
    
    result = run_agent_workflow(session_id, user_request)
    
    print(f"\nFINAL DECISION: {result.get('final_decision', 'No decision')}")
    print(f"NUMBER OF AGENT RESULTS: {len(result.get('agent_results', []))}")
    
    print("\nAGENT RESULTS:")
    for i, agent_result in enumerate(result.get('agent_results', [])):
        agent_name = agent_result.get('agent_name', 'Unknown')
        task = agent_result.get('task', 'No task')
        result_content = agent_result.get('result', 'No result')
        
        print(f"  {i+1}. Agent: {agent_name}")
        print(f"     Task preview: {task[:100]}...")
        print(f"     Result preview: {result_content[:200]}...")
        print(f"     Artifacts created: {agent_result.get('artifacts_created', [])}")
        print(f"     Result length: {len(result_content)} chars")
        print()
    
    # Check for expected agents
    agent_names = [ar.get('agent_name', '') for ar in result.get('agent_results', [])]
    print(f"AGENTS USED: {set(agent_names)}")
    
    # Expected agents based on the requirement
    expected_agents = {'researcher', 'backend_dev', 'tester', 'doc_writer', 'devops'}
    actual_agents = set(agent_names)
    
    print(f"EXPECTED AGENTS: {expected_agents}")
    print(f"ACTUAL AGENTS: {actual_agents}")
    print(f"MISSING AGENTS: {expected_agents - actual_agents}")
    print(f"EXTRA AGENTS: {actual_agents - expected_agents}")
    
    # Check workspace artifacts
    import os
    workspace_path = f"./workspace/{session_id}/"
    if os.path.exists(workspace_path):
        files = os.listdir(workspace_path)
        print(f"\nFILES IN WORKSPACE {workspace_path}: {files}")
        
        # Let's also check the content of the execution checkpoints
        if 'execution_checkpoints.json' in files:
            try:
                import json
                with open(f"{workspace_path}/execution_checkpoints.json", 'r', encoding='utf-8') as f:
                    checkpoints = json.load(f)
                    print(f"EXECUTION CHECKPOINTS: {checkpoints}")
            except Exception as e:
                print(f"Error reading checkpoints: {e}")
    else:
        print(f"\nWORKSPACE {workspace_path} DOES NOT EXIST")
    
    return result

if __name__ == "__main__":
    test_task2_detailed()
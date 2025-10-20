from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_task11_simple():
    """
    Simple test for Task 11: License compliance auditing utility
    """
    load_dotenv()
    
    session_id = "task11_simple"
    user_request = """Создай утилиту для аудита и автоматического исправления лицензионной совместимости зависимостей.
    CLI-инструмент `license-audit`, который:
    license-audit --path ./project --policy ./license-policy.yaml
    → проверяет `requirements.txt`, `package.json`,  
    → сравнивает лицензии с политикой (например, «запрещены GPL, разрешены MIT/Apache»),  
    → предлагает замены (например, `gpl-lib` → `mit-alternative`),  
    → генерирует отчёт `compliance_report.md`.

    Делегирование:
    - Researcher: собрать базу данных лицензий и их совместимости (SPDX).
    - BackendDev: реализовать парсер зависимостей + движок правил.
    - Tester: проверить обработку транзитивных зависимостей.
    - DocWriter: шаблон `license-policy.yaml` и объяснение лицензионных рисков.
    - DevOpsAgent: интеграция в pre-commit hook и CI.

    Мастер проверяет:  
    - отчёт точно указывает нарушения,  
    - предложенные замены действительно совместимы,  
    - утилита не модифицирует код без согласия (только предлагает патчи)."""
    
    print(f"=== TESTING TASK 11: License Compliance Utility ===")
    print(f"Session: {session_id}")
    print(f"Request length: {len(user_request)} chars")
    print("-" * 60)
    
    try:
        result = run_agent_workflow(session_id, user_request)
        
        print(f"\nFINAL DECISION: {result.get('final_decision', 'No decision')}")
        print(f"NUMBER OF AGENT RESULTS: {len(result.get('agent_results', []))}")
        
        print("\nAGENT RESULTS:")
        for i, agent_result in enumerate(result.get('agent_results', [])):
            agent_name = agent_result.get('agent_name', 'Unknown')
            task = agent_result.get('task', 'No task')
            
            print(f"  {i+1}. Agent: {agent_name}")
            print(f"     Task preview: {task[:100]}...")
            
        # Check for expected agents
        agent_names = [ar.get('agent_name', '') for ar in result.get('agent_results', [])]
        print(f"\nAGENTS USED: {set(agent_names)}")
        
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
        else:
            print(f"\nWORKSPACE {workspace_path} DOES NOT EXIST")
        
        return result
    except Exception as e:
        print(f"Error in test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_task11_simple()
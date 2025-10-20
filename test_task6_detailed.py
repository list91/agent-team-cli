from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_task6_detailed():
    """
    Detailed test for Task 6: Secure secrets management utility
    Expected: Master should delegate to Researcher, BackendDev, Tester, DocWriter, DevOps
    """
    load_dotenv()
    
    session_id = "task6_detailed"
    user_request = """Создай утилиту для безопасного управления секретами в CLI-проектах.
    Инструмент vault-cli, который шифрует .env-файлы с помощью мастер-пароля и позволяет безопасно хранить их в Git.
    
    Что должен сделать мастер-агент:
    Делегировать Researcher:
    Изучить подходы: git-crypt, sops, age.
    Выбрать алгоритм (например, AES-256-GCM + PBKDF2).
    
    Делегировать BackendDev:
    Реализовать vault-cli encrypt .env --output .env.vault и vault-cli decrypt .env.vault --output .env.
    Хранить соль и IV в заголовке файла.
    Поддержка пароля через getpass() (без логгирования).
    
    Делегировать Tester:
    Написать тесты на:
    корректность round-trip (encrypt → decrypt → совпадение),
    устойчивость к подбору пароля (slow KDF),
    отказ при неверном пароле.
    
    Делегировать DocWriter:
    Написать SECURITY_MODEL.md с описанием криптографии.
    Пример .gitignore и workflow для команды.
    
    Делегировать DevOpsAgent:
    Создать setup.py и pyproject.toml для установки через pip install vault-cli.
    Добавить pre-commit hook для запрета коммита .env.
    
    Мастер проверяет:
    Утилита не оставляет временных файлов,
    Зашифрованный файл нельзя расшифровать без пароля,
    Установка через pip работает."""
    
    print(f"=== TESTING TASK 6: Detailed ===")
    print(f"Session: {session_id}")
    print(f"Request: {user_request[:100]}...")
    print("-" * 60)
    
    result = run_agent_workflow(session_id, user_request)
    
    print(f"\nFINAL DECISION: {result.get('final_decision', 'No decision')}")
    print(f"REVIEW NOTES: {result.get('review_notes', 'No review notes')[:200]}...")
    print(f"NUMBER OF AGENT RESULTS: {len(result.get('agent_results', []))}")
    
    print("\nAGENT RESULTS:")
    for i, agent_result in enumerate(result.get('agent_results', [])):
        agent_name = agent_result.get('agent_name', 'Unknown')
        task = agent_result.get('task', 'No task')
        result_content = agent_result.get('result', 'No result')
        
        print(f"  {i+1}. Agent: {agent_name}")
        print(f"     Task preview: {task[:100]}...")
        print(f"     Result preview: {result_content[:200]}...")
        print(f"     Result length: {len(result_content)} chars")
        print()
    
    # Check for expected agents
    agent_names = [ar.get('agent_name', '') for ar in result.get('agent_results', [])]
    print(f"AGENTS USED: {set(agent_names)}")
    
    # Expected agents based on the requirement: researcher, backend_dev, tester, doc_writer, devops
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
        
        # Let's also look at the content of the files if there are any
        for file in files:
            file_path = os.path.join(workspace_path, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"  Content of {file}: {content[:200]}...")
            except:
                print(f"  Could not read {file}")
    else:
        print(f"\nWORKSPACE {workspace_path} DOES NOT EXIST")
    
    return result

if __name__ == "__main__":
    test_task6_detailed()
from dotenv import load_dotenv
from workflow import run_agent_workflow
import uuid

def test_multilevel_architecture():
    """
    Test the multilevel architecture with comprehensive task processing
    """
    load_dotenv()
    
    session_id = f"test_multilevel_{uuid.uuid4().hex[:8]}"
    user_request = """Создай CLI-инструмент для автоматической генерации unit-тестов к существующему Python-коду с учётом покрытия и edge cases.
    
    Мастер делегирует Researcher'у изучить best practices по генерации тестов (pytest, coverage), BackendDev'у — реализовать генератор на основе AST-анализа, Tester'у — проверить корректность и покрытие, DocWriter'у — документацию по использованию, DevOpsAgent'у — интеграцию в pre-commit hook."""
    
    print(f"=== TESTING MULTILEVEL ARCHITECTURE ===")
    print(f"Session ID: {session_id}")
    print(f"Request: {user_request}")
    print("-" * 60)
    
    try:
        result = run_agent_workflow(session_id, user_request)
        
        print("\n=== FINAL RESULT ===")
        print(f"Decision: {result.get('final_decision', 'No final decision')}")
        print(f"Review notes: {result.get('review_notes', 'No review notes')[:200]}...")
        
        # Check agent results
        agent_results = result.get('agent_results', [])
        print(f"\nNumber of agent results: {len(agent_results)}")
        
        for i, agent_result in enumerate(agent_results):
            agent_name = agent_result.get('agent_name', 'Unknown')
            task = agent_result.get('task', 'No task')
            result_content = agent_result.get('result', 'No result')
            
            print(f"\n{i+1}. Agent: {agent_name}")
            print(f"   Task: {task[:100]}...")
            print(f"   Result: {result_content[:200]}...")
            
            # Check quality validation
            quality_validation = agent_result.get('quality_validation', {})
            if quality_validation:
                print(f"   Quality Score: {quality_validation.get('quality_score', 'N/A')}")
                print(f"   Valid: {quality_validation.get('valid', 'N/A')}")
            
            # Check self-assessment
            self_assessment = agent_result.get('self_assessment', {})
            if self_assessment:
                print(f"   Self-Assessment Score: {self_assessment.get('performance_score', 'N/A')}")
        
        # Check if all expected agents participated
        expected_agents = {'researcher', 'backend_dev', 'tester', 'doc_writer', 'devops'}
        actual_agents = {ar.get('agent_name', '') for ar in agent_results}
        
        print(f"\nExpected agents: {expected_agents}")
        print(f"Actual agents: {actual_agents}")
        print(f"Missing agents: {expected_agents - actual_agents}")
        
        # Check workspace artifacts
        import os
        workspace_path = f"./workspace/{session_id}/"
        if os.path.exists(workspace_path):
            files = os.listdir(workspace_path)
            print(f"\nWorkspace files: {files}")
        else:
            print(f"\nNo workspace directory found")
            
        return result
        
    except Exception as e:
        print(f"Error running workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_multilevel_architecture()
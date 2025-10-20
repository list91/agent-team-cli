#!/usr/bin/env python3
"""
Tester Agent - MSP Agent for validating results of other agents
"""
import argparse
import json
import sys
import time
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_contract import AgentContract
from src.fallbacks import get_fallback_config, get_timestamp

config = get_fallback_config()


class TesterAgent(AgentContract):
    """
    Agent responsible for validating results of other agents
    """

    def __init__(self, scratchpad_path: Path, max_scratchpad_chars: int = None, bridge_manager=None):
        super().__init__(scratchpad_path, max_scratchpad_chars, bridge_manager)
        self.validation_results = {}

    def execute(self, task: dict, allowed_tools: list, clarification_endpoint: str = None) -> dict:
        """
        Execute the testing/validation task
        :param task: Task description with context
        :param allowed_tools: List of allowed tools
        :param clarification_endpoint: Clarification endpoint URL
        :return: Result dictionary
        """
        original_request = task.get("description", "")
        produced_files = task.get("produced_files", [])
        context_from_producers = task.get("context_from_producers", {})
        validation_level = task.get("context", {}).get("validation_level", "standard")

        # Write initial status to scratchpad
        self.scratchpad.append(f"[{get_timestamp()}] Tester Agent started\n")
        self.scratchpad.append(f"[{get_timestamp()}] Validating files: {produced_files}\n")
        self.scratchpad.append(f"[{get_timestamp()}] Validation level: {validation_level}\n")
        
        # Analyze original request to form validation criteria
        validation_criteria = self._form_validation_criteria(original_request, context_from_producers)
        self.scratchpad.append(f"[{get_timestamp()}] Formed validation criteria: {list(validation_criteria.keys())}\n")
        
        # Validate each artifact
        issues = []
        validated_files = []
        
        for file_path_str in produced_files:
            file_path = Path(file_path_str)
            if not file_path.exists():
                issues.append(f"File does not exist: {file_path}")
                continue
                
            self.scratchpad.append(f"[{get_timestamp()}] Validating {file_path.name}...\n")
            
            # Perform validation based on file type and validation level
            file_issues = self._validate_file(file_path, validation_criteria, validation_level, allowed_tools)
            issues.extend(file_issues)
            
            if not file_issues:
                validated_files.append(str(file_path))
        
        # Calculate quality score
        total_files = len(produced_files)
        valid_files = len(validated_files)
        quality_score = valid_files / total_files if total_files > 0 else 1.0
        
        # Prepare result
        result = {
            "status": "failed" if issues else "success",
            "quality_score": quality_score,
            "issues": issues,
            "validated_files": validated_files
        }
        
        # If issues found, suggest fixes based on the problems
        if issues:
            result["suggested_fixes"] = self._suggest_fixes(issues, produced_files)
        
        self.scratchpad.append(f"[{get_timestamp()}] Validation completed. Quality score: {quality_score}\n")
        if issues:
            self.scratchpad.append(f"[{get_timestamp()}] Found {len(issues)} issues\n")
        
        return {
            "status": "failed" if issues else "success",
            "result": result,
            "produced_files": []
        }
    
    def _form_validation_criteria(self, original_request: str, context: dict) -> Dict[str, Any]:
        """
        Form validation criteria based on original request
        :param original_request: Original task description
        :param context: Context from producing agents
        :return: Dictionary of validation criteria
        """
        criteria = {}
        request_lower = original_request.lower()
        
        # Functional requirements
        if "crud" in request_lower or "create" in request_lower or "manage" in request_lower:
            criteria["has_crud_endpoints"] = True
        if "fastapi" in request_lower:
            criteria["has_fastapi_import"] = True
        if "docker" in request_lower:
            criteria["has_dockerfile"] = True
        if "documentation" in request_lower or "readme" in request_lower:
            criteria["has_documentation"] = True
        
        # Technical requirements
        if "port" in request_lower and "8000" in request_lower:
            criteria["uses_port_8000"] = True
        if "no authentication" in request_lower or "without auth" in request_lower:
            criteria["no_auth_required"] = True
        
        # Add any criteria from context
        criteria.update(context.get("validation_criteria", {}))
        
        return criteria
    
    def _validate_file(self, file_path: Path, criteria: Dict, validation_level: str, allowed_tools: List[str]) -> List[str]:
        """
        Validate a single file based on criteria and validation level
        :param file_path: Path to the file to validate
        :param criteria: Validation criteria
        :param validation_level: Level of validation (basic, standard, deep)
        :param allowed_tools: List of allowed tools
        :return: List of issues found
        """
        issues = []

        # Try to read file with error handling
        try:
            content = file_path.read_text(encoding='utf-8')
        except (IOError, PermissionError) as e:
            issues.append(f"Cannot read file {file_path.name}: Permission denied or I/O error")
            return issues
        except UnicodeDecodeError as e:
            issues.append(f"File {file_path.name} contains invalid UTF-8 encoding")
            return issues
        except Exception as e:
            issues.append(f"Error reading file {file_path.name}: {str(e)}")
            return issues
        
        # Basic validation - check file exists and has content
        if not content.strip():
            issues.append(f"File {file_path.name} is empty")
            return issues
        
        # Validate based on file extension
        if file_path.suffix == '.py':
            issues.extend(self._validate_python_file(file_path, content, criteria, validation_level, allowed_tools))
        elif file_path.name.lower() == 'dockerfile':
            issues.extend(self._validate_dockerfile(file_path, content, criteria))
        elif file_path.suffix in ['.md', '.txt']:
            issues.extend(self._validate_documentation_file(file_path, content, criteria))
        elif file_path.suffix in ['.yaml', '.yml']:
            issues.extend(self._validate_yaml_file(file_path, content, criteria))
        
        # Check against specific criteria if they apply to this file
        if criteria.get("uses_port_8000") and "Dockerfile" in str(file_path):
            if "8000" not in content:
                issues.append("Dockerfile does not expose port 8000")
        elif criteria.get("has_fastapi_import") and file_path.suffix == ".py":
            if "from fastapi" not in content and "import fastapi" not in content:
                issues.append(f"Python file {file_path.name} does not contain FastAPI import")
        
        return issues
    
    def _validate_python_file(self, file_path: Path, content: str, criteria: Dict, validation_level: str, allowed_tools: List[str]) -> List[str]:
        """
        Validate Python file
        """
        issues = []
        
        # Basic syntax check if shell is allowed
        if "shell" in allowed_tools:
            tmp_path = None
            try:
                # Create a temporary file to check syntax
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name

                # Run syntax check using Python
                result = subprocess.run([sys.executable, "-m", "py_compile", tmp_path],
                                      capture_output=True, text=True, timeout=config.syntax_check_timeout_seconds)

                if result.returncode != 0:
                    issues.append(f"Python syntax error in {file_path.name}: {result.stderr}")

            except subprocess.TimeoutExpired:
                issues.append(f"Python syntax check timeout for {file_path.name}")
            except FileNotFoundError:
                issues.append(f"Python interpreter not found for syntax check of {file_path.name}")
            except PermissionError as e:
                issues.append(f"Permission denied during syntax check of {file_path.name}")
            except (IOError, OSError) as e:
                issues.append(f"I/O error during syntax check of {file_path.name}: {str(e)}")
            except Exception as e:
                issues.append(f"Error during syntax check of {file_path.name}: {str(e)}")
            finally:
                # Always clean up temp file
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass  # Ignore cleanup errors
        else:
            # If shell is not allowed, do basic checks
            if criteria.get("has_fastapi_import") and "from fastapi" not in content and "import fastapi" not in content:
                issues.append(f"Python file {file_path.name} does not contain FastAPI import")
        
        # Check for basic CRUD operations if required
        if criteria.get("has_crud_endpoints"):
            crud_patterns = ["@app.get", "@app.post", "@app.put", "@app.delete"]
            has_crud = any(pattern in content for pattern in crud_patterns)
            if not has_crud:
                issues.append(f"Python file {file_path.name} does not contain CRUD endpoints")
        
        return issues
    
    def _validate_dockerfile(self, file_path: Path, content: str, criteria: Dict) -> List[str]:
        """
        Validate Dockerfile
        """
        issues = []
        
        if criteria.get("uses_port_8000") and "EXPOSE 8000" not in content:
            issues.append(f"Dockerfile does not expose port 8000")
        
        if "EXPOSE " not in content:
            issues.append(f"Dockerfile does not expose any port")
        
        if "CMD [" not in content and "ENTRYPOINT [" not in content:
            issues.append(f"Dockerfile does not have CMD or ENTRYPOINT")
        
        return issues
    
    def _validate_documentation_file(self, file_path: Path, content: str, criteria: Dict) -> List[str]:
        """
        Validate documentation file
        """
        issues = []
        
        if not content.strip():
            issues.append(f"Documentation file {file_path.name} is empty")
        
        return issues
    
    def _validate_yaml_file(self, file_path: Path, content: str, criteria: Dict) -> List[str]:
        """
        Validate YAML file
        """
        issues = []

        try:
            import yaml
        except ImportError:
            issues.append(f"Cannot validate YAML file {file_path.name}: yaml module not installed")
            return issues

        try:
            parsed = yaml.safe_load(content)
            if parsed is None:
                issues.append(f"YAML file {file_path.name} is empty or invalid")
        except yaml.YAMLError as e:
            issues.append(f"YAML file {file_path.name} has parsing errors: {str(e)}")
        except Exception as e:
            issues.append(f"Unexpected error parsing YAML file {file_path.name}: {str(e)}")

        return issues
    
    def _suggest_fixes(self, issues: List[str], produced_files: List[str]) -> List[Dict[str, Any]]:
        """
        Suggest fixes based on the issues found
        :param issues: List of issues
        :param produced_files: List of produced files
        :return: List of suggested fixes
        """
        fixes = []
        
        for issue in issues:
            # Determine which agent likely created the problematic file
            agent = "coder"
            if "Dockerfile" in issue:
                agent = "packager"
            elif "documentation" in issue.lower() or "readme" in issue.lower():
                agent = "documenter"
            
            fixes.append({
                "agent": agent,
                "issue": issue,
                "suggestion": f"Fix the issue: {issue}"
            })
        
        return fixes


def main():
    parser = argparse.ArgumentParser(description="Tester Agent - MSP Validation Agent")
    parser.add_argument("--task", required=True, help="Task JSON string")
    parser.add_argument("--scratchpad-path", required=True, help="Path to scratchpad file")
    parser.add_argument("--max-scratchpad-chars", type=int, default=config.max_scratchpad_chars, help="Max scratchpad characters")
    parser.add_argument("--allowed-tools", default="", help="Comma-separated list of allowed tools")
    parser.add_argument("--clarification-endpoint", help="HTTP endpoint for clarification requests")
    parser.add_argument("--bridge-dir", help="Path to shared bridge directory for inter-agent communication")

    args = parser.parse_args()

    # Parse task
    task = json.loads(args.task)
    allowed_tools = args.allowed_tools.split(",") if args.allowed_tools else []

    # Create bridge manager if bridge directory provided
    bridge_manager = None
    if args.bridge_dir:
        from bridge import BridgeManager
        bridge_manager = BridgeManager(Path(args.bridge_dir))

    # Create and run the tester agent
    agent = TesterAgent(Path(args.scratchpad_path), max_scratchpad_chars=args.max_scratchpad_chars, bridge_manager=bridge_manager)
    result = agent.execute(task, allowed_tools, args.clarification_endpoint)

    # Output result as JSON to stdout
    print(json.dumps(result))


if __name__ == "__main__":
    main()
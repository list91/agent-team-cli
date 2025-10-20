"""
Debug script to see what qwen actually returns
"""
import subprocess
import logging

logging.basicConfig(level=logging.DEBUG)

# Simulated master prompt
master_prompt = """You are a Master Orchestrator in an MSP (Multi-Specialist) system."""

user_prompt = """
Task: Создай простой Python REST API с одним endpoint /hello который возвращает {"message": "Hello World"}

Available Agents:
- coder: basic file operations, code generation
- documenter: documentation writing
- echo: basic task execution
- tester: testing and validation

Analyze this task and determine:
1. Which agents are needed?
2. What subtask should each agent work on?
3. What bridges (communication channels) are needed between agents?
4. What is the complexity level (1-10)?
5. What execution strategy should be used?

CRITICAL INSTRUCTION: You MUST respond with ONLY a valid JSON object. Do NOT include any explanatory text, markdown formatting, or additional commentary before or after the JSON. Your entire response should be parseable as JSON.

Required JSON format:
{
  "complexity": 4,
  "strategy": "flat_delegation",
  "agents": [
    {
      "name": "coder",
      "subtask": "Implement REST API with CRUD operations",
      "priority": 1,
      "tools": ["file_write", "shell"]
    }
  ],
  "bridges": [
    {
      "from": "coder",
      "to": "documenter",
      "type": "api_specification",
      "purpose": "Share API endpoints"
    }
  ],
  "reasoning": "Explanation of your decisions"
}

Remember: Output ONLY the JSON object, nothing else.
"""

combined_prompt = f"{master_prompt}\n\n{user_prompt}"

print("=" * 80)
print("CALLING QWEN...")
print("=" * 80)

cmd = [
    r"C:\Users\Дарья\AppData\Roaming\npm\qwen.cmd",
    "-p", combined_prompt,
    "-y"
]

try:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = proc.communicate(timeout=120)

    print("\n" + "=" * 80)
    print("QWEN STDOUT:")
    print("=" * 80)
    print(stdout)
    print("\n" + "=" * 80)
    print(f"STDOUT LENGTH: {len(stdout)} chars")
    print("=" * 80)

    if stderr:
        print("\n" + "=" * 80)
        print("QWEN STDERR:")
        print("=" * 80)
        print(stderr)
        print("=" * 80)

    print(f"\nReturn code: {proc.returncode}")

    # Try to find JSON
    print("\n" + "=" * 80)
    print("SEARCHING FOR JSON...")
    print("=" * 80)

    import json
    import re

    # Try balanced braces
    potential_jsons = []
    brace_count = 0
    start_idx = None

    for i, char in enumerate(stdout):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx is not None:
                potential_jsons.append(stdout[start_idx:i+1])
                start_idx = None

    print(f"Found {len(potential_jsons)} potential JSON objects")

    for idx, json_str in enumerate(potential_jsons):
        print(f"\n--- Candidate {idx + 1} ---")
        print(f"Length: {len(json_str)}")
        print(f"Preview: {json_str[:200]}...")
        try:
            parsed = json.loads(json_str)
            print(f"✅ Valid JSON")
            print(f"Keys: {list(parsed.keys())}")
            if 'agents' in parsed:
                print(f"✅ Has 'agents' field")
                print(f"Agents: {parsed['agents']}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")

except subprocess.TimeoutExpired:
    print("❌ Timeout!")
    proc.kill()
except Exception as e:
    print(f"❌ Error: {e}")

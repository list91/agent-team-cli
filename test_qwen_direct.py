"""
Тестируем разные способы вызова qwen CLI
"""
import subprocess

# Вариант 1: Один промпт без разделения на system/user
prompt1 = """Execute this task immediately and return ONLY a JSON response.

Task: Analyze this request and return JSON with agents needed.
Request: "Создай простой Python REST API с одним endpoint /hello"

Available agents: coder, documenter, echo, tester

Return ONLY this JSON structure (no other text):
{
  "complexity": 3,
  "strategy": "flat_delegation",
  "agents": [
    {"name": "coder", "subtask": "Create API", "priority": 1, "tools": ["file_write"]}
  ],
  "bridges": [],
  "reasoning": "Simple API task"
}

IMPORTANT: Output ONLY the JSON object above. No explanations, no questions, ONLY JSON."""

# Вариант 2: Еще более прямой
prompt2 = """Return this JSON and nothing else:
{
  "complexity": 3,
  "strategy": "flat_delegation",
  "agents": [{"name": "coder", "subtask": "Create API", "priority": 1, "tools": ["file_write"]}],
  "bridges": [],
  "reasoning": "Test"
}"""

# Вариант 3: Через stdin
prompt3 = """Output JSON:
{"complexity": 3, "agents": [{"name": "coder", "subtask": "test", "priority": 1}], "bridges": [], "reasoning": "test", "strategy": "flat_delegation"}"""

qwen_cmd = r"C:\Users\Дарья\AppData\Roaming\npm\qwen.cmd"

for idx, prompt in enumerate([prompt1, prompt2, prompt3], 1):
    print(f"\n{'='*80}")
    print(f"ВАРИАНТ {idx}")
    print(f"{'='*80}")
    print(f"Prompt length: {len(prompt)}")

    try:
        proc = subprocess.Popen(
            [qwen_cmd, "-p", prompt, "-y"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(timeout=30)

        print(f"\nSTDOUT ({len(stdout)} chars):")
        print(stdout)

        # Ищем JSON
        import json
        import re

        brace_count = 0
        start_idx = None
        potential_jsons = []

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

        if potential_jsons:
            print(f"\n✅ Found {len(potential_jsons)} potential JSON(s)")
            for json_str in potential_jsons:
                try:
                    parsed = json.loads(json_str)
                    print(f"✅ Valid JSON with keys: {list(parsed.keys())}")
                    if 'agents' in parsed:
                        print(f"✅✅ HAS AGENTS FIELD!")
                except:
                    print(f"❌ Invalid JSON")
        else:
            print("❌ No JSON found")

    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT")
        proc.kill()
    except Exception as e:
        print(f"❌ ERROR: {e}")

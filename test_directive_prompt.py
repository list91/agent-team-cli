"""
Быстрый тест директивного промпта для qwen
"""
import subprocess
from pathlib import Path
import uuid

qwen_cmd = r"C:\Users\Дарья\AppData\Roaming\npm\qwen.cmd"
project_root = Path.cwd()
temp_dir = project_root / ".qwen_temp"
temp_dir.mkdir(exist_ok=True)

call_id = uuid.uuid4().hex[:8]
output_file = temp_dir / f"response_{call_id}.json"

# ДИРЕКТИВНЫЙ промпт
task = f"""EXECUTE THIS TASK IMMEDIATELY. DO NOT ASK QUESTIONS. DO NOT WAIT FOR APPROVAL. JUST DO IT NOW.

YOUR ROLE: You are a Master Orchestrator analyzing tasks.

YOUR TASK: Analyze this simple task: "Создай файл test.py"
Determine which agents needed: coder, documenter, or tester.

WHAT YOU MUST DO RIGHT NOW:
1. Analyze the task
2. Formulate response as JSON
3. CREATE FILE '.qwen_temp/response_{call_id}.json' with this JSON:
{{
  "complexity": 2,
  "agents": [{{"name": "coder", "subtask": "Create test.py", "priority": 1}}],
  "bridges": [],
  "reasoning": "Simple file creation"
}}
4. The file MUST contain ONLY valid JSON, no markdown, no explanations
5. After creating the file, EXIT

DO NOT:
- Ask "what should I do next"
- Wait for user input
- Explain what you're doing
- Ask for confirmation

START WORKING NOW. CREATE THE FILE. DO IT."""

print("=" * 80)
print("TESTING DIRECTIVE PROMPT WITH QWEN")
print("=" * 80)
print(f"Output file: {output_file}")
print(f"Call ID: {call_id}")
print("\nCalling qwen...")

try:
    proc = subprocess.Popen(
        [qwen_cmd, "-p", task, "--approval-mode", "yolo"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = proc.communicate(timeout=60)

    print("\n" + "=" * 80)
    print("QWEN COMPLETED")
    print("=" * 80)
    print(f"Return code: {proc.returncode}")
    print(f"\nSTDOUT ({len(stdout)} chars):")
    print(stdout[:500])

    if stderr:
        print(f"\nSTDERR:")
        print(stderr[:300])

    print("\n" + "=" * 80)
    print("CHECKING FOR OUTPUT FILE")
    print("=" * 80)

    if output_file.exists():
        content = output_file.read_text()
        print(f"✅ FILE CREATED!")
        print(f"Size: {len(content)} chars")
        print(f"Content:\n{content}")

        import json
        try:
            parsed = json.loads(content)
            print(f"\n✅ VALID JSON!")
            print(f"Keys: {list(parsed.keys())}")
            if 'agents' in parsed:
                print(f"✅✅ HAS AGENTS FIELD!")
                print(f"SUCCESS!!!")
        except:
            print(f"❌ Invalid JSON")
    else:
        print(f"❌ FILE NOT CREATED")
        print(f"Expected: {output_file}")

        # Check if any files created
        print(f"\nFiles in .qwen_temp/:")
        for f in temp_dir.iterdir():
            print(f"  - {f.name}")

except subprocess.TimeoutExpired:
    print("\n❌ TIMEOUT")
    proc.kill()
except Exception as e:
    print(f"\n❌ ERROR: {e}")

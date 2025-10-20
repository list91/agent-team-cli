"""
Тест qwen через stdin
"""
import subprocess
import sys

prompt = """Return ONLY this JSON (no other text or actions):
{"complexity": 3, "agents": [{"name": "coder", "subtask": "test", "priority": 1, "tools": ["file_write"]}], "bridges": [], "reasoning": "test", "strategy": "flat_delegation"}"""

qwen_cmd = r"C:\Users\Дарья\AppData\Roaming\npm\qwen.cmd"

print("Calling qwen via stdin...")
print(f"Prompt: {prompt}")
print("=" * 80)

try:
    # Попробуем с --approval-mode plan (только планирование, без выполнения)
    proc = subprocess.Popen(
        [qwen_cmd, "-y", "--approval-mode", "plan"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = proc.communicate(input=prompt, timeout=15)

    print("STDOUT:")
    print(stdout)
    print("\nSTDERR:")
    print(stderr)
    print(f"\nReturn code: {proc.returncode}")

except subprocess.TimeoutExpired:
    print("TIMEOUT - qwen hangs")
    proc.kill()
    stdout, stderr = proc.communicate()
    print(f"Partial stdout: {stdout[:500]}")
except Exception as e:
    print(f"ERROR: {e}")

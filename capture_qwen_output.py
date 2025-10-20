#!/usr/bin/env python
"""Capture real qwen stdout from subprocess"""

import subprocess
from pathlib import Path

# Simple prompt
prompt = """You are a Master Orchestrator.

Task: Create hello.py file.

Respond with ONLY valid JSON. No explanations, no markdown, just JSON."""

print(f"Running qwen with prompt...")
print(f"Prompt length: {len(prompt)}")

qwen_path = r"C:\Users\Дарья\AppData\Roaming\npm\qwen.cmd"

result = subprocess.run(
    [qwen_path, "-p", prompt, "--approval-mode", "yolo"],
    cwd=Path.cwd(),
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace',
    timeout=60
)

print("\n=== STDOUT ===")
print(f"Length: {len(result.stdout)}")
print(f"Content:\n{result.stdout}")

print("\n=== STDERR ===")
print(f"Length: {len(result.stderr)}")
print(f"Content:\n{result.stderr[:500]}")

# Save to file
Path("qwen_stdout.txt").write_text(result.stdout, encoding='utf-8')
Path("qwen_stderr.txt").write_text(result.stderr, encoding='utf-8')

print("\n✅ Saved to qwen_stdout.txt and qwen_stderr.txt")

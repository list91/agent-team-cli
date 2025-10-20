#!/usr/bin/env python3
"""Debug test"""
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent))

from agents.available.coder.agent import CoderAgent

with tempfile.TemporaryDirectory() as tmpdir:
    scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
    agent = CoderAgent(scratchpad_path)

    task = {
        "description": "Create a FastAPI service with CRUD operations",
        "context": {"type": "code_generation"}
    }
    allowed_tools = ["file_read", "file_write"]

    result = agent.execute(task, allowed_tools)

    print("Result status:", result["status"])
    print("Produced files:", result.get("produced_files", []))

    main_py = Path(tmpdir) / "main.py"
    print("Main.py exists?", main_py.exists())

    print("\nScratchpad content:")
    if scratchpad_path.exists():
        print(scratchpad_path.read_text())

    print("\nFiles in tmpdir:")
    for f in Path(tmpdir).iterdir():
        print(f"  {f.name}")

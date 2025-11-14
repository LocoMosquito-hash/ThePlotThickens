#!/usr/bin/env python3
"""Debug multi-line condition parsing."""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))

from CSA import ConditionalStructureAnalyzer

analyzer = ConditionalStructureAnalyzer()
text = """if (condition1 and
    condition2):
    do_something()
else:
    do_else()"""

print("Text to parse:")
print(text)
print("\n" + "="*60)

try:
    block = analyzer.analyze_conditional(text)
    print(f"Branches found: {block.get_branch_count()}")
    for i, branch in enumerate(block.branches):
        print(f"\nBranch {i}:")
        print(f"  Type: {branch.branch_type}")
        print(f"  Condition: {branch.condition}")
        print(f"  Start: {branch.start_line}, End: {branch.end_line}")
        print(f"  Content: {branch.content_lines}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()


#!/usr/bin/env python3
"""
Detailed debug script to understand line structure and indexing.
"""

import sys
import tempfile
import shutil
from pathlib import Path

sys.path.append('..')

from flow_tracer import FlowTracer
from start_label_finder import StartLabelFinder

def detailed_debug():
    """Debug the exact line structure and indexing."""
    # Create a simple test project
    test_dir = tempfile.mkdtemp()
    project_root = Path(test_dir)
    game_dir = project_root / 'game'
    game_dir.mkdir(exist_ok=True)

    script_content = '''
label start:
    "Hello, world!"
    "This is a test."
    return
'''

    script_path = game_dir / 'script.rpy'
    script_path.write_text(script_content)

    print('=== DETAILED LINE STRUCTURE DEBUG ===')
    
    # Read the file back and show exact structure
    content_back = script_path.read_text()
    lines = content_back.split('\n')
    
    print(f'File content:')
    print(repr(content_back))
    print(f'\nLine by line:')
    for i, line in enumerate(lines):
        print(f'  Line {i+1}: "{line}"')
    
    # Now test start label finder
    start_finder = StartLabelFinder(str(project_root))
    start_location = start_finder.get_start_location()
    print(f'\nStartLabelFinder result: {start_location}')
    
    # Get the parsed lines from the parser
    tracer = FlowTracer(str(project_root))
    parsed_lines = tracer._get_file_lines('game\\script.rpy')
    
    print(f'\nParsed lines from RenpyParser:')
    for i, renpy_line in enumerate(parsed_lines):
        print(f'  Index {i} (Line {i+1}): "{renpy_line.content}" -> {renpy_line.line_type}')
    
    # Test flow tracer step by step
    print(f'\nFlowTracer tracing:')
    result = tracer.trace_from_start(max_steps=10)
    
    print(f'Start location: {result.start_location}')
    print(f'Steps: {len(result.steps)}')
    print(f'Stop reason: {result.stop_reason}')
    
    for i, step in enumerate(result.steps):
        print(f'  Step {i+1}: Line {step.line_number} [{step.statement_type}] "{step.content}"')

    # Cleanup
    shutil.rmtree(test_dir)

if __name__ == "__main__":
    detailed_debug() 
#!/usr/bin/env python3
"""
Debug script for FlowTracer to understand implementation issues.
"""

import sys
import tempfile
import shutil
from pathlib import Path

sys.path.append('..')

from flow_tracer import FlowTracer
from start_label_finder import StartLabelFinder

def debug_simple_test():
    """Debug a simple flow tracer test."""
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

    print('=== DEBUGGING FLOW TRACER ===')
    print(f'Project: {project_root}')
    
    try:
        # First check start finder
        start_finder = StartLabelFinder(str(project_root))
        start_location = start_finder.get_start_location()
        print(f'Start location from finder: {start_location}')
        
        # Now test flow tracer
        tracer = FlowTracer(str(project_root))
        result = tracer.trace_from_start()
        
        print(f'Start location from tracer: {result.start_location}')
        print(f'Steps: {len(result.steps)}')
        print(f'Stop reason: {result.stop_reason}')
        
        print('\nDetailed steps:')
        for i, step in enumerate(result.steps):
            print(f'  {i+1}. Line {step.line_number}: [{step.statement_type}] "{step.content}"')
            if step.parsed_data:
                print(f'      Parsed data: {step.parsed_data}')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

    # Cleanup
    shutil.rmtree(test_dir)


def debug_statement_classification():
    """Debug statement classification."""
    test_dir = tempfile.mkdtemp()
    project_root = Path(test_dir)
    game_dir = project_root / 'game'
    game_dir.mkdir(exist_ok=True)

    script_content = '''
label start:
    scene bg room
    
    "Empty line above"
    # This is a comment
    return
'''

    script_path = game_dir / 'script.rpy'
    script_path.write_text(script_content)

    print('\n=== DEBUGGING STATEMENT CLASSIFICATION ===')
    
    try:
        tracer = FlowTracer(str(project_root))
        
        # Test classification directly
        test_statements = [
            'label start:',
            'scene bg room',
            '',
            '"Empty line above"',
            '# This is a comment',
            'return'
        ]
        
        print('Testing statement classification:')
        for stmt in test_statements:
            stmt_type, parsed_data = tracer._classify_statement(stmt)
            print(f'  "{stmt}" -> [{stmt_type}] {parsed_data}')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

    # Cleanup
    shutil.rmtree(test_dir)


if __name__ == "__main__":
    debug_simple_test()
    debug_statement_classification() 
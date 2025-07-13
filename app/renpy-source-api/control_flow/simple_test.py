#!/usr/bin/env python3

import sys
import tempfile
import shutil
from pathlib import Path

sys.path.append('..')

try:
    from flow_tracer import FlowTracer
    print("✅ FlowTracer imported successfully")
    
    # Create a simple test project
    test_dir = tempfile.mkdtemp()
    project_root = Path(test_dir)
    game_dir = project_root / 'game'
    game_dir.mkdir(exist_ok=True)

    script_content = '''label start:
    "Hello, world!"
    return
'''

    script_path = game_dir / 'script.rpy'
    script_path.write_text(script_content)
    print("✅ Test project created")

    # Test FlowTracer
    tracer = FlowTracer(str(project_root))
    print("✅ FlowTracer initialized")
    
    result = tracer.trace_from_start()
    print(f"✅ Trace completed: {len(result.steps)} steps")
    
    for i, step in enumerate(result.steps):
        print(f"  {i+1}. Line {step.line_number}: [{step.statement_type}] {step.content}")

    # Cleanup
    shutil.rmtree(test_dir)
    print("✅ Test completed successfully")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 
#!/usr/bin/env python3
"""
Detailed debug script to trace each iteration of the flow tracing.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to import flow_tracer
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from flow_tracer import FlowTracer, FlowStep, FlowTraceResult

def create_test_project():
    """Create a simple test project."""
    test_dir = tempfile.mkdtemp()
    project_root = Path(test_dir)
    game_dir = project_root / 'game'
    game_dir.mkdir(exist_ok=True)
    
    script_content = '''
label start:
    "Beginning of story"
    jump middle_scene
    "This should not be reached"

label middle_scene:
    "Middle of the story"
    "More dialogue"
    jump ending

label ending:
    "The end"
    return
'''
    
    script_path = game_dir / 'script.rpy'
    script_path.write_text(script_content)
    
    return str(project_root)

class DetailedFlowTracer(FlowTracer):
    """Extended FlowTracer with detailed debugging."""
    
    def trace_flow_debug(self, max_steps: int = 100) -> FlowTraceResult:
        """Modified trace_flow with detailed debug output."""
        print(f"\n🔍 Starting detailed trace (max_steps={max_steps})")
        
        start_file, start_line = self.start_location
        steps = []
        visited_labels = set()
        
        print(f"   📍 Starting at {start_file}:{start_line}")
        
        try:
            # Get the file containing the start label
            current_file_lines = self._get_file_lines(start_file)
            
            # Start from the start label itself (convert to 0-based index)
            current_line_idx = start_line - 1  # start_line is 1-based, convert to 0-based
            current_file = start_file
            
            print(f"   📂 Loaded {len(current_file_lines)} lines from {current_file}")
            print(f"   ⬇️  Starting at line index {current_line_idx} (line {current_line_idx + 1})")
            
            step_count = 0
            
            while step_count < max_steps:
                print(f"\n   🔄 Iteration {step_count + 1}:")
                print(f"      Current position: {current_file}:{current_line_idx + 1}")
                
                # Check if we're still within the current file
                if current_line_idx >= len(current_file_lines):
                    print(f"      ❌ End of file reached ({current_line_idx} >= {len(current_file_lines)})")
                    return FlowTraceResult(
                        start_location=self.start_location,
                        steps=steps,
                        stop_reason="end_of_file",
                        stop_location=(current_file, current_line_idx + 1),
                        total_lines_traced=len(steps)
                    )
                
                # Get current line
                current_renpy_line = current_file_lines[current_line_idx]
                content = current_renpy_line.content.strip()
                
                print(f"      📄 Line content: '{content}'")
                print(f"      🏷️  Parser type: '{current_renpy_line.line_type}'")
                
                # Classify the statement - use both our classifier and the parser's classification
                stmt_type, parsed_data = self._classify_statement(content)
                
                print(f"      🔍 Our classification: '{stmt_type}' with data: {parsed_data}")
                
                # Handle cases where RenpyParser classified jumps as "choice_jump"
                if current_renpy_line.line_type == 'choice_jump' and stmt_type == 'unknown':
                    stmt_type = 'jump'
                    # Re-parse the jump target
                    jump_match = self.statement_patterns['jump'].match(content)
                    if jump_match:
                        parsed_data = {'target': jump_match.group(1)}
                    print(f"      🔧 Fixed classification: '{stmt_type}' with data: {parsed_data}")
                
                # Also handle return statements that might be classified as "choice_return"
                if current_renpy_line.line_type == 'choice_return' and stmt_type == 'unknown':
                    stmt_type = 'return'
                    print(f"      🔧 Fixed classification: '{stmt_type}'")
                
                # Create flow step
                step = FlowStep(
                    line_number=current_line_idx + 1,
                    file_path=current_file,
                    content=content,
                    statement_type=stmt_type,
                    parsed_data=parsed_data
                )
                steps.append(step)
                
                print(f"      ✅ Added step: {stmt_type} - '{content}'")
                
                # Special handling for jump statements - follow the jump
                if stmt_type == 'jump' and parsed_data and 'target' in parsed_data:
                    target_label = parsed_data['target']
                    
                    print(f"      🎯 Processing jump to '{target_label}'")
                    
                    # Check for infinite jump loops
                    jump_key = f"{current_file}:{current_line_idx + 1}->{target_label}"
                    if jump_key in visited_labels:
                        print(f"      🔄 Infinite loop detected: {jump_key}")
                        return FlowTraceResult(
                            start_location=self.start_location,
                            steps=steps,
                            stop_reason="infinite_jump_loop",
                            stop_location=(current_file, current_line_idx + 1),
                            total_lines_traced=len(steps),
                            flow_control_encountered='jump'
                        )
                    
                    visited_labels.add(jump_key)
                    print(f"      📝 Marked jump as visited: {jump_key}")
                    
                    # Find the target label location
                    target_location = self._find_label_location(target_label, current_file)
                    
                    if target_location is None:
                        print(f"      ❌ Target label '{target_label}' not found")
                        return FlowTraceResult(
                            start_location=self.start_location,
                            steps=steps,
                            stop_reason="jump_target_not_found",
                            stop_location=(current_file, current_line_idx + 1),
                            total_lines_traced=len(steps),
                            flow_control_encountered='jump'
                        )
                    
                    # Jump to the target label
                    target_file, target_line = target_location
                    print(f"      ✈️  Jumping to {target_file}:{target_line}")
                    
                    # If jumping to a different file, load it
                    if target_file != current_file:
                        print(f"      📂 Loading new file: {target_file}")
                        current_file = target_file
                        current_file_lines = self._get_file_lines(current_file)
                        print(f"      📄 Loaded {len(current_file_lines)} lines")
                    
                    # Jump to the target label line (convert to 0-based index)
                    current_line_idx = target_line - 1
                    step_count += 1
                    print(f"      ⬇️  New position: line {current_line_idx + 1}")
                    continue  # Continue tracing from the jump target
                
                # Check if this is a flow control statement (excluding jumps, which we handle above)
                if stmt_type in self.flow_control_statements:
                    print(f"      🛑 Flow control statement encountered: {stmt_type}")
                    return FlowTraceResult(
                        start_location=self.start_location,
                        steps=steps,
                        stop_reason=f"flow_control_{stmt_type}",
                        stop_location=(current_file, current_line_idx + 1),
                        total_lines_traced=len(steps),
                        flow_control_encountered=stmt_type
                    )
                
                # Move to next line
                current_line_idx += 1
                step_count += 1
                print(f"      ⬇️  Moving to next line: {current_line_idx + 1}")
            
            # Max steps reached
            print(f"      ⚠️  Max steps reached ({max_steps})")
            return FlowTraceResult(
                start_location=self.start_location,
                steps=steps,
                stop_reason="max_steps_reached",
                stop_location=(current_file, current_line_idx + 1),
                total_lines_traced=len(steps)
            )
            
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return FlowTraceResult(
                start_location=self.start_location,
                steps=steps,
                stop_reason=f"error: {str(e)}",
                total_lines_traced=len(steps)
            )

def main():
    """Run detailed debug."""
    print("🔧 Detailed Jump Following Debug")
    print("=" * 50)
    
    project = create_test_project()
    
    try:
        tracer = DetailedFlowTracer(project)
        result = tracer.trace_flow_debug(max_steps=15)
        
        print(f"\n📊 Final Result:")
        print(f"   Stop reason: {result.stop_reason}")
        print(f"   Flow control: {result.flow_control_encountered}")
        print(f"   Total steps: {len(result.steps)}")
        
        print(f"\n📝 All traced steps:")
        for i, step in enumerate(result.steps, 1):
            print(f"   {i:2d}. [{step.statement_type:10}] Line {step.line_number}: '{step.content}'")
            if step.parsed_data:
                print(f"       Data: {step.parsed_data}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(project)

if __name__ == "__main__":
    main() 
# Isolated Testing Methodology for Flow Visualizer Components

**Created**: November 10, 2025  
**Status**: Active Development Guide  
**Component**: All Flow Visualizer Components (CSAP, CMAP, Label Parsing, etc.)

---

## Overview

This document provides a systematic methodology for debugging and testing Flow Visualizer components in isolation. This approach enables fast feedback loops and precise bug identification without the overhead of running the full GUI application.

### When to Use Isolated Testing

- ✅ Component appears to work in isolation but fails in integration
- ✅ Need to reproduce a bug reported by users
- ✅ Testing new parsing logic or grammar changes
- ✅ Debugging data transformation pipelines
- ✅ Investigating why specific game content fails to parse
- ✅ Performance profiling of specific components

---

## Core Principles

### 1. **Layered Isolation**

Test each layer of the system separately:

```
User Report → Full Pipeline Test → Component Test → Unit Test
```

### 2. **Fast Feedback Loops**

Create scripts that run in seconds, not minutes:

- No GUI initialization
- Direct function calls
- Minimal dependencies

### 3. **Capture and Compare**

Save intermediate data to files:

- Extracted content before parsing
- Parsed structures after transformation
- Final visualization data

### 4. **Progressive Narrowing**

Start broad, end narrow:

1. Does the full pipeline work?
2. Which component is failing?
3. What input causes the failure?
4. What line of code is the problem?

### 5. **Reproducible Test Cases**

Create standalone scripts that:

- Can be run by others
- Don't require specific game installations
- Include the exact input that causes failure

---

## Testing Component: CSAP (Screen Parsing)

### Scenario 1: Screen Not Showing Elements

**Symptom**: A screen appears empty in the Flow Visualizer, but should have buttons/hotspots.

#### **Step 1: Full Pipeline Test**

Create `test_game_screen_load.py`:

```python
#!/usr/bin/env python3
"""
Test full pipeline for a specific game and screen.
"""
import sys
import os

# Fix encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_specific_screen():
    """Test a specific screen through the full pipeline."""

    game_path = r"T:\AG\YourGame-pc"
    target_screen = "problematic_screen_name"

    print(f"Testing screen '{target_screen}' from game: {game_path}")
    print("=" * 70)

    try:
        from renpy_data_adapter import RenpyFlowDataAdapter

        # Create adapter and analyze game
        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        viz_data = adapter.analyze_project(game_path, use_sdk=False)

        # Look for the screen in visualization data
        screen_found = False
        for node in viz_data.nodes:
            if node.display_name and target_screen in node.display_name:
                print(f"\n✅ FOUND: {node.display_name}")
                print(f"   Type: {node.node_type}")
                print(f"   Metadata: {node.metadata}")
                screen_found = True
                break

        if not screen_found:
            print(f"\n❌ ERROR: Screen '{target_screen}' not found in visualization data")
            print("\n📋 Available screens (first 10):")
            screen_nodes = [n for n in viz_data.nodes
                          if n.display_name and 'Screen:' in n.display_name]
            for i, node in enumerate(screen_nodes[:10]):
                print(f"   {i+1}. {node.display_name}")

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(test_specific_screen())
```

**Run it**:

```powershell
cd ideas-lab\flow-visualizer-poc
python test_game_screen_load.py
```

#### **Step 2: Isolate CSAP**

If the screen isn't found, test CSAP directly. Create `test_csap_isolated.py`:

```python
#!/usr/bin/env python3
"""
Test CSAP parsing with manual screen content.
"""
import sys

def test_csap_parsing():
    """Test CSAP with a known screen structure."""

    # Copy the exact screen definition from your .rpy file
    screen_text = """screen problem_screen():
    modal True
    imagemap:
        ground "background.png"
        hotspot(100, 100, 200, 200) action Jump("label1")
        hotspot(400, 100, 200, 200) action Jump("label2")
"""

    print("Testing CSAP with manual screen content...")
    print("=" * 70)

    try:
        from csap.csap_parser import CSAPParser
        from csap.csap_compatibility import convert_csap_to_screen_structure

        # Parse with CSAP
        parser = CSAPParser()
        screen_node = parser.parse_screen_text(screen_text)

        print(f"\n📊 CSAP Parse Results:")
        print(f"   Screen name: {screen_node.screen_name}")
        print(f"   Elements: {len(screen_node.elements)}")

        if len(screen_node.elements) == 0:
            print(f"\n❌ BUG: CSAP parsed 0 elements")
            return 1

        # Show element details
        for i, elem in enumerate(screen_node.elements):
            print(f"   {i+1}. {type(elem).__name__}")
            if hasattr(elem, 'hotspots'):
                print(f"      └─ Contains {len(elem.hotspots)} hotspots")

        # Test conversion to ScreenStructure
        print(f"\n🔄 Testing Conversion to ScreenStructure...")
        screen_structure = convert_csap_to_screen_structure(screen_node, "test.rpy")
        print(f"   ScreenStructure elements: {len(screen_structure.elements)}")

        if len(screen_structure.elements) == 0:
            print(f"\n❌ BUG: Conversion produced 0 elements")
            return 1

        for i, elem in enumerate(screen_structure.elements):
            print(f"   {i+1}. {elem.element_type} -> {elem.destination}")

        print(f"\n✅ SUCCESS: CSAP is working correctly")

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(test_csap_parsing())
```

#### **Step 3: Capture Real Extraction**

If CSAP works in isolation but fails with real game content, capture what's being extracted.

**Add to `csap_integration.py`** (temporary debug):

```python
# In parse_screen_structure method, after screen_content extraction:
if 'problematic_screen' in screen_name:
    # Save extracted content
    debug_file = f"debug_extracted_{screen_name}.txt"
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(screen_content)
    print(f"[DEBUG] Saved extracted content to {debug_file}")

    # Print key info
    print(f"[DEBUG] Content length: {len(screen_content)}")
    print(f"[DEBUG] First 200 chars: {screen_content[:200]}")
    print(f"[DEBUG] Last 200 chars: {screen_content[-200:]}")
```

Then create `test_extracted_content.py`:

```python
#!/usr/bin/env python3
"""
Test CSAP with extracted content from real game load.
"""

def test_with_extracted():
    """Test CSAP with the exact content extracted during game load."""

    # Read the extracted content
    with open("debug_extracted_problematic_screen.txt", 'r', encoding='utf-8') as f:
        screen_text = f.read()

    print(f"Testing with extracted content ({len(screen_text)} chars)...")

    from csap.csap_parser import CSAPParser

    parser = CSAPParser()
    screen_node = parser.parse_screen_text(screen_text)

    print(f"Result: {len(screen_node.elements)} elements")

    if len(screen_node.elements) == 0:
        print("\n❌ Reproduced the bug with extracted content!")
        print("\nNow compare this file with your manual test.")
        print("Look for:")
        print("  - Extra newlines")
        print("  - Missing lines")
        print("  - Incorrect indentation")
        print("  - Extra content at the end")

    return 0

if __name__ == "__main__":
    test_with_extracted()
```

---

## Testing Component: CMAP (Menu Parsing)

### Scenario 2: Menu Choices Not Appearing or Wrong Destinations

**Symptom**: Menu choices are missing, duplicated, or point to wrong destinations.

#### **Step 1: Full Pipeline Test**

Create `test_menu_parsing.py`:

```python
#!/usr/bin/env python3
"""
Test menu parsing for a specific game.
"""

def test_menu_in_game():
    """Test menu parsing through the full pipeline."""

    game_path = r"T:\AG\YourGame-pc"
    target_label = "label_with_menu"  # Label that contains the problematic menu

    print(f"Testing menu parsing for label '{target_label}'")
    print("=" * 70)

    try:
        from renpy_data_adapter import RenpyFlowDataAdapter

        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        viz_data = adapter.analyze_project(game_path, use_sdk=False)

        # Look for the label
        target_node = None
        for node in viz_data.nodes:
            if node.display_name and target_label in node.display_name:
                target_node = node
                break

        if not target_node:
            print(f"❌ Label '{target_label}' not found")
            return 1

        print(f"\n✅ Found label: {target_node.display_name}")
        print(f"   Node ID: {target_node.node_id}")

        # Find menu containers associated with this label
        menu_containers = [n for n in viz_data.nodes
                          if n.node_type == 'menu_container'
                          and target_label in n.node_id]

        print(f"\n📋 Menu containers: {len(menu_containers)}")
        for i, menu in enumerate(menu_containers):
            print(f"   {i+1}. {menu.display_name}")

            # Find choices in this menu
            choices = [n for n in viz_data.nodes
                      if n.node_type == 'choice_button'
                      and menu.node_id in n.node_id]

            print(f"      └─ Choices: {len(choices)}")
            for j, choice in enumerate(choices):
                print(f"         {j+1}. {choice.display_name}")

                # Find where this choice leads
                edges = [e for e in viz_data.edges if e.from_node == choice.node_id]
                if edges:
                    target = next((n for n in viz_data.nodes
                                 if n.node_id == edges[0].to_node), None)
                    if target:
                        print(f"            → {target.display_name}")
                else:
                    print(f"            → ⚠️ No destination!")

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    test_menu_in_game()
```

#### **Step 2: Isolate CMAP**

Create `test_cmap_isolated.py`:

```python
#!/usr/bin/env python3
"""
Test CMAP (Custom Menu AST Parser) in isolation.
"""

def test_cmap_parsing():
    """Test CMAP with a specific menu structure."""

    # Copy the exact menu from your .rpy file
    menu_text = """menu:
    "First choice":
        jump label1
    "Second choice":
        $ variable = True
        jump label2
    "Third choice" if condition:
        call screen some_screen
"""

    print("Testing CMAP with manual menu content...")
    print("=" * 70)

    try:
        from csap.cmap_parser import CMAPParser

        parser = CMAPParser()
        menu_node = parser.parse_menu(menu_text)

        print(f"\n📊 CMAP Parse Results:")
        print(f"   Choices: {len(menu_node.choices)}")

        for i, choice in enumerate(menu_node.choices):
            print(f"   {i+1}. Text: {choice.text}")
            print(f"      Condition: {choice.condition or 'None'}")
            print(f"      Destination: {choice.destination or 'inline code'}")
            if choice.has_inline_code:
                print(f"      Has inline code: {choice.has_inline_code}")

        if len(menu_node.choices) == 0:
            print(f"\n❌ BUG: CMAP parsed 0 choices")
            return 1

        print(f"\n✅ SUCCESS: CMAP is working correctly")

    except Exception as e:
        print(f"\n❌ CMAP Parse Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    test_cmap_parsing()
```

#### **Step 3: Extract Real Menu from File**

Create `extract_menu_from_file.py`:

```python
#!/usr/bin/env python3
"""
Extract a specific menu from a .rpy file for testing.
"""

def extract_menu(file_path, line_number):
    """Extract menu starting at line_number from file."""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the menu start
    menu_start = line_number - 1  # Convert to 0-based

    # Extract until we hit something at the same or lower indentation
    base_indent = len(lines[menu_start]) - len(lines[menu_start].lstrip())
    menu_lines = [lines[menu_start]]

    for i in range(menu_start + 1, len(lines)):
        line = lines[i]
        if not line.strip():  # Empty line
            menu_lines.append(line)
            continue

        indent = len(line) - len(line.lstrip())
        if indent <= base_indent:
            break

        menu_lines.append(line)

    menu_text = ''.join(menu_lines)

    # Save to file
    output_file = f"extracted_menu_line_{line_number}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(menu_text)

    print(f"Extracted menu ({len(menu_lines)} lines) to: {output_file}")
    print("\nContent:")
    print(menu_text)

    return menu_text

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python extract_menu_from_file.py <file_path> <line_number>")
        sys.exit(1)

    file_path = sys.argv[1]
    line_number = int(sys.argv[2])

    extract_menu(file_path, line_number)
```

**Usage**:

```powershell
python extract_menu_from_file.py "T:\AG\YourGame-pc\game\script.rpy" 150
```

Then test with `test_cmap_isolated.py` using the extracted content.

---

## Testing Component: Label Parsing

### Scenario 3: Label Not Found or Wrong Connections

**Symptom**: A label exists in the game but doesn't appear in the visualizer, or has incorrect connections.

#### **Step 1: Check if Label is Parsed**

Create `test_label_detection.py`:

```python
#!/usr/bin/env python3
"""
Test if a specific label is detected by the parser.
"""

def test_label_detection():
    """Check if a label is found and parsed correctly."""

    game_path = r"T:\AG\YourGame-pc"
    target_label = "problematic_label"

    print(f"Searching for label '{target_label}' in game: {game_path}")
    print("=" * 70)

    try:
        # Test with regex parser
        from app.renpy_source_api.parser import RenpyParser

        parser = RenpyParser()
        game_data = parser.parse_project(game_path)

        # Search for the label
        label_found = False
        for file_path, file_data in game_data.items():
            for label in file_data.get('labels', []):
                if label['name'] == target_label:
                    print(f"\n✅ FOUND in {file_path}")
                    print(f"   Line: {label['line']}")
                    print(f"   Name: {label['name']}")
                    print(f"   Flows: {label.get('flows', [])}")
                    label_found = True
                    break
            if label_found:
                break

        if not label_found:
            print(f"\n❌ Label '{target_label}' not found by regex parser")
            print("\nPossible reasons:")
            print("  1. Label uses dot notation (e.g., 'namespace.label')")
            print("  2. Label is dynamically generated")
            print("  3. Typo in label name")
            print("  4. File not in game/common directories")
            return 1

        # Now check if it makes it to the flow graph
        from renpy_data_adapter import RenpyFlowDataAdapter

        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        viz_data = adapter.analyze_project(game_path, use_sdk=False)

        found_in_viz = False
        for node in viz_data.nodes:
            if node.display_name and target_label in node.display_name:
                print(f"\n✅ Found in visualization data:")
                print(f"   Display name: {node.display_name}")
                print(f"   Node type: {node.node_type}")
                found_in_viz = True
                break

        if not found_in_viz:
            print(f"\n⚠️ Label parsed but NOT in visualization data")
            print("   Check flow graph integration logic")

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    test_label_detection()
```

#### **Step 2: Test Flow Connections**

Create `test_label_flows.py`:

```python
#!/usr/bin/env python3
"""
Test flow connections for a specific label.
"""

def test_label_flows():
    """Check what flows into and out of a label."""

    game_path = r"T:\AG\YourGame-pc"
    target_label = "problematic_label"

    print(f"Testing flows for label '{target_label}'")
    print("=" * 70)

    try:
        from renpy_data_adapter import RenpyFlowDataAdapter

        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        viz_data = adapter.analyze_project(game_path, use_sdk=False)

        # Find the label node
        target_node = None
        for node in viz_data.nodes:
            if node.display_name and target_label in node.display_name:
                target_node = node
                break

        if not target_node:
            print(f"❌ Label not found in visualization data")
            return 1

        print(f"\n✅ Found: {target_node.display_name}")
        print(f"   Node ID: {target_node.node_id}")
        print(f"   Type: {target_node.node_type}")

        # Find incoming connections
        incoming = [e for e in viz_data.edges if e.to_node == target_node.node_id]
        print(f"\n📥 Incoming connections: {len(incoming)}")
        for edge in incoming:
            source = next((n for n in viz_data.nodes if n.node_id == edge.from_node), None)
            if source:
                print(f"   ← {source.display_name} ({edge.edge_type})")

        # Find outgoing connections
        outgoing = [e for e in viz_data.edges if e.from_node == target_node.node_id]
        print(f"\n📤 Outgoing connections: {len(outgoing)}")
        for edge in outgoing:
            target = next((n for n in viz_data.nodes if n.node_id == edge.to_node), None)
            if target:
                print(f"   → {target.display_name} ({edge.edge_type})")

        if len(incoming) == 0:
            print(f"\n⚠️ WARNING: No incoming connections (orphan label)")

        if len(outgoing) == 0:
            print(f"\n⚠️ WARNING: No outgoing connections (dead end)")

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    test_label_flows()
```

---

## Performance Profiling

### Scenario 4: Parsing is Slow

Create `profile_parsing.py`:

```python
#!/usr/bin/env python3
"""
Profile parsing performance for a specific game.
"""
import time

def profile_game_parsing():
    """Profile each stage of game parsing."""

    game_path = r"T:\AG\YourGame-pc"

    print(f"Profiling game: {game_path}")
    print("=" * 70)

    from renpy_data_adapter import RenpyFlowDataAdapter

    # Profile adapter creation
    start = time.time()
    adapter = RenpyFlowDataAdapter(use_hybrid=True)
    print(f"\n⏱️ Adapter creation: {time.time() - start:.2f}s")

    # Profile project analysis
    start = time.time()
    viz_data = adapter.analyze_project(game_path, use_sdk=False)
    total_time = time.time() - start
    print(f"⏱️ Project analysis: {total_time:.2f}s")

    # Show statistics
    print(f"\n📊 Results:")
    print(f"   Nodes: {len(viz_data.nodes)}")
    print(f"   Edges: {len(viz_data.edges)}")
    print(f"   Avg time per node: {total_time / len(viz_data.nodes) * 1000:.2f}ms")

    # Break down by node type
    node_types = {}
    for node in viz_data.nodes:
        node_types[node.node_type] = node_types.get(node.node_type, 0) + 1

    print(f"\n📋 Node types:")
    for node_type, count in sorted(node_types.items(), key=lambda x: -x[1]):
        print(f"   {node_type}: {count}")

if __name__ == "__main__":
    profile_game_parsing()
```

---

## Best Practices

### 1. **Always Test Both Isolation and Integration**

```python
# Isolation test (component alone)
test_csap_isolated()

# Integration test (full pipeline)
test_game_screen_load()
```

### 2. **Save Intermediate Data to Files**

```python
# Save for comparison
with open("debug_before.txt", 'w') as f:
    f.write(data_before_transform)

with open("debug_after.txt", 'w') as f:
    f.write(data_after_transform)
```

### 3. **Use Descriptive Test File Names**

```
test_csap_imagemap_hotspots.py
test_cmap_conditional_choices.py
test_label_dot_notation.py
extract_menu_from_file.py
```

### 4. **Include Context in Debug Output**

```python
print(f"[{component}] Stage: {stage_name}")
print(f"  Input: {input_summary}")
print(f"  Output: {output_summary}")
print(f"  Expected: {expected}")
```

### 5. **Make Tests Reproducible**

Include the exact input data in the test file:

```python
# Bad: Relies on external file
with open("some_file.rpy") as f:
    content = f.read()

# Good: Self-contained
content = """label test:
    "Hello"
    menu:
        "Yes":
            jump label2
"""
```

### 6. **Clean Up After Testing**

```python
# Remove test scripts when done
test_*.py
debug_*.txt
extracted_*.txt
```

---

## Template: Generic Component Test

```python
#!/usr/bin/env python3
"""
Template for testing any Flow Visualizer component.

Replace COMPONENT_NAME, test content, and import paths.
"""
import sys
import os

# Fix encoding on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def test_component_isolated():
    """Test COMPONENT_NAME in isolation."""

    # Your test input
    test_input = """
    # Paste exact Ren'Py code here
    """

    print("Testing COMPONENT_NAME...")
    print("=" * 70)

    try:
        # Import your component
        from some.module import YourComponent

        # Initialize
        component = YourComponent()

        # Parse/process
        result = component.process(test_input)

        # Validate
        print(f"\n📊 Results:")
        print(f"   Type: {type(result)}")
        print(f"   Length/Count: {len(result)}")

        # Check for expected output
        if len(result) == 0:
            print(f"\n❌ BUG: Got empty result")
            return 1

        # Show details
        for i, item in enumerate(result):
            print(f"   {i+1}. {item}")

        print(f"\n✅ SUCCESS")
        return 0

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

def test_component_in_pipeline():
    """Test COMPONENT_NAME through full pipeline."""

    game_path = r"T:\AG\TestGame-pc"

    print(f"Testing COMPONENT_NAME with game: {game_path}")
    print("=" * 70)

    try:
        from renpy_data_adapter import RenpyFlowDataAdapter

        adapter = RenpyFlowDataAdapter(use_hybrid=True)
        viz_data = adapter.analyze_project(game_path, use_sdk=False)

        # Check results
        print(f"\n📊 Pipeline Results:")
        print(f"   Nodes: {len(viz_data.nodes)}")
        print(f"   Edges: {len(viz_data.edges)}")

        # Add specific checks for your component's output

        return 0

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    print("Running isolated test...\n")
    result1 = test_component_isolated()

    print("\n" + "=" * 70)
    print("Running pipeline test...\n")
    result2 = test_component_in_pipeline()

    sys.exit(max(result1, result2))
```

---

## Troubleshooting Common Issues

### Issue: "Module not found" when running test scripts

**Solution**: Run from the correct directory

```powershell
cd ideas-lab\flow-visualizer-poc
python test_your_script.py
```

### Issue: Unicode errors on Windows

**Solution**: Always include encoding fix at top of scripts

```python
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
```

### Issue: Test works but real game fails

**Solution**: Extract the exact content from the real game

1. Add debug file save in integration layer
2. Run game load
3. Test with extracted content
4. Compare with manual test input

### Issue: Need to test specific line from .rpy file

**Solution**: Use the extraction script

```powershell
python extract_menu_from_file.py "path\to\file.rpy" 123
```

---

## Summary

The key to effective debugging is **progressive isolation**:

1. ✅ **Full Pipeline Test** - Does it work end-to-end?
2. ✅ **Component Test** - Does the component work alone?
3. ✅ **Capture Real Data** - What data is actually flowing through?
4. ✅ **Compare** - What's different between working and broken?
5. ✅ **Fix** - Make the minimal change to fix the issue
6. ✅ **Verify** - Rerun all tests to confirm

Create standalone test scripts that:

- Run in seconds
- Don't require GUI
- Save intermediate data
- Can be shared with others
- Use real game content

This methodology has successfully identified and fixed bugs in:

- ✅ CSAP screen parsing (double newlines, comment inclusion)
- ✅ CMAP menu parsing (conditional choices, nested menus)
- ✅ Label detection (dot notation, implicit flows)
- ✅ Encoding issues (BOM detection, UTF-8 handling)

Apply these same techniques to any future debugging scenarios.

---

**Document Version**: 1.0  
**Last Updated**: November 10, 2025

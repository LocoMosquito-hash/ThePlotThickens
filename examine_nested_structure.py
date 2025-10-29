#!/usr/bin/env python3
"""
Examine the actual Ren'Py source code structure around the problematic menus
to understand how nested menus are defined vs. sequential menus.
"""

def examine_menu_structure():
    """Read and analyze the source code around the problematic menu lines."""
    
    file_path = r"T:\AG\sixteenyearslaternb-episode5.3-pc\game\romanceday05script2b_1.rpy"
    
    # Lines of interest from our diagnosis
    problem_lines = [
        (843, "Tell me a bit about [felicia]."),  # Should be parent
        (865, "You are beautiful too."),          # Should be child of above
        (952, "What do you usually do in your free time?"),  # Should be parent  
        (961, "It's not stupid at all.")          # Should be child of above
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("🔍 EXAMINING NESTED MENU STRUCTURE")
        print("=" * 60)
        
        for line_num, description in problem_lines:
            print(f"\n📍 Examining around line {line_num}: {description}")
            print("-" * 50)
            
            # Show context around each problematic line
            start = max(0, line_num - 10)
            end = min(len(lines), line_num + 15)
            
            for i in range(start, end):
                line_content = lines[i].rstrip()
                line_number = i + 1
                
                # Highlight the target line
                if line_number == line_num:
                    print(f">>> {line_number:4d}| {line_content}")
                else:
                    print(f"    {line_number:4d}| {line_content}")
                
                # Look for menu patterns
                if "menu:" in line_content:
                    indent = len(line_content) - len(line_content.lstrip())
                    print(f"         ^^ MENU DETECTED (indent: {indent})")
                elif line_content.strip().startswith('"') and line_content.strip().endswith('":'):
                    indent = len(line_content) - len(line_content.lstrip())
                    print(f"         ^^ CHOICE DETECTED (indent: {indent})")
        
        print("\n🎯 ANALYSIS SUMMARY:")
        print("=" * 40)
        print("Look for patterns in:")
        print("1. Menu indentation levels")
        print("2. Choice indentation levels") 
        print("3. Block structure after choices")
        print("4. How nested menus are introduced")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    examine_menu_structure()

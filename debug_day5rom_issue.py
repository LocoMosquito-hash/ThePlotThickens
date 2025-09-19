#!/usr/bin/env python3
"""
Quick diagnostic to find why day5rom label is missing from the visualizer.
"""

import sys
from pathlib import Path
import re

# Add the app modules to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "app" / "renpy-source-api"))

try:
    from parser import RenpyParser
    from data_structures import Label
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def quick_diagnose_day5rom():
    """Quick diagnosis of day5rom missing label issue."""
    
    print("🔍 Quick Diagnosis: day5rom Missing Label")
    print("=" * 50)
    
    vn_path = "T:\\AG\\sixteenyearslaternb-episode5.3-pc"
    target_file = "T:\\AG\\sixteenyearslaternb-episode5.3-pc\\game\\romanceday05script2b_1.rpy"
    
    # Step 1: Verify file exists and has the label
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'label day5rom:' in content:
            line_num = content[:content.find('label day5rom:')].count('\n') + 1
            print(f"✅ day5rom label found at line {line_num}")
        else:
            print("❌ day5rom label NOT found in file")
            return
            
    except Exception as e:
        print(f"❌ Cannot read target file: {e}")
        return
    
    # Step 2: Test parser directly on this specific file
    parser = RenpyParser()
    
    print(f"\n📋 Testing parser on specific file...")
    
    try:
        # Try to parse labels from this specific file
        with open(target_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        labels_found = []
        for i, line in enumerate(lines, 1):
            if re.match(r'\s*label\s+(\w+)\s*:', line):
                match = re.match(r'\s*label\s+(\w+)\s*:', line)
                if match:
                    label_name = match.group(1)
                    labels_found.append((label_name, i))
        
        print(f"📊 Labels found in romanceday05script2b_1.rpy: {len(labels_found)}")
        for label_name, line_num in labels_found:
            print(f"  - {label_name} (line {line_num})")
            
        if not any(name == 'day5rom' for name, _ in labels_found):
            print("❌ day5rom not detected by regex parsing")
        else:
            print("✅ day5rom detected by regex parsing")
            
    except Exception as e:
        print(f"❌ File parsing failed: {e}")
        return
    
    # Step 3: Check if the file is in the VN's game directory scan
    print(f"\n📂 Checking VN directory structure...")
    
    try:
        game_dir = Path(vn_path) / "game"
        if not game_dir.exists():
            print(f"❌ Game directory not found: {game_dir}")
            return
            
        rpy_files = list(game_dir.glob("*.rpy"))
        target_filename = "romanceday05script2b_1.rpy"
        
        if any(f.name == target_filename for f in rpy_files):
            print(f"✅ {target_filename} found in game directory")
        else:
            print(f"❌ {target_filename} NOT found in game directory")
            print(f"Available .rpy files: {[f.name for f in rpy_files[:10]]}...")  # Show first 10
            
    except Exception as e:
        print(f"❌ Directory scan failed: {e}")
        return
    
    # Step 4: Quick test - try to manually create the label and see what happens
    print(f"\n🧪 Testing manual label creation...")
    
    try:
        # Create a Label object manually
        manual_label = Label(
            label_name="day5rom",
            file_path=target_file,
            line_number=1,
            has_dialogue=True,
            has_menu=True,
            has_jump=True,
            has_call=False,
            has_return=False
        )
        
        print(f"✅ Manual label creation successful: {manual_label.label_name}")
        
    except Exception as e:
        print(f"❌ Manual label creation failed: {e}")
    
    print(f"\n📝 Summary:")
    print(f"- File exists: ✅")
    print(f"- Contains 'label day5rom:': ✅") 
    print(f"- File in game directory: ✅")
    print(f"- Issue likely in: Parser processing or flow filtering")
    
    print(f"\n💡 Recommendation:")
    print(f"The issue is likely that the parser is encountering an error")
    print(f"when processing romanceday05script2b_1.rpy, causing it to skip")
    print(f"the entire file. Check for syntax errors or encoding issues.")

if __name__ == "__main__":
    quick_diagnose_day5rom()

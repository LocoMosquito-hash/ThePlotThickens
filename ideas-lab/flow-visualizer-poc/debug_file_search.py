#!/usr/bin/env python3
"""
Debug script to check Last Call game files and find ch1mckellycar content.
"""

import os
from pathlib import Path

def debug_file_search():
    """Debug file search in Last Call game."""
    
    print("🔍 DEBUGGING LAST CALL FILE SEARCH")
    print("=" * 60)
    
    game_path = Path("T:/AG/LastCall-0.4-pc/game")
    
    print(f"📂 Checking path: {game_path}")
    print(f"   Path exists: {game_path.exists()}")
    
    if not game_path.exists():
        # Try alternative paths
        alt_paths = [
            "T:/AG/LastCall-0.4-pc",
            "T:/AG/LastCall-0.4-pc/game",
        ]
        
        print("🔍 Trying alternative paths:")
        for alt_path in alt_paths:
            path_obj = Path(alt_path)
            print(f"   {alt_path}: {path_obj.exists()}")
            if path_obj.exists():
                print(f"   Contents: {list(path_obj.iterdir())[:10]}")
        return
        
    print(f"📊 Directory contents:")
    files = list(game_path.iterdir())
    print(f"   Total items: {len(files)}")
    
    rpy_files = list(game_path.glob("*.rpy"))
    print(f"   .rpy files: {len(rpy_files)}")
    
    for rpy_file in rpy_files:
        print(f"     {rpy_file.name} ({rpy_file.stat().st_size} bytes)")
        
    print(f"\n📝 Searching for 'ch1mckellycar' in all files:")
    
    # Search in all files, not just .rpy
    for file_path in files:
        if file_path.is_file():
            try:
                # Try different encodings
                content = None
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                        
                if content and 'ch1mckellycar' in content:
                    print(f"   ✅ Found in: {file_path.name}")
                    
                    # Show context around ch1mckellycar
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'ch1mckellycar' in line:
                            print(f"     Line {i+1}: {line.strip()}")
                            
                            # Show menu context
                            if 'label ch1mckellycar:' in line:
                                print(f"     📍 Found label at line {i+1}")
                                # Show next 20 lines to find the menu
                                for j in range(i+1, min(len(lines), i+21)):
                                    if 'menu:' in lines[j]:
                                        print(f"     🎯 Found menu at line {j+1}: '{lines[j].strip()}'")
                                        # Show menu structure
                                        for k in range(j, min(len(lines), j+10)):
                                            print(f"       {k+1:3d}: {lines[k].rstrip()}")
                                        break
                                break
                            
            except Exception as e:
                print(f"   ❌ Error reading {file_path.name}: {e}")
                
    print(f"\n🔍 Also checking for 'menu:' patterns:")
    menu_count = 0
    for file_path in rpy_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            if 'menu:' in content:
                menu_occurrences = content.count('menu:')
                menu_count += menu_occurrences
                print(f"   {file_path.name}: {menu_occurrences} menu occurrences")
                
        except Exception as e:
            print(f"   ❌ Error reading {file_path.name}: {e}")
            
    print(f"\n📊 Total 'menu:' occurrences across all files: {menu_count}")

if __name__ == "__main__":
    debug_file_search() 
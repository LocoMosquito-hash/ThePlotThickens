#!/usr/bin/env python3
"""
Simple test script to debug Ren'Py API character and media data.
"""

import sys
import os
from pathlib import Path

# Add the renpy-source-api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'renpy-source-api'))

from core import RenpyProject

def test_api():
    """Test the Ren'Py API and show what data it returns."""
    
    test_path = r"T:\AG\Savior-0.16c-pc\game"
    
    print(f"Testing with path: {test_path}")
    print("=" * 60)
    
    try:
        # Initialize project
        project = RenpyProject(test_path)
        
        # Analyze
        print("Analyzing project...")
        overview = project.analyze()
        print(f"Analysis complete: {overview.total_characters} characters found")
        
        # Get character stats
        print("\n--- CHARACTER STATS ---")
        character_stats = project.get_character_stats()
        print(f"Character stats loaded: {len(character_stats)} characters")
        
        for code, stats in list(character_stats.items())[:10]:  # Show first 10
            name = stats.get('name', 'N/A')
            dialogue_lines = stats.get('dialogue_lines', 0)
            print(f"  {code}: name='{name}', lines={dialogue_lines}")
        
        # Test assets
        print("\n--- ASSETS ---")
        all_assets = project.get_all_assets()
        
        for category in ['images', 'video']:
            if category in all_assets:
                assets = all_assets[category]
                print(f"{category}: {len(assets)} assets")
                
                # Show sample assets with labels
                for asset in assets[:5]:
                    print(f"  {asset.get('name', 'N/A')} -> label: {asset.get('label', 'N/A')}")
        
        # Test dialogue search
        print("\n--- DIALOGUE SEARCH TEST ---")
        search_results = project.search_dialogue("the", case_sensitive=False)
        print(f"Search results for 'the': {len(search_results)} matches")
        
        for result in search_results[:3]:
            speaker = result.get('speaker', 'N/A')
            dialogue = result.get('dialogue', '')[:50] + "..."
            print(f"  {speaker}: \"{dialogue}\"")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api() 
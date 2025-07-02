#!/usr/bin/env python3
"""
Test script for enhanced character analysis features.
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to Python path for imports
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Try relative imports (when used as package)
    from .core import RenpyProject
    from .config import TEST_VN_PATH, ALTERNATIVE_PATHS
except ImportError:
    # Fall back to direct imports (when run standalone)
    from core import RenpyProject
    from config import TEST_VN_PATH, ALTERNATIVE_PATHS

def get_test_vn_path() -> str:
    """Get the best available test VN path."""
    if os.path.exists(TEST_VN_PATH):
        return TEST_VN_PATH
    
    for name, path in ALTERNATIVE_PATHS.items():
        if os.path.exists(path):
            print(f"Using fallback VN: {name} at {path}")
            return path
    
    return TEST_VN_PATH

def test_enhanced_character_analysis():
    """Test the enhanced character analysis features."""
    print("=" * 70)
    print("ENHANCED CHARACTER ANALYSIS TEST")
    print("=" * 70)
    
    # Get test VN path
    test_vn_path = get_test_vn_path()
    
    if not os.path.exists(test_vn_path):
        print(f"❌ Test VN path doesn't exist: {test_vn_path}")
        print("Please update TEST_VN_PATH in config.py")
        return False
    
    print(f"📁 Testing VN: {test_vn_path}")
    
    try:
        # Initialize project
        project = RenpyProject(test_vn_path)
        project.analyze()
        
        # Test 1: Enhanced Character Stats
        print("\n🔬 Test 1: Enhanced Character Stats")
        print("-" * 40)
        
        char_stats = project.get_character_stats()
        print(f"✅ Enhanced stats calculated for {len(char_stats)} characters")
        
        # Show detailed stats for first few characters
        chars_with_dialogue = [(code, stats) for code, stats in char_stats.items() 
                              if stats["dialogue_lines"] > 0]
        chars_with_dialogue.sort(key=lambda x: x[1]["dialogue_lines"], reverse=True)
        
        print("\n📊 Top Characters by Dialogue (Detailed):")
        for i, (code, stats) in enumerate(chars_with_dialogue[:5]):
            print(f"   {i+1}. {code} ({stats['name']})")
            print(f"      💬 Lines: {stats['dialogue_lines']}")
            print(f"      📝 Words: {stats['word_count']}")
            print(f"      📏 Avg words/line: {stats['average_words_per_line']}")
            print(f"      📂 Files: {len(stats['files_appeared_in'])}")
            print(f"      🏷️  Labels: {len(stats['labels_appeared_in'])}")
            
            if stats['first_appearance']:
                first = stats['first_appearance']
                print(f"      🎬 First: {first['file']}:{first['line']} (label: {first['label']})")
            print()
        
        # Test 2: Top Characters Method
        print("\n🏆 Test 2: Top Characters by Dialogue")
        print("-" * 40)
        
        top_chars = project.get_top_characters_by_dialogue(10)
        print(f"✅ Top {len(top_chars)} characters retrieved")
        
        for i, char in enumerate(top_chars[:8]):
            print(f"   {i+1}. {char['code']} ({char['name']}) - {char['dialogue_lines']} lines, "
                  f"{char['word_count']} words ({char['average_words_per_line']} avg)")
        
        # Test 3: Character Search
        print("\n🔍 Test 3: Character Search by Name")
        print("-" * 40)
        
        # Search for common character names/codes
        search_terms = ["mc", "girl", "woman", "man", "narrator"]
        
        for term in search_terms:
            results = project.get_character_by_name(term)
            if results:
                print(f"   🔍 Search '{term}': {len(results)} matches")
                for result in results[:3]:  # Show top 3 matches
                    print(f"     • {result['code']} ({result['name']}) - {result['dialogue_lines']} lines")
                break
        
        # Test 4: Character Dialogue Retrieval
        print("\n💬 Test 4: Character Dialogue Retrieval")
        print("-" * 40)
        
        if top_chars:
            # Get dialogue for the most talkative character
            main_char = top_chars[0]
            dialogue_lines = project.get_dialogue_for_character(main_char['code'], limit=10)
            
            print(f"✅ Retrieved {len(dialogue_lines)} dialogue lines for {main_char['code']}")
            print(f"   📝 Sample dialogue from {main_char['name']}:")
            
            for i, line in enumerate(dialogue_lines[:5]):
                dialogue_preview = line['dialogue'][:60] + "..." if len(line['dialogue']) > 60 else line['dialogue']
                print(f"     {i+1}. \"{dialogue_preview}\"")
                print(f"        📍 {line['file']}:{line['line_number']} (label: {line['label']})")
                print(f"        📊 {line['word_count']} words")
                print()
        
        # Test 5: Character Summary
        print("\n📈 Test 5: Character Summary")
        print("-" * 40)
        
        summary = project.get_character_summary()
        print("✅ Character summary generated")
        print(f"   👥 Total characters: {summary['total_characters']}")
        print(f"   ✅ Defined characters: {summary['defined_characters']}")
        print(f"   ❓ Undefined speakers: {summary['undefined_speakers']}")
        print(f"   📖 Narrator included: {summary['narrator_included']}")
        print(f"   💬 Total dialogue lines: {summary['total_dialogue_lines']}")
        print(f"   📝 Total words: {summary['total_words']}")
        print(f"   📏 Average words per line: {summary['average_words_per_line']}")
        
        print(f"\n🏆 Top 5 Most Talkative Characters:")
        for i, char in enumerate(summary['top_characters']):
            print(f"   {i+1}. {char['name']} ({char['code']}) - {char['dialogue_lines']} lines")
        
        print(f"\n📋 Character Categories:")
        print(f"   ✅ Defined: {', '.join(summary['character_codes']['defined'][:10])}")
        if len(summary['character_codes']['defined']) > 10:
            print(f"       ... and {len(summary['character_codes']['defined']) - 10} more")
        
        if summary['character_codes']['undefined']:
            print(f"   ❓ Undefined: {', '.join(summary['character_codes']['undefined'][:10])}")
            if len(summary['character_codes']['undefined']) > 10:
                print(f"          ... and {len(summary['character_codes']['undefined']) - 10} more")
        
        print("\n" + "=" * 70)
        print("🎉 ENHANCED CHARACTER ANALYSIS TESTS PASSED!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def export_character_analysis(filename: str = "character_analysis.json"):
    """Export detailed character analysis to JSON."""
    print(f"\n📤 Exporting character analysis to {filename}...")
    
    try:
        test_vn_path = get_test_vn_path()
        project = RenpyProject(test_vn_path)
        
        # Get all analysis data
        char_stats = project.get_character_stats()
        top_chars = project.get_top_characters_by_dialogue(20)
        summary = project.get_character_summary()
        
        # Get sample dialogue for top characters
        for char in top_chars[:5]:
            dialogue = project.get_dialogue_for_character(char['code'], limit=20)
            char['sample_dialogue'] = dialogue
        
        # Compile complete analysis
        analysis = {
            "project_path": test_vn_path,
            "analysis_type": "enhanced_character_analysis",
            "timestamp": project.get_project_overview()["analysis_timestamp"],
            "summary": summary,
            "top_characters": top_chars,
            "all_character_stats": char_stats
        }
        
        # Export to JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Character analysis exported to {filename}")
        print(f"   📊 {len(char_stats)} character profiles")
        print(f"   🏆 Top {len(top_chars)} characters with sample dialogue")
        print(f"   📈 Complete statistical summary")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting enhanced character analysis tests...\n")
    
    success = test_enhanced_character_analysis()
    
    if success:
        # Ask if user wants to export analysis
        try:
            response = input("\n❓ Export detailed character analysis to JSON? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                export_character_analysis()
        except KeyboardInterrupt:
            print("\n\n👋 Test completed!")
    
    print("\n🔚 Character analysis test finished.") 
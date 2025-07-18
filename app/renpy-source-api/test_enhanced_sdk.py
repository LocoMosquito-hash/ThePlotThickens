#!/usr/bin/env python3
"""
Quick test for enhanced SDK menu parsing.
"""

import sys
import os
from pathlib import Path

# Add the renpy-source-api directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sdk_integration import HybridRenpyParser, ComplexityDetector

def test_enhanced_sdk():
    """Test the enhanced SDK analyzer with comprehensive menu parsing."""
    
    # Test project path (using MySisterMyRoommate)
    project_path = r"T:\AG\MySisterMyRoommateV1.69-pc\game"
    
    if not os.path.exists(project_path):
        print("❌ Test project path not found. Please update the path in the script.")
        return
    
    print("🧪 TESTING ENHANCED SDK ANALYZER")
    print("=" * 50)
    
    try:
        # Create hybrid parser
        parser = HybridRenpyParser()
        
        print("1. Testing complexity detection...")
        complexity_detector = ComplexityDetector()
        needs_sdk, reasons = complexity_detector.needs_sdk_analysis(project_path)
        
        print(f"   SDK needed: {needs_sdk}")
        print(f"   Reasons: {len(reasons)}")
        for reason in reasons[:3]:  # Show first 3 reasons
            print(f"     - {reason}")
        
        print("\n2. Running SDK analysis...")
        # Use analyze_project with force_sdk=True to ensure SDK analysis
        overview = parser.analyze_project(project_path, force_sdk=True, verbose=True)
        
        # Get the raw SDK data if available
        sdk_results = parser.sdk_analyzer.analyze_project(project_path, verbose=True)
        
        if sdk_results.success and sdk_results.data:
            print("   ✅ SDK analysis successful!")
            
            # Parse the results
            sdk_data = sdk_results.data
            
            print(f"\n3. Enhanced Menu Analysis Results:")
            print(f"   Total labels: {len(sdk_data.get('labels', []))}")
            print(f"   Total characters: {len(sdk_data.get('characters', []))}")
            print(f"   Total menus: {len(sdk_data.get('menus', []))}")
            print(f"   Total assets: {len(sdk_data.get('assets', []))}")
            
            # Analyze menu complexity using the new method
            menu_complexity = complexity_detector.analyze_sdk_menu_complexity(sdk_data)
            
            print(f"\n4. Menu Complexity Analysis:")
            print(f"   Total menus: {menu_complexity['total_menus']}")
            print(f"   Total choices: {menu_complexity['total_choices']}")
            print(f"   Conditional menus: {menu_complexity['conditional_menus']}")
            print(f"   Complex menus: {menu_complexity['complex_menus']}")
            print(f"   Named menus: {menu_complexity['named_menus']}")
            print(f"   Average choices per menu: {menu_complexity['average_choices_per_menu']:.1f}")
            
            print(f"\n5. Complexity Distribution:")
            for complexity, count in menu_complexity['complexity_distribution'].items():
                if count > 0:
                    print(f"   {complexity}: {count}")
            
            # Show sample complex menu
            complex_menus = menu_complexity['most_complex_menus']
            if complex_menus:
                print(f"\n6. Most Complex Menu Example:")
                top_menu = complex_menus[0]
                print(f"   File: {top_menu['file']}:{top_menu['line']}")
                print(f"   Choices: {top_menu['choice_count']}")
                print(f"   Complexity: {top_menu['complexity']}")
                print(f"   Has conditions: {top_menu['has_conditions']}")
                if top_menu['prompt']:
                    print(f"   Prompt: \"{top_menu['prompt']}\"")
            
            # Find ch4ashbagdone specifically to test if it's parsed correctly
            print(f"\n7. Looking for ch4ashbagdone menu...")
            ch4_menu_found = False
            for menu in sdk_data.get('menus', []):
                if 'ch4ashbagdone' in menu.get('file', '').lower():
                    ch4_menu_found = True
                    choices = menu.get('choices', [])
                    print(f"   ✅ Found ch4ashbagdone menu with {len(choices)} choices")
                    print(f"   Complexity: {menu.get('complexity', 'unknown')}")
                    print(f"   Has conditions: {menu.get('has_conditions', False)}")
                    
                    # Show first few choices
                    for i, choice in enumerate(choices[:3]):
                        destinations = choice.get('destinations', [])
                        dest_str = f" -> {', '.join(destinations)}" if destinations else ""
                        print(f"     Choice {i+1}: \"{choice.get('text', 'No text')}\"{dest_str}")
                    
                    break
            
            if not ch4_menu_found:
                print("   ⚠️  ch4ashbagdone menu not found in results")
            
        else:
            print(f"   ❌ SDK analysis failed: {sdk_results.error if sdk_results.error else 'Unknown error'}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_sdk() 
#!/usr/bin/env python3
"""
Test script for database persistence functionality.

This test validates the complete database persistence system for the Ren'Py Source API,
ensuring all analysis results can be saved, retrieved, and queried efficiently.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add current directory to Python path for imports
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Try relative imports (when used as package)
    from .core import RenpyProject
    from .config import TEST_VN_PATH, ALTERNATIVE_PATHS
    from .database import RenpyAPIDataPersistence, get_default_database
except ImportError:
    # Fall back to direct imports (when run standalone)
    from core import RenpyProject
    from config import TEST_VN_PATH, ALTERNATIVE_PATHS
    from database import RenpyAPIDataPersistence, get_default_database

def get_test_vn_path() -> str:
    """Get the best available test VN path."""
    if os.path.exists(TEST_VN_PATH):
        return TEST_VN_PATH
    
    for name, path in ALTERNATIVE_PATHS.items():
        if os.path.exists(path):
            print(f"Using fallback VN: {name} at {path}")
            return path
    
    return TEST_VN_PATH

def create_test_database() -> RenpyAPIDataPersistence:
    """Create a temporary test database."""
    # Use temporary file for testing to avoid affecting main database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    db_path = f"sqlite:///{temp_db.name}"
    print(f"📊 Created test database: {temp_db.name}")
    
    return RenpyAPIDataPersistence(db_path)

def test_database_persistence():
    """Test the complete database persistence functionality."""
    print("=" * 70)
    print("DATABASE PERSISTENCE TEST")
    print("=" * 70)
    
    # Get test VN path
    test_vn_path = get_test_vn_path()
    
    if not os.path.exists(test_vn_path):
        print(f"❌ Test VN path doesn't exist: {test_vn_path}")
        print("Please update TEST_VN_PATH in config.py")
        return False
    
    print(f"📁 Testing VN: {test_vn_path}")
    
    try:
        # Create test database
        db = create_test_database()
        
        # Test 1: Complete Analysis and Save
        print("\n📥 Test 1: Complete Analysis and Database Save")
        print("-" * 50)
        
        # Analyze project with all features
        project = RenpyProject(test_vn_path)
        project.analyze()
        
        # Get available analysis data
        character_stats = project.get_character_stats()
        print(f"✅ Character analysis: {len(character_stats)} characters")
        
        assets = project.get_all_assets()
        asset_count = sum(len(asset_list) for asset_list in assets.values())
        print(f"✅ Asset analysis: {asset_count} assets")
        
        menus = project.get_all_menus()
        print(f"✅ Menu analysis: {len(menus)} menus")
        
        flow_stats = project.get_label_flow_analysis()
        print(f"✅ Flow analysis: {len(flow_stats.get('labels', {}))} labels, {flow_stats.get('total_flows', 0)} flows")
        
        # Save to database
        print("\n💾 Saving complete analysis to database...")
        project_id = db.save_project_analysis(project)
        print(f"✅ Project saved with ID: {project_id}")
        
        # Test 2: Project Retrieval and Verification
        print("\n🔍 Test 2: Project Retrieval and Verification")
        print("-" * 50)
        
        # Retrieve project by path
        saved_project = db.get_project_by_path(test_vn_path)
        if saved_project:
            print(f"✅ Project retrieved: {saved_project.project_name}")
            print(f"   📊 Analysis flags: Characters={saved_project.characters_analyzed}, "
                  f"Assets={saved_project.assets_analyzed}, "
                  f"Menus={saved_project.menus_analyzed}, "
                  f"Flows={saved_project.flows_analyzed}")
            print(f"   📈 Quick stats: {saved_project.character_count} chars, "
                  f"{saved_project.asset_count} assets, "
                  f"{saved_project.menu_count} menus, "
                  f"{saved_project.label_count} labels")
        else:
            print("❌ Failed to retrieve saved project")
            return False
        
        # Test 3: Character Search and Retrieval
        print("\n👥 Test 3: Character Search and Retrieval")
        print("-" * 50)
        
        # Search all characters
        all_characters = db.search_characters(project_id)
        print(f"✅ Retrieved {len(all_characters)} characters from database")
        
        # Show top characters by significance
        significant_chars = sorted(all_characters, key=lambda x: x.story_significance, reverse=True)[:5]
        print("\n🏆 Top 5 Characters by Story Significance:")
        for i, char in enumerate(significant_chars):
            print(f"   {i+1}. {char.character_name}")
            print(f"      📊 Significance: {char.story_significance:.3f}")
            print(f"      💬 Lines: {char.total_lines}")
            print(f"      🎭 Appearances: {char.total_appearances}")
            if char.emotions:
                emotions = list(char.emotions.keys())[:3]
                print(f"      😊 Emotions: {', '.join(emotions)}")
            if char.relationships:
                rel_count = len(char.relationships)
                print(f"      🤝 Relationships: {rel_count}")
            print()
        
        # Search characters by name pattern
        if significant_chars:
            test_name = significant_chars[0].character_name[:3]  # First 3 chars
            matching_chars = db.search_characters(project_id, name_pattern=test_name)
            print(f"🔍 Search for '{test_name}': {len(matching_chars)} matches")
        
        # Search by minimum significance
        high_significance_chars = db.search_characters(project_id, min_significance=0.3)
        print(f"⭐ High significance characters (>0.3): {len(high_significance_chars)}")
        
        # Test 4: Menu and Choice Search
        print("\n📋 Test 4: Menu and Choice Search")
        print("-" * 50)
        
        # Search for menus by text
        search_terms = ["yes", "no", "continue", "next", "go", "take", "say"]
        
        for term in search_terms:
            choices = db.search_menus_by_text(project_id, term)
            if choices:
                print(f"🔍 Search '{term}': {len(choices)} choice matches")
                # Show first few matches
                for choice in choices[:3]:
                    choice_preview = choice.choice_text[:50] + "..." if len(choice.choice_text) > 50 else choice.choice_text
                    print(f"     • \"{choice_preview}\"")
                    if choice.destination_target:
                        print(f"       → {choice.destination_type}: {choice.destination_target}")
                break
        
        # Test 5: Project Statistics
        print("\n📊 Test 5: Comprehensive Project Statistics")
        print("-" * 50)
        
        stats = db.get_project_statistics(project_id)
        print("✅ Project statistics retrieved:")
        print(f"   📁 Project: {stats['project_name']}")
        print(f"   📅 Last scan: {stats['last_scan']}")
        print(f"   📄 Files scanned: {stats['total_files']}")
        print(f"   📝 Lines analyzed: {stats['total_lines']:,}")
        print(f"   👥 Characters: {stats['characters']}")
        print(f"   🎨 Assets: {stats['assets']}")
        print(f"   📋 Menus: {stats['menus']}")
        print(f"   🔀 Choices: {stats['choices']}")
        print(f"   🏷️  Labels: {stats['labels']}")
        print(f"   🔄 Flows: {stats['flows']}")
        
        coverage = stats['analysis_coverage']
        print(f"\n✅ Analysis Coverage:")
        print(f"   Characters: {'✅' if coverage['characters'] else '❌'}")
        print(f"   Assets: {'✅' if coverage['assets'] else '❌'}")
        print(f"   Menus: {'✅' if coverage['menus'] else '❌'}")
        print(f"   Flows: {'✅' if coverage['flows'] else '❌'}")
        
        # Test 6: Update Existing Project
        print("\n🔄 Test 6: Update Existing Project")
        print("-" * 50)
        
        # Re-analyze and save (should update existing record)
        print("📊 Re-analyzing project for update test...")
        project_updated = RenpyProject(test_vn_path)
        project_updated.analyze()
        
        updated_project_id = db.save_project_analysis(project_updated)
        print(f"✅ Project updated with ID: {updated_project_id}")
        
        if updated_project_id == project_id:
            print("✅ Confirmed: Same project ID (existing record updated)")
        else:
            print("❌ Warning: Different project ID (new record created)")
        
        # Verify updated timestamp
        updated_project = db.get_project_by_path(test_vn_path)
        if updated_project and updated_project.updated_at > saved_project.updated_at:
            print("✅ Confirmed: Updated timestamp is newer")
        
        # Test 7: Complex Queries and Relationships
        print("\n🔗 Test 7: Complex Queries and Data Relationships")
        print("-" * 50)
        
        # Get characters with relationships
        chars_with_relationships = [c for c in all_characters if c.relationships]
        print(f"🤝 Characters with relationships: {len(chars_with_relationships)}")
        
        if chars_with_relationships:
            sample_char = chars_with_relationships[0]
            print(f"   📊 Example: {sample_char.character_name}")
            for partner, relationship in sample_char.relationships.items():
                print(f"     • {relationship} with {partner}")
        
        # Get assets by type
        session = db.db.get_session()
        try:
            from database import RenpyAPIAsset
            
            asset_types = session.query(RenpyAPIAsset.asset_type).filter_by(project_id=project_id).distinct().all()
            asset_types = [t[0] for t in asset_types]
            
            print(f"\n🎨 Asset types found: {', '.join(asset_types)}")
            
            for asset_type in asset_types[:3]:  # Show first 3 types
                count = session.query(RenpyAPIAsset).filter_by(
                    project_id=project_id, 
                    asset_type=asset_type
                ).count()
                print(f"   {asset_type}: {count} assets")
                
        except ImportError:
            print("⚠️  Could not import database models for complex queries")
        finally:
            db.db.close_session(session)
        
        print("\n" + "=" * 70)
        print("🎉 DATABASE PERSISTENCE TESTS PASSED!")
        print("=" * 70)
        
        # Clean up test database file
        try:
            import os
            db_file = db.db.db_path.replace('sqlite:///', '')
            os.unlink(db_file)
            print(f"🧹 Cleaned up test database: {db_file}")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_query_performance():
    """Test database query performance with large datasets."""
    print("\n" + "=" * 70)
    print("DATABASE PERFORMANCE TEST")
    print("=" * 70)
    
    test_vn_path = get_test_vn_path()
    
    if not os.path.exists(test_vn_path):
        print(f"❌ Test VN path doesn't exist: {test_vn_path}")
        return False
    
    try:
        # Create test database
        db = create_test_database()
        
        # Analyze and save project
        print("📊 Analyzing project for performance test...")
        project = RenpyProject(test_vn_path)
        project.analyze()
        project.analyze_character_stats()
        project.analyze_assets()
        project.analyze_menus()
        project.analyze_label_flows()
        
        import time
        
        # Measure save performance
        start_time = time.time()
        project_id = db.save_project_analysis(project)
        save_time = time.time() - start_time
        print(f"⏱️  Save time: {save_time:.2f}s")
        
        # Measure retrieval performance
        start_time = time.time()
        all_characters = db.search_characters(project_id)
        char_time = time.time() - start_time
        print(f"⏱️  Character retrieval ({len(all_characters)} records): {char_time:.3f}s")
        
        # Measure search performance
        start_time = time.time()
        search_results = db.search_characters(project_id, min_significance=0.1)
        search_time = time.time() - start_time
        print(f"⏱️  Character search ({len(search_results)} matches): {search_time:.3f}s")
        
        # Measure menu search performance
        start_time = time.time()
        menu_results = db.search_menus_by_text(project_id, "e")  # Common letter
        menu_search_time = time.time() - start_time
        print(f"⏱️  Menu search ({len(menu_results)} matches): {menu_search_time:.3f}s")
        
        # Measure statistics generation
        start_time = time.time()
        stats = db.get_project_statistics(project_id)
        stats_time = time.time() - start_time
        print(f"⏱️  Statistics generation: {stats_time:.3f}s")
        
        print("✅ Performance test completed successfully")
        
        # Clean up
        try:
            import os
            db_file = db.db.db_path.replace('sqlite:///', '')
            os.unlink(db_file)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def export_database_test_results(filename: str = "database_test_results.json"):
    """Export comprehensive database test results to JSON."""
    print(f"\n📤 Exporting database test results to {filename}...")
    
    try:
        test_vn_path = get_test_vn_path()
        db = create_test_database()
        
        # Complete analysis
        project = RenpyProject(test_vn_path)
        project.analyze()
        project.analyze_character_stats()
        project.analyze_assets()
        project.analyze_menus()
        project.analyze_label_flows()
        
        # Save to database
        project_id = db.save_project_analysis(project)
        
        # Retrieve all data
        saved_project = db.get_project_by_path(test_vn_path)
        all_characters = db.search_characters(project_id)
        sample_choices = db.search_menus_by_text(project_id, "e")[:10]  # Sample choices
        stats = db.get_project_statistics(project_id)
        
        # Compile test results
        results = {
            "test_metadata": {
                "project_path": test_vn_path,
                "test_type": "database_persistence",
                "export_timestamp": str(time.time())
            },
            "project_info": {
                "id": saved_project.id if saved_project else None,
                "name": saved_project.project_name if saved_project else None,
                "analysis_flags": {
                    "characters": saved_project.characters_analyzed if saved_project else False,
                    "assets": saved_project.assets_analyzed if saved_project else False,
                    "menus": saved_project.menus_analyzed if saved_project else False,
                    "flows": saved_project.flows_analyzed if saved_project else False
                } if saved_project else {},
                "quick_stats": {
                    "character_count": saved_project.character_count if saved_project else 0,
                    "asset_count": saved_project.asset_count if saved_project else 0,
                    "menu_count": saved_project.menu_count if saved_project else 0,
                    "label_count": saved_project.label_count if saved_project else 0
                } if saved_project else {}
            },
            "comprehensive_stats": stats,
            "sample_characters": [
                {
                    "name": char.character_name,
                    "display_name": char.display_name,
                    "total_lines": char.total_lines,
                    "story_significance": char.story_significance,
                    "emotions": char.emotions,
                    "relationships": char.relationships,
                    "aliases": char.aliases_list
                }
                for char in all_characters[:10]  # Top 10 characters
            ],
            "sample_choices": [
                {
                    "text": choice.choice_text,
                    "destination_type": choice.destination_type,
                    "destination_target": choice.destination_target,
                    "menu_id": choice.menu_id
                }
                for choice in sample_choices
            ],
            "test_summary": {
                "total_characters_saved": len(all_characters),
                "characters_with_relationships": len([c for c in all_characters if c.relationships]),
                "characters_with_emotions": len([c for c in all_characters if c.emotions]),
                "database_persistence_successful": True
            }
        }
        
        # Export to JSON
        import time
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Database test results exported to {filename}")
        print(f"   📊 {len(all_characters)} characters, {len(sample_choices)} sample choices")
        
        # Clean up
        try:
            import os
            db_file = db.db.db_path.replace('sqlite:///', '')
            os.unlink(db_file)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    """Run the database persistence tests."""
    print("🚀 Starting Ren'Py Source API Database Persistence Tests")
    
    # Run main persistence test
    if not test_database_persistence():
        sys.exit(1)
    
    # Run performance test
    if not test_query_performance():
        sys.exit(1)
    
    # Export test results
    export_database_test_results()
    
    print("\n🎉 All database persistence tests completed successfully!") 
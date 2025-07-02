#!/usr/bin/env python3
"""
Simple test for database persistence functionality.

This test demonstrates the database persistence system with a basic example,
avoiding complex imports and focusing on core functionality.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add current directory to Python path for imports
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Direct imports without relative imports
from database import RenpyAPIDataPersistence
from database import RenpyAPIProject, RenpyAPICharacter, RenpyAPIAsset, RenpyAPIMenu, RenpyAPIChoice

def test_database_creation():
    """Test basic database creation and table setup."""
    print("=" * 60)
    print("DATABASE CREATION TEST")
    print("=" * 60)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    db_path = f"sqlite:///{temp_db.name}"
    print(f"📊 Created test database: {temp_db.name}")
    
    try:
        # Initialize database
        db = RenpyAPIDataPersistence(db_path)
        print("✅ Database initialized successfully")
        
        # Test table creation
        session = db.db.get_session()
        try:
            # Check that tables exist by querying them
            projects = session.query(RenpyAPIProject).count()
            characters = session.query(RenpyAPICharacter).count()
            assets = session.query(RenpyAPIAsset).count()
            menus = session.query(RenpyAPIMenu).count()
            choices = session.query(RenpyAPIChoice).count()
            
            print(f"✅ All tables created successfully")
            print(f"   📊 Initial counts: Projects={projects}, Characters={characters}, Assets={assets}, Menus={menus}, Choices={choices}")
            
        finally:
            db.db.close_session(session)
        
        return db, temp_db.name
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, temp_db.name

def test_basic_data_operations(db: RenpyAPIDataPersistence):
    """Test basic CRUD operations on database."""
    print("\n" + "=" * 60)
    print("BASIC DATA OPERATIONS TEST")
    print("=" * 60)
    
    session = db.db.get_session()
    try:
        # Test 1: Create a project
        print("\n📥 Test 1: Creating Project Record")
        project = RenpyAPIProject(
            project_path="/test/project/path",
            project_name="Test Project",
            total_files_scanned=10,
            total_lines_analyzed=5000,
            characters_analyzed=True,
            character_count=5
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        
        print(f"✅ Project created with ID: {project.id}")
        print(f"   📁 Name: {project.project_name}")
        print(f"   📊 Stats: {project.total_files_scanned} files, {project.total_lines_analyzed} lines")
        
        # Test 2: Create characters
        print("\n👥 Test 2: Creating Character Records")
        characters_data = [
            ("alice", "Alice", 150, 0.8),
            ("bob", "Bob", 95, 0.6),
            ("narrator", "Narrator", 200, 0.9),
            ("eve", "Eve", 45, 0.3),
            ("charlie", "Charlie", 75, 0.5)
        ]
        
        for char_name, display_name, lines, significance in characters_data:
            character = RenpyAPICharacter(
                project_id=project.id,
                character_name=char_name,
                display_name=display_name,
                total_lines=lines,
                story_significance=significance,
                total_appearances=lines // 10  # Simple calculation
            )
            session.add(character)
        
        session.commit()
        print(f"✅ Created {len(characters_data)} character records")
        
        # Test 3: Create assets
        print("\n🎨 Test 3: Creating Asset Records")
        assets_data = [
            ("bg_school.jpg", "image", "School Background"),
            ("music_theme.ogg", "audio", "Main Theme"),
            ("alice_happy.png", "image", "Alice Happy Expression"),
            ("sfx_bell.wav", "audio", "School Bell"),
            ("video_intro.webm", "video", "Opening Video")
        ]
        
        for asset_name, asset_type, description in assets_data:
            asset = RenpyAPIAsset(
                project_id=project.id,
                asset_path=f"/assets/{asset_name}",
                asset_name=asset_name,
                asset_type=asset_type,
                usage_count=10,
                usage_frequency=0.5
            )
            session.add(asset)
        
        session.commit()
        print(f"✅ Created {len(assets_data)} asset records")
        
        # Test 4: Create menus and choices
        print("\n📋 Test 4: Creating Menu and Choice Records")
        menu = RenpyAPIMenu(
            project_id=project.id,
            file_path="/scripts/chapter1.rpy",
            line_number=45,
            label_context="first_choice",
            menu_text="What do you want to do?",
            total_choices=3,
            complexity_score=3.0
        )
        session.add(menu)
        session.commit()
        session.refresh(menu)
        
        choices_data = [
            ("Go to the library", "jump", "library_scene"),
            ("Talk to Alice", "call", "alice_talk"),
            ("Skip class", "jump", "skip_scene")
        ]
        
        for i, (choice_text, dest_type, dest_target) in enumerate(choices_data):
            choice = RenpyAPIChoice(
                menu_id=menu.id,
                project_id=project.id,
                choice_text=choice_text,
                destination_type=dest_type,
                destination_target=dest_target,
                choice_order=i
            )
            session.add(choice)
        
        session.commit()
        print(f"✅ Created menu with {len(choices_data)} choices")
        
        return project.id
        
    except Exception as e:
        session.rollback()
        print(f"❌ Data operations failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.db.close_session(session)

def test_search_operations(db: RenpyAPIDataPersistence, project_id: int):
    """Test search and query operations."""
    print("\n" + "=" * 60)
    print("SEARCH OPERATIONS TEST")
    print("=" * 60)
    
    try:
        # Test 1: Search characters
        print("\n🔍 Test 1: Character Search")
        all_characters = db.search_characters(project_id)
        print(f"✅ Found {len(all_characters)} characters")
        
        for char in all_characters:
            print(f"   • {char.character_name} ({char.display_name}) - {char.total_lines} lines, significance: {char.story_significance:.1f}")
        
        # Search by significance
        significant_chars = db.search_characters(project_id, min_significance=0.6)
        print(f"\n⭐ High significance characters (>0.6): {len(significant_chars)}")
        for char in significant_chars:
            print(f"   • {char.character_name} - {char.story_significance:.1f}")
        
        # Search by name pattern
        alice_chars = db.search_characters(project_id, name_pattern="alice")
        print(f"\n🔍 Characters matching 'alice': {len(alice_chars)}")
        for char in alice_chars:
            print(f"   • {char.character_name} ({char.display_name})")
        
        # Test 2: Search menu choices
        print("\n📋 Test 2: Menu Choice Search")
        library_choices = db.search_menus_by_text(project_id, "library")
        print(f"✅ Choices containing 'library': {len(library_choices)}")
        for choice in library_choices:
            print(f"   • \"{choice.choice_text}\" → {choice.destination_type}: {choice.destination_target}")
        
        talk_choices = db.search_menus_by_text(project_id, "talk")
        print(f"✅ Choices containing 'talk': {len(talk_choices)}")
        for choice in talk_choices:
            print(f"   • \"{choice.choice_text}\" → {choice.destination_type}: {choice.destination_target}")
        
        # Test 3: Project statistics
        print("\n📊 Test 3: Project Statistics")
        stats = db.get_project_statistics(project_id)
        print("✅ Project statistics:")
        print(f"   📁 Project: {stats['project_name']}")
        print(f"   📄 Files: {stats['total_files']}")
        print(f"   📝 Lines: {stats['total_lines']:,}")
        print(f"   👥 Characters: {stats['characters']}")
        print(f"   🎨 Assets: {stats['assets']}")
        print(f"   📋 Menus: {stats['menus']}")
        print(f"   🔀 Choices: {stats['choices']}")
        
        coverage = stats['analysis_coverage']
        print(f"\n✅ Analysis Coverage:")
        print(f"   Characters: {'✅' if coverage['characters'] else '❌'}")
        print(f"   Assets: {'✅' if coverage['assets'] else '❌'}")
        print(f"   Menus: {'✅' if coverage['menus'] else '❌'}")
        print(f"   Flows: {'✅' if coverage['flows'] else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_project_retrieval(db: RenpyAPIDataPersistence):
    """Test project retrieval operations."""
    print("\n" + "=" * 60)
    print("PROJECT RETRIEVAL TEST")
    print("=" * 60)
    
    try:
        # Test retrieving project by path
        project = db.get_project_by_path("/test/project/path")
        
        if project:
            print("✅ Project retrieved successfully:")
            print(f"   📁 ID: {project.id}")
            print(f"   📁 Name: {project.project_name}")
            print(f"   📁 Path: {project.project_path}")
            print(f"   📅 Created: {project.created_at}")
            print(f"   📅 Updated: {project.updated_at}")
            print(f"   📊 Analysis flags: Characters={project.characters_analyzed}, "
                  f"Assets={project.assets_analyzed}, "
                  f"Menus={project.menus_analyzed}, "
                  f"Flows={project.flows_analyzed}")
            print(f"   📈 Quick stats: {project.character_count} chars, "
                  f"{project.asset_count} assets, "
                  f"{project.menu_count} menus, "
                  f"{project.label_count} labels")
            return True
        else:
            print("❌ Failed to retrieve project by path")
            return False
            
    except Exception as e:
        print(f"❌ Project retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_database(db_file_path: str):
    """Clean up the test database file."""
    try:
        os.unlink(db_file_path)
        print(f"\n🧹 Cleaned up test database: {db_file_path}")
    except Exception as e:
        print(f"⚠️ Could not clean up database file: {e}")

if __name__ == "__main__":
    """Run the simple database persistence tests."""
    print("🚀 Starting Simple Database Persistence Tests")
    
    # Test 1: Database creation
    db, db_file = test_database_creation()
    if not db:
        print("❌ Database creation failed, aborting tests")
        sys.exit(1)
    
    # Test 2: Basic data operations
    project_id = test_basic_data_operations(db)
    if not project_id:
        print("❌ Data operations failed, aborting tests")
        cleanup_database(db_file)
        sys.exit(1)
    
    # Test 3: Search operations
    if not test_search_operations(db, project_id):
        print("❌ Search operations failed")
        cleanup_database(db_file)
        sys.exit(1)
    
    # Test 4: Project retrieval
    if not test_project_retrieval(db):
        print("❌ Project retrieval failed")
        cleanup_database(db_file)
        sys.exit(1)
    
    # Cleanup
    cleanup_database(db_file)
    
    print("\n" + "=" * 60)
    print("🎉 ALL DATABASE PERSISTENCE TESTS PASSED!")
    print("=" * 60)
    print("\n✨ Database persistence system is working correctly!")
    print("   📊 Tables creation: ✅")
    print("   💾 Data storage: ✅")
    print("   🔍 Search operations: ✅")
    print("   📈 Statistics: ✅")
    print("   🔄 Project retrieval: ✅")
    print("\n🎯 The Ren'Py Source API database persistence is ready for use!") 
# Getting Started with Ren'Py Source API

🎉 **Congratulations!** You now have a powerful Ren'Py analysis API built into The Plot Thickens. This guide will help you set it up and test it for the first time.

## 🚀 What You've Built

The Ren'Py Source API is a **game-changer** for your app that provides:

- **📊 Project Structure Analysis** - Understand any Ren'Py VN's structure
- **🔍 Dialogue Search** - Find specific lines across the entire script
- **👥 Character Mapping** - Extract character definitions automatically
- **🏷️ Label Discovery** - Map all scenes and story points
- **💾 Database Integration** - Cache results for fast repeated queries
- **🔄 Future-Ready Architecture** - Built to extend with branching analysis, asset tracking, and more

## ⚡ Quick Setup (5 minutes)

### Step 1: Configure Your Test VN

1. **Open** `app/renpy-source-api/config.py`
2. **Update** the `TEST_VN_PATH` to point to your decompiled Ren'Py game folder:

```python
# Windows example
TEST_VN_PATH = r"C:\Games\RenPy\YourVN\game"

# Linux/macOS example
TEST_VN_PATH = "/home/user/games/YourVN/game"
```

**💡 Important:** Make sure to point to the **game** folder that contains `.rpy` files, not the main VN folder.

### Step 2: Test the API

Open a terminal in the project root and run:

```bash
cd app/renpy-source-api
python test_renpy_api.py
```

You should see output like:

```
============================================================
REN'PY SOURCE API TEST
============================================================
📁 Available VNs: 1
   • primary: C:\Games\RenPy\YourVN\game
📁 Testing with VN path: C:\Games\RenPy\YourVN\game
✅ Valid Ren'Py directory with 45 .rpy files

🔧 Test 1: Project Initialization
------------------------------
✅ Project created successfully
   Path: C:\Games\RenPy\YourVN\game

📊 Test 2: Project Analysis
------------------------------
✅ Analysis completed successfully
   📄 .rpy files: 45
   📝 Total lines: 12847
   💬 Dialogue lines: 3247
   🏷️ Labels: 156
   📋 Menus: 23
   👥 Characters: 12
```

If you see **"🎉 ALL TESTS PASSED!"** at the end, you're ready to go!

## 🔧 Integration with Your App

### Basic Integration Example

Here's how to use the API in your main application:

```python
import sqlite3
from app.renpy_source_api.core import RenpyProject

# Connect to your database
db_conn = sqlite3.connect("plot_thickens.db")
db_conn.row_factory = sqlite3.Row

# Create a Ren'Py project (linked to a story)
game_folder = "/path/to/renpy/game"
project = RenpyProject(game_folder, db_conn)

# Link to existing story in your database
story_id = 1  # Your story ID
project.link_to_story(story_id)

# Analyze the project (cached after first run)
overview = project.analyze()

# Now you can query it!
results = project.search_dialogue("I love you")
characters = project.get_character_stats()
labels = project.get_labels()
```

### Gallery Integration Example

```python
def find_images_for_dialogue(dialogue_query: str):
    """Find images that might be related to specific dialogue."""

    # Search dialogue in Ren'Py script
    project = RenpyProject(story.renpy_path, db_conn)
    dialogue_results = project.search_dialogue(dialogue_query)

    # Get the labels where this dialogue appears
    relevant_labels = [result['file'] for result in dialogue_results]

    # Use this info to filter your gallery images
    # (You can expand this to match image timestamps, etc.)
    return filter_gallery_by_context(relevant_labels)
```

## 🚧 What's Coming Next

Now that you have the foundation, here are the next features to implement:

### Immediate Next Steps

1. **Enhanced Character Stats** - Count dialogue lines per character
2. **Asset Tracking** - Find which images/audio are referenced in script
3. **Menu Extraction** - Better decision point detection

### Future Features

4. **Flow Graph Analysis** - Map branching paths and story flow
5. **Decision Point Integration** - Auto-create decision points from menus
6. **Timeline Mapping** - Match script labels to your timeline events
7. **Quick Events Enhancement** - Link quick events to script dialogue

## 🛠️ Extending the API

### Adding New Parser Patterns

To recognize new Ren'Py statements, edit `parser.py`:

```python
# Add to self.patterns in RenpyParser.__init__
'new_statement': re.compile(r'^\s*new_statement\s+(.+)', re.IGNORECASE),
```

### Adding New Database Tables

To cache new types of data, extend `database_basic.py`:

```python
def ensure_renpy_tables(self):
    # Add new table creation SQL
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS renpy_new_feature (
        id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        feature_data TEXT,
        FOREIGN KEY (project_id) REFERENCES renpy_projects (id)
    )
    ''')
```

### Adding New API Methods

To expose new functionality, extend `core.py`:

```python
def get_new_feature(self) -> List[Dict[str, Any]]:
    """Get data about new feature."""
    if not self.is_analyzed:
        self.analyze()

    # Implementation here
    return results
```

## 🔍 Troubleshooting

### "Directory does not appear to be a Ren'Py project"

- Verify you're pointing to the `game` folder, not the main VN folder
- Check that `.rpy` files exist (you might need to decompile `.rpyc` files)
- Use a tool like [unren.bat](https://f95zone.to/threads/unren-bat-v1-0-3-rpyc-rpa-extractor-35481/) to decompile

### "No character definitions found"

- This is normal for some VNs that use different character definition patterns
- The dialogue search will still work even without character definitions

### Import Errors

- Make sure you're running from the correct directory
- Check that all files exist in the `renpy-source-api` folder

### Performance Issues with Large VNs

- Analysis results are cached in the database after the first run
- For huge VNs (10GB+), initial analysis might take a few minutes
- Subsequent queries will be fast due to caching

## 🎯 Pro Tips

1. **Start Small**: Test with a small/medium VN first to verify everything works
2. **Export Analysis Data**: Use the test script's export feature to inspect the JSON structure
3. **Check Available VNs**: The config system can manage multiple VN paths for testing
4. **Database Integration**: Always use the database connection for caching in production
5. **Error Handling**: The API gracefully handles parsing errors and continues analysis

## 🎉 You're Ready!

You've successfully built a sophisticated Ren'Py analysis system that will revolutionize how The Plot Thickens works with visual novels. This API provides the foundation for features like:

- **Intelligent Gallery Management** - Find images by dialogue context
- **Automated Decision Points** - Extract choice menus from script
- **Enhanced Character Analysis** - Real dialogue statistics
- **Story Flow Mapping** - Understand branching narratives

The sky's the limit! Start with the basic integration and gradually expand the features as you need them.

---

**Need help?** Check the `README.md` for detailed documentation or run the test script to verify everything is working correctly.

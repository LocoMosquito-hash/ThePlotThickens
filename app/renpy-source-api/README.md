# Ren'Py Source Analysis API

A powerful Python API for analyzing Ren'Py visual novel source files (`.rpy`) and extracting meaningful information about dialogue, characters, labels, assets, and branching paths.

## 🎯 Purpose

This API is designed to integrate with "The Plot Thickens" app to provide **Ren'Py awareness** - the ability to understand and query the structure of visual novels built with the Ren'Py engine. Instead of just working with images and manual input, the app can now:

- **Understand the story structure** by parsing labels and flow
- **Search dialogue** to find specific scenes or conversations
- **Map character relationships** from the script itself
- **Track assets** (images, audio) and where they're used
- **Identify decision points** and branching paths automatically

## 🚀 Quick Start

### Testing the API

1. **Edit the test path**: Open `test_renpy_api.py` and change `TEST_VN_PATH` to point to your decompiled Ren'Py game folder:

```python
TEST_VN_PATH = r"C:\Games\RenPy\YourVN\game"  # Windows
# or
TEST_VN_PATH = "/home/user/games/YourVN/game"  # Linux/macOS
```

2. **Run the test**:

```bash
cd app/renpy-source-api
python test_renpy_api.py
```

### Basic Usage

```python
from app.renpy_source_api.core import RenpyProject

# Initialize project
project = RenpyProject("/path/to/renpy/game/folder")

# Analyze the project
overview = project.analyze()

# Get project statistics
stats = project.get_project_overview()
print(f"Found {stats['statistics']['total_dialogue_lines']} dialogue lines")

# Search dialogue
results = project.search_dialogue("Hello world")
for result in results:
    print(f"{result['speaker']}: {result['dialogue']}")

# Get character definitions
characters = project.get_character_stats()
for code, info in characters.items():
    print(f"{code} = \"{info['name']}\"")
```

## 📁 Project Structure

```
app/renpy-source-api/
├── __init__.py              # Package initialization
├── core.py                  # Main RenpyProject class
├── parser.py                # .rpy file parser
├── database_basic.py        # Database integration
├── exceptions.py            # Custom exceptions
├── test_renpy_api.py       # Test script
├── README.md               # This file
└── renpy-code-analysis-strategy.md  # Detailed strategy document
```

## 🔧 Core Components

### `RenpyProject`

The main interface for analyzing Ren'Py projects.

**Key Methods:**

- `analyze()` - Parse and analyze all .rpy files
- `get_project_overview()` - Get summary statistics
- `search_dialogue(query)` - Search for dialogue text
- `get_character_stats()` - Get character information
- `get_labels()` - List all scene/function labels
- `link_to_story(story_id)` - Link to database story

### `RenpyParser`

Lightweight parser for .rpy files using regex patterns.

**Recognizes:**

- Character definitions (`define e = Character("Eileen")`)
- Dialogue lines (`e "Hello world!"`)
- Labels (`label start:`)
- Scene/Show statements (`scene bg beach`)
- Menu choices
- Jump/Call statements
- Audio playback commands

### `RenpyDatabase`

Extends the existing Plot Thickens database with Ren'Py-specific tables for caching analysis results.

## 📊 What It Analyzes

### Project Structure Overview

- Total .rpy files and lines of code
- Number of dialogue lines, labels, menus
- Character definitions found
- File list and structure

### Dialogue Analysis

- Full-text search through all dialogue
- Speaker identification and mapping
- Context information (file, line number)
- Character speech statistics (planned)

### Character Mapping

- Character code to name mapping (`e` → `"Eileen"`)
- Character appearance tracking (planned)
- Dialogue count per character (planned)

### Label Structure

- All scene and function labels
- Jump/call relationships (planned)
- Flow graph generation (planned)

### Asset Tracking

- Image definitions and usage (planned)
- Audio file references (planned)
- Unused asset detection (planned)

## 🎮 Supported VN Examples

The API has been designed to work with various types of Ren'Py visual novels:

**Small/Abandoned VNs** (good for testing):

- Accept the Past
- Blairewood
- Stars of Salvation

**Medium VNs**:

- The Way
- Deviant Anomalies
- Detective Necro

**Large Commercial VNs**:

- Grandma's House
- Summertime Saga

## 🔄 Integration with Plot Thickens

The API is designed to integrate seamlessly with the existing app:

### Database Integration

- Extends existing SQLite database with `renpy_projects` table
- Links to existing `stories` table via `story_id`
- Caches analysis results for performance

### Workflow Integration

- **Gallery Batch Import**: Search dialogue to find related images
- **Decision Points**: Automatically detect menu choices from script
- **Character Analysis**: Enhanced character stats from actual dialogue
- **Timeline Mapping**: Use labels and flow to understand story progression

### Example Integration

```python
# In your main app
from app.db_sqlite import get_story
from app.renpy_source_api.core import RenpyProject

# Get story from main database
story = get_story(db_conn, story_id)
if story and story.get('renpy_game_path'):
    # Create Ren'Py project
    project = RenpyProject(story['renpy_game_path'], db_conn)
    project.link_to_story(story_id)

    # Now you can query the VN structure
    results = project.search_dialogue("important scene text")
    # Use results to filter gallery images, etc.
```

## 🚧 Current Status & Roadmap

### ✅ Implemented (v0.1.0)

- [x] Basic .rpy file parsing
- [x] Project structure analysis
- [x] Character definition extraction
- [x] Simple dialogue search
- [x] Label identification
- [x] Database integration foundation
- [x] Comprehensive test suite

### 🚧 In Development

- [ ] Enhanced dialogue search with context
- [ ] Character speech statistics
- [ ] Asset usage tracking
- [ ] Menu choice extraction

### 📋 Planned Features

- [ ] Flow graph generation (using renpy-graphviz)
- [ ] Decision point mapping
- [ ] Branching path analysis
- [ ] Asset optimization
- [ ] Integration with existing Quick Events
- [ ] Advanced character relationship mapping

## 🛠️ Development

### Adding New Features

1. **Parser Extensions**: Add new regex patterns to `parser.py`
2. **Database Schema**: Extend `database_basic.py` with new tables
3. **API Methods**: Add new query methods to `core.py`
4. **Testing**: Update `test_renpy_api.py` with new test cases

### Performance Considerations

- **Caching**: All analysis results are cached in the database
- **Lazy Loading**: Analysis only runs when needed
- **Incremental Updates**: Only re-analyze if files change (planned)
- **Memory Efficiency**: Parser processes files line-by-line

## 🔍 Troubleshooting

### Common Issues

**"Directory does not appear to be a Ren'Py project"**

- Make sure you're pointing to the `game` folder containing .rpy files
- Check that .rpy files exist (you may need to decompile .rpyc files first)

**"No character definitions found"**

- Some VNs define characters in separate files or use different patterns
- This is normal for some VNs - the API will still work for dialogue search

**Import errors**

- Make sure you're running from the correct directory
- Check that all required files exist in the renpy-source-api folder

### Getting Help

1. Run the test script to verify basic functionality
2. Check the exported JSON sample data to understand the structure
3. Enable debug output by examining the console logs
4. Refer to the detailed strategy document for implementation details

## 📚 References

- [Ren'Py Documentation](https://www.renpy.org/doc/html/)
- [Detailed Analysis Strategy](./renpy-code-analysis-strategy.md)
- [Plot Thickens Main Documentation](../../README.md)

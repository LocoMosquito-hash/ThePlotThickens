# Ren'Py Source API Database Persistence

## Overview

The database persistence system for the Ren'Py Source API provides comprehensive caching and querying capabilities for all analysis results. This system is designed to be completely separate from The Plot Thickens (TPT) main application database to ensure no linking issues when VN source code changes.

## ✅ Implementation Status

**Phase 2 Task 5: Full Database Persistence** - **COMPLETED** ✅

All database persistence functionality has been successfully implemented and tested:

- ✅ Database schema design
- ✅ Table creation and management
- ✅ Data storage and retrieval
- ✅ Search and query operations
- ✅ Project statistics generation
- ✅ Complete separation from TPT tables

## Architecture

### Database Design Principles

1. **Complete Separation**: All API tables use `renpy_api_` prefix to ensure no conflicts with TPT tables
2. **No Foreign Key Links**: Zero associations between API data and TPT data
3. **Query-Only Usage**: API serves as a read-only source for populating TPT manually
4. **Version Tracking**: Analysis version tracking for compatibility management

### Database Tables

#### Core Tables

- **`renpy_api_projects`**: Project-level metadata and analysis flags
- **`renpy_api_characters`**: Character analysis data with stats and relationships
- **`renpy_api_assets`**: Asset tracking with usage analysis
- **`renpy_api_menus`**: Menu structures and decision points
- **`renpy_api_choices`**: Individual choice options within menus
- **`renpy_api_labels`**: Scene/label information and connectivity
- **`renpy_api_flows`**: Flow connections between scenes

#### Key Features

- **Comprehensive Indexing**: Optimized for fast queries
- **JSON Storage**: Complex data stored as JSON for flexibility
- **Metadata Tracking**: Created/updated timestamps for all records
- **Analysis Flags**: Track which analysis types have been completed

## Usage

### Basic Database Operations

```python
from database import RenpyAPIDataPersistence

# Initialize database
db = RenpyAPIDataPersistence()

# Save project analysis
project_id = db.save_project_analysis(renpy_project)

# Retrieve project
project = db.get_project_by_path("/path/to/vn")

# Search characters
characters = db.search_characters(project_id, min_significance=0.5)

# Search menu choices
choices = db.search_menus_by_text(project_id, "yes")

# Get statistics
stats = db.get_project_statistics(project_id)
```

### Integration with RenpyProject

The persistence system automatically extracts data from `RenpyProject` instances:

```python
# Analyze VN
project = RenpyProject("/path/to/vn")
project.analyze()

# Save all analysis results
db = RenpyAPIDataPersistence()
project_id = db.save_project_analysis(project)
```

## Database Schema Details

### Project Table

```sql
renpy_api_projects:
- id (Primary Key)
- project_path (Unique)
- project_name
- total_files_scanned
- total_lines_analyzed
- analysis_version
- characters_analyzed (Boolean)
- assets_analyzed (Boolean)
- menus_analyzed (Boolean)
- flows_analyzed (Boolean)
- character_count, asset_count, menu_count, label_count
- created_at, updated_at, last_scan_at
```

### Character Table

```sql
renpy_api_characters:
- id (Primary Key)
- project_id (Foreign Key)
- character_name
- display_name
- total_lines, total_appearances
- story_significance, interaction_frequency
- emotions_json (JSON)
- relationships_json (JSON)
- character_arcs_json (JSON)
- first_appearance_file, first_appearance_line
```

### Asset Table

```sql
renpy_api_assets:
- id (Primary Key)
- project_id (Foreign Key)
- asset_path, asset_name, asset_type
- file_size, usage_count, usage_frequency
- related_assets_json (JSON)
- used_in_scenes_json (JSON)
```

### Menu/Choice Tables

```sql
renpy_api_menus:
- id (Primary Key)
- project_id (Foreign Key)
- file_path, line_number, label_context
- menu_text, total_choices
- complexity_score, branching_factor

renpy_api_choices:
- id (Primary Key)
- menu_id, project_id (Foreign Keys)
- choice_text, choice_condition
- destination_type, destination_target
- choice_order, popularity_score
```

### Label/Flow Tables

```sql
renpy_api_labels:
- id (Primary Key)
- project_id (Foreign Key)
- label_name, file_path, line_number
- total_flows_in, total_flows_out
- is_reachable, depth_from_start
- scene_type, narrative_importance

renpy_api_flows:
- id (Primary Key)
- source_label_id, target_label_id, project_id (Foreign Keys)
- flow_type, condition
- file_path, line_number
- frequency_score, is_critical_path, creates_cycle
```

## Testing

### Test Coverage

The database persistence system has been thoroughly tested:

- ✅ **Database Creation**: Table creation and schema validation
- ✅ **Data Storage**: CRUD operations for all entity types
- ✅ **Search Operations**: Character and choice search functionality
- ✅ **Statistics**: Comprehensive project statistics generation
- ✅ **Project Retrieval**: Project lookup and metadata access

### Running Tests

```bash
# Run simple database tests (recommended)
cd app/renpy-source-api
python test_simple_database.py

# Output:
# 🎉 ALL DATABASE PERSISTENCE TESTS PASSED!
# ✨ Database persistence system is working correctly!
```

### Test Results Summary

```
📊 Tables creation: ✅
💾 Data storage: ✅
🔍 Search operations: ✅
📈 Statistics: ✅
🔄 Project retrieval: ✅
```

## Use Cases for TPT Integration

### 1. Character Discovery

```python
# Find characters for a story
characters = db.search_characters(project_id, min_significance=0.3)
for char in characters:
    # Use char.character_name, char.display_name to populate TPT
    pass
```

### 2. Decision Point Assistance

```python
# Find choices matching text pattern
choices = db.search_menus_by_text(project_id, "library")
for choice in choices:
    # Use choice.choice_text to populate TPT Decision Point options
    pass
```

### 3. Asset Discovery

```python
# Get project statistics for overview
stats = db.get_project_statistics(project_id)
print(f"Found {stats['assets']} assets, {stats['characters']} characters")
```

### 4. Source Update Detection

```python
# Check if VN source has been updated
project = db.get_project_by_path("/path/to/vn")
if project and project.last_scan_at < vn_last_modified:
    # Re-scan needed
    pass
```

## Configuration

### Database Path

By default, the system uses a **completely separate SQLite database** (`renpy_source_api.db`) to ensure perfect isolation from TPT:

```python
# Default configuration (recommended)
db = RenpyAPIDataPersistence()  # Uses separate renpy_source_api.db

# Custom database path
db = RenpyAPIDataPersistence('sqlite:///custom_api.db')

# If you still want to use TPT database (not recommended)
db = RenpyAPIDataPersistence('sqlite:///the_plot_thickens.db')
```

**Architecture Benefits:**

- ✅ **Zero conflicts** with TPT database changes
- ✅ **Independent backup/restore** of API data
- ✅ **Cross-project queries** across multiple VN analyses
- ✅ **Safe sharing** between TPT instances

### Analysis Flags

The system tracks which types of analysis have been completed:

```python
project = db.get_project_by_path("/path/to/vn")
if not project.characters_analyzed:
    # Need to run character analysis
    pass
```

## Performance

### Indexing Strategy

- Primary keys on all tables
- Composite indexes on frequently queried fields
- Project-based partitioning for efficient filtering

### Query Optimization

- Lazy loading of JSON fields
- Cached project statistics
- Optimized search queries with proper indexing

## Security & Data Integrity

### Separation Guarantees

- **No Foreign Keys** to TPT tables
- **Separate Table Prefix** (`renpy_api_`)
- **Independent Schema** evolution
- **Isolated Transactions**

### Data Consistency

- Transaction-based updates
- Automatic cleanup on re-analysis
- Timestamp tracking for staleness detection

## Future Enhancements

### Potential Improvements

1. **Incremental Updates**: Only re-analyze changed files
2. **Asset Thumbnail Caching**: Store image thumbnails in database
3. **Advanced Relationship Analysis**: Character interaction networks
4. **Performance Metrics**: Query execution time tracking
5. **Export Formats**: JSON/CSV export of analysis results

### Integration Possibilities

1. **TPT Story Wizard**: Auto-populate new stories from API data
2. **Character Import**: Batch character creation from API
3. **Decision Tree Visualization**: Generate flowcharts from flow data
4. **Asset Management**: Link VN assets to TPT image gallery

## Conclusion

The Ren'Py Source API database persistence system provides a robust, scalable foundation for caching and querying VN analysis results. With complete separation from TPT data and comprehensive test coverage, it's ready for production use.

The system successfully addresses the key requirements:

- ✅ Complete separation from TPT tables
- ✅ Comprehensive analysis data storage
- ✅ Fast search and query capabilities
- ✅ Project update and re-analysis support
- ✅ Ready for TPT integration as query-only source

**Status**: Phase 2 Task 5 - Full Database Persistence - **COMPLETED** ✅

import sqlite3
import json

conn = sqlite3.connect('the_plot_thickens.db')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

# Check if relationship_types table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relationship_types'")
if cursor.fetchone():
    print("relationship_types table exists")
    
    # Get column info for relationship_types table
    cursor.execute("PRAGMA table_info(relationship_types)")
    columns = cursor.fetchall()
    print("Columns in relationship_types:")
    for col in columns:
        print(f"  {col['name']} ({col['type']})")
    
    # Check if category_id column exists
    has_category_id = any(col['name'] == 'category_id' for col in columns)
    print(f"Has category_id column: {has_category_id}")
    
    # Check sample data
    cursor.execute("SELECT * FROM relationship_types LIMIT 3")
    rows = [dict(row) for row in cursor.fetchall()]
    print("\nSample data:")
    print(json.dumps(rows, indent=2, default=str))
else:
    print("relationship_types table does not exist")

conn.close() 
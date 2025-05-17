import sqlite3
import os

print(f"Current directory: {os.getcwd()}")
print(f"Database file exists: {os.path.exists('the_plot_thickens.db')}")
print(f"Database file size: {os.path.getsize('the_plot_thickens.db')} bytes")

# Connect to the database
conn = sqlite3.connect('the_plot_thickens.db')
cursor = conn.cursor()

# Check for tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables found: {len(tables)}")
for table in tables:
    print(f"- {table[0]}")

# Count rows in some key tables if they exist
try:
    cursor.execute("SELECT COUNT(*) FROM characters;")
    character_count = cursor.fetchone()[0]
    print(f"Character count: {character_count}")
except sqlite3.OperationalError as e:
    print(f"Error accessing characters table: {e}")

try:
    cursor.execute("SELECT COUNT(*) FROM events;")
    event_count = cursor.fetchone()[0]
    print(f"Event count: {event_count}")
except sqlite3.OperationalError as e:
    print(f"Error accessing events table: {e}")

# Check a few sample records
try:
    cursor.execute("SELECT id, name, gender FROM characters LIMIT 3;")
    characters = cursor.fetchall()
    print("\nSample characters:")
    for char in characters:
        print(f"ID: {char[0]}, Name: {char[1]}, Gender: {char[2]}")
except sqlite3.OperationalError as e:
    print(f"Error getting sample characters: {e}")

conn.close() 
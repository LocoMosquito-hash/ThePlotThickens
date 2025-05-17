import sqlite3
import os

print(f"Current working directory: {os.getcwd()}")
print(f"Database path: {os.path.abspath('the_plot_thickens.db')}")
print(f"Database exists: {os.path.exists('the_plot_thickens.db')}")

try:
    # Connect to the database
    conn = sqlite3.connect('the_plot_thickens.db')
    cursor = conn.cursor()
    
    # Get table count
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    table_count = cursor.fetchone()[0]
    print(f"Number of tables: {table_count}")
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    # Close connection
    conn.close()
    print("Database connection test successful!")
except Exception as e:
    print(f"Error connecting to database: {str(e)}") 
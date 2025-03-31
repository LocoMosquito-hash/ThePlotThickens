#!/usr/bin/env python3
"""
This script makes the character_id column in quick_events table optional.

It runs the migration to update the database schema and prints instructions
for using the new feature.
"""

from run_migration import main

if __name__ == "__main__":
    print("Making Quick Events Character Optional")
    print("======================================")
    print("This script will update your database to allow creating quick events")
    print("without assigning them to a specific character.\n")
    print("This is useful for events like:")
    print("- 'The door opens'")
    print("- 'A loud explosion is heard'")
    print("- 'The simulation is reset'\n")
    print("These events don't belong to any specific character but can still")
    print("contain character mentions and be assigned to scenes.\n")
    
    main() 
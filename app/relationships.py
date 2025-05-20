#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relationship management module for The Plot Thickens application.

This module handles relationship types, categories, and instances between characters.
"""

import os
import json
import sqlite3
from datetime import datetime
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Tuple, Union


# Relationship Category Enum
class RelationshipCategory(Enum):
    """Enumeration of relationship categories."""
    FAMILY = auto()
    WORK = auto()
    STUDY = auto()
    ROMANTIC = auto()
    SEXUAL = auto()
    SOCIAL = auto()
    GENERAL = auto()
    OTHER = auto()
    
    def __str__(self):
        return self.name.title()


# Gender Context Enum
class GenderContext(Enum):
    """Enumeration of gender contexts for relationship types."""
    MALE = auto()
    FEMALE = auto()
    NEUTRAL = auto()
    
    def __str__(self):
        return self.name.title()


def create_relationship_tables(conn: sqlite3.Connection) -> None:
    """Create relationship-related tables if they don't exist.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Create relationship_types table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relationship_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name TEXT NOT NULL,
        type_key TEXT NOT NULL,
        color TEXT DEFAULT '#cccccc',
        gender_context TEXT DEFAULT 'NEUTRAL',
        inverse_id INTEGER,
        is_common BOOLEAN DEFAULT 1,
        is_custom BOOLEAN DEFAULT 0,
        display_name TEXT,
        description TEXT,
        FOREIGN KEY (inverse_id) REFERENCES relationship_types (id)
    )
    ''')
    
    # Check if the relationship_types table exists but is missing the gender_context column
    ensure_gender_context_column(conn)
    
    # Update relationships table if it exists but is missing fields
    cursor.execute("PRAGMA table_info(relationships)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    if "relationship_type_id" not in existing_columns:
        # Add relationship_type_id column if it doesn't exist
        cursor.execute('''
        ALTER TABLE relationships ADD COLUMN relationship_type_id INTEGER
        REFERENCES relationship_types(id)
        ''')
    
    if "strength" not in existing_columns:
        # Add strength column if it doesn't exist
        cursor.execute('''
        ALTER TABLE relationships ADD COLUMN strength INTEGER DEFAULT 3
        ''')
    
    if "is_custom" not in existing_columns:
        # Add is_custom column if it doesn't exist
        cursor.execute('''
        ALTER TABLE relationships ADD COLUMN is_custom BOOLEAN DEFAULT 0
        ''')
    
    if "custom_label" not in existing_columns:
        # Add custom_label column if it doesn't exist
        cursor.execute('''
        ALTER TABLE relationships ADD COLUMN custom_label TEXT
        ''')
    
    conn.commit()


def ensure_gender_context_column(conn: sqlite3.Connection) -> None:
    """Ensure the gender_context column exists in the relationship_types table.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Check if the relationship_types table exists
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='relationship_types'
    ''')
    
    if cursor.fetchone():
        # Table exists, check if gender_context column exists
        cursor.execute("PRAGMA table_info(relationship_types)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "gender_context" not in columns:
            # Add the missing column
            print("Adding missing gender_context column to relationship_types table")
            try:
                cursor.execute('''
                ALTER TABLE relationship_types 
                ADD COLUMN gender_context TEXT DEFAULT 'NEUTRAL'
                ''')
                conn.commit()
            except sqlite3.Error as e:
                print(f"Error adding gender_context column: {e}")
                # Don't fail the entire operation if this fails
                pass


def initialize_relationship_categories(conn: sqlite3.Connection) -> None:
    """Initialize default relationship categories if they don't exist.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Check if categories already exist
    cursor.execute('SELECT COUNT(*) FROM relationship_categories')
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insert default categories
        categories = [
            (1, "Family", "Family relationships", 1),
            (2, "Work", "Professional relationships", 2),
            (3, "Study", "Academic relationships", 3),
            (4, "Romantic", "Romantic relationships", 4),
            (5, "Sexual", "Sexual relationships", 5),
            (6, "Social", "Social relationships", 6),
            (7, "General", "General relationships", 7),
            (8, "Other", "Other relationship types", 8)
        ]
        
        cursor.executemany('''
        INSERT INTO relationship_categories (id, name, description, display_order)
        VALUES (?, ?, ?, ?)
        ''', categories)
        
        conn.commit()


def initialize_relationship_types(conn: sqlite3.Connection) -> None:
    """Initialize default relationship types if they don't exist.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Check if relationship types already exist
    cursor.execute('SELECT COUNT(*) FROM relationship_types')
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Family relationships
        family_types = [
            # Name, Type Key, Gender Context, Is Common, Description
            ("Father", "FAMILY", "MALE", 1, "Paternal relationship"),
            ("Mother", "FAMILY", "FEMALE", 1, "Maternal relationship"),
            ("Son", "FAMILY", "MALE", 1, "Male child relationship"),
            ("Daughter", "FAMILY", "FEMALE", 1, "Female child relationship"),
            ("Brother", "FAMILY", "MALE", 1, "Male sibling relationship"),
            ("Sister", "FAMILY", "FEMALE", 1, "Female sibling relationship"),
            ("Husband", "FAMILY", "MALE", 1, "Male spouse relationship"),
            ("Wife", "FAMILY", "FEMALE", 1, "Female spouse relationship"),
            ("Grandfather", "FAMILY", "MALE", 1, "Male grandparent relationship"),
            ("Grandmother", "FAMILY", "FEMALE", 1, "Female grandparent relationship"),
            ("Grandson", "FAMILY", "MALE", 1, "Male grandchild relationship"),
            ("Granddaughter", "FAMILY", "FEMALE", 1, "Female grandchild relationship"),
            ("Uncle", "FAMILY", "MALE", 1, "Male parental sibling relationship"),
            ("Aunt", "FAMILY", "FEMALE", 1, "Female parental sibling relationship"),
            ("Nephew", "FAMILY", "MALE", 1, "Male sibling's child relationship"),
            ("Niece", "FAMILY", "FEMALE", 1, "Female sibling's child relationship"),
            ("Cousin", "FAMILY", "NEUTRAL", 1, "Extended family relationship"),
            ("Step-father", "FAMILY", "MALE", 1, "Male step-parent relationship"),
            ("Step-mother", "FAMILY", "FEMALE", 1, "Female step-parent relationship"),
            ("Step-son", "FAMILY", "MALE", 1, "Male step-child relationship"),
            ("Step-daughter", "FAMILY", "FEMALE", 1, "Female step-child relationship"),
            ("Step-brother", "FAMILY", "MALE", 1, "Male step-sibling relationship"),
            ("Step-sister", "FAMILY", "FEMALE", 1, "Female step-sibling relationship"),
            ("Parent", "FAMILY", "NEUTRAL", 0, "Neutral parent relationship"),
            ("Child", "FAMILY", "NEUTRAL", 0, "Neutral child relationship"),
            ("Sibling", "FAMILY", "NEUTRAL", 0, "Neutral sibling relationship"),
            ("Spouse", "FAMILY", "NEUTRAL", 0, "Neutral spouse relationship"),
            ("Grandparent", "FAMILY", "NEUTRAL", 0, "Neutral grandparent relationship"),
            ("Grandchild", "FAMILY", "NEUTRAL", 0, "Neutral grandchild relationship")
        ]
        
        # Work relationships
        work_types = [
            ("Boss", "WORK", "NEUTRAL", 1, "Superior at work"),
            ("Employee", "WORK", "NEUTRAL", 1, "Reports to another person at work"),
            ("Coworker", "WORK", "NEUTRAL", 1, "Works alongside another person"),
            ("Colleague", "WORK", "NEUTRAL", 1, "Professional associate"),
            ("Assistant", "WORK", "NEUTRAL", 1, "Helps or supports another person at work"),
            ("Mentor", "WORK", "NEUTRAL", 1, "Provides guidance and advice"),
            ("Mentee", "WORK", "NEUTRAL", 1, "Receives guidance and advice"),
            ("Supervisor", "WORK", "NEUTRAL", 1, "Oversees work of another person"),
            ("Subordinate", "WORK", "NEUTRAL", 1, "Work is overseen by another person"),
            ("Business partner", "WORK", "NEUTRAL", 1, "Shares business interests")
        ]
        
        # Study relationships
        study_types = [
            ("Teacher", "STUDY", "NEUTRAL", 1, "Provides education"),
            ("Student", "STUDY", "NEUTRAL", 1, "Receives education"),
            ("Classmate", "STUDY", "NEUTRAL", 1, "Attends same class"),
            ("Schoolmate", "STUDY", "NEUTRAL", 1, "Attends same school"),
            ("Roommate", "STUDY", "NEUTRAL", 1, "Shares living space")
        ]
        
        # Romantic relationships
        romantic_types = [
            ("Boyfriend", "ROMANTIC", "MALE", 1, "Male romantic partner"),
            ("Girlfriend", "ROMANTIC", "FEMALE", 1, "Female romantic partner"),
            ("Fiancé", "ROMANTIC", "MALE", 1, "Male engaged partner"),
            ("Fiancée", "ROMANTIC", "FEMALE", 1, "Female engaged partner"),
            ("Lover", "ROMANTIC", "NEUTRAL", 1, "Romantic or sexual partner"),
            ("Ex-boyfriend", "ROMANTIC", "MALE", 1, "Former male romantic partner"),
            ("Ex-girlfriend", "ROMANTIC", "FEMALE", 1, "Former female romantic partner"),
            ("Ex-husband", "ROMANTIC", "MALE", 1, "Former male spouse"),
            ("Ex-wife", "ROMANTIC", "FEMALE", 1, "Former female spouse"),
            ("Ex-spouse", "ROMANTIC", "NEUTRAL", 0, "Former spouse"),
            ("Partner", "ROMANTIC", "NEUTRAL", 1, "Committed relationship partner"),
            ("Significant other", "ROMANTIC", "NEUTRAL", 0, "Romantic partner")
        ]
        
        # Social relationships
        social_types = [
            ("Friend", "SOCIAL", "NEUTRAL", 1, "Social companion"),
            ("Best friend", "SOCIAL", "NEUTRAL", 1, "Close friend"),
            ("Acquaintance", "SOCIAL", "NEUTRAL", 1, "Casual social connection"),
            ("Neighbor", "SOCIAL", "NEUTRAL", 1, "Lives nearby"),
            ("Roommate", "SOCIAL", "NEUTRAL", 1, "Shares living space")
        ]
        
        # Other relationships
        other_types = [
            ("Rival", "OTHER", "NEUTRAL", 1, "Competes against"),
            ("Enemy", "OTHER", "NEUTRAL", 1, "Hostile relationship"),
            ("Ally", "OTHER", "NEUTRAL", 1, "Cooperates with"),
            ("Guardian", "OTHER", "NEUTRAL", 1, "Protects or looks after"),
            ("Ward", "OTHER", "NEUTRAL", 1, "Protected by another person"),
            ("Caretaker", "OTHER", "NEUTRAL", 1, "Provides care")
        ]
        
        # Combine all relationship types
        all_types = family_types + work_types + study_types + romantic_types + social_types + other_types
        
        # Insert all relationship types
        for rel_type in all_types:
            cursor.execute('''
            INSERT INTO relationship_types (name, type_key, gender_context, is_common, description)
            VALUES (?, ?, ?, ?, ?)
            ''', rel_type)
            
        # Now set up inverse relationships
        inverse_pairs = [
            # Family
            ("Father", "Son", "Daughter", "Child"),
            ("Mother", "Son", "Daughter", "Child"),
            ("Son", "Father", "Mother", "Parent"),
            ("Daughter", "Father", "Mother", "Parent"),
            ("Brother", "Brother", "Sister", "Sibling"),
            ("Sister", "Brother", "Sister", "Sibling"),
            ("Husband", "Wife", None, "Spouse"),
            ("Wife", "Husband", None, "Spouse"),
            ("Grandfather", "Grandson", "Granddaughter", "Grandchild"),
            ("Grandmother", "Grandson", "Granddaughter", "Grandchild"),
            ("Grandson", "Grandfather", "Grandmother", "Grandparent"),
            ("Granddaughter", "Grandfather", "Grandmother", "Grandparent"),
            ("Uncle", "Nephew", "Niece", None),
            ("Aunt", "Nephew", "Niece", None),
            ("Nephew", "Uncle", "Aunt", None),
            ("Niece", "Uncle", "Aunt", None),
            ("Cousin", "Cousin", "Cousin", "Cousin"),
            ("Step-father", "Step-son", "Step-daughter", None),
            ("Step-mother", "Step-son", "Step-daughter", None),
            ("Step-son", "Step-father", "Step-mother", None),
            ("Step-daughter", "Step-father", "Step-mother", None),
            ("Step-brother", "Step-brother", "Step-sister", None),
            ("Step-sister", "Step-brother", "Step-sister", None),
            
            # Work
            ("Boss", "Employee", None, None),
            ("Employee", "Boss", None, None),
            ("Coworker", "Coworker", None, None),
            ("Colleague", "Colleague", None, None),
            ("Assistant", "Boss", None, None),
            ("Mentor", "Mentee", None, None),
            ("Mentee", "Mentor", None, None),
            ("Supervisor", "Subordinate", None, None),
            ("Subordinate", "Supervisor", None, None),
            ("Business partner", "Business partner", None, None),
            
            # Study
            ("Teacher", "Student", None, None),
            ("Student", "Teacher", None, None),
            ("Classmate", "Classmate", None, None),
            ("Schoolmate", "Schoolmate", None, None),
            ("Roommate", "Roommate", None, None),
            
            # Romantic
            ("Boyfriend", "Girlfriend", None, None),
            ("Girlfriend", "Boyfriend", None, None),
            ("Fiancé", "Fiancée", None, None),
            ("Fiancée", "Fiancé", None, None),
            ("Lover", "Lover", None, None),
            ("Ex-boyfriend", "Ex-girlfriend", None, None),
            ("Ex-girlfriend", "Ex-boyfriend", None, None),
            ("Ex-husband", "Ex-wife", None, None),
            ("Ex-wife", "Ex-husband", None, None),
            ("Partner", "Partner", None, None),
            
            # Social
            ("Friend", "Friend", None, None),
            ("Best friend", "Best friend", None, None),
            ("Acquaintance", "Acquaintance", None, None),
            ("Neighbor", "Neighbor", None, None),
            
            # Other
            ("Rival", "Rival", None, None),
            ("Enemy", "Enemy", None, None),
            ("Ally", "Ally", None, None),
            ("Guardian", "Ward", None, None),
            ("Ward", "Guardian", None, None),
            ("Caretaker", "Ward", None, None)
        ]
        
        # Update inverse relationships
        for rel, male_inv, female_inv, neutral_inv in inverse_pairs:
            # Get the ID of the relationship type
            cursor.execute('SELECT id FROM relationship_types WHERE name = ?', (rel,))
            rel_id = cursor.fetchone()[0]
            
            # Get the IDs of inverse relationship types
            male_inv_id = None
            if male_inv:
                cursor.execute('SELECT id FROM relationship_types WHERE name = ?', (male_inv,))
                result = cursor.fetchone()
                if result:
                    male_inv_id = result[0]
            
            female_inv_id = None
            if female_inv:
                cursor.execute('SELECT id FROM relationship_types WHERE name = ?', (female_inv,))
                result = cursor.fetchone()
                if result:
                    female_inv_id = result[0]
            
            neutral_inv_id = None
            if neutral_inv:
                cursor.execute('SELECT id FROM relationship_types WHERE name = ?', (neutral_inv,))
                result = cursor.fetchone()
                if result:
                    neutral_inv_id = result[0]
            
            # Use male inverse as default if available
            inverse_id = male_inv_id or female_inv_id or neutral_inv_id
            
            if inverse_id:
                cursor.execute('''
                UPDATE relationship_types SET inverse_id = ? WHERE id = ?
                ''', (inverse_id, rel_id))
        
        conn.commit()


def create_relationship(conn: sqlite3.Connection, source_id: int, target_id: int, 
                       relationship_type_id: int, description: Optional[str] = None, 
                       strength: int = 3, color: str = "#FF0000", width: float = 1.0,
                       is_custom: bool = False, custom_label: Optional[str] = None) -> int:
    """Create a new relationship in the database.
    
    Args:
        conn: Database connection
        source_id: ID of the source character
        target_id: ID of the target character
        relationship_type_id: ID of the relationship type
        description: Optional description
        strength: Relationship strength (1-5)
        color: Hex color for visualization
        width: Line width for visualization
        is_custom: Whether this is a custom relationship
        custom_label: Custom relationship label (if is_custom is True)
        
    Returns:
        ID of the created relationship
    """
    cursor = conn.cursor()
    
    # Get the relationship type label to use for the legacy relationship_type column
    relationship_type_label = custom_label
    if not is_custom or not custom_label:
        try:
            cursor.execute("SELECT label FROM relationship_types_new WHERE type_id = ?", (relationship_type_id,))
            result = cursor.fetchone()
            if result:
                relationship_type_label = result[0]
            else:
                # Fallback if relationship type not found
                relationship_type_label = "Unknown Relationship"
        except Exception as e:
            print(f"Error fetching relationship type label: {e}")
            relationship_type_label = "Unknown Relationship"
    
    cursor.execute('''
    INSERT INTO relationships (
        source_id, target_id, relationship_type_id, relationship_type,
        description, strength, color, width,
        is_custom, custom_label
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        source_id, target_id, relationship_type_id, relationship_type_label,
        description, strength, color, width,
        1 if is_custom else 0, custom_label
    ))
    
    conn.commit()
    return cursor.lastrowid


def get_relationship_categories(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get all relationship categories.
    
    Args:
        conn: Database connection
        
    Returns:
        List of relationship category dictionaries
    """
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM relationship_categories 
    ORDER BY display_order, name
    ''')
    return [dict(row) for row in cursor.fetchall()]


def get_relationship_types(conn: sqlite3.Connection, 
                         category_id: Optional[str] = None,
                         is_common: Optional[bool] = None,
                         gender_context: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get relationship types with optional filtering.
    
    Args:
        conn: Database connection
        category_id: Optional category type_key to filter by
        is_common: Optional flag to filter by common/uncommon types
        gender_context: Optional gender context to filter by
        
    Returns:
        List of relationship type dictionaries
    """
    cursor = conn.cursor()
    
    query = 'SELECT * FROM relationship_types'
    params = []
    
    # Add filters
    filters = []
    if category_id is not None:
        filters.append('type_key = ?')
        params.append(category_id)
    
    if is_common is not None:
        filters.append('is_common = ?')
        params.append(1 if is_common else 0)
    
    if gender_context is not None:
        filters.append('gender_context = ?')
        params.append(gender_context)
    
    # Add WHERE clause if we have filters
    if filters:
        query += ' WHERE ' + ' AND '.join(filters)
    
    # Add ordering
    query += ' ORDER BY name'
    
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def get_relationship_type_by_id(conn: sqlite3.Connection, type_id: int) -> Optional[Dict[str, Any]]:
    """Get a relationship type by ID.
    
    Args:
        conn: Database connection
        type_id: ID of the relationship type
        
    Returns:
        Relationship type dictionary or None if not found
    """
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM relationship_types WHERE id = ?', (type_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_relationship_type_inverse(conn: sqlite3.Connection, type_id: int, 
                                target_gender: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get the inverse relationship type based on target character's gender.
    
    Args:
        conn: Database connection
        type_id: ID of the relationship type
        target_gender: Gender of the target character (MALE, FEMALE, or None)
        
    Returns:
        Inverse relationship type dictionary or None if not found
    """
    cursor = conn.cursor()
    
    # Get the relationship type
    cursor.execute('SELECT * FROM relationship_types WHERE id = ?', (type_id,))
    rel_type = cursor.fetchone()
    
    if not rel_type or not rel_type['inverse_id']:
        return None
    
    # Get the inverse relationship type
    cursor.execute('SELECT * FROM relationship_types WHERE id = ?', (rel_type['inverse_id'],))
    inverse = cursor.fetchone()
    
    if not inverse:
        return None
    
    # Return the inverse relationship type
    return dict(inverse)


def get_character_relationships(conn: sqlite3.Connection, character_id: int) -> List[Dict[str, Any]]:
    """Get all relationships for a character with detailed information.
    
    Args:
        conn: Database connection
        character_id: ID of the character
        
    Returns:
        List of relationship dictionaries with details for display
    """
    cursor = conn.cursor()
    
    # Get relationships where the character is the source
    cursor.execute('''
    SELECT r.*, c.name as target_name, 
           rt.label as relationship_name, rt.gender_context,
           rc.name as category_name
    FROM relationships r
    JOIN characters c ON r.target_id = c.id
    LEFT JOIN relationship_types_new rt ON r.relationship_type_id = rt.type_id
    LEFT JOIN relationship_categories rc ON rt.category_id = rc.id
    WHERE r.source_id = ?
    ORDER BY r.strength DESC, r.updated_at DESC
    ''', (character_id,))
    
    outgoing = [dict(row) for row in cursor.fetchall()]
    
    # Get relationships where the character is the target
    cursor.execute('''
    SELECT r.*, c.name as source_name, 
           rt.label as relationship_name, rt.gender_context,
           rc.name as category_name
    FROM relationships r
    JOIN characters c ON r.source_id = c.id
    LEFT JOIN relationship_types_new rt ON r.relationship_type_id = rt.type_id
    LEFT JOIN relationship_categories rc ON rt.category_id = rc.id
    WHERE r.target_id = ?
    ORDER BY r.strength DESC, r.updated_at DESC
    ''', (character_id,))
    
    incoming = [dict(row) for row in cursor.fetchall()]
    
    # Process relationships for display
    relationships = []
    
    # Process outgoing relationships
    for rel in outgoing:
        display_name = rel['relationship_name']
        if rel['is_custom'] and rel['custom_label']:
            display_name = rel['custom_label']
        
        relationships.append({
            'id': rel['id'],
            'name': rel['target_name'],
            'character_id': rel['target_id'],
            'type': display_name,
            'direction': 'outgoing',
            'strength': rel['strength'],
            'category': rel['category_name'],
            'updated_at': rel['updated_at'],
            'description': rel['description'],
            'is_custom': rel['is_custom']
        })
    
    # Process incoming relationships
    for rel in incoming:
        display_name = rel['relationship_name']
        if rel['is_custom'] and rel['custom_label']:
            display_name = rel['custom_label']
        
        relationships.append({
            'id': rel['id'],
            'name': rel['source_name'],
            'character_id': rel['source_id'],
            'type': display_name,
            'direction': 'incoming',
            'strength': rel['strength'],
            'category': rel['category_name'],
            'updated_at': rel['updated_at'],
            'description': rel['description'],
            'is_custom': rel['is_custom']
        })
    
    # Sort by strength and update time
    relationships.sort(key=lambda x: (-(x['strength'] or 0), x['updated_at']), reverse=True)
    
    return relationships


def get_relationship(conn: sqlite3.Connection, relationship_id: int) -> Optional[Dict[str, Any]]:
    """Get a relationship by ID with detailed information.
    
    Args:
        conn: Database connection
        relationship_id: ID of the relationship
        
    Returns:
        Relationship dictionary with details or None if not found
    """
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.*, 
           s.name as source_name, s.gender as source_gender,
           t.name as target_name, t.gender as target_gender,
           rt.label as relationship_name, rt.gender_context,
           rc.name as category_name
    FROM relationships r
    JOIN characters s ON r.source_id = s.id
    JOIN characters t ON r.target_id = t.id
    LEFT JOIN relationship_types_new rt ON r.relationship_type_id = rt.type_id
    LEFT JOIN relationship_categories rc ON rt.category_id = rc.id
    WHERE r.id = ?
    ''', (relationship_id,))
    
    row = cursor.fetchone()
    
    if not row:
        return None
    
    # Process relationship for display
    result = dict(row)
    
    # Set display name
    if result['is_custom'] and result['custom_label']:
        result['display_name'] = result['custom_label']
    else:
        result['display_name'] = result['relationship_name']
    
    return result


def update_relationship(conn: sqlite3.Connection, relationship_id: int,
                      description: Optional[str] = None,
                      relationship_type_id: Optional[int] = None,
                      strength: Optional[int] = None,
                      color: Optional[str] = None,
                      width: Optional[float] = None,
                      is_custom: Optional[bool] = None,
                      custom_label: Optional[str] = None) -> bool:
    """Update a relationship.
    
    Args:
        conn: Database connection
        relationship_id: ID of the relationship to update
        description: Optional new description
        relationship_type_id: Optional new relationship type ID
        strength: Optional new strength value
        color: Optional new color
        width: Optional new width
        is_custom: Optional new custom flag
        custom_label: Optional new custom label
        
    Returns:
        True if successful, False otherwise
    """
    cursor = conn.cursor()
    
    # Build the update query
    updates = []
    params = []
    
    if description is not None:
        updates.append('description = ?')
        params.append(description)
    
    if relationship_type_id is not None:
        updates.append('relationship_type_id = ?')
        params.append(relationship_type_id)
        
        # Also update the relationship_type column with the label
        try:
            cursor.execute("SELECT label FROM relationship_types_new WHERE type_id = ?", (relationship_type_id,))
            result = cursor.fetchone()
            if result:
                updates.append('relationship_type = ?')
                params.append(result[0])
        except Exception as e:
            print(f"Error fetching relationship type label: {e}")
    
    if strength is not None:
        updates.append('strength = ?')
        params.append(strength)
    
    if color is not None:
        updates.append('color = ?')
        params.append(color)
    
    if width is not None:
        updates.append('width = ?')
        params.append(width)
    
    if is_custom is not None:
        updates.append('is_custom = ?')
        params.append(1 if is_custom else 0)
    
    if custom_label is not None:
        updates.append('custom_label = ?')
        params.append(custom_label)
        
        # If this is a custom relationship, also update the relationship_type column
        if is_custom or (is_custom is None and cursor.execute("SELECT is_custom FROM relationships WHERE id = ?", (relationship_id,)).fetchone()[0]):
            updates.append('relationship_type = ?')
            params.append(custom_label)
    
    # Always update the timestamp
    updates.append('updated_at = CURRENT_TIMESTAMP')
    
    # If nothing to update, return True
    if not updates:
        return True
    
    # Build the query
    query = f'UPDATE relationships SET {", ".join(updates)} WHERE id = ?'
    params.append(relationship_id)
    
    # Execute the update
    cursor.execute(query, params)
    conn.commit()
    
    return cursor.rowcount > 0


def delete_relationship(conn: sqlite3.Connection, relationship_id: int) -> bool:
    """Delete a relationship.
    
    Args:
        conn: Database connection
        relationship_id: ID of the relationship to delete
        
    Returns:
        True if successful, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute('DELETE FROM relationships WHERE id = ?', (relationship_id,))
    conn.commit()
    return cursor.rowcount > 0


def suggest_relationship_type(conn: sqlite3.Connection, source_id: int, target_id: int) -> List[Dict[str, Any]]:
    """Suggest potential relationship types based on characters' genders.
    
    Args:
        conn: Database connection
        source_id: ID of the source character
        target_id: ID of the target character
        
    Returns:
        List of suggested relationship type dictionaries
    """
    cursor = conn.cursor()
    
    # Get character information
    cursor.execute('SELECT gender FROM characters WHERE id = ?', (source_id,))
    source_row = cursor.fetchone()
    
    cursor.execute('SELECT gender FROM characters WHERE id = ?', (target_id,))
    target_row = cursor.fetchone()
    
    if not source_row or not target_row:
        return []
    
    source_gender = source_row['gender']
    target_gender = target_row['gender']
    
    # Map the application's gender values to our simplified ones
    gender_map = {
        'MALE': 'masculine',
        'FEMALE': 'feminine',
        'NOT_SPECIFIED': 'neutral',
        'OTHER': 'neutral'
    }
    
    source_context = gender_map.get(source_gender, 'neutral')
    
    # Get relationship types appropriate for source's gender
    query = '''
    SELECT rt.*, rc.name as category_name
    FROM relationship_types_new rt
    JOIN relationship_categories rc ON rt.category_id = rc.id
    WHERE (rt.gender_context = ? OR rt.gender_context = 'neutral')
    ORDER BY rc.display_order, rt.name
    '''
    
    cursor.execute(query, (source_context,))
    return [dict(row) for row in cursor.fetchall()]


def get_story_relationships(conn: sqlite3.Connection, story_id: int) -> List[Dict[str, Any]]:
    """Get all relationships for a story with detailed information.
    
    Args:
        conn: Database connection
        story_id: ID of the story
        
    Returns:
        List of relationship dictionaries with details for visualization
    """
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.*, 
           s.name as source_name, s.id as source_id,
           t.name as target_name, t.id as target_id,
           COALESCE(r.custom_label, rt.label) as relationship_name
    FROM relationships r
    JOIN characters s ON r.source_id = s.id
    JOIN characters t ON r.target_id = t.id
    LEFT JOIN relationship_types_new rt ON r.relationship_type_id = rt.type_id
    WHERE s.story_id = ?
    ORDER BY r.strength DESC, r.updated_at DESC
    ''', (story_id,))
    
    relationships = []
    for row in cursor.fetchall():
        relationship = dict(row)
        relationships.append({
            'id': relationship['id'],
            'source_id': relationship['source_id'],
            'source_name': relationship['source_name'],
            'target_id': relationship['target_id'],
            'target_name': relationship['target_name'],
            'type': relationship['relationship_name'],
            'strength': relationship['strength'],
            'color': relationship['color'],
            'width': relationship['width'],
            'is_custom': relationship['is_custom']
        })
    
    return relationships 
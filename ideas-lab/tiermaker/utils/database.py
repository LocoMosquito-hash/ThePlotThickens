#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database manager for Tier Maker.

This module provides database operations for tier templates and character data.
"""

import sqlite3
import os
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from models.tier_template import TierTemplate, TierTemplateTier
from models.rankable_item import RankableItem, ItemType


class DatabaseManager:
    """Manages database operations for the Tier Maker."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database manager.
        
        Args:
            db_path: Path to the database file. If None, uses the main app database.
        """
        if db_path is None:
            # Use the main app database
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "..", "..", "..", "the_plot_thickens.db")
        
        self.db_path = os.path.abspath(db_path)
        self._ensure_tables_exist()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_tables_exist(self) -> None:
        """Ensure tier maker tables exist in the database."""
        with self._get_connection() as conn:
            # Create tier_templates table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tier_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create tier_template_tiers table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tier_template_tiers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id INTEGER NOT NULL,
                    tier_name TEXT NOT NULL,
                    tier_color TEXT NOT NULL,
                    tier_order INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES tier_templates(id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
    
    # Template operations
    def save_template(self, template: TierTemplate) -> int:
        """Save a tier template to the database.
        
        Args:
            template: The template to save
            
        Returns:
            The ID of the saved template
            
        Raises:
            sqlite3.IntegrityError: If template name already exists
        """
        with self._get_connection() as conn:
            if template.id is None:
                # Insert new template
                cursor = conn.execute(
                    "INSERT INTO tier_templates (name) VALUES (?)",
                    (template.name,)
                )
                template_id = cursor.lastrowid
            else:
                # Update existing template
                conn.execute(
                    "UPDATE tier_templates SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (template.name, template.id)
                )
                template_id = template.id
                
                # Delete existing tiers
                conn.execute("DELETE FROM tier_template_tiers WHERE template_id = ?", (template_id,))
            
            # Insert tiers
            for tier in template.tiers:
                conn.execute(
                    "INSERT INTO tier_template_tiers (template_id, tier_name, tier_color, tier_order) VALUES (?, ?, ?, ?)",
                    (template_id, tier.tier_name, tier.tier_color, tier.tier_order)
                )
            
            conn.commit()
            return template_id
    
    def load_template(self, template_id: int) -> Optional[TierTemplate]:
        """Load a tier template from the database.
        
        Args:
            template_id: The ID of the template to load
            
        Returns:
            The loaded template or None if not found
        """
        with self._get_connection() as conn:
            # Load template
            template_row = conn.execute(
                "SELECT * FROM tier_templates WHERE id = ?",
                (template_id,)
            ).fetchone()
            
            if not template_row:
                return None
            
            # Load tiers
            tier_rows = conn.execute(
                "SELECT * FROM tier_template_tiers WHERE template_id = ? ORDER BY tier_order",
                (template_id,)
            ).fetchall()
            
            # Create template object
            template = TierTemplate(
                id=template_row['id'],
                name=template_row['name'],
                created_at=datetime.fromisoformat(template_row['created_at']),
                updated_at=datetime.fromisoformat(template_row['updated_at']),
                tiers=[]
            )
            
            # Add tiers
            for tier_row in tier_rows:
                tier = TierTemplateTier(
                    id=tier_row['id'],
                    template_id=tier_row['template_id'],
                    tier_name=tier_row['tier_name'],
                    tier_color=tier_row['tier_color'],
                    tier_order=tier_row['tier_order'],
                    created_at=datetime.fromisoformat(tier_row['created_at'])
                )
                template.tiers.append(tier)
            
            return template
    
    def list_templates(self) -> List[Tuple[int, str]]:
        """List all available templates.
        
        Returns:
            List of (id, name) tuples
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name FROM tier_templates ORDER BY name"
            ).fetchall()
            
            return [(row['id'], row['name']) for row in rows]
    
    def delete_template(self, template_id: int) -> bool:
        """Delete a tier template.
        
        Args:
            template_id: The ID of the template to delete
            
        Returns:
            True if template was deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM tier_templates WHERE id = ?",
                (template_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def template_name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a template name already exists.
        
        Args:
            name: The template name to check
            exclude_id: Template ID to exclude from check (for updates)
            
        Returns:
            True if name exists, False otherwise
        """
        with self._get_connection() as conn:
            if exclude_id is not None:
                row = conn.execute(
                    "SELECT 1 FROM tier_templates WHERE name = ? AND id != ?",
                    (name, exclude_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT 1 FROM tier_templates WHERE name = ?",
                    (name,)
                ).fetchone()
            
            return row is not None
    
    # Character operations
    def get_stories(self) -> List[Tuple[int, str]]:
        """Get all available stories.
        
        Returns:
            List of (id, title) tuples
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, title FROM stories ORDER BY title"
            ).fetchall()
            
            return [(row['id'], row['title']) for row in rows]
    
    def get_genders_for_story(self, story_id: int) -> List[str]:
        """Get all unique genders for characters in a story.
        
        Args:
            story_id: The story ID
            
        Returns:
            List of unique gender values
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT gender FROM characters WHERE story_id = ? AND gender IS NOT NULL ORDER BY gender",
                (story_id,)
            ).fetchall()
            
            return [row['gender'] for row in rows]
    
    def get_characters(self, story_id: int, gender_filter: Optional[str] = None, 
                      min_love_interest: int = 0) -> List[RankableItem]:
        """Get characters from a story with optional filters.
        
        Args:
            story_id: The story ID
            gender_filter: Optional gender filter
            min_love_interest: Minimum love interest rating
            
        Returns:
            List of RankableItem objects representing characters
        """
        with self._get_connection() as conn:
            query = """
                SELECT id, name, avatar_path, gender, love_interest 
                FROM characters 
                WHERE story_id = ? AND love_interest >= ? AND is_archived = 0
            """
            params = [story_id, min_love_interest]
            
            if gender_filter:
                query += " AND gender = ?"
                params.append(gender_filter)
            
            query += " ORDER BY name"
            
            rows = conn.execute(query, params).fetchall()
            
            characters = []
            for row in rows:
                character = RankableItem.from_character(
                    character_id=row['id'],
                    name=row['name'],
                    avatar_path=row['avatar_path'],
                    gender=row['gender'],
                    love_interest=row['love_interest']
                )
                characters.append(character)
            
            return characters 
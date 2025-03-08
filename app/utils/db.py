#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database utility functions for The Plot Thickens application.

This module provides utility functions for database operations.
"""

import os
from typing import Optional

from app.models import Database, Base, RelationshipType


def initialize_database(db_path: str = 'sqlite:///the_plot_thickens.db') -> Database:
    """Initialize the database and create tables if they don't exist.
    
    Args:
        db_path: Path to the database file or connection string
        
    Returns:
        Database instance
    """
    db = Database(db_path)
    db.create_tables()
    
    # Initialize with default data
    session = db.get_session()
    try:
        # Add default relationship types if they don't exist
        create_default_relationship_types(session)
        db.commit_session(session)
    except Exception as e:
        db.rollback_session(session)
        raise e
    finally:
        db.close_session(session)
    
    return db


def create_default_relationship_types(session) -> None:
    """Create default relationship types if they don't exist.
    
    Args:
        session: Database session
    """
    # Check if we already have relationship types
    count = session.query(RelationshipType).count()
    if count > 0:
        return
    
    # Family relationships
    father = RelationshipType(
        name="Father",
        description="Paternal relationship",
        has_inverse=True,
        is_global=True,
        male_variant="Son",
        female_variant="Daughter"
    )
    session.add(father)
    session.flush()
    
    son = RelationshipType(
        name="Son",
        description="Male child relationship",
        has_inverse=True,
        inverse_id=father.id,
        is_global=True
    )
    session.add(son)
    
    daughter = RelationshipType(
        name="Daughter",
        description="Female child relationship",
        has_inverse=True,
        inverse_id=father.id,
        is_global=True
    )
    session.add(daughter)
    
    mother = RelationshipType(
        name="Mother",
        description="Maternal relationship",
        has_inverse=True,
        is_global=True,
        male_variant="Son",
        female_variant="Daughter"
    )
    session.add(mother)
    session.flush()
    
    # Update son and daughter to point to mother as well
    son.inverse_id = mother.id
    daughter.inverse_id = mother.id
    
    # Sibling relationships
    brother = RelationshipType(
        name="Brother",
        description="Male sibling relationship",
        has_inverse=True,
        is_global=True,
        male_variant="Brother",
        female_variant="Sister"
    )
    session.add(brother)
    session.flush()
    
    sister = RelationshipType(
        name="Sister",
        description="Female sibling relationship",
        has_inverse=True,
        inverse_id=brother.id,
        is_global=True,
        male_variant="Brother",
        female_variant="Sister"
    )
    session.add(sister)
    brother.inverse_id = sister.id
    
    # Friend/enemy relationships
    friend = RelationshipType(
        name="Friend",
        description="Friendship relationship",
        has_inverse=True,
        is_global=True
    )
    session.add(friend)
    session.flush()
    friend.inverse_id = friend.id
    
    enemy = RelationshipType(
        name="Enemy",
        description="Antagonistic relationship",
        has_inverse=True,
        is_global=True
    )
    session.add(enemy)
    session.flush()
    enemy.inverse_id = enemy.id
    
    # Work relationships
    coworker = RelationshipType(
        name="Coworker",
        description="Work colleague relationship",
        has_inverse=True,
        is_global=True
    )
    session.add(coworker)
    session.flush()
    coworker.inverse_id = coworker.id
    
    boss = RelationshipType(
        name="Boss",
        description="Supervisory relationship",
        has_inverse=True,
        is_global=True
    )
    session.add(boss)
    session.flush()
    
    employee = RelationshipType(
        name="Employee",
        description="Subordinate relationship",
        has_inverse=True,
        inverse_id=boss.id,
        is_global=True
    )
    session.add(employee)
    boss.inverse_id = employee.id
    
    # Romantic relationships
    spouse = RelationshipType(
        name="Spouse",
        description="Marital relationship",
        has_inverse=True,
        is_global=True
    )
    session.add(spouse)
    session.flush()
    spouse.inverse_id = spouse.id
    
    boyfriend = RelationshipType(
        name="Boyfriend",
        description="Male romantic partner",
        has_inverse=True,
        is_global=True
    )
    session.add(boyfriend)
    session.flush()
    
    girlfriend = RelationshipType(
        name="Girlfriend",
        description="Female romantic partner",
        has_inverse=True,
        inverse_id=boyfriend.id,
        is_global=True
    )
    session.add(girlfriend)
    boyfriend.inverse_id = girlfriend.id
    
    # Other relationships
    mentor = RelationshipType(
        name="Mentor",
        description="Teaching/guiding relationship",
        has_inverse=True,
        is_global=True
    )
    session.add(mentor)
    session.flush()
    
    student = RelationshipType(
        name="Student",
        description="Learning relationship",
        has_inverse=True,
        inverse_id=mentor.id,
        is_global=True
    )
    session.add(student)
    mentor.inverse_id = student.id 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal database schema for The Plot Thickens application.

This module defines a minimal version of the SQLAlchemy models for the Story Board feature.
"""

import os
import json
from datetime import datetime
from enum import Enum, auto
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

# Create the base model class
Base = declarative_base()


# Enumerations
class StoryType(Enum):
    """Enumeration of story types."""
    VISUAL_NOVEL = auto()
    TV_SERIES = auto()
    MOVIE = auto()
    GAME = auto()
    OTHER = auto()
    
    def __str__(self):
        return self.name.replace('_', ' ').title()


# Models
class Story(Base):
    """Model representing a story in the application."""
    __tablename__ = 'stories'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type_name = Column(String(50), nullable=False, default="OTHER")  # Store as string instead of enum
    folder_path = Column(String(1024), nullable=False, unique=True)
    
    # Relationships
    characters = relationship("Character", back_populates="story", cascade="all, delete-orphan")
    board_views = relationship("StoryBoardView", back_populates="story", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Story(id={self.id}, title='{self.title}', type={self.type_name})>"
    
    @property
    def images_folder(self):
        return os.path.join(self.folder_path, "images")
    
    def ensure_folders_exist(self):
        os.makedirs(self.folder_path, exist_ok=True)
        os.makedirs(self.images_folder, exist_ok=True)


class StoryBoardView(Base):
    """Model representing a saved view of the story board."""
    __tablename__ = 'story_board_views'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    layout_data = Column(Text, nullable=False)  # JSON string with layout information
    
    # Foreign keys
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=False)
    
    # Relationships
    story = relationship("Story", back_populates="board_views")
    
    def __repr__(self):
        return f"<StoryBoardView(id={self.id}, name='{self.name}', story_id={self.story_id})>"
    
    @property
    def layout(self):
        return json.loads(self.layout_data)
    
    @layout.setter
    def layout(self, value):
        self.layout_data = json.dumps(value)


class Character(Base):
    """Model representing a character in a story."""
    __tablename__ = 'characters'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Basic information
    name = Column(String(255), nullable=False)
    aliases = Column(Text, nullable=True)  # Comma-separated list of aliases
    is_main_character = Column(Boolean, default=False)
    
    # Physical attributes
    age_value = Column(Integer, nullable=True)  # Actual age if known
    age_category = Column(String(50), nullable=True)  # Store as string instead of enum
    gender = Column(String(50), default="NOT_SPECIFIED")  # Store as string instead of enum
    
    # Additional information
    avatar_path = Column(String(1024), nullable=True)  # Path to avatar image
    
    # Foreign keys
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=False)
    
    # Relationships
    story = relationship("Story", back_populates="characters")
    
    # Relationships with other characters
    outgoing_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.source_id",
        back_populates="source",
        cascade="all, delete-orphan"
    )
    incoming_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.target_id",
        back_populates="target",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Character(id={self.id}, name='{self.name}', story_id={self.story_id})>"
    
    @property
    def alias_list(self):
        if not self.aliases:
            return []
        return [alias.strip() for alias in self.aliases.split(',')]
    
    @alias_list.setter
    def alias_list(self, aliases):
        self.aliases = ','.join(aliases) if aliases else None
    
    @property
    def age_display(self):
        if self.age_value is not None:
            return str(self.age_value)
        if self.age_category is not None:
            return self.age_category
        return "Unknown"
    
    @property
    def all_relationships(self):
        return self.outgoing_relationships + self.incoming_relationships


class Relationship(Base):
    """Model representing a relationship between two characters."""
    __tablename__ = 'relationships'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship properties
    description = Column(Text, nullable=True)
    relationship_type = Column(String(255), nullable=False)  # Store as string instead of foreign key
    color = Column(String(20), default="#FF0000")  # Hex color code for visualization
    width = Column(Float, default=1.0)  # Line width for visualization
    
    # Foreign keys
    source_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    
    # Relationships
    source = relationship("Character", foreign_keys=[source_id], back_populates="outgoing_relationships")
    target = relationship("Character", foreign_keys=[target_id], back_populates="incoming_relationships")
    
    def __repr__(self):
        return f"<Relationship(id={self.id}, source_id={self.source_id}, target_id={self.target_id}, type='{self.relationship_type}')>"


# Database connection and session management
class Database:
    """Database connection and session management."""
    
    def __init__(self, db_path='sqlite:///the_plot_thickens.db'):
        """Initialize the database connection."""
        self.engine = create_engine(db_path)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
    
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a new session for database operations."""
        return self.Session()
    
    def close_session(self, session):
        """Close the session."""
        session.close()
    
    def commit_session(self, session):
        """Commit the session."""
        session.commit()
    
    def rollback_session(self, session):
        """Rollback the session."""
        session.rollback()


def initialize_database(db_path='sqlite:///the_plot_thickens.db'):
    """Initialize the database and create tables if they don't exist."""
    db = Database(db_path)
    db.create_tables()
    return db 
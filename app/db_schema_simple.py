#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simplified database schema for The Plot Thickens application.

This module defines a simplified version of the SQLAlchemy models for the application.
"""

import os
import json
from datetime import datetime
from enum import Enum, auto
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

# Create the base model class
Base = declarative_base()

# Association tables
character_traits = Table(
    'character_traits',
    Base.metadata,
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True),
    Column('trait_id', Integer, ForeignKey('traits.id'), primary_key=True)
)


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
    
    # Universe information
    universe = Column(String(255), nullable=True)
    is_part_of_series = Column(Boolean, default=False)
    series_name = Column(String(255), nullable=True)
    series_order = Column(Integer, nullable=True)
    
    # Metadata
    author = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    
    # Relationships
    characters = relationship("Character", back_populates="story", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="story", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="story", cascade="all, delete-orphan")
    board_views = relationship("StoryBoardView", back_populates="story", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Story(id={self.id}, title='{self.title}', type={self.type_name})>"
    
    @property
    def images_folder(self):
        return os.path.join(self.folder_path, "images")
    
    @property
    def backups_folder(self):
        return os.path.join(self.folder_path, "backups")
    
    def ensure_folders_exist(self):
        os.makedirs(self.folder_path, exist_ok=True)
        os.makedirs(self.images_folder, exist_ok=True)
        os.makedirs(self.backups_folder, exist_ok=True)


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
    is_archived = Column(Boolean, default=False)
    is_deceased = Column(Boolean, default=False)
    
    # Foreign keys
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=False)
    
    # Relationships
    story = relationship("Story", back_populates="characters")
    traits = relationship("CharacterTrait", secondary=character_traits, back_populates="characters")
    details = relationship("CharacterDetail", back_populates="character", cascade="all, delete-orphan")
    
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
    
    # Events
    events = relationship("EventCharacter", back_populates="character", cascade="all, delete-orphan")
    
    # Image tags
    image_tags = relationship("ImageTag", back_populates="character", cascade="all, delete-orphan")
    
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
    
    @property
    def tagged_images(self):
        return [tag.image for tag in self.image_tags]


class CharacterTrait(Base):
    """Model representing a character trait."""
    __tablename__ = 'traits'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    characters = relationship("Character", secondary=character_traits, back_populates="traits")
    
    def __repr__(self):
        return f"<CharacterTrait(id={self.id}, name='{self.name}')>"


class CharacterDetail(Base):
    """Model representing a custom detail for a character."""
    __tablename__ = 'character_details'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=True)
    
    # Foreign keys
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    
    # Relationships
    character = relationship("Character", back_populates="details")
    
    def __repr__(self):
        return f"<CharacterDetail(id={self.id}, key='{self.key}', character_id={self.character_id})>"


class RelationshipType(Base):
    """Model representing a type of relationship between characters."""
    __tablename__ = 'relationship_types'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Inverse relationship information
    has_inverse = Column(Boolean, default=False)
    inverse_id = Column(Integer, ForeignKey('relationship_types.id'), nullable=True)
    
    # Gender-specific variants
    male_variant = Column(String(255), nullable=True)
    female_variant = Column(String(255), nullable=True)
    
    # Global flag (available across all stories)
    is_global = Column(Boolean, default=False)
    
    # Relationships
    inverse = relationship("RelationshipType", remote_side=[id])
    relationships = relationship("Relationship", back_populates="relationship_type")
    
    def __repr__(self):
        return f"<RelationshipType(id={self.id}, name='{self.name}')>"
    
    def get_variant_for_gender(self, gender):
        if gender == "MALE" and self.male_variant:
            return self.male_variant
        if gender == "FEMALE" and self.female_variant:
            return self.female_variant
        return self.name


class Relationship(Base):
    """Model representing a relationship between two characters."""
    __tablename__ = 'relationships'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship properties
    description = Column(Text, nullable=True)
    strength = Column(Float, default=1.0)  # 0.0 to 1.0, used for visualization
    color = Column(String(20), default="#FF0000")  # Hex color code for visualization
    width = Column(Float, default=1.0)  # Line width for visualization
    
    # Timeline information
    start_event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    end_event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    
    # Custom properties (stored as JSON)
    properties_json = Column(Text, nullable=True)
    
    # Foreign keys
    source_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    relationship_type_id = Column(Integer, ForeignKey('relationship_types.id'), nullable=False)
    
    # Relationships
    source = relationship("Character", foreign_keys=[source_id], back_populates="outgoing_relationships")
    target = relationship("Character", foreign_keys=[target_id], back_populates="incoming_relationships")
    relationship_type = relationship("RelationshipType", back_populates="relationships")
    start_event = relationship("Event", foreign_keys=[start_event_id])
    end_event = relationship("Event", foreign_keys=[end_event_id])
    
    def __repr__(self):
        return f"<Relationship(id={self.id}, source_id={self.source_id}, target_id={self.target_id})>"
    
    @property
    def properties(self):
        if not self.properties_json:
            return {}
        return json.loads(self.properties_json)
    
    @properties.setter
    def properties(self, value):
        self.properties_json = json.dumps(value) if value else None


class Event(Base):
    """Model representing an event in a story."""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Event information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Timeline information
    date = Column(DateTime, nullable=True)
    is_approximate_date = Column(Boolean, default=False)
    
    # Custom properties (stored as JSON)
    properties_json = Column(Text, nullable=True)
    
    # Foreign keys
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=False)
    
    # Relationships
    story = relationship("Story", back_populates="events")
    characters = relationship("EventCharacter", back_populates="event", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="event")
    
    # Relationships that start or end with this event
    starting_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.start_event_id",
        back_populates="start_event"
    )
    ending_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.end_event_id",
        back_populates="end_event"
    )
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', story_id={self.story_id})>"
    
    @property
    def properties(self):
        if not self.properties_json:
            return {}
        return json.loads(self.properties_json)
    
    @properties.setter
    def properties(self, value):
        self.properties_json = json.dumps(value) if value else None
    
    @property
    def involved_characters(self):
        return [ec.character for ec in self.characters]
    
    @property
    def date_display(self):
        if not self.date:
            return "Unknown date"
        
        prefix = "Approximately " if self.is_approximate_date else ""
        return f"{prefix}{self.date.strftime('%Y-%m-%d')}"


class EventCharacter(Base):
    """Model representing a character's involvement in an event."""
    __tablename__ = 'event_characters'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Involvement information
    role = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Foreign keys
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="characters")
    character = relationship("Character", back_populates="events")
    
    def __repr__(self):
        return f"<EventCharacter(id={self.id}, event_id={self.event_id}, character_id={self.character_id})>"


class Image(Base):
    """Model representing an image in the application."""
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Image information
    filename = Column(String(255), nullable=False)
    path = Column(String(1024), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Image metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)  # In bytes
    mime_type = Column(String(50), nullable=True)
    
    # Image flags
    is_featured = Column(Boolean, default=False)
    
    # Timeline information
    date_taken = Column(DateTime, nullable=True)
    
    # Custom metadata (stored as JSON)
    metadata_json = Column(Text, nullable=True)
    
    # Foreign keys
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    
    # Relationships
    story = relationship("Story", back_populates="images")
    event = relationship("Event", back_populates="images")
    tags = relationship("ImageTag", back_populates="image", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Image(id={self.id}, filename='{self.filename}', story_id={self.story_id})>"
    
    @property
    def full_path(self):
        return os.path.join(self.path, self.filename)
    
    @property
    def metadata(self):
        if not self.metadata_json:
            return {}
        return json.loads(self.metadata_json)
    
    @metadata.setter
    def metadata(self, value):
        self.metadata_json = json.dumps(value) if value else None
    
    @property
    def tagged_characters(self):
        return [tag.character for tag in self.tags]


class ImageTag(Base):
    """Model representing a character tag in an image."""
    __tablename__ = 'image_tags'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Tag information
    x = Column(Float, nullable=True)  # X coordinate (0.0 to 1.0)
    y = Column(Float, nullable=True)  # Y coordinate (0.0 to 1.0)
    width = Column(Float, nullable=True)  # Width of the tag box (0.0 to 1.0)
    height = Column(Float, nullable=True)  # Height of the tag box (0.0 to 1.0)
    
    # Foreign keys
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    
    # Relationships
    image = relationship("Image", back_populates="tags")
    character = relationship("Character", back_populates="image_tags")
    
    def __repr__(self):
        return f"<ImageTag(id={self.id}, image_id={self.image_id}, character_id={self.character_id})>"
    
    @property
    def box(self):
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }
    
    @box.setter
    def box(self, value):
        if value:
            self.x = value.get('x')
            self.y = value.get('y')
            self.width = value.get('width')
            self.height = value.get('height')
        else:
            self.x = None
            self.y = None
            self.width = None
            self.height = None


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


def create_default_relationship_types(session):
    """Create default relationship types if they don't exist."""
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
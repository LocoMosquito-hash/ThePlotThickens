#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Character models for The Plot Thickens application.

This module defines the Character model and related classes.
"""

from typing import List, Optional, Set, TYPE_CHECKING
from enum import Enum, auto

from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLAEnum, Text, Boolean, Table
from sqlalchemy.orm import relationship

from app.models.base import Base, BaseModel

# Import types for type checking only
if TYPE_CHECKING:
    from app.models.relationship import Relationship
    from app.models.image import Image


# Association table for character traits
character_traits = Table(
    'character_traits',
    Base.metadata,
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True),
    Column('trait_id', Integer, ForeignKey('traits.id'), primary_key=True)
)

# Association table for character groups
character_groups = Table(
    'character_groups',
    Base.metadata,
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('role', String(255), nullable=True)
)


class AgeCategory(Enum):
    """Enumeration of age categories."""
    
    MINOR = auto()
    TEEN = auto()
    YOUNG = auto()
    ADULT = auto()
    MIDDLE_AGED = auto()
    MATURE = auto()
    OLD = auto()
    
    def __str__(self) -> str:
        """Return a string representation of the age category."""
        return self.name.replace('_', ' ').title()


class Gender(Enum):
    """Enumeration of gender options."""
    
    MALE = auto()
    FEMALE = auto()
    NOT_SPECIFIED = auto()
    FUTA = auto()
    
    def __str__(self) -> str:
        """Return a string representation of the gender."""
        if self == Gender.NOT_SPECIFIED:
            return "Not Specified"
        return self.name.title()


class Character(BaseModel):
    """Model representing a character in a story."""
    
    __tablename__ = 'characters'
    
    # Basic information
    name = Column(String(255), nullable=False)
    aliases = Column(Text, nullable=True)  # Comma-separated list of aliases
    is_main_character = Column(Boolean, default=False)
    
    # Physical attributes
    age_value = Column(Integer, nullable=True)  # Actual age if known
    age_category = Column(SQLAEnum(AgeCategory), nullable=True)
    gender = Column(SQLAEnum(Gender), default=Gender.NOT_SPECIFIED)
    
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
    groups = relationship("CharacterGroup", secondary=character_groups, back_populates="characters")
    
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
    
    def __repr__(self) -> str:
        """Return a string representation of the character."""
        return f"<Character(id={self.id}, name='{self.name}', story_id={self.story_id})>"
    
    @property
    def alias_list(self) -> List[str]:
        """Get the list of aliases for this character."""
        if not self.aliases:
            return []
        return [alias.strip() for alias in self.aliases.split(',')]
    
    @alias_list.setter
    def alias_list(self, aliases: List[str]) -> None:
        """Set the aliases for this character from a list."""
        self.aliases = ','.join(aliases) if aliases else None
    
    @property
    def age_display(self) -> str:
        """Get a display string for the character's age."""
        if self.age_value is not None:
            return str(self.age_value)
        if self.age_category is not None:
            return str(self.age_category)
        return "Unknown"
    
    @property
    def all_relationships(self) -> List["Relationship"]:
        """Get all relationships this character is involved in."""
        return self.outgoing_relationships + self.incoming_relationships
    
    @property
    def tagged_images(self) -> List["Image"]:
        """Get all images this character is tagged in."""
        return [tag.image for tag in self.image_tags]


class CharacterTrait(BaseModel):
    """Model representing a character trait."""
    
    __tablename__ = 'traits'
    
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    characters = relationship("Character", secondary=character_traits, back_populates="traits")
    
    def __repr__(self) -> str:
        """Return a string representation of the trait."""
        return f"<CharacterTrait(id={self.id}, name='{self.name}')>"


class CharacterDetail(BaseModel):
    """Model representing a custom detail for a character."""
    
    __tablename__ = 'character_details'
    
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=True)
    
    # Foreign keys
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    
    # Relationships
    character = relationship("Character", back_populates="details")
    
    def __repr__(self) -> str:
        """Return a string representation of the character detail."""
        return f"<CharacterDetail(id={self.id}, key='{self.key}', character_id={self.character_id})>"


class CharacterGroup(BaseModel):
    """Model representing a group or organization that characters can belong to."""
    
    __tablename__ = 'groups'
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Foreign keys
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=False)
    
    # Relationships
    story = relationship("Story")
    characters = relationship("Character", secondary=character_groups, back_populates="groups")
    
    def __repr__(self) -> str:
        """Return a string representation of the character group."""
        return f"<CharacterGroup(id={self.id}, name='{self.name}', story_id={self.story_id})>" 
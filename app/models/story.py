#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Story models for The Plot Thickens application.

This module defines the Story model and related classes.
"""

from typing import List, Optional
from enum import Enum, auto
import os
import json

from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLAEnum, Text, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base, BaseModel


class StoryType(Enum):
    """Enumeration of story types."""
    
    VISUAL_NOVEL = auto()
    TV_SERIES = auto()
    MOVIE = auto()
    GAME = auto()
    OTHER = auto()
    
    def __str__(self) -> str:
        """Return a string representation of the story type."""
        return self.name.replace('_', ' ').title()


class Story(BaseModel):
    """Model representing a story in the application."""
    
    __tablename__ = 'stories'
    
    # Basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(SQLAEnum(StoryType), nullable=False, default=StoryType.OTHER)
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
    
    # Story board views
    board_views = relationship("StoryBoardView", back_populates="story", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """Return a string representation of the story."""
        return f"<Story(id={self.id}, title='{self.title}', type={self.type})>"
    
    @property
    def images_folder(self) -> str:
        """Get the path to the images folder for this story."""
        return os.path.join(self.folder_path, "images")
    
    @property
    def backups_folder(self) -> str:
        """Get the path to the backups folder for this story."""
        return os.path.join(self.folder_path, "backups")
    
    def ensure_folders_exist(self) -> None:
        """Ensure that all required folders for this story exist."""
        os.makedirs(self.folder_path, exist_ok=True)
        os.makedirs(self.images_folder, exist_ok=True)
        os.makedirs(self.backups_folder, exist_ok=True)


class StoryBoardView(BaseModel):
    """Model representing a saved view of the story board."""
    
    __tablename__ = 'story_board_views'
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    layout_data = Column(Text, nullable=False)  # JSON string with layout information
    
    # Foreign keys
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=False)
    
    # Relationships
    story = relationship("Story", back_populates="board_views")
    
    def __repr__(self) -> str:
        """Return a string representation of the story board view."""
        return f"<StoryBoardView(id={self.id}, name='{self.name}', story_id={self.story_id})>"
    
    @property
    def layout(self) -> dict:
        """Get the layout data as a dictionary."""
        return json.loads(self.layout_data)
    
    @layout.setter
    def layout(self, value: dict) -> None:
        """Set the layout data from a dictionary."""
        self.layout_data = json.dumps(value) 
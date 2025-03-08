#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image models for The Plot Thickens application.

This module defines the Image model and related classes.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
import os
import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, Float, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base, BaseModel

# Import types for type checking only
if TYPE_CHECKING:
    from app.models.character import Character


class Image(BaseModel):
    """Model representing an image in the application."""
    
    __tablename__ = 'images'
    
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
    
    def __repr__(self) -> str:
        """Return a string representation of the image."""
        return f"<Image(id={self.id}, filename='{self.filename}', story_id={self.story_id})>"
    
    @property
    def full_path(self) -> str:
        """Get the full path to the image file."""
        return os.path.join(self.path, self.filename)
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the custom metadata as a dictionary."""
        if not self.metadata_json:
            return {}
        return json.loads(self.metadata_json)
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]) -> None:
        """Set the custom metadata from a dictionary."""
        self.metadata_json = json.dumps(value) if value else None
    
    @property
    def tagged_characters(self) -> List["Character"]:
        """Get all characters tagged in this image."""
        return [tag.character for tag in self.tags]


class ImageTag(BaseModel):
    """Model representing a character tag in an image."""
    
    __tablename__ = 'image_tags'
    
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
    
    def __repr__(self) -> str:
        """Return a string representation of the image tag."""
        return f"<ImageTag(id={self.id}, image_id={self.image_id}, character_id={self.character_id})>"
    
    @property
    def box(self) -> Dict[str, float]:
        """Get the tag box as a dictionary."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }
    
    @box.setter
    def box(self, value: Dict[str, float]) -> None:
        """Set the tag box from a dictionary."""
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
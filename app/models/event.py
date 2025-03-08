#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Event models for The Plot Thickens application.

This module defines the Event model and related classes.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime, Table
from sqlalchemy.orm import relationship

from app.models.base import Base, BaseModel

# Import types for type checking only
if TYPE_CHECKING:
    from app.models.character import Character


class Event(BaseModel):
    """Model representing an event in a story."""
    
    __tablename__ = 'events'
    
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
    
    def __repr__(self) -> str:
        """Return a string representation of the event."""
        return f"<Event(id={self.id}, title='{self.title}', story_id={self.story_id})>"
    
    @property
    def properties(self) -> Dict[str, Any]:
        """Get the custom properties as a dictionary."""
        if not self.properties_json:
            return {}
        return json.loads(self.properties_json)
    
    @properties.setter
    def properties(self, value: Dict[str, Any]) -> None:
        """Set the custom properties from a dictionary."""
        self.properties_json = json.dumps(value) if value else None
    
    @property
    def involved_characters(self) -> List["Character"]:
        """Get all characters involved in this event."""
        return [ec.character for ec in self.characters]
    
    @property
    def date_display(self) -> str:
        """Get a display string for the event date."""
        if not self.date:
            return "Unknown date"
        
        prefix = "Approximately " if self.is_approximate_date else ""
        return f"{prefix}{self.date.strftime('%Y-%m-%d')}"


class EventCharacter(BaseModel):
    """Model representing a character's involvement in an event."""
    
    __tablename__ = 'event_characters'
    
    # Involvement information
    role = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Foreign keys
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="characters")
    character = relationship("Character", back_populates="events")
    
    def __repr__(self) -> str:
        """Return a string representation of the event character."""
        return f"<EventCharacter(id={self.id}, event_id={self.event_id}, character_id={self.character_id})>" 
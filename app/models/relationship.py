#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relationship models for The Plot Thickens application.

This module defines the Relationship model and related classes.
"""

from typing import List, Optional, Dict, Any
from enum import Enum, auto
import json

from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLAEnum, Text, Boolean, Float
from sqlalchemy.orm import relationship

from app.models.base import Base, BaseModel


class RelationshipType(BaseModel):
    """Model representing a type of relationship between characters."""
    
    __tablename__ = 'relationship_types'
    
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
    
    def __repr__(self) -> str:
        """Return a string representation of the relationship type."""
        return f"<RelationshipType(id={self.id}, name='{self.name}')>"
    
    def get_variant_for_gender(self, gender: str) -> str:
        """Get the gender-specific variant of this relationship type."""
        if gender == "MALE" and self.male_variant:
            return self.male_variant
        if gender == "FEMALE" and self.female_variant:
            return self.female_variant
        return self.name


class Relationship(BaseModel):
    """Model representing a relationship between two characters."""
    
    __tablename__ = 'relationships'
    
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
    
    def __repr__(self) -> str:
        """Return a string representation of the relationship."""
        return f"<Relationship(id={self.id}, source_id={self.source_id}, target_id={self.target_id}, type='{self.relationship_type.name}')>"
    
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
    
    def create_inverse(self, session: Any) -> "Relationship":
        """Create an inverse relationship if the relationship type has an inverse."""
        if not self.relationship_type.has_inverse or not self.relationship_type.inverse_id:
            return None
            
        inverse = Relationship(
            source_id=self.target_id,
            target_id=self.source_id,
            relationship_type_id=self.relationship_type.inverse_id,
            description=self.description,
            strength=self.strength,
            color=self.color,
            width=self.width,
            start_event_id=self.start_event_id,
            end_event_id=self.end_event_id,
            properties_json=self.properties_json
        )
        
        session.add(inverse)
        session.flush()
        return inverse 
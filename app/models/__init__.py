#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database models for The Plot Thickens application.

This package contains all the SQLAlchemy models used in the application.
"""

from app.models.base import Base, BaseModel, Database
from app.models.story import Story, StoryType
from app.models.character import Character, CharacterTrait, CharacterDetail, CharacterGroup
from app.models.relationship import Relationship, RelationshipType
from app.models.image import Image, ImageTag
from app.models.event import Event, EventCharacter

__all__ = [
    'Base',
    'BaseModel',
    'Database',
    'Story',
    'StoryType',
    'Character',
    'CharacterTrait',
    'CharacterDetail',
    'CharacterGroup',
    'Relationship',
    'RelationshipType',
    'Image',
    'ImageTag',
    'Event',
    'EventCharacter'
] 
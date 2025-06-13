#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rankable item data models.

This module contains data classes for items that can be ranked in tiers.
Currently supports characters, designed to be extensible for other types.
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict
from enum import Enum


class ItemType(Enum):
    """Enum for different types of rankable items."""
    CHARACTER = "character"
    # Future types can be added here:
    # IMAGE = "image"
    # VIDEO = "video"
    # STORY = "story"


@dataclass
class RankableItem:
    """Represents an item that can be ranked in tiers.
    
    This is designed to be extensible for different item types.
    Currently focused on characters but can be extended later.
    """
    
    id: int
    name: str
    item_type: ItemType
    avatar_path: Optional[str] = None
    tooltip_text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None  # Additional data specific to item type
    
    def __post_init__(self):
        """Initialize data dict if not provided."""
        if self.data is None:
            self.data = {}
    
    @classmethod
    def from_character(cls, character_id: int, name: str, avatar_path: Optional[str] = None, 
                      gender: Optional[str] = None, love_interest: int = 0) -> 'RankableItem':
        """Create a RankableItem from character data.
        
        Args:
            character_id: The character's database ID
            name: The character's name
            avatar_path: Path to character's avatar image
            gender: Character's gender
            love_interest: Love interest rating
            
        Returns:
            A RankableItem representing the character
        """
        tooltip = name
        if gender:
            tooltip += f" ({gender})"
        
        return cls(
            id=character_id,
            name=name,
            item_type=ItemType.CHARACTER,
            avatar_path=avatar_path,
            tooltip_text=tooltip,
            data={
                'gender': gender,
                'love_interest': love_interest
            }
        )
    
    def get_display_name(self) -> str:
        """Get the display name for this item."""
        return self.name
    
    def get_tooltip(self) -> str:
        """Get the tooltip text for this item."""
        return self.tooltip_text or self.name 
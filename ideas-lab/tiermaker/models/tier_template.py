#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tier template data models.

This module contains data classes for tier templates and individual tiers.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class TierTemplateTier:
    """Represents a single tier within a template."""
    
    id: Optional[int] = None
    template_id: Optional[int] = None
    tier_name: str = ""
    tier_color: str = "#ff0000"  # Default red
    tier_order: int = 0
    created_at: Optional[datetime] = None


@dataclass
class TierTemplate:
    """Represents a tier template with multiple tiers."""
    
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tiers: List[TierTemplateTier] = None
    
    def __post_init__(self):
        """Initialize tiers list if not provided."""
        if self.tiers is None:
            self.tiers = []
    
    @classmethod
    def create_default_template(cls, name: str) -> 'TierTemplate':
        """Create a default template with S, A, B, C, D tiers.
        
        Args:
            name: The name for the template
            
        Returns:
            A TierTemplate with default tiers
        """
        template = cls(name=name)
        
        # Default tier colors (red to green gradient)
        default_tiers = [
            ("S", "#ff4444"),  # Red
            ("A", "#ff8844"),  # Orange
            ("B", "#ffdd44"),  # Yellow
            ("C", "#88ff44"),  # Light green
            ("D", "#44ff44"),  # Green
        ]
        
        for i, (tier_name, color) in enumerate(default_tiers):
            tier = TierTemplateTier(
                tier_name=tier_name,
                tier_color=color,
                tier_order=i
            )
            template.tiers.append(tier)
        
        return template 
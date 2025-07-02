#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database persistence for Ren'Py Source API.

This module provides database models and operations for caching all analysis results
from the Ren'Py Source API. All tables are completely separate from The Plot Thickens
main application tables to avoid any linking issues when VN source code changes.

Tables use 'renpy_api_' prefix to ensure complete separation from TPT data.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, 
    ForeignKey, Index, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

try:
    from .core import RenpyProject
    from .parser import MenuChoice, MenuStructure, LabelFlow, LabelNode
except ImportError:
    # Fall back to direct imports (when run standalone)
    from core import RenpyProject
    from parser import MenuChoice, MenuStructure, LabelFlow, LabelNode

# Create the base model class for API tables
APIBase = declarative_base()


class RenpyAPIProject(APIBase):
    """Model representing a Ren'Py project analyzed by the API."""
    __tablename__ = 'renpy_api_projects'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scan_at = Column(DateTime, default=datetime.utcnow)
    
    # Project information
    project_path = Column(String(1024), nullable=False, unique=True)
    project_name = Column(String(255), nullable=False)
    
    # Analysis metadata
    total_files_scanned = Column(Integer, default=0)
    total_lines_analyzed = Column(BigInteger, default=0)
    analysis_version = Column(String(50), default="1.0")  # Track API version for compatibility
    
    # Analysis flags
    characters_analyzed = Column(Boolean, default=False)
    assets_analyzed = Column(Boolean, default=False)
    menus_analyzed = Column(Boolean, default=False)
    flows_analyzed = Column(Boolean, default=False)
    
    # Quick stats (for fast queries without joining)
    character_count = Column(Integer, default=0)
    asset_count = Column(Integer, default=0)
    menu_count = Column(Integer, default=0)
    label_count = Column(Integer, default=0)
    
    # Relationships
    characters = relationship("RenpyAPICharacter", back_populates="project", cascade="all, delete-orphan")
    assets = relationship("RenpyAPIAsset", back_populates="project", cascade="all, delete-orphan")
    menus = relationship("RenpyAPIMenu", back_populates="project", cascade="all, delete-orphan")
    labels = relationship("RenpyAPILabel", back_populates="project", cascade="all, delete-orphan")
    flows = relationship("RenpyAPIFlow", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<RenpyAPIProject(id={self.id}, name='{self.project_name}', path='{self.project_path}')>"


class RenpyAPICharacter(APIBase):
    """Model representing a character discovered by the API."""
    __tablename__ = 'renpy_api_characters'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Character identification
    character_name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    aliases = Column(Text, nullable=True)  # JSON array of aliases
    
    # Character stats
    total_lines = Column(Integer, default=0)
    total_appearances = Column(Integer, default=0)
    first_appearance_file = Column(String(512), nullable=True)
    first_appearance_line = Column(Integer, nullable=True)
    
    # Story significance metrics
    story_significance = Column(Float, default=0.0)  # 0.0 to 1.0
    interaction_frequency = Column(Float, default=0.0)
    relationship_centrality = Column(Float, default=0.0)
    
    # Character analysis
    emotions_json = Column(Text, nullable=True)  # JSON: {"emotion": count, ...}
    relationships_json = Column(Text, nullable=True)  # JSON: {"character": "relationship_type", ...}
    character_arcs_json = Column(Text, nullable=True)  # JSON: [{"arc": "description", "scenes": [...]}]
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey('renpy_api_projects.id'), nullable=False)
    
    # Relationships
    project = relationship("RenpyAPIProject", back_populates="characters")
    
    def __repr__(self) -> str:
        return f"<RenpyAPICharacter(id={self.id}, name='{self.character_name}', project_id={self.project_id})>"
    
    @property
    def aliases_list(self) -> List[str]:
        """Get aliases as a list."""
        if not self.aliases:
            return []
        return json.loads(self.aliases)
    
    @aliases_list.setter
    def aliases_list(self, value: List[str]) -> None:
        """Set aliases from a list."""
        self.aliases = json.dumps(value) if value else None
    
    @property
    def emotions(self) -> Dict[str, int]:
        """Get emotions as a dictionary."""
        if not self.emotions_json:
            return {}
        return json.loads(self.emotions_json)
    
    @emotions.setter
    def emotions(self, value: Dict[str, int]) -> None:
        """Set emotions from a dictionary."""
        self.emotions_json = json.dumps(value) if value else None
    
    @property
    def relationships(self) -> Dict[str, str]:
        """Get relationships as a dictionary."""
        if not self.relationships_json:
            return {}
        return json.loads(self.relationships_json)
    
    @relationships.setter
    def relationships(self, value: Dict[str, str]) -> None:
        """Set relationships from a dictionary."""
        self.relationships_json = json.dumps(value) if value else None
    
    @property
    def character_arcs(self) -> List[Dict[str, Any]]:
        """Get character arcs as a list."""
        if not self.character_arcs_json:
            return []
        return json.loads(self.character_arcs_json)
    
    @character_arcs.setter
    def character_arcs(self, value: List[Dict[str, Any]]) -> None:
        """Set character arcs from a list."""
        self.character_arcs_json = json.dumps(value) if value else None


class RenpyAPIAsset(APIBase):
    """Model representing an asset discovered by the API."""
    __tablename__ = 'renpy_api_assets'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Asset identification
    asset_path = Column(String(1024), nullable=False)
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False)  # image, audio, video, etc.
    asset_category = Column(String(100), nullable=True)  # bg, character, music, etc.
    
    # File information
    file_size = Column(BigInteger, nullable=True)
    file_extension = Column(String(20), nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Usage analysis
    usage_count = Column(Integer, default=0)
    usage_frequency = Column(Float, default=0.0)
    first_usage_file = Column(String(512), nullable=True)
    first_usage_line = Column(Integer, nullable=True)
    
    # Asset relationships
    related_assets_json = Column(Text, nullable=True)  # JSON: ["asset_path", ...]
    used_in_scenes_json = Column(Text, nullable=True)  # JSON: ["label_name", ...]
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey('renpy_api_projects.id'), nullable=False)
    
    # Relationships
    project = relationship("RenpyAPIProject", back_populates="assets")
    
    def __repr__(self) -> str:
        return f"<RenpyAPIAsset(id={self.id}, name='{self.asset_name}', type='{self.asset_type}')>"
    
    @property
    def related_assets(self) -> List[str]:
        """Get related assets as a list."""
        if not self.related_assets_json:
            return []
        return json.loads(self.related_assets_json)
    
    @related_assets.setter
    def related_assets(self, value: List[str]) -> None:
        """Set related assets from a list."""
        self.related_assets_json = json.dumps(value) if value else None
    
    @property
    def used_in_scenes(self) -> List[str]:
        """Get scenes where asset is used as a list."""
        if not self.used_in_scenes_json:
            return []
        return json.loads(self.used_in_scenes_json)
    
    @used_in_scenes.setter
    def used_in_scenes(self, value: List[str]) -> None:
        """Set scenes from a list."""
        self.used_in_scenes_json = json.dumps(value) if value else None


class RenpyAPIMenu(APIBase):
    """Model representing a menu/choice discovered by the API."""
    __tablename__ = 'renpy_api_menus'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Menu identification
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, nullable=False)
    label_context = Column(String(255), nullable=True)
    
    # Menu content
    menu_text = Column(Text, nullable=True)
    total_choices = Column(Integer, default=0)
    
    # Analysis metrics
    complexity_score = Column(Float, default=0.0)
    branching_factor = Column(Integer, default=0)
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey('renpy_api_projects.id'), nullable=False)
    
    # Relationships
    project = relationship("RenpyAPIProject", back_populates="menus")
    choices = relationship("RenpyAPIChoice", back_populates="menu", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<RenpyAPIMenu(id={self.id}, choices={self.total_choices}, file='{self.file_path}')>"


class RenpyAPIChoice(APIBase):
    """Model representing a choice option within a menu."""
    __tablename__ = 'renpy_api_choices'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Choice content
    choice_text = Column(Text, nullable=False)
    choice_condition = Column(Text, nullable=True)
    destination_type = Column(String(50), nullable=True)  # jump, call, expression, etc.
    destination_target = Column(String(255), nullable=True)
    
    # Choice analysis
    popularity_score = Column(Float, default=0.0)
    choice_order = Column(Integer, default=0)
    
    # Foreign keys
    menu_id = Column(Integer, ForeignKey('renpy_api_menus.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('renpy_api_projects.id'), nullable=False)
    
    # Relationships
    menu = relationship("RenpyAPIMenu", back_populates="choices")
    project = relationship("RenpyAPIProject")
    
    def __repr__(self) -> str:
        return f"<RenpyAPIChoice(id={self.id}, text='{self.choice_text[:50]}...', menu_id={self.menu_id})>"


class RenpyAPILabel(APIBase):
    """Model representing a label/scene discovered by the API."""
    __tablename__ = 'renpy_api_labels'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Label identification
    label_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # Label analysis
    total_flows_in = Column(Integer, default=0)
    total_flows_out = Column(Integer, default=0)
    is_reachable = Column(Boolean, default=False)
    depth_from_start = Column(Integer, nullable=True)
    
    # Scene categorization
    scene_type = Column(String(100), nullable=True)  # hub, bridge, endpoint, etc.
    narrative_importance = Column(Float, default=0.0)
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey('renpy_api_projects.id'), nullable=False)
    
    # Relationships
    project = relationship("RenpyAPIProject", back_populates="labels")
    outgoing_flows = relationship(
        "RenpyAPIFlow", 
        foreign_keys="RenpyAPIFlow.source_label_id",
        back_populates="source_label",
        cascade="all, delete-orphan"
    )
    incoming_flows = relationship(
        "RenpyAPIFlow",
        foreign_keys="RenpyAPIFlow.target_label_id", 
        back_populates="target_label"
    )
    
    def __repr__(self) -> str:
        return f"<RenpyAPILabel(id={self.id}, name='{self.label_name}', flows_in={self.total_flows_in}, flows_out={self.total_flows_out})>"


class RenpyAPIFlow(APIBase):
    """Model representing a flow/connection between labels."""
    __tablename__ = 'renpy_api_flows'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Flow information
    flow_type = Column(String(50), nullable=False)  # jump, call, return, menu_choice, etc.
    condition = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # Flow analysis
    frequency_score = Column(Float, default=0.0)
    is_critical_path = Column(Boolean, default=False)
    creates_cycle = Column(Boolean, default=False)
    
    # Foreign keys
    source_label_id = Column(Integer, ForeignKey('renpy_api_labels.id'), nullable=False)
    target_label_id = Column(Integer, ForeignKey('renpy_api_labels.id'), nullable=True)  # Nullable for external/unknown targets
    project_id = Column(Integer, ForeignKey('renpy_api_projects.id'), nullable=False)
    
    # Relationships
    source_label = relationship("RenpyAPILabel", foreign_keys=[source_label_id], back_populates="outgoing_flows")
    target_label = relationship("RenpyAPILabel", foreign_keys=[target_label_id], back_populates="incoming_flows")
    project = relationship("RenpyAPIProject", back_populates="flows")
    
    def __repr__(self) -> str:
        return f"<RenpyAPIFlow(id={self.id}, type='{self.flow_type}', source={self.source_label_id}, target={self.target_label_id})>"


# Database indexes for performance
Index('idx_renpy_projects_path', RenpyAPIProject.project_path)
Index('idx_renpy_characters_name', RenpyAPICharacter.character_name)
Index('idx_renpy_characters_project', RenpyAPICharacter.project_id)
Index('idx_renpy_assets_project_type', RenpyAPIAsset.project_id, RenpyAPIAsset.asset_type)
Index('idx_renpy_assets_name', RenpyAPIAsset.asset_name)
Index('idx_renpy_menus_project', RenpyAPIMenu.project_id)
Index('idx_renpy_choices_menu', RenpyAPIChoice.menu_id)
Index('idx_renpy_labels_project_name', RenpyAPILabel.project_id, RenpyAPILabel.label_name)
Index('idx_renpy_flows_source', RenpyAPIFlow.source_label_id)
Index('idx_renpy_flows_target', RenpyAPIFlow.target_label_id)
Index('idx_renpy_flows_project', RenpyAPIFlow.project_id)


class RenpyAPIDatabase:
    """Database manager for Ren'Py Source API persistence."""
    
    def __init__(self, db_path: str = 'sqlite:///renpy_source_api.db'):
        """Initialize the database connection.
        
        Args:
            db_path: Database connection string. Defaults to separate API database.
        """
        self.db_path = db_path
        self.engine = create_engine(db_path)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
    def create_tables(self) -> None:
        """Create all API tables."""
        APIBase.metadata.create_all(self.engine)
        
    def get_session(self):
        """Get a database session."""
        return self.Session()
        
    def close_session(self, session) -> None:
        """Close a database session."""
        session.close()
        
    def commit_session(self, session) -> None:
        """Commit a database session."""
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
            
    def rollback_session(self, session) -> None:
        """Rollback a database session."""
        session.rollback()


class RenpyAPIDataPersistence:
    """High-level interface for persisting Ren'Py analysis data."""
    
    def __init__(self, db_path: str = 'sqlite:///renpy_source_api.db'):
        """Initialize the persistence manager.
        
        Args:
            db_path: Database connection string.
        """
        self.db = RenpyAPIDatabase(db_path)
        self.db.create_tables()
        
    def save_project_analysis(self, renpy_project: RenpyProject) -> int:
        """Save complete project analysis to database.
        
        Args:
            renpy_project: The analyzed RenpyProject instance.
            
        Returns:
            The database ID of the saved project.
        """
        session = self.db.get_session()
        try:
            # Create or update project record
            project = session.query(RenpyAPIProject).filter_by(
                project_path=renpy_project.project_path
            ).first()
            
            if not project:
                project = RenpyAPIProject(
                    project_path=renpy_project.project_path,
                    project_name=os.path.basename(renpy_project.project_path) or "Unknown Project"
                )
                session.add(project)
                session.flush()  # Get the ID
            else:
                # Clear existing data for re-analysis
                self._clear_project_data(session, project.id)
                project.updated_at = datetime.utcnow()
                project.last_scan_at = datetime.utcnow()
            
            # Update project metadata
            overview = renpy_project.get_project_overview()
            project.total_files_scanned = overview['statistics']['total_rpy_files']
            project.total_lines_analyzed = overview['statistics']['total_lines']
            
            # Save characters
            try:
                character_stats = renpy_project.get_character_stats()
                if character_stats:
                    self._save_characters(session, project.id, character_stats)
                    project.characters_analyzed = True
                    project.character_count = len(character_stats)
            except Exception as e:
                print(f"Warning: Could not save characters: {e}")
                
            # Save assets
            try:
                assets = renpy_project.get_all_assets()
                if assets:
                    self._save_assets(session, project.id, assets)
                    project.assets_analyzed = True
                    # Count total assets across categories
                    project.asset_count = sum(len(asset_list) for asset_list in assets.values())
            except Exception as e:
                print(f"Warning: Could not save assets: {e}")
                
            # Save menus
            try:
                menus = renpy_project.get_all_menus()
                if menus:
                    self._save_menus(session, project.id, menus)
                    project.menus_analyzed = True
                    project.menu_count = len(menus)
            except Exception as e:
                print(f"Warning: Could not save menus: {e}")
                
            # Save label flows
            try:
                flow_analysis = renpy_project.get_label_flow_analysis()
                if flow_analysis:
                    self._save_label_flows(session, project.id, flow_analysis)
                    project.flows_analyzed = True
                    project.label_count = len(flow_analysis.get('labels', {}))
            except Exception as e:
                print(f"Warning: Could not save label flows: {e}")
            
            self.db.commit_session(session)
            return project.id
            
        except Exception as e:
            self.db.rollback_session(session)
            raise e
        finally:
            self.db.close_session(session)
    
    def _clear_project_data(self, session, project_id: int) -> None:
        """Clear existing analysis data for a project."""
        # Delete in correct order due to foreign key constraints
        session.query(RenpyAPIFlow).filter_by(project_id=project_id).delete()
        session.query(RenpyAPIChoice).filter_by(project_id=project_id).delete()
        session.query(RenpyAPIMenu).filter_by(project_id=project_id).delete()
        session.query(RenpyAPILabel).filter_by(project_id=project_id).delete()
        session.query(RenpyAPIAsset).filter_by(project_id=project_id).delete()
        session.query(RenpyAPICharacter).filter_by(project_id=project_id).delete()
        
    def _save_characters(self, session, project_id: int, character_stats: Dict[str, Dict[str, Any]]) -> None:
        """Save character analysis data."""
        for char_code, char_data in character_stats.items():
            character = RenpyAPICharacter(
                project_id=project_id,
                character_name=char_code,
                display_name=char_data.get('name', char_code),
                total_lines=char_data.get('dialogue_lines', 0),
                total_appearances=len(char_data.get('files_appeared_in', [])),
                first_appearance_file=char_data.get('first_appearance', {}).get('file'),
                first_appearance_line=char_data.get('first_appearance', {}).get('line'),
                story_significance=min(char_data.get('dialogue_lines', 0) / 1000.0, 1.0),  # Simple significance calculation
                interaction_frequency=char_data.get('average_words_per_line', 0.0) / 50.0,  # Normalize
                relationship_centrality=0.0  # Can be enhanced later
            )
            session.add(character)
    
    def _save_assets(self, session, project_id: int, assets: Dict[str, List[Dict[str, Any]]]) -> None:
        """Save asset analysis data."""
        for asset_type, asset_list in assets.items():
            for asset in asset_list:
                asset_record = RenpyAPIAsset(
                    project_id=project_id,
                    asset_path=asset.get('path', ''),
                    asset_name=asset.get('name', ''),
                    asset_type=asset_type,
                    asset_category=asset.get('category', asset_type),
                    file_size=asset.get('size'),
                    usage_count=asset.get('usage_count', 0),
                    usage_frequency=asset.get('usage_frequency', 0.0),
                    first_usage_file=asset.get('first_usage', {}).get('file'),
                    first_usage_line=asset.get('first_usage', {}).get('line')
                )
                session.add(asset_record)
    
    def _save_menus(self, session, project_id: int, menus: List[MenuStructure]) -> None:
        """Save menu/choice analysis data."""
        for menu in menus:
            menu_record = RenpyAPIMenu(
                project_id=project_id,
                file_path=menu.file_path,
                line_number=menu.line_number,
                label_context=menu.label_context,
                menu_text=menu.name,
                total_choices=menu.total_choices,
                complexity_score=float(menu.total_choices),  # Simple complexity
                branching_factor=menu.total_choices
            )
            session.add(menu_record)
            session.flush()  # Get the menu ID
            
            # Save choices
            for i, choice in enumerate(menu.choices):
                choice_record = RenpyAPIChoice(
                    menu_id=menu_record.id,
                    project_id=project_id,
                    choice_text=choice.text,
                    choice_condition=choice.condition,
                    destination_type=choice.action_type,
                    destination_target=choice.destination,
                    choice_order=i,
                    popularity_score=0.0  # Can be calculated later from usage patterns
                )
                session.add(choice_record)
    
    def _save_label_flows(self, session, project_id: int, flow_analysis: Dict[str, Any]) -> None:
        """Save label flow analysis data."""
        labels = flow_analysis.get('labels', {})
        
        # First, save all labels
        label_id_map = {}
        for label_name, label_data in labels.items():
            label_record = RenpyAPILabel(
                project_id=project_id,
                label_name=label_name,
                file_path=label_data.get('file', ''),
                line_number=label_data.get('line', 0),
                total_flows_in=len(label_data.get('incoming_connections', [])),
                total_flows_out=len(label_data.get('outgoing_connections', [])),
                is_reachable=label_data.get('reachable', True),
                depth_from_start=label_data.get('depth'),
                scene_type=self._categorize_scene(label_data),
                narrative_importance=self._calculate_narrative_importance(label_data)
            )
            session.add(label_record)
            session.flush()  # Get the label ID
            label_id_map[label_name] = label_record.id
        
        # Then, save flow connections (simplified)
        for label_name, label_data in labels.items():
            source_id = label_id_map[label_name]
            
            for connection in label_data.get('outgoing_connections', []):
                target_label = connection.get('target')
                target_id = label_id_map.get(target_label)
                
                flow_record = RenpyAPIFlow(
                    project_id=project_id,
                    source_label_id=source_id,
                    target_label_id=target_id,  # May be None for external targets
                    flow_type=connection.get('type', 'unknown'),
                    condition=connection.get('condition'),
                    file_path=connection.get('file', ''),
                    line_number=connection.get('line', 0),
                    frequency_score=0.0,  # Can be calculated from usage patterns
                    is_critical_path=False,  # Can be enhanced
                    creates_cycle=False  # Can be enhanced
                )
                session.add(flow_record)
    
    def _categorize_scene(self, label_data: Dict[str, Any]) -> str:
        """Categorize a scene based on its connectivity."""
        incoming_count = len(label_data.get('incoming_connections', []))
        outgoing_count = len(label_data.get('outgoing_connections', []))
        
        if incoming_count == 0 and outgoing_count > 0:
            return "start"
        elif incoming_count > 0 and outgoing_count == 0:
            return "endpoint"
        elif incoming_count >= 3 and outgoing_count >= 3:
            return "hub"
        elif incoming_count == 1 and outgoing_count == 1:
            return "linear"
        else:
            return "branching"
    
    def _calculate_narrative_importance(self, label_data: Dict[str, Any]) -> float:
        """Calculate narrative importance based on connectivity."""
        total_connections = len(label_data.get('incoming_connections', [])) + len(label_data.get('outgoing_connections', []))
        # Normalize to 0.0-1.0 scale (assuming max 20 connections is very high)
        return min(total_connections / 20.0, 1.0)
    
    def get_project_by_path(self, project_path: str) -> Optional[RenpyAPIProject]:
        """Get a project by its path.
        
        Args:
            project_path: The project path to search for.
            
        Returns:
            The project record if found, None otherwise.
        """
        session = self.db.get_session()
        try:
            return session.query(RenpyAPIProject).filter_by(project_path=project_path).first()
        finally:
            self.db.close_session(session)
    
    def search_characters(self, project_id: int, name_pattern: str = None, 
                         min_significance: float = None) -> List[RenpyAPICharacter]:
        """Search for characters with optional filters.
        
        Args:
            project_id: The project ID to search in.
            name_pattern: Optional name pattern to match.
            min_significance: Optional minimum story significance.
            
        Returns:
            List of matching character records.
        """
        session = self.db.get_session()
        try:
            query = session.query(RenpyAPICharacter).filter_by(project_id=project_id)
            
            if name_pattern:
                query = query.filter(RenpyAPICharacter.character_name.contains(name_pattern))
            
            if min_significance is not None:
                query = query.filter(RenpyAPICharacter.story_significance >= min_significance)
            
            return query.order_by(RenpyAPICharacter.story_significance.desc()).all()
        finally:
            self.db.close_session(session)
    
    def search_menus_by_text(self, project_id: int, text_pattern: str) -> List[RenpyAPIChoice]:
        """Search for menu choices by text pattern.
        
        Args:
            project_id: The project ID to search in.
            text_pattern: Text pattern to search for in choice text.
            
        Returns:
            List of matching choice records.
        """
        session = self.db.get_session()
        try:
            return session.query(RenpyAPIChoice).filter(
                RenpyAPIChoice.project_id == project_id,
                RenpyAPIChoice.choice_text.contains(text_pattern)
            ).all()
        finally:
            self.db.close_session(session)
    
    def get_project_statistics(self, project_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a project.
        
        Args:
            project_id: The project ID.
            
        Returns:
            Dictionary with project statistics.
        """
        session = self.db.get_session()
        try:
            project = session.query(RenpyAPIProject).get(project_id)
            if not project:
                return {}
            
            # Calculate additional statistics
            character_stats = session.query(RenpyAPICharacter).filter_by(project_id=project_id).count()
            asset_stats = session.query(RenpyAPIAsset).filter_by(project_id=project_id).count()
            menu_stats = session.query(RenpyAPIMenu).filter_by(project_id=project_id).count()
            choice_stats = session.query(RenpyAPIChoice).filter_by(project_id=project_id).count()
            label_stats = session.query(RenpyAPILabel).filter_by(project_id=project_id).count()
            flow_stats = session.query(RenpyAPIFlow).filter_by(project_id=project_id).count()
            
            return {
                'project_name': project.project_name,
                'last_scan': project.last_scan_at,
                'total_files': project.total_files_scanned,
                'total_lines': project.total_lines_analyzed,
                'characters': character_stats,
                'assets': asset_stats,
                'menus': menu_stats,
                'choices': choice_stats,
                'labels': label_stats,
                'flows': flow_stats,
                'analysis_coverage': {
                    'characters': project.characters_analyzed,
                    'assets': project.assets_analyzed,
                    'menus': project.menus_analyzed,
                    'flows': project.flows_analyzed
                }
            }
        finally:
            self.db.close_session(session)


# Initialize database when module is imported
_default_db = None

def get_default_database() -> RenpyAPIDataPersistence:
    """Get the default database instance."""
    global _default_db
    if _default_db is None:
        _default_db = RenpyAPIDataPersistence()
    return _default_db 
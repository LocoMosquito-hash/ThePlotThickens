#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base database models for The Plot Thickens application.

This module provides the base SQLAlchemy setup and common model functionality.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from datetime import datetime
import uuid

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.sql import func

# Create the base model class
Base = declarative_base()

# Type variable for model classes
T = TypeVar('T', bound='BaseModel')

class BaseModel(Base):
    """Base model class with common functionality for all models."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def create(cls: Type[T], session: Any, **kwargs: Any) -> T:
        """Create a new instance of the model and add it to the session."""
        instance = cls(**kwargs)
        session.add(instance)
        session.flush()
        return instance
    
    def update(self, session: Any, **kwargs: Any) -> None:
        """Update the instance with the provided attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        session.flush()
    
    def delete(self, session: Any) -> None:
        """Delete the instance from the database."""
        session.delete(self)
        session.flush()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary."""
        result = {}
        for column in self.__table__.columns:
            result[column.name] = getattr(self, column.name)
        return result


# Database connection and session management
class Database:
    """Database connection and session management."""
    
    def __init__(self, db_path: str = 'sqlite:///the_plot_thickens.db'):
        """Initialize the database connection.
        
        Args:
            db_path: Path to the database file or connection string
        """
        self.engine = create_engine(db_path)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
    
    def create_tables(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self) -> Any:
        """Get a new session for database operations."""
        return self.Session()
    
    def close_session(self, session: Any) -> None:
        """Close the session."""
        session.close()
    
    def commit_session(self, session: Any) -> None:
        """Commit the session."""
        session.commit()
    
    def rollback_session(self, session: Any) -> None:
        """Rollback the session."""
        session.rollback() 
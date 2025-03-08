#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Very simple test script for SQLAlchemy.

This script tests basic SQLAlchemy functionality.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create the base model class
Base = declarative_base()

# Define a simple model
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}')>"

def main():
    """Test basic SQLAlchemy functionality."""
    # Create an in-memory SQLite database
    engine = create_engine('sqlite:///:memory:')
    
    # Create the tables
    Base.metadata.create_all(engine)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create a user
        user = User(name="Test User")
        session.add(user)
        session.commit()
        
        # Query the user
        queried_user = session.query(User).filter_by(name="Test User").first()
        print(f"Created user: {queried_user}")
        
        print("Basic SQLAlchemy test completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main() 
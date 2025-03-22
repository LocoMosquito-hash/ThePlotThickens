from typing import List, Dict, Tuple, Optional, Any, Union
import os
import json
import numpy as np
from pathlib import Path
import sqlite3
import face_recognition  # Will need to be installed
from PyQt6.QtGui import QImage
import pickle
from datetime import datetime


class FaceRecognitionUtil:
    """Utility for handling facial recognition in the application."""
    
    def __init__(self, db_conn: sqlite3.Connection, cache_dir: str = None):
        """Initialize the face recognition utility.
        
        Args:
            db_conn: Database connection
            cache_dir: Directory to store face encoding cache
        """
        self.db_conn = db_conn
        
        # Set up cache directory for face encodings
        if cache_dir is None:
            # Default to a .faces directory in the app's data folder
            app_data_dir = os.path.join(os.path.expanduser("~"), ".ThePlotThickens")
            self.cache_dir = os.path.join(app_data_dir, "faces")
        else:
            self.cache_dir = cache_dir
            
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Ensure face encodings table exists
        self._create_face_encodings_table()
    
    def _create_face_encodings_table(self) -> None:
        """Create the face_encodings table if it doesn't exist."""
        cursor = self.db_conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_encodings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            encoding_path TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 1.0,
            is_avatar INTEGER NOT NULL DEFAULT 0,
            image_id INTEGER,
            x INTEGER,
            y INTEGER,
            width INTEGER,
            height INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE,
            FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
        )
        ''')
        
        # Add index for fast querying by character_id
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_face_encodings_character_id ON face_encodings(character_id)')
        
        self.db_conn.commit()
    
    def extract_faces_from_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Extract face locations and encodings from an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of dicts with face data: {'location': (top, right, bottom, left), 'encoding': encoding}
        """
        # Load image
        image = face_recognition.load_image_file(image_path)
        
        # Find face locations and encodings
        face_locations = face_recognition.face_locations(image, model="hog")  # Use CNN for better accuracy but slower
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        # Combine results
        faces = []
        for i, (location, encoding) in enumerate(zip(face_locations, face_encodings)):
            faces.append({
                'location': location,  # (top, right, bottom, left)
                'encoding': encoding   # 128-dimensional face encoding
            })
        
        return faces
    
    def save_face_encoding(self, character_id: int, encoding: np.ndarray, is_avatar: bool = False, 
                         image_id: Optional[int] = None, location: Optional[Tuple[int, int, int, int]] = None) -> int:
        """Save a face encoding for a character.
        
        Args:
            character_id: ID of the character
            encoding: The face encoding (128-dim vector)
            is_avatar: Whether this encoding is from the character's avatar
            image_id: ID of the source image, if applicable
            location: Face location as (top, right, bottom, left)
            
        Returns:
            ID of the saved encoding
        """
        # Generate a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        encoding_filename = f"face_{character_id}_{timestamp}.pkl"
        encoding_path = os.path.join(self.cache_dir, encoding_filename)
        
        # Save the encoding to disk
        with open(encoding_path, 'wb') as f:
            pickle.dump(encoding, f)
        
        # Save to database
        cursor = self.db_conn.cursor()
        now = datetime.now().isoformat()
        
        if location:
            top, right, bottom, left = location
            cursor.execute('''
            INSERT INTO face_encodings (
                character_id, encoding_path, is_avatar, image_id, 
                x, y, width, height, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                character_id, encoding_path, 1 if is_avatar else 0, image_id,
                left, top, right - left, bottom - top, now, now
            ))
        else:
            cursor.execute('''
            INSERT INTO face_encodings (
                character_id, encoding_path, is_avatar, image_id, 
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                character_id, encoding_path, 1 if is_avatar else 0, image_id,
                now, now
            ))
        
        self.db_conn.commit()
        return cursor.lastrowid
    
    def get_character_face_encodings(self, character_id: int = None) -> Dict[int, List[np.ndarray]]:
        """Get face encodings for characters.
        
        Args:
            character_id: Optional character ID to filter by
            
        Returns:
            Dictionary mapping character IDs to lists of face encodings
        """
        cursor = self.db_conn.cursor()
        
        if character_id:
            cursor.execute('''
            SELECT id, character_id, encoding_path
            FROM face_encodings
            WHERE character_id = ?
            ''', (character_id,))
        else:
            cursor.execute('''
            SELECT id, character_id, encoding_path
            FROM face_encodings
            ''')
        
        results = cursor.fetchall()
        
        # Group encodings by character
        encodings_by_character = {}
        for row in results:
            row_dict = dict(row)
            char_id = row_dict['character_id']
            encoding_path = row_dict['encoding_path']
            
            # Load encoding from disk
            try:
                with open(encoding_path, 'rb') as f:
                    encoding = pickle.load(f)
                
                if char_id not in encodings_by_character:
                    encodings_by_character[char_id] = []
                
                encodings_by_character[char_id].append(encoding)
            except (FileNotFoundError, pickle.PickleError) as e:
                print(f"Error loading face encoding {encoding_path}: {e}")
        
        return encodings_by_character
    
    def identify_faces(self, image_path: str, tolerance: float = 0.6) -> List[Dict[str, Any]]:
        """Identify characters in an image based on face recognition.
        
        Args:
            image_path: Path to the image
            tolerance: Matching tolerance (lower = more strict)
            
        Returns:
            List of dicts with recognition data: {
                'character_id': id,
                'confidence': score,
                'location': (top, right, bottom, left)
            }
        """
        # Get face encodings for all characters
        character_encodings = self.get_character_face_encodings()
        
        if not character_encodings:
            return []
        
        # Extract faces from the image
        faces = self.extract_faces_from_image(image_path)
        
        if not faces:
            return []
        
        # Prepare results
        recognition_results = []
        
        # For each face found in the image
        for face in faces:
            face_encoding = face['encoding']
            face_location = face['location']
            
            best_match = None
            best_confidence = 0
            
            # Compare against each character's face encodings
            for character_id, encodings in character_encodings.items():
                # Calculate face distances
                face_distances = face_recognition.face_distance(encodings, face_encoding)
                
                if len(face_distances) > 0:
                    # Convert distance to confidence score (0-1)
                    min_distance = min(face_distances)
                    confidence = 1.0 - min(min_distance, 1.0)
                    
                    # If we found a better match and it's within tolerance
                    if confidence > best_confidence and min_distance <= tolerance:
                        best_match = character_id
                        best_confidence = confidence
            
            # If we found a match
            if best_match:
                recognition_results.append({
                    'character_id': best_match,
                    'confidence': best_confidence,
                    'location': face_location
                })
        
        return recognition_results
    
    def extract_face_from_avatar(self, character_id: int, avatar_path: str) -> bool:
        """Extract and save face encoding from a character's avatar.
        
        Args:
            character_id: Character ID
            avatar_path: Path to the avatar image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract faces
            faces = self.extract_faces_from_image(avatar_path)
            
            if not faces:
                print(f"No faces found in avatar: {avatar_path}")
                return False
            
            # Use the first face found (avatar should typically have one face)
            face = faces[0]
            
            # Save face encoding
            self.save_face_encoding(
                character_id=character_id,
                encoding=face['encoding'],
                is_avatar=True,
                location=face['location']
            )
            
            return True
        except Exception as e:
            print(f"Error extracting face from avatar: {e}")
            return False
    
    def build_character_face_database(self) -> None:
        """Build/rebuild the face database from character avatars and tagged images."""
        cursor = self.db_conn.cursor()
        
        # Get all characters with avatars
        cursor.execute('''
        SELECT id, avatar_path
        FROM characters
        WHERE avatar_path IS NOT NULL AND avatar_path != ''
        ''')
        
        characters = cursor.fetchall()
        
        # Extract faces from avatars
        for character in characters:
            character_dict = dict(character)
            character_id = character_dict['id']
            avatar_path = character_dict['avatar_path']
            
            if os.path.exists(avatar_path):
                self.extract_face_from_avatar(character_id, avatar_path) 
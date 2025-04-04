"""
Image recognition utility for suggesting character tags.

This module provides a simplified image recognition system that doesn't require
external dependencies like face_recognition.
"""

from typing import List, Dict, Tuple, Optional, Any, Union
import os
import sqlite3
import json
from datetime import datetime
from PyQt6.QtGui import QImage, QPixmap, qRgb, qRed, qGreen, qBlue
from PyQt6.QtCore import QRect, QBuffer, QByteArray, QIODevice
import numpy as np


class ImageRecognitionUtil:
    """Utility for basic image recognition to suggest character tags."""
    
    def __init__(self, db_conn: sqlite3.Connection, cache_dir: str = None):
        """Initialize the image recognition utility.
        
        Args:
            db_conn: Database connection
            cache_dir: Directory to store image feature cache
        """
        self.db_conn = db_conn
        
        # Set up cache directory for image features
        if cache_dir is None:
            # Default to a .features directory in the app's data folder
            app_data_dir = os.path.join(os.path.expanduser("~"), ".ThePlotThickens")
            self.cache_dir = os.path.join(app_data_dir, "image_features")
        else:
            self.cache_dir = cache_dir
            
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Ensure image features table exists
        self._create_image_features_table()
    
    def _create_image_features_table(self) -> None:
        """Create the image_features table if it doesn't exist."""
        cursor = self.db_conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            image_id INTEGER,
            is_avatar INTEGER NOT NULL DEFAULT 0,
            feature_data TEXT NOT NULL, 
            color_histogram TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE,
            FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
        )
        ''')
        
        # Add index for fast querying by character_id
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_image_features_character_id ON image_features(character_id)')
        
        self.db_conn.commit()
    
    def _calculate_color_histogram(self, image: QImage) -> List[int]:
        """Calculate color histogram for an image.
        
        Args:
            image: QImage to analyze
            
        Returns:
            List of color histogram bins
        """
        # Resize image for faster processing
        if image.width() > 100 or image.height() > 100:
            image = image.scaled(100, 100)
            
        # Create a histogram with 4x4x4 bins for R,G,B
        histogram = [0] * 64  # 4^3 = 64 bins
        
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixel(x, y)
                r = qRed(pixel) // 64    # 0-3
                g = qGreen(pixel) // 64   # 0-3
                b = qBlue(pixel) // 64    # 0-3
                
                # Calculate bin index
                bin_idx = r*16 + g*4 + b
                histogram[bin_idx] += 1
        
        # Normalize histogram
        total_pixels = image.width() * image.height()
        if total_pixels > 0:
            histogram = [count / total_pixels for count in histogram]
            
        return histogram
    
    def _calculate_image_features(self, image: QImage) -> Dict[str, Any]:
        """Calculate features for an image.
        
        Args:
            image: QImage to analyze
            
        Returns:
            Dictionary of image features
        """
        # Calculate color histogram
        color_histogram = self._calculate_color_histogram(image)
        
        # Create simplified feature representation
        features = {
            "width": image.width(),
            "height": image.height(),
            "aspect_ratio": image.width() / max(1, image.height()),
            "brightness": self._calculate_brightness(image),
            "colorfulness": self._calculate_colorfulness(image)
        }
        
        return {
            "features": features,
            "color_histogram": color_histogram
        }
    
    def _calculate_brightness(self, image: QImage) -> float:
        """Calculate average brightness of an image.
        
        Args:
            image: QImage to analyze
            
        Returns:
            Average brightness value 0-1
        """
        # Resize for faster processing
        if image.width() > 50 or image.height() > 50:
            image = image.scaled(50, 50)
            
        total_brightness = 0
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixel(x, y)
                brightness = (qRed(pixel) + qGreen(pixel) + qBlue(pixel)) / (3 * 255)
                total_brightness += brightness
        
        return total_brightness / (image.width() * image.height())
    
    def _calculate_colorfulness(self, image: QImage) -> float:
        """Calculate colorfulness of an image.
        
        Args:
            image: QImage to analyze
            
        Returns:
            Colorfulness score 0-1
        """
        # Resize for faster processing
        if image.width() > 50 or image.height() > 50:
            image = image.scaled(50, 50)
            
        total_saturation = 0
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixel(x, y)
                r, g, b = qRed(pixel), qGreen(pixel), qBlue(pixel)
                # Calculate max and min RGB values
                max_rgb = max(r, g, b)
                min_rgb = min(r, g, b)
                # Calculate saturation as (max - min) / max if max > 0
                if max_rgb > 0:
                    saturation = (max_rgb - min_rgb) / max_rgb
                else:
                    saturation = 0
                total_saturation += saturation
        
        return total_saturation / (image.width() * image.height())
    
    def extract_features_from_path(self, image_path: str) -> Dict[str, Any]:
        """Extract features from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary of image features
        """
        image = QImage(image_path)
        if image.isNull():
            raise ValueError(f"Failed to load image from {image_path}")
        
        return self._calculate_image_features(image)
    
    def extract_features_from_qimage(self, image: QImage) -> Dict[str, Any]:
        """Extract features from a QImage.
        
        Args:
            image: QImage to analyze
            
        Returns:
            Dictionary of image features
        """
        if image.isNull():
            raise ValueError("Cannot extract features from null image")
        
        return self._calculate_image_features(image)
    
    def extract_features_from_pixmap(self, pixmap: QPixmap) -> Dict[str, Any]:
        """Extract features from a QPixmap.
        
        Args:
            pixmap: QPixmap to analyze
            
        Returns:
            Dictionary of image features
        """
        return self.extract_features_from_qimage(pixmap.toImage())
    
    def save_character_image_features(self, character_id: int, features: Dict[str, Any], 
                                    is_avatar: bool = False, image_id: Optional[int] = None) -> int:
        """Save image features for a character.
        
        Args:
            character_id: ID of the character
            features: Image features dictionary
            is_avatar: Whether this is from a character's avatar
            image_id: ID of the source image, if applicable
            
        Returns:
            ID of the saved features
        """
        # Serialize features to JSON
        feature_data = json.dumps(features["features"])
        color_histogram = json.dumps(features["color_histogram"])
        
        # Save to database
        cursor = self.db_conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO image_features (
            character_id, image_id, is_avatar,
            feature_data, color_histogram, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            character_id, image_id, 1 if is_avatar else 0,
            feature_data, color_histogram, now, now
        ))
        
        self.db_conn.commit()
        return cursor.lastrowid
    
    def get_character_image_features(self, character_id: int = None) -> Dict[int, List[Dict[str, Any]]]:
        """Get image features for characters.
        
        Args:
            character_id: Optional character ID to filter by
            
        Returns:
            Dictionary mapping character IDs to lists of image features
        """
        cursor = self.db_conn.cursor()
        
        if character_id:
            cursor.execute('''
            SELECT id, character_id, feature_data, color_histogram
            FROM image_features
            WHERE character_id = ?
            ''', (character_id,))
        else:
            cursor.execute('''
            SELECT id, character_id, feature_data, color_histogram
            FROM image_features
            ''')
        
        results = cursor.fetchall()
        
        # Group features by character
        features_by_character = {}
        for row in results:
            row_dict = dict(row)
            char_id = row_dict['character_id']
            
            try:
                feature_data = json.loads(row_dict['feature_data'])
                color_histogram = json.loads(row_dict['color_histogram'])
                
                if char_id not in features_by_character:
                    features_by_character[char_id] = []
                
                features_by_character[char_id].append({
                    'features': feature_data,
                    'color_histogram': color_histogram
                })
            except json.JSONDecodeError as e:
                print(f"Error parsing feature data: {e}")
        
        return features_by_character
    
    def _calculate_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate similarity between two sets of image features.
        
        Args:
            features1: First set of image features
            features2: Second set of image features
            
        Returns:
            Similarity score 0-1 (higher is more similar)
        """
        # Compare basic features
        aspect_ratio_diff = abs(features1['features']['aspect_ratio'] - features2['features']['aspect_ratio'])
        brightness_diff = abs(features1['features']['brightness'] - features2['features']['brightness'])
        colorfulness_diff = abs(features1['features']['colorfulness'] - features2['features']['colorfulness'])
        
        # Compare color histograms
        histogram1 = features1['color_histogram']
        histogram2 = features2['color_histogram']
        
        # Calculate histogram intersection
        hist_intersection = sum(min(h1, h2) for h1, h2 in zip(histogram1, histogram2))
        
        # Combine metrics (weighted)
        similarity = (
            (1.0 - min(aspect_ratio_diff / 2.0, 1.0)) * 0.1 +  # 10% weight
            (1.0 - min(brightness_diff, 1.0)) * 0.2 +          # 20% weight
            (1.0 - min(colorfulness_diff, 1.0)) * 0.2 +        # 20% weight
            hist_intersection * 0.5                           # 50% weight
        )
        
        return similarity
    
    def identify_characters_in_image(self, image_features: Dict[str, Any], 
                                  threshold: float = 0.6,
                                  story_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Identify possible characters in an image based on similarity.
        
        Args:
            image_features: Features of the image to analyze
            threshold: Minimum similarity threshold (0-1)
            story_id: Optional story ID to filter characters by story
            
        Returns:
            List of dicts with identification data: {
                'character_id': id,
                'character_name': name,
                'similarity': score
            }
        """
        # Get image features for all characters
        character_features = self.get_character_image_features()
        
        if not character_features:
            return []
        
        # Get character names and filter by story_id if provided
        cursor = self.db_conn.cursor()
        if story_id is not None:
            cursor.execute('SELECT id, name FROM characters WHERE story_id = ?', (story_id,))
        else:
            cursor.execute('SELECT id, name FROM characters')
            
        characters = {row['id']: row['name'] for row in cursor.fetchall()}
        
        # Calculate similarity with each character's features
        results = []
        
        for character_id, feature_list in character_features.items():
            # Skip characters not in the current story if story_id is provided
            if story_id is not None and character_id not in characters:
                continue
                
            # Calculate similarity with each feature set
            similarities = []
            for features in feature_list:
                similarity = self._calculate_similarity(image_features, features)
                similarities.append(similarity)
            
            # Use the highest similarity score
            if similarities:
                max_similarity = max(similarities)
                
                # If similarity is above threshold, add to results
                if max_similarity >= threshold:
                    results.append({
                        'character_id': character_id,
                        'character_name': characters.get(character_id, f"Character {character_id}"),
                        'similarity': max_similarity
                    })
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results
    
    def extract_features_from_avatar(self, character_id: int, avatar_path: str) -> bool:
        """Extract and save image features from a character's avatar.
        
        Args:
            character_id: Character ID
            avatar_path: Path to the avatar image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract features
            features = self.extract_features_from_path(avatar_path)
            
            # Save features
            self.save_character_image_features(
                character_id=character_id,
                features=features,
                is_avatar=True
            )
            
            return True
        except Exception as e:
            print(f"Error extracting features from avatar: {e}")
            return False
    
    def build_character_image_database(self) -> None:
        """Build/rebuild the image features database from character avatars."""
        cursor = self.db_conn.cursor()
        
        # Get all characters with avatars
        cursor.execute('''
        SELECT id, avatar_path, name
        FROM characters
        WHERE avatar_path IS NOT NULL AND avatar_path != ''
        ''')
        
        characters = cursor.fetchall()
        print(f"Building recognition database - found {len(characters)} characters with avatars")
        
        # Count before
        cursor.execute('SELECT COUNT(*) FROM image_features')
        count_before = cursor.fetchone()[0]
        
        # Clear existing features if they exist
        cursor.execute('DELETE FROM image_features WHERE is_avatar = 1')
        self.db_conn.commit()
        
        # Extract features from avatars
        success_count = 0
        error_count = 0
        
        for character in characters:
            character_dict = dict(character)
            character_id = character_dict['id']
            avatar_path = character_dict['avatar_path']
            character_name = character_dict['name']
            
            if os.path.exists(avatar_path):
                try:
                    print(f"Processing character: {character_name} (ID: {character_id})")
                    result = self.extract_features_from_avatar(character_id, avatar_path)
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                        print(f"Failed to extract features for character: {character_name}")
                except Exception as e:
                    error_count += 1
                    print(f"Error processing character {character_name}: {str(e)}")
            else:
                print(f"Avatar path does not exist: {avatar_path} for character: {character_name}")
                error_count += 1
        
        # Count after
        cursor.execute('SELECT COUNT(*) FROM image_features WHERE is_avatar = 1')
        count_after = cursor.fetchone()[0]
        
        print(f"Character recognition database build complete:")
        print(f"- Found {len(characters)} characters with avatars")
        print(f"- Successfully processed: {success_count}")
        print(f"- Errors: {error_count}")
        print(f"- Features before: {count_before}, after: {count_after}")
        
        # Commit any pending changes
        self.db_conn.commit() 
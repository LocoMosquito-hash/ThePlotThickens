"""
Configuration for Ren'Py Source API testing and development.

This file contains configuration settings that can be easily modified
for testing with different VNs without editing the main code.
"""

import os
from pathlib import Path

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

# Primary test VN path - CHANGE THIS to your decompiled Ren'Py game folder
TEST_VN_PATH = r"T:\AG\Savior-0.16c-pc\game"

# Alternative test paths - uncomment and modify as needed
ALTERNATIVE_PATHS = {
    "accept_the_past": r"T:\AG\AcceptthePast-0.1-pc\game",
    "blairewood": r"T:\AG\Blairewood-1.0-pc\game",
    "the_way": r"T:\AG\TheWay-pc\game",
    "detective_necro": r"T:\AG\DetectiveNecro-0.55-pc\game",
    "grandmas_house": r"T:\AG\GrandmasHouse-V0.11-pc\game",
    # Add your own paths here:
    # "my_vn": r"C:\Path\To\Your\VN\game",
}

# Default test VN to use if PRIMARY_TEST_VN_PATH doesn't exist
FALLBACK_VN_KEY = "accept_the_past"

# =============================================================================
# PARSER CONFIGURATION  
# =============================================================================

# Files to exclude from analysis (system/UI files)
EXCLUDED_FILES = {
    'screens.rpy', 'gui.rpy', 'options.rpy', '00keymap.rpy', 
    '00action_file.rpy', '00accessibility.rpy', '00auto.rpy',
    '00barvalues.rpy', '00build.rpy', '00console.rpy',
    '00defaults.rpy', '00definitions.rpy', '00director.rpy',
    '00functions.rpy', '00gallery.rpy', '00gltest.rpy',
    '00iap.rpy', '00icon.rpy', '00images.rpy', '00musicroom.rpy',
    '00nvl_mode.rpy', '00preferences.rpy', '00speech.rpy',
    '00splines.rpy', '00start.rpy', '00steam.rpy', '00style.rpy',
    '00themes.rpy', '00updater.rpy', '00voice.rpy'
}

# File patterns to exclude
EXCLUDED_PATTERNS = [
    "tl/*.rpy",  # Translation files
    "backup/*.rpy",  # Backup files
]

# =============================================================================
# ANALYSIS CONFIGURATION
# =============================================================================

# Maximum file size to process (in MB)
MAX_FILE_SIZE_MB = 10

# Whether to analyze files in subdirectories
RECURSIVE_ANALYSIS = True

# Whether to cache analysis results
ENABLE_CACHING = True

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_test_vn_path() -> str:
    """
    Get the best available test VN path.
    
    Returns:
        Path to a valid VN directory, or raises exception if none found
    """
    # Try primary path first
    if os.path.exists(TEST_VN_PATH):
        return TEST_VN_PATH
    
    # Try alternative paths
    for name, path in ALTERNATIVE_PATHS.items():
        if os.path.exists(path):
            print(f"Using fallback VN: {name} at {path}")
            return path
    
    # If nothing found, return primary path anyway (will fail with helpful error)
    return TEST_VN_PATH

def list_available_vns() -> dict:
    """
    Get a list of all available VN paths that actually exist.
    
    Returns:
        Dictionary of {name: path} for existing VN directories
    """
    available = {}
    
    if os.path.exists(TEST_VN_PATH):
        available["primary"] = TEST_VN_PATH
    
    for name, path in ALTERNATIVE_PATHS.items():
        if os.path.exists(path):
            available[name] = path
    
    return available

def validate_vn_path(path: str) -> tuple[bool, str]:
    """
    Validate that a path looks like a valid Ren'Py game directory.
    
    Args:
        path: Directory path to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not os.path.exists(path):
        return False, f"Directory does not exist: {path}"
    
    if not os.path.isdir(path):
        return False, f"Path is not a directory: {path}"
    
    # Look for .rpy files
    rpy_files = list(Path(path).glob("*.rpy"))
    if not rpy_files:
        # Check subdirectories
        for subdir in Path(path).iterdir():
            if subdir.is_dir():
                sub_rpy_files = list(subdir.glob("*.rpy"))
                if sub_rpy_files:
                    rpy_files.extend(sub_rpy_files)
                    break
    
    if not rpy_files:
        return False, f"No .rpy files found in directory: {path}"
    
    return True, f"Valid Ren'Py directory with {len(rpy_files)} .rpy files"

# =============================================================================
# PLATFORM-SPECIFIC PATHS
# =============================================================================

def get_common_renpy_paths():
    """Get common Ren'Py installation and game paths for different platforms."""
    
    if os.name == 'nt':  # Windows
        return {
            "steam_common": r"C:\Program Files (x86)\Steam\steamapps\common",
            "documents_games": os.path.expanduser(r"~\Documents\Games"),
            "downloads": os.path.expanduser(r"~\Downloads"),
            "desktop": os.path.expanduser(r"~\Desktop"),
        }
    else:  # Linux/macOS
        return {
            "home_games": os.path.expanduser("~/Games"),
            "downloads": os.path.expanduser("~/Downloads"),
            "desktop": os.path.expanduser("~/Desktop"),
        }

# =============================================================================
# DEBUG CONFIGURATION
# =============================================================================

# Enable verbose logging
DEBUG_MODE = True

# Print file parsing progress
SHOW_PARSING_PROGRESS = True

# Export analysis results to JSON for inspection
EXPORT_ANALYSIS_RESULTS = True

# Maximum number of search results to display in tests
MAX_SEARCH_RESULTS = 10 
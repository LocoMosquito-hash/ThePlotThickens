"""
Utility functions for Ren'Py SDK integration.

This module handles SDK path setup and provides safe imports for Ren'Py components.
"""

import os
import sys
import warnings
import platform
from pathlib import Path
from typing import Optional, Tuple, Any


class RenpySDKManager:
    """Manages Ren'Py SDK path setup and component imports."""
    
    def __init__(self, sdk_version: str = "renpy-8.4.0-sdk"):
        """
        Initialize SDK manager.
        
        Args:
            sdk_version: Name of the SDK folder to use
        """
        self.sdk_version = sdk_version
        self.sdk_path: Optional[Path] = None
        self.renpy_module: Optional[Any] = None
        self.is_available = False
        self.bootstrap_complete = False
        
        self._setup_sdk_path()
    
    def _setup_sdk_path(self) -> None:
        """Set up the SDK path and add to sys.path if found."""
        try:
            # Get the path to this file and navigate to SDK
            current_dir = Path(__file__).parent.parent  # /renpy_sdk/
            sdk_dir = current_dir / self.sdk_version
            
            if sdk_dir.exists():
                self.sdk_path = sdk_dir
                print(f"✅ SDK path found: {sdk_dir}")
            else:
                print(f"❌ SDK directory not found: {sdk_dir}")
                
        except Exception as e:
            print(f"❌ Error setting up SDK path: {e}")
    
    def _add_library_paths(self) -> None:
        """Add SDK library paths to sys.path for dependencies."""
        if not self.sdk_path:
            return
        
        lib_dir = self.sdk_path / "lib"
        
        # Add Python 3.12 libraries (contains pygame_sdl2, etc.)
        python_lib = lib_dir / "python3.12"
        if python_lib.exists():
            python_lib_str = str(python_lib)
            if python_lib_str not in sys.path:
                sys.path.insert(0, python_lib_str)
                print(f"✅ Added Python libraries: {python_lib}")
        
        # Add platform-specific libraries  
        if platform.system() == "Windows":
            if platform.machine().lower() == "amd64":
                platform_lib = lib_dir / "py3-windows-x86_64"
            else:
                platform_lib = lib_dir / "py3-windows-i686"
        elif platform.system() == "Darwin":  # macOS
            platform_lib = lib_dir / "py3-mac-universal"
        elif platform.system() == "Linux":
            platform_lib = lib_dir / "py3-linux-x86_64"
        else:
            print(f"⚠️  Unknown platform: {platform.system()}")
            return
        
        if platform_lib.exists():
            platform_lib_str = str(platform_lib)
            if platform_lib_str not in sys.path:
                sys.path.insert(0, platform_lib_str)
                print(f"✅ Added platform libraries: {platform_lib}")
    
    def initialize_sdk(self) -> bool:
        """
        Attempt to bootstrap and import Ren'Py SDK components.
        
        Returns:
            True if SDK components imported successfully, False otherwise
        """
        if self.sdk_path is None:
            print("❌ SDK path not available")
            return False
        
        try:
            # Follow Ren'Py's bootstrap pattern
            renpy_base = str(self.sdk_path)
            
            # Add renpy base to sys.path (like renpy.py does)
            if renpy_base not in sys.path:
                sys.path.insert(0, renpy_base)
                print(f"✅ Added SDK to sys.path: {renpy_base}")
            
            # Add library dependencies BEFORE bootstrapping
            self._add_library_paths()
            
            # Suppress warnings like Ren'Py does
            warnings.simplefilter("ignore", DeprecationWarning)
            
            # Import and bootstrap Ren'Py
            import renpy.bootstrap
            print("✅ Successfully imported renpy.bootstrap")
            
            # Bootstrap the Ren'Py environment
            print("🔄 Bootstrapping Ren'Py environment...")
            renpy.bootstrap.bootstrap(renpy_base)
            self.bootstrap_complete = True
            print("✅ Ren'Py bootstrap complete")
            
            # Now we can safely import the main renpy module
            import renpy
            self.renpy_module = renpy
            self.is_available = True
            
            print("✅ Successfully imported Ren'Py main module")
            print(f"   Ren'Py version: {getattr(renpy, 'version_string', 'Unknown')}")
            
            return True
            
        except ImportError as e:
            print(f"❌ Failed to import Ren'Py components: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during SDK initialization: {e}")
            # Print more detailed error info
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            return False
    
    def get_parser(self) -> Optional[Any]:
        """Get the Ren'Py parser module if available."""
        if not self.is_available:
            return None
        try:
            return self.renpy_module.parser
        except AttributeError:
            print("❌ Parser not available in Ren'Py module")
            return None
    
    def get_ast(self) -> Optional[Any]:
        """Get the Ren'Py AST module if available."""
        if not self.is_available:
            return None
        try:
            return self.renpy_module.ast
        except AttributeError:
            print("❌ AST not available in Ren'Py module")
            return None
    
    def parse_script(self, script_content: str, filename: str = "test.rpy") -> Tuple[bool, Any]:
        """
        Parse Ren'Py script content using the SDK parser.
        
        Args:
            script_content: The .rpy script content to parse
            filename: Filename for error reporting
            
        Returns:
            Tuple of (success, result) where result is either AST nodes or error message
        """
        if not self.is_available:
            return False, "SDK not available"
        
        try:
            parser = self.get_parser()
            if parser is None:
                return False, "Parser not available"
            
            # Use Ren'Py's parser to parse the script content
            ast_nodes = parser.parse(script_content, filename)
            return True, ast_nodes
        except Exception as e:
            return False, f"Parse error: {e}"
    
    def get_sdk_info(self) -> dict:
        """Get information about the SDK setup."""
        return {
            'sdk_version': self.sdk_version,
            'sdk_path': str(self.sdk_path) if self.sdk_path else None,
            'is_available': self.is_available,
            'bootstrap_complete': self.bootstrap_complete,
            'parser_available': self.get_parser() is not None,
            'ast_available': self.get_ast() is not None,
            'renpy_version': getattr(self.renpy_module, 'version_string', 'Unknown') if self.renpy_module else None
        }


# Global SDK manager instance
sdk_manager = RenpySDKManager() 
"""
Minimal SDK parser test - imports only what we need for parsing.

This test avoids the full Ren'Py bootstrap and focuses on just the parsing functionality.
"""

import sys
import os
from pathlib import Path

# Add the src directory to path so we can import our utilities
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))


class MinimalRenpyParser:
    """Minimal Ren'Py parser that imports only parsing components."""
    
    def __init__(self, sdk_version: str = "renpy-8.4.0-sdk"):
        self.sdk_version = sdk_version
        self.sdk_path = None
        self.parser_module = None
        self.ast_module = None
        self.is_available = False
        
        self._setup_sdk_path()
    
    def _setup_sdk_path(self):
        """Set up SDK path."""
        current_dir = Path(__file__).parent.parent  # /renpy_sdk/
        sdk_dir = current_dir / self.sdk_version
        
        if sdk_dir.exists():
            self.sdk_path = sdk_dir
            print(f"✅ SDK path found: {sdk_dir}")
            return True
        else:
            print(f"❌ SDK directory not found: {sdk_dir}")
            return False
    
    def initialize_minimal(self):
        """Initialize minimal parser without full bootstrap."""
        if not self.sdk_path:
            print("❌ SDK path not available")
            return False
        
        try:
            # Add the SDK renpy directory to path
            renpy_dir = str(self.sdk_path)
            if renpy_dir not in sys.path:
                sys.path.insert(0, renpy_dir)
                print(f"✅ Added SDK to sys.path: {renpy_dir}")
            
            # Try to import just the parser module directly
            print("🔄 Importing renpy.parser directly...")
            import renpy.parser
            self.parser_module = renpy.parser
            print("✅ Successfully imported renpy.parser")
            
            # Try to import AST module
            print("🔄 Importing renpy.ast directly...")
            import renpy.ast
            self.ast_module = renpy.ast
            print("✅ Successfully imported renpy.ast")
            
            self.is_available = True
            return True
            
        except Exception as e:
            print(f"❌ Failed to import parser components: {e}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            return False
    
    def parse_script(self, script_content: str, filename: str = "test.rpy"):
        """Parse script using the minimal parser."""
        if not self.is_available:
            return False, "Parser not available"
        
        try:
            # Use the parser directly
            ast_nodes = self.parser_module.parse(script_content, filename)
            return True, ast_nodes
        except Exception as e:
            return False, f"Parse error: {e}"


def test_minimal_parsing():
    """Test minimal parsing approach."""
    print("="*60)
    print("TESTING MINIMAL PARSER APPROACH")
    print("="*60)
    
    parser = MinimalRenpyParser()
    
    print("\n1. Initializing minimal parser...")
    success = parser.initialize_minimal()
    
    if not success:
        print("❌ Minimal parser initialization failed")
        return False
    
    print("\n2. Testing simple script parsing...")
    simple_script = '''
label start:
    "Hello, world!"
    "This is a minimal test."
    
    menu:
        "Choice 1":
            jump choice1
        "Choice 2":
            jump choice2
    
label choice1:
    "You chose option 1"
    return
    
label choice2:
    "You chose option 2"
    return
'''
    
    success, result = parser.parse_script(simple_script)
    
    if success:
        print("✅ Parsing successful!")
        print(f"Number of AST nodes: {len(result)}")
        
        # Analyze the AST nodes
        for i, node in enumerate(result):
            node_type = type(node).__name__
            print(f"  Node {i}: {node_type}")
            
            # Basic info extraction
            if hasattr(node, 'name'):
                print(f"    Name: {node.name}")
            if hasattr(node, 'what'):
                print(f"    Text: {repr(node.what)}")
        
        return True
    else:
        print(f"❌ Parsing failed: {result}")
        return False


def main():
    """Run minimal parser test."""
    print("Minimal Ren'Py Parser Test")
    print("Attempting to import only parser components without full bootstrap...")
    
    success = test_minimal_parsing()
    
    print("\n" + "="*60)
    print("MINIMAL PARSER TEST SUMMARY")
    print("="*60)
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎉 Minimal parser approach works!")
        print("This means we can use Ren'Py's parser without full environment setup.")
    else:
        print("\n💥 Minimal parser approach failed.")
        print("May need to use SDK's own Python runtime or different approach.")
    
    return success


if __name__ == "__main__":
    main() 
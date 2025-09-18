#!/usr/bin/env python3
"""
Basic CSAP functionality tests.

Tests core parser functionality before running regression tests.
"""

import pytest
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from csap_parser import CSAPParser
from csap_ast import ScreenNode, TextButtonNode, ImageButtonNode, HotspotNode
from csap_exceptions import CSAPError, CSAPParseError


class TestCSAPBasic:
    """Basic CSAP functionality tests."""
    
    @pytest.fixture
    def parser(self):
        """Create a CSAP parser instance."""
        return CSAPParser()
    
    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly."""
        assert parser is not None
        assert parser.parser is not None
        assert parser.transformer is not None
    
    def test_simple_textbutton(self, parser):
        """Test parsing a simple textbutton."""
        screen_text = '''screen test:
    textbutton "Click me" action Jump("destination")'''
        
        result = parser.parse_screen_text(screen_text)
        
        assert isinstance(result, ScreenNode)
        assert result.screen_name == "test"
        assert len(result.elements) == 1
        
        element = result.elements[0]
        assert isinstance(element, TextButtonNode)
        assert element.text == "Click me"
        assert element.action is not None
        assert element.action.action_type == "Jump"
        assert element.action.destination == "destination"
    
    def test_simple_hotspot(self, parser):
        """Test parsing a simple hotspot."""
        screen_text = '''screen test:
    hotspot (100, 200, 50, 75) action Jump("target")'''
        
        result = parser.parse_screen_text(screen_text)
        
        assert isinstance(result, ScreenNode)
        assert len(result.elements) == 1
        
        element = result.elements[0]
        assert isinstance(element, HotspotNode)
        assert element.coordinates == (100, 200, 50, 75)
        assert element.action.action_type == "Jump"
        assert element.action.destination == "target"
    
    def test_parse_error_handling(self, parser):
        """Test that parse errors are handled properly."""
        # Invalid syntax should raise CSAPParseError
        invalid_screen = '''screen test:
    invalid_element "text" action'''
        
        with pytest.raises(CSAPParseError):
            parser.parse_screen_text(invalid_screen)
    
    def test_grammar_validation(self, parser):
        """Test grammar validation."""
        assert parser.validate_grammar() == True


def main():
    """Run basic tests manually."""
    print("🧪 Running CSAP Basic Tests...")
    
    try:
        parser = CSAPParser()
        print("✅ Parser initialized successfully")
        
        # Test simple textbutton
        screen_text = '''screen test:
    textbutton "Click me" action Jump("destination")'''
        
        result = parser.parse_screen_text(screen_text)
        print(f"✅ Parsed textbutton: {result.elements[0].text} -> {result.elements[0].action.destination}")
        
        # Test simple hotspot
        screen_text = '''screen test:
    hotspot (100, 200, 50, 75) action Jump("target")'''
        
        result = parser.parse_screen_text(screen_text)
        print(f"✅ Parsed hotspot: {result.elements[0].coordinates} -> {result.elements[0].action.destination}")
        
        print("🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

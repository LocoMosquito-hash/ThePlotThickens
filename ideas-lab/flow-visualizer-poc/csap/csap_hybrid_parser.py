#!/usr/bin/env python3
"""
CSAP Hybrid Parser

A drop-in replacement for RenpyParser that uses CSAP for screen parsing
while maintaining all other functionality through delegation.

This provides a safe way to integrate CSAP into production without
modifying the original parser.py file.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import the original parser
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent.parent / "app" / "renpy-source-api"
sys.path.insert(0, str(app_dir))

try:
    from parser import RenpyParser, ScreenStructure, ScreenElement
    from csap_integration import CSAPIntegratedParser
    ORIGINAL_PARSER_AVAILABLE = True
except ImportError as e:
    print(f"[CSAP HYBRID] Could not import original parser: {e}")
    ORIGINAL_PARSER_AVAILABLE = False
    RenpyParser = object  # Fallback


class CSAPHybridParser(RenpyParser):
    """
    Hybrid parser that uses CSAP for screen parsing and delegates
    everything else to the original RenpyParser.
    
    This is a safe, non-invasive way to integrate CSAP into production.
    """
    
    def __init__(self):
        """Initialize the hybrid parser."""
        # Initialize the original parser
        if ORIGINAL_PARSER_AVAILABLE:
            super().__init__()
        
        # Initialize CSAP for screen parsing
        try:
            self.csap_parser = CSAPIntegratedParser()
            self.csap_enabled = True
            print("[CSAP HYBRID] Enhanced screen parsing enabled")
        except Exception as e:
            print(f"[CSAP HYBRID] CSAP initialization failed: {e}")
            self.csap_parser = None
            self.csap_enabled = False
        
        # Performance tracking
        self.total_screens_parsed = 0
        self.csap_successes = 0
        self.regex_fallbacks = 0
    
    def parse_screen_structure(self, file_path: str, start_line: int, lines: List[str], screen_name: str) -> ScreenStructure:
        """
        Enhanced screen parsing using CSAP with regex fallback.
        
        This method replaces the original regex-based screen parsing
        with CSAP while maintaining full backward compatibility.
        """
        self.total_screens_parsed += 1
        
        # Try CSAP first
        if self.csap_enabled and self.csap_parser:
            try:
                result = self.csap_parser.parse_screen_structure(file_path, start_line, lines, screen_name)
                self.csap_successes += 1
                return result
            except Exception as e:
                print(f"[CSAP HYBRID] CSAP failed for '{screen_name}': {e}")
                self.regex_fallbacks += 1
        
        # Fall back to original regex parsing
        if ORIGINAL_PARSER_AVAILABLE:
            try:
                return super().parse_screen_structure(file_path, start_line, lines, screen_name)
            except Exception as e:
                print(f"[CSAP HYBRID] Regex fallback also failed for '{screen_name}': {e}")
        
        # Last resort: return empty screen structure
        return ScreenStructure(
            screen_name=screen_name,
            file_path=file_path,
            line_number=start_line,
            elements=[],
            total_elements=0,
            interactive_elements=0
        )
    
    def find_all_screens(self, project_path: str) -> List[ScreenStructure]:
        """
        Enhanced screen discovery using CSAP.
        
        Uses CSAP's integrated screen finding with fallback to original method.
        """
        if self.csap_enabled and self.csap_parser:
            try:
                return self.csap_parser.find_all_screens(project_path)
            except Exception as e:
                print(f"[CSAP HYBRID] CSAP find_all_screens failed: {e}")
        
        # Fall back to original method
        if ORIGINAL_PARSER_AVAILABLE:
            return super().find_all_screens(project_path)
        
        return []
    
    def get_csap_performance_stats(self) -> Dict[str, Any]:
        """Get CSAP performance statistics."""
        stats = {
            'total_screens_parsed': self.total_screens_parsed,
            'csap_successes': self.csap_successes,
            'regex_fallbacks': self.regex_fallbacks,
            'csap_enabled': self.csap_enabled
        }
        
        if self.total_screens_parsed > 0:
            stats['csap_success_rate'] = (self.csap_successes / self.total_screens_parsed) * 100
        else:
            stats['csap_success_rate'] = 0.0
        
        # Get detailed CSAP stats if available
        if self.csap_parser:
            csap_stats = self.csap_parser.get_parsing_stats()
            stats.update({f'csap_{k}': v for k, v in csap_stats.items()})
        
        return stats
    
    def print_performance_report(self):
        """Print a comprehensive performance report."""
        stats = self.get_csap_performance_stats()
        
        print("\\n" + "=" * 50)
        print("📊 CSAP HYBRID PARSER PERFORMANCE REPORT")
        print("=" * 50)
        print(f"🎯 Total Screens Parsed: {stats['total_screens_parsed']}")
        print(f"✅ CSAP Successes: {stats['csap_successes']}")
        print(f"🔄 Regex Fallbacks: {stats['regex_fallbacks']}")
        print(f"📈 CSAP Success Rate: {stats['csap_success_rate']:.1f}%")
        print(f"🔧 CSAP Enabled: {stats['csap_enabled']}")
        
        if 'csap_csap_successes' in stats:
            print(f"\\n🔍 Detailed CSAP Stats:")
            print(f"   CSAP Internal Successes: {stats.get('csap_csap_successes', 0)}")
            print(f"   CSAP Internal Failures: {stats.get('csap_csap_failures', 0)}")
            print(f"   CSAP Fallback Uses: {stats.get('csap_fallback_uses', 0)}")
        
        print("=" * 50)
    
    # All other methods are delegated to the original parser
    # This ensures full compatibility with existing code
    
    def __getattr__(self, name):
        """Delegate all other methods to the original parser."""
        if ORIGINAL_PARSER_AVAILABLE and hasattr(super(), name):
            return getattr(super(), name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


# Convenience function for easy integration
def create_enhanced_parser() -> CSAPHybridParser:
    """
    Create an enhanced parser with CSAP integration.
    
    This is the main entry point for integrating CSAP into existing code.
    Simply replace:
        parser = RenpyParser()
    with:
        parser = create_enhanced_parser()
    """
    return CSAPHybridParser()


# For backward compatibility
def get_csap_enhanced_parser() -> CSAPHybridParser:
    """Alternative name for create_enhanced_parser()."""
    return create_enhanced_parser()

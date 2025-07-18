"""
Ren'Py SDK Integration Module

This module provides seamless integration between the existing regex-based parser
and the official Ren'Py SDK standalone analyzer. It implements a hybrid strategy
that uses regex parsing for standard cases and falls back to SDK analysis for
complex structures.
"""

import os
import sys
import json
import subprocess
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass

try:
    # Try relative imports (when used as package)
    from .parser import RenpyParser, ProjectOverview
    from .exceptions import RenpyAnalysisError, RenpyProjectError
except ImportError:
    # Fall back to direct imports (when run standalone)
    from parser import RenpyParser, ProjectOverview
    from exceptions import RenpyAnalysisError, RenpyProjectError


@dataclass
class SDKAnalysisResult:
    """Result from SDK analysis with metadata."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    analysis_time: float = 0.0
    cache_hit: bool = False


class ComplexityDetector:
    """Detects when VN structures are too complex for regex parsing."""
    
    def __init__(self):
        self.complex_patterns = {
            # Menu patterns that often break regex
            'complex_menu_sets': r'menu\s+\w+\s*\([^)]*\)\s*:',
            'nested_conditionals': r'if\s+.*:\s*\n\s*if\s+.*:',
            'python_blocks': r'python:\s*\n',
            'complex_expressions': r'\$\s+\w+\s*=.*\([^)]*\)',
            'dynamic_jumps': r'jump\s+expression',
            'atl_blocks': r'transform\s+\w+:',
            'screen_definitions': r'screen\s+\w+\s*\([^)]*\)\s*:',
        }
    
    def needs_sdk_analysis(self, project_path: str, regex_results: Optional[ProjectOverview] = None) -> Tuple[bool, List[str]]:
        """
        Determine if a project needs SDK analysis based on complexity indicators.
        
        Args:
            project_path: Path to the VN project
            regex_results: Results from regex parsing (if available)
            
        Returns:
            Tuple of (needs_sdk, reasons)
        """
        reasons = []
        
        # Check regex parsing issues
        if regex_results:
            if regex_results.errors:
                reasons.append(f"Regex parsing errors: {len(regex_results.errors)}")
            
            # Check for suspiciously low results (may indicate parsing failures)
            if regex_results.total_menus == 0 and regex_results.total_labels > 10:
                reasons.append("No menus found despite having many labels (potential parsing issue)")
            
            if regex_results.total_characters == 0 and regex_results.total_dialogue_lines > 100:
                reasons.append("No characters found despite having dialogue (potential parsing issue)")
            
            # Enhanced check: Look for complex menu indicators in basic results
            if regex_results.total_menus > 20:
                reasons.append(f"High menu count ({regex_results.total_menus}) may have complex structures")
        
        # Check file content for complex patterns
        complex_patterns_found = self._scan_for_complex_patterns(project_path)
        if complex_patterns_found:
            reasons.extend([f"Complex pattern found: {pattern}" for pattern in complex_patterns_found])
        
        # Check file sizes (very large files often have complex structures)
        large_files = self._find_large_files(project_path)
        if large_files:
            reasons.append(f"Large files detected: {len(large_files)} files > 50KB")
        
        # Enhanced: Check for conditional menu patterns
        conditional_menu_indicators = self._scan_for_conditional_menus(project_path)
        if conditional_menu_indicators:
            reasons.append(f"Conditional menu patterns detected: {conditional_menu_indicators}")
        
        needs_sdk = len(reasons) > 0
        return needs_sdk, reasons
    
    def _scan_for_complex_patterns(self, project_path: str) -> List[str]:
        """Scan project files for complex patterns that regex struggles with."""
        import re
        found_patterns = []
        
        try:
            project_dir = Path(project_path)
            rpy_files = list(project_dir.glob("**/*.rpy"))
            
            for rpy_file in rpy_files[:5]:  # Sample first 5 files for performance
                try:
                    with open(rpy_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern_name, pattern in self.complex_patterns.items():
                        if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                            if pattern_name not in found_patterns:
                                found_patterns.append(pattern_name)
                
                except Exception:
                    continue  # Skip problematic files
        
        except Exception:
            pass  # If scanning fails, don't block the process
        
        return found_patterns
    
    def _scan_for_conditional_menus(self, project_path: str) -> int:
        """Scan for conditional menu patterns that indicate complexity."""
        import re
        conditional_count = 0
        
        try:
            project_dir = Path(project_path)
            rpy_files = list(project_dir.glob("**/*.rpy"))
            
            # Pattern for conditional choices: "choice" if condition:
            conditional_pattern = re.compile(r'^\s*"[^"]+"\s+if\s+.+:', re.MULTILINE | re.IGNORECASE)
            
            for rpy_file in rpy_files[:10]:  # Sample files for performance
                try:
                    with open(rpy_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    matches = conditional_pattern.findall(content)
                    conditional_count += len(matches)
                
                except Exception:
                    continue  # Skip problematic files
        
        except Exception:
            pass  # If scanning fails, don't block the process
        
        return conditional_count
    
    def _find_large_files(self, project_path: str) -> List[str]:
        """Find unusually large .rpy files that may have complex structures."""
        large_files = []
        
        try:
            project_dir = Path(project_path)
            rpy_files = list(project_dir.glob("**/*.rpy"))
            
            for rpy_file in rpy_files:
                try:
                    file_size = rpy_file.stat().st_size
                    if file_size > 50 * 1024:  # 50KB threshold
                        large_files.append(str(rpy_file.relative_to(project_dir)))
                except Exception:
                    continue
        
        except Exception:
            pass
        
        return large_files
    
    def analyze_sdk_menu_complexity(self, sdk_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze menu complexity from SDK results.
        
        Args:
            sdk_results: Results from the enhanced SDK analyzer
            
        Returns:
            Dict with complexity analysis
        """
        complexity_analysis = {
            "total_menus": 0,
            "total_choices": 0,
            "conditional_menus": 0,
            "complex_menus": 0,
            "named_menus": 0,
            "menu_set_menus": 0,
            "dynamic_menus": 0,
            "average_choices_per_menu": 0,
            "complexity_distribution": {},
            "most_complex_menus": []
        }
        
        if "menus" not in sdk_results:
            return complexity_analysis
        
        menus = sdk_results["menus"]
        complexity_analysis["total_menus"] = len(menus)
        
        complexity_counts = {"simple": 0, "moderate": 0, "conditional": 0, "complex": 0, "dynamic": 0}
        complex_menu_details = []
        
        for menu in menus:
            choices = menu.get("choices", [])
            choice_count = len(choices)
            complexity_analysis["total_choices"] += choice_count
            
            # Count menu types
            if menu.get("has_conditions", False):
                complexity_analysis["conditional_menus"] += 1
            
            if menu.get("menu_name"):
                complexity_analysis["named_menus"] += 1
            
            if menu.get("menu_set"):
                complexity_analysis["menu_set_menus"] += 1
            
            complexity = menu.get("complexity", "simple")
            
            if complexity == "dynamic":
                complexity_analysis["dynamic_menus"] += 1
            
            if complexity in ["complex", "dynamic"]:
                complexity_analysis["complex_menus"] += 1
                
                # Track complex menu details
                complex_menu_details.append({
                    "file": menu.get("file", "unknown"),
                    "line": menu.get("line", 0),
                    "choice_count": choice_count,
                    "complexity": complexity,
                    "has_conditions": menu.get("has_conditions", False),
                    "prompt": menu.get("prompt", "")[:50] + "..." if menu.get("prompt", "") and len(menu.get("prompt", "")) > 50 else menu.get("prompt", "")
                })
            
            # Count complexity distribution
            if complexity in complexity_counts:
                complexity_counts[complexity] += 1
        
        complexity_analysis["complexity_distribution"] = complexity_counts
        
        if complexity_analysis["total_menus"] > 0:
            complexity_analysis["average_choices_per_menu"] = complexity_analysis["total_choices"] / complexity_analysis["total_menus"]
        
        # Keep top 5 most complex menus
        complex_menu_details.sort(key=lambda x: (x["choice_count"], x["complexity"] == "dynamic"), reverse=True)
        complexity_analysis["most_complex_menus"] = complex_menu_details[:5]
        
        return complexity_analysis


class SDKResultsCache:
    """Simple file-based cache for SDK analysis results."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Use a cache directory in the SDK folder
            sdk_dir = Path(__file__).parent / "renpy_sdk"
            self.cache_dir = sdk_dir / "cache"
        
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_project_hash(self, project_path: str) -> str:
        """Generate a hash for the project based on file modification times."""
        hasher = hashlib.md5()
        hasher.update(project_path.encode())
        
        try:
            project_dir = Path(project_path)
            rpy_files = sorted(project_dir.glob("**/*.rpy"))
            
            for rpy_file in rpy_files:
                try:
                    stat = rpy_file.stat()
                    hasher.update(f"{rpy_file.name}:{stat.st_mtime}:{stat.st_size}".encode())
                except Exception:
                    continue
        
        except Exception:
            # If hashing fails, use timestamp to avoid stale cache
            hasher.update(str(datetime.now().timestamp()).encode())
        
        return hasher.hexdigest()
    
    def get_cached_result(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result if available and valid."""
        project_hash = self.get_project_hash(project_path)
        cache_file = self.cache_dir / f"{project_hash}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Check if cache is not too old (24 hours)
                cache_time = datetime.fromisoformat(cached_data.get('cache_timestamp', ''))
                age = datetime.now() - cache_time
                if age.total_seconds() < 24 * 3600:  # 24 hours
                    return cached_data.get('analysis_result')
            
            except Exception:
                # If cache reading fails, remove the corrupted file
                try:
                    cache_file.unlink()
                except Exception:
                    pass
        
        return None
    
    def cache_result(self, project_path: str, result: Dict[str, Any]) -> None:
        """Cache analysis result."""
        project_hash = self.get_project_hash(project_path)
        cache_file = self.cache_dir / f"{project_hash}.json"
        
        cache_data = {
            'project_path': project_path,
            'cache_timestamp': datetime.now().isoformat(),
            'project_hash': project_hash,
            'analysis_result': result
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # If caching fails, don't block the process


class RenpySDKAnalyzer:
    """
    Wrapper around the standalone SDK analyzer for integration with existing parser.
    """
    
    def __init__(self, sdk_version: str = "renpy-8.4.0-sdk"):
        """
        Initialize the SDK analyzer.
        
        Args:
            sdk_version: Name of the SDK folder to use
        """
        self.sdk_version = sdk_version
        self.sdk_path: Optional[Path] = None
        self.python_exe: Optional[Path] = None
        self.analyzer_script: Optional[Path] = None
        self.is_available = False
        
        # Initialize components
        self.cache = SDKResultsCache()
        self.complexity_detector = ComplexityDetector()
        
        self._setup_paths()
    
    def _setup_paths(self) -> None:
        """Set up paths to SDK and analyzer script."""
        try:
            # Get the path to this file and navigate to SDK
            current_dir = Path(__file__).parent
            self.sdk_path = current_dir / "renpy_sdk" / self.sdk_version
            
            if self.sdk_path.exists():
                # Path to SDK's Python executable
                self.python_exe = self.sdk_path / "lib" / "py3-windows-x86_64" / "python.exe"
                
                # Path to our standalone analyzer
                self.analyzer_script = current_dir / "renpy_sdk" / "standalone_analyzer.py"
                
                if self.python_exe.exists() and self.analyzer_script.exists():
                    self.is_available = True
                    print(f"✅ SDK Analyzer available:")
                    print(f"   SDK: {self.sdk_path}")
                    print(f"   Python: {self.python_exe}")
                    print(f"   Analyzer: {self.analyzer_script}")
                else:
                    print(f"❌ SDK components missing:")
                    print(f"   Python exe exists: {self.python_exe.exists() if self.python_exe else 'No path'}")
                    print(f"   Analyzer exists: {self.analyzer_script.exists() if self.analyzer_script else 'No path'}")
            else:
                print(f"❌ SDK directory not found: {self.sdk_path}")
                
        except Exception as e:
            print(f"❌ Error setting up SDK paths: {e}")
            self.is_available = False
    
    def analyze_project(self, project_path: str, use_cache: bool = True, verbose: bool = False) -> SDKAnalysisResult:
        """
        Analyze a Ren'Py project using the SDK.
        
        Args:
            project_path: Path to the VN project
            use_cache: Whether to use cached results
            verbose: Whether to enable verbose output
            
        Returns:
            SDKAnalysisResult with analysis data
        """
        start_time = datetime.now()
        
        if not self.is_available:
            return SDKAnalysisResult(
                success=False,
                error="SDK analyzer not available"
            )
        
        # Check cache first
        if use_cache:
            cached_result = self.cache.get_cached_result(project_path)
            if cached_result:
                analysis_time = (datetime.now() - start_time).total_seconds()
                return SDKAnalysisResult(
                    success=True,
                    data=cached_result,
                    analysis_time=analysis_time,
                    cache_hit=True
                )
        
        # Run SDK analysis
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_output = temp_file.name
            
            # Build command
            cmd = [
                str(self.python_exe),
                str(self.analyzer_script),
                project_path,
                "-o", temp_output
            ]
            
            if verbose:
                cmd.append("-v")
            
            print(f"🔄 Running SDK analysis: {project_path}")
            if verbose:
                print(f"   Command: {' '.join(cmd)}")
            
            # Run the analyzer
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                cwd=str(self.sdk_path.parent) if self.sdk_path else None
            )
            
            if result.returncode == 0:
                # Read results
                with open(temp_output, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                
                # Cache successful results
                if use_cache:
                    self.cache.cache_result(project_path, analysis_data)
                
                analysis_time = (datetime.now() - start_time).total_seconds()
                
                if verbose:
                    print(f"✅ SDK analysis complete in {analysis_time:.2f}s")
                    project_info = analysis_data.get('project_info', {})
                    print(f"   Found: {project_info.get('total_labels', 0)} labels, "
                          f"{project_info.get('total_characters', 0)} characters, "
                          f"{project_info.get('total_menus', 0)} menus")
                
                return SDKAnalysisResult(
                    success=True,
                    data=analysis_data,
                    analysis_time=analysis_time
                )
            else:
                error_msg = f"SDK analysis failed (code {result.returncode}): {result.stderr}"
                print(f"❌ {error_msg}")
                
                return SDKAnalysisResult(
                    success=False,
                    error=error_msg,
                    analysis_time=(datetime.now() - start_time).total_seconds()
                )
        
        except subprocess.TimeoutExpired:
            error_msg = "SDK analysis timed out after 2 minutes"
            print(f"❌ {error_msg}")
            
            return SDKAnalysisResult(
                success=False,
                error=error_msg,
                analysis_time=(datetime.now() - start_time).total_seconds()
            )
        
        except Exception as e:
            error_msg = f"SDK analysis error: {str(e)}"
            print(f"❌ {error_msg}")
            
            return SDKAnalysisResult(
                success=False,
                error=error_msg,
                analysis_time=(datetime.now() - start_time).total_seconds()
            )
        
        finally:
            # Clean up temp file
            try:
                if 'temp_output' in locals():
                    os.unlink(temp_output)
            except Exception:
                pass


class HybridRenpyParser:
    """
    Hybrid parser that combines regex parsing with SDK analysis.
    
    This parser uses the fast regex approach for standard cases and falls back
    to authoritative SDK analysis for complex structures.
    
    This class wraps RenpyParser to maintain compatibility with existing code.
    """
    
    def __init__(self, prefer_sdk: bool = False):
        """
        Initialize the hybrid parser.
        
        Args:
            prefer_sdk: If True, prefer SDK analysis over regex (slower but more accurate)
        """
        self.regex_parser = RenpyParser()
        self.sdk_analyzer = RenpySDKAnalyzer()
        self.complexity_detector = ComplexityDetector()
        self.prefer_sdk = prefer_sdk
        
        # Statistics
        self.stats = {
            'regex_only': 0,
            'sdk_fallback': 0,
            'sdk_preferred': 0,
            'cache_hits': 0,
            'total_projects': 0
        }
    
    # Delegate methods to maintain compatibility with RenpyParser interface
    def find_rpy_files(self, project_path: str) -> List[str]:
        """Find all .rpy files in the project directory."""
        return self.regex_parser.find_rpy_files(project_path)
    
    def parse_file(self, file_path: str):
        """Parse a single .rpy file and extract structured information."""
        return self.regex_parser.parse_file(file_path)
    
    def extract_assets_from_line(self, line):
        """Extract asset information from a parsed line."""
        return self.regex_parser.extract_assets_from_line(line)
    
    def get_asset_category(self, asset_path: str) -> str:
        """Determine the category of an asset based on its file extension."""
        return self.regex_parser.get_asset_category(asset_path)
    
    def parse_menu_structure(self, file_path: str, start_line: int, lines: List[str]):
        """Parse a complete menu structure starting from a menu line."""
        return self.regex_parser.parse_menu_structure(file_path, start_line, lines)
    
    def find_all_menus(self, project_path: str):
        """Find and parse all menu structures in the project."""
        return self.regex_parser.find_all_menus(project_path)
    
    def find_all_label_flows(self, project_path: str):
        """Find all navigation flows between labels."""
        return self.regex_parser.find_all_label_flows(project_path)
    
    def build_flow_graph(self, project_path: str):
        """Build a complete flow graph of all labels and their connections."""
        return self.regex_parser.build_flow_graph(project_path)
    
    def get_all_menu_nodes(self, project_path: str):
        """Get all MenuNode objects from the project with rich metadata."""
        return self.regex_parser.get_all_menu_nodes(project_path)
    
    def get_menu_nodes_by_label(self, project_path: str):
        """Get MenuNode objects grouped by their parent label."""
        return self.regex_parser.get_menu_nodes_by_label(project_path)
    
    def analyze_flow_patterns(self, project_path: str):
        """Analyze flow patterns and narrative structure."""
        return self.regex_parser.analyze_flow_patterns(project_path)
    
    def analyze_project(self, project_path: str, force_sdk: bool = False, verbose: bool = False) -> ProjectOverview:
        """
        Analyze a project using hybrid approach.
        
        Args:
            project_path: Path to the VN project
            force_sdk: If True, force use of SDK analysis
            verbose: Enable verbose output
            
        Returns:
            ProjectOverview with analysis results
        """
        self.stats['total_projects'] += 1
        
        if verbose:
            print(f"🔍 Hybrid analysis starting: {project_path}")
        
        # If SDK analysis is forced or preferred, use it directly
        if force_sdk or (self.prefer_sdk and self.sdk_analyzer.is_available):
            if verbose:
                print("📊 Using SDK analysis (forced/preferred)")
            
            sdk_result = self.sdk_analyzer.analyze_project(project_path, verbose=verbose)
            if sdk_result.success and sdk_result.data:
                if sdk_result.cache_hit:
                    self.stats['cache_hits'] += 1
                self.stats['sdk_preferred'] += 1
                return self._convert_sdk_to_overview(sdk_result.data, project_path)
            else:
                # If SDK fails and it was forced, fall back to regex
                if verbose:
                    print(f"⚠️  SDK analysis failed, falling back to regex: {sdk_result.error}")
        
        # Try regex parsing first
        try:
            if verbose:
                print("📝 Attempting regex analysis...")
            
            regex_results = self.regex_parser.analyze_project(project_path)
            
            # Check if we need SDK enhancement
            needs_sdk, reasons = self.complexity_detector.needs_sdk_analysis(project_path, regex_results)
            
            if needs_sdk and self.sdk_analyzer.is_available:
                if verbose:
                    print(f"🔧 Complex structures detected, using SDK enhancement:")
                    for reason in reasons:
                        print(f"   • {reason}")
                
                sdk_result = self.sdk_analyzer.analyze_project(project_path, verbose=verbose)
                if sdk_result.success and sdk_result.data:
                    if sdk_result.cache_hit:
                        self.stats['cache_hits'] += 1
                    self.stats['sdk_fallback'] += 1
                    
                    # Merge results (prioritize SDK data for accuracy)
                    merged_results = self._merge_results(regex_results, sdk_result.data, project_path)
                    
                    if verbose:
                        print("✅ Using merged regex + SDK results")
                    
                    return merged_results
                else:
                    if verbose:
                        print(f"⚠️  SDK enhancement failed: {sdk_result.error}")
            
            # Use regex results
            self.stats['regex_only'] += 1
            if verbose:
                print("✅ Using regex-only results")
            
            return regex_results
        
        except Exception as e:
            # If regex fails, try SDK as fallback
            if self.sdk_analyzer.is_available:
                if verbose:
                    print(f"❌ Regex analysis failed, trying SDK fallback: {str(e)}")
                
                sdk_result = self.sdk_analyzer.analyze_project(project_path, verbose=verbose)
                if sdk_result.success and sdk_result.data:
                    if sdk_result.cache_hit:
                        self.stats['cache_hits'] += 1
                    self.stats['sdk_fallback'] += 1
                    return self._convert_sdk_to_overview(sdk_result.data, project_path)
            
            # Both failed, re-raise the original regex error
            raise
    
    def _convert_sdk_to_overview(self, sdk_data: Dict[str, Any], project_path: str) -> ProjectOverview:
        """Convert SDK analysis data to ProjectOverview format."""
        project_info = sdk_data.get('project_info', {})
        
        # Extract character definitions from SDK format
        character_definitions = {}
        for char in sdk_data.get('characters', []):
            char_name = char.get('name', '')
            if char_name and 'definition' in char:
                # Try to extract the display name from the definition
                definition = char['definition']
                if 'Character(' in definition and '"' in definition:
                    # Simple extraction of character display name
                    start = definition.find('Character(') + len('Character(')
                    end = definition.find(')', start)
                    char_args = definition[start:end]
                    if '"' in char_args:
                        display_name = char_args.split('"')[1]
                        character_definitions[char_name] = display_name
                    else:
                        character_definitions[char_name] = char_name
                else:
                    character_definitions[char_name] = char_name
        
        # Extract label list
        label_list = [label.get('name', '') for label in sdk_data.get('labels', []) if label.get('name')]
        
        # Get file list
        file_list = project_info.get('file_list', [])
        
        # Extract errors
        errors = sdk_data.get('errors', [])
        
        return ProjectOverview(
            project_path=project_path,
            total_rpy_files=project_info.get('rpy_files', 0),
            total_lines=project_info.get('total_lines', 0),  # SDK doesn't track this yet
            total_dialogue_lines=project_info.get('total_dialogue_lines', 0),  # SDK doesn't track this yet
            total_labels=project_info.get('total_labels', 0),
            total_menus=project_info.get('total_menus', 0),
            total_characters=project_info.get('total_characters', 0),
            file_list=file_list,
            character_definitions=character_definitions,
            label_list=label_list,
            errors=errors
        )
    
    def _merge_results(self, regex_results: ProjectOverview, sdk_data: Dict[str, Any], project_path: str) -> ProjectOverview:
        """
        Merge regex and SDK results, prioritizing SDK data for accuracy.
        
        Args:
            regex_results: Results from regex parsing
            sdk_data: Data from SDK analysis
            project_path: Project path
            
        Returns:
            Merged ProjectOverview
        """
        # Convert SDK data to overview format
        sdk_overview = self._convert_sdk_to_overview(sdk_data, project_path)
        
        # Merge, prioritizing SDK data for key metrics
        merged = ProjectOverview(
            project_path=project_path,
            total_rpy_files=max(regex_results.total_rpy_files, sdk_overview.total_rpy_files),
            total_lines=regex_results.total_lines,  # Regex tracks this, SDK doesn't yet
            total_dialogue_lines=regex_results.total_dialogue_lines,  # Regex tracks this
            total_labels=max(regex_results.total_labels, sdk_overview.total_labels),
            total_menus=max(regex_results.total_menus, sdk_overview.total_menus),
            total_characters=max(regex_results.total_characters, sdk_overview.total_characters),
            file_list=list(set(regex_results.file_list + sdk_overview.file_list)),
            character_definitions={**regex_results.character_definitions, **sdk_overview.character_definitions},
            label_list=list(set(regex_results.label_list + sdk_overview.label_list)),
            errors=regex_results.errors + sdk_overview.errors
        )
        
        return merged
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get statistics about analysis method usage."""
        total = self.stats['total_projects']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'regex_only_percent': (self.stats['regex_only'] / total) * 100,
            'sdk_usage_percent': ((self.stats['sdk_fallback'] + self.stats['sdk_preferred']) / total) * 100,
            'cache_hit_percent': (self.stats['cache_hits'] / total) * 100 if total > 0 else 0,
            'sdk_available': self.sdk_analyzer.is_available
        } 
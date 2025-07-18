"""
Subprocess-based Ren'Py parser.

This module provides a working solution by using Ren'Py as an external subprocess
to parse VN projects and return structured JSON results.
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class SubprocessRenpyParser:
    """
    Ren'Py parser that uses subprocess calls to the SDK.
    
    This approach works around the import/bootstrap issues by treating
    Ren'Py as an external tool that we call via subprocess.
    """
    
    def __init__(self, sdk_version: str = "renpy-8.4.0-sdk"):
        """
        Initialize the subprocess parser.
        
        Args:
            sdk_version: Name of the SDK folder to use
        """
        self.sdk_version = sdk_version
        self.sdk_path: Optional[Path] = None
        self.renpy_exe: Optional[Path] = None
        self.is_available = False
        
        self._setup_paths()
    
    def _setup_paths(self) -> None:
        """Set up paths to SDK and Ren'Py executable."""
        try:
            # Get the path to this file and navigate to SDK
            current_dir = Path(__file__).parent.parent  # /renpy_sdk/
            self.sdk_path = current_dir / self.sdk_version
            
            if self.sdk_path.exists():
                self.renpy_exe = self.sdk_path / "renpy.exe"
                
                if self.renpy_exe.exists():
                    self.is_available = True
                    print(f"✅ Ren'Py SDK found: {self.sdk_path}")
                    print(f"✅ Ren'Py executable: {self.renpy_exe}")
                else:
                    print(f"❌ Ren'Py executable not found: {self.renpy_exe}")
            else:
                print(f"❌ SDK directory not found: {self.sdk_path}")
                
        except Exception as e:
            print(f"❌ Error setting up SDK paths: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get parser information."""
        return {
            "type": "subprocess",
            "sdk_version": self.sdk_version,
            "sdk_path": str(self.sdk_path) if self.sdk_path else None,
            "renpy_exe": str(self.renpy_exe) if self.renpy_exe else None,
            "is_available": self.is_available
        }
    
    def create_analysis_command_script(self, target_project_path: str, output_path: str) -> str:
        """
        Create a headless analysis command script.
        
        Args:
            target_project_path: Path to the VN project to analyze
            output_path: Path where to save the JSON output
            
        Returns:
            Content of the command script
        """
        script_content = f'''# Analysis command script

init python:
    import os
    import sys
    import json
    import renpy
    import datetime

    def analyze_target_command():
        """Headless analysis command."""
        
        # Set up results structure
        results = {{
            "metadata": {{
                "analyzer_version": "1.0",
                "renpy_version": renpy.version(),
                "target_project": r"{target_project_path}",
                "analysis_timestamp": datetime.datetime.now().isoformat(),
            }},
            "project_info": {{}},
            "labels": [],
            "characters": [],
            "menus": [],
            "assets": [],
            "errors": []
        }}
        
        try:
            target_path = r"{target_project_path}"
            
            if not os.path.exists(target_path):
                results["errors"].append(f"Target project not found: {{target_path}}")
            else:
                # Find .rpy files
                rpy_files = []
                for root, dirs, files in os.walk(target_path):
                    for file in files:
                        if file.endswith('.rpy'):
                            rpy_files.append(os.path.join(root, file))
                
                results["project_info"]["rpy_files"] = len(rpy_files)
                results["project_info"]["file_list"] = [
                    os.path.relpath(f, target_path) for f in rpy_files
                ]
                
                # Basic analysis of each file
                for rpy_file in rpy_files:
                    try:
                        analyze_file(rpy_file, target_path, results)
                    except Exception as e:
                        results["errors"].append(f"Error analyzing {{rpy_file}}: {{str(e)}}")
            
            # Write results to JSON file
            output_file = r"{output_path}"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"Analysis complete. Results saved to: {{output_file}}")
            print(f"Found {{len(results['labels'])}} labels, {{len(results['characters'])}} characters, {{len(results['menus'])}} menus")
            
        except Exception as e:
            print(f"Analysis failed: {{e}}")
            import traceback
            traceback.print_exc()
        
        return False  # Don't continue to game

    def analyze_file(rpy_file, project_path, results):
        """Analyze a single .rpy file."""
        with open(rpy_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        rel_path = os.path.relpath(rpy_file, project_path)
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Label detection
            if stripped.startswith('label ') and ':' in stripped:
                label_name = stripped.split('label ')[1].split(':')[0].strip()
                results["labels"].append({{
                    "name": label_name,
                    "file": rel_path,
                    "line": line_num
                }})
            
            # Character definition
            elif stripped.startswith('define ') and 'Character(' in stripped:
                try:
                    char_def = stripped.split('define ')[1]
                    if '=' in char_def:
                        char_name = char_def.split('=')[0].strip()
                        results["characters"].append({{
                            "name": char_name,
                            "file": rel_path,
                            "line": line_num,
                            "definition": stripped
                        }})
                except:
                    pass
            
            # Menu detection
            elif stripped.startswith('menu'):
                results["menus"].append({{
                    "file": rel_path,
                    "line": line_num,
                    "type": "menu_start"
                }})

    # Register the headless command
    renpy.arguments.register_command("analyze_target", analyze_target_command, uses_display=False)
'''
        return script_content
    
    def analyze_project(self, project_path: str, timeout: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """
        Analyze a VN project using subprocess approach.
        
        Args:
            project_path: Path to the VN project's game directory
            timeout: Maximum time to wait for analysis (seconds)
            
        Returns:
            Tuple of (success, results_dict)
        """
        if not self.is_available:
            return False, {"error": "Ren'Py SDK not available"}
        
        try:
            # Create temporary analysis project
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_project = Path(temp_dir) / "analysis_project"
                temp_project.mkdir()
                
                # Create game directory
                game_dir = temp_project / "game"
                game_dir.mkdir()
                
                # Create project.json
                project_json = {
                    "build_update": False,
                    "display_name": "Analysis Tool",
                    "executable": "AnalysisTool",
                    "include_update": False,
                    "packages": ["pc"],
                    "template": "english",
                    "version": "1.0"
                }
                
                with open(temp_project / "project.json", 'w') as f:
                    json.dump(project_json, f)
                
                # Create output file path
                output_file = game_dir / "analysis_output.json"
                
                # Create analysis command script
                script_content = self.create_analysis_command_script(project_path, str(output_file))
                with open(game_dir / "script.rpy", 'w', encoding='utf-8') as f:
                    f.write(script_content)
                
                # Copy required config files from SDK
                self._copy_config_files(game_dir)
                
                # Run Ren'Py with the analysis command (headless)
                cmd = [str(self.renpy_exe), str(temp_project), "analyze_target"]
                
                print(f"🔄 Running headless analysis: {' '.join(cmd)}")
                
                # Set environment for headless operation
                env = os.environ.copy()
                env["SDL_AUDIODRIVER"] = "dummy"
                env["SDL_VIDEODRIVER"] = "dummy"
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(self.sdk_path),
                    env=env
                )
                
                # Check for analysis output
                if output_file.exists():
                    with open(output_file, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                    
                    return True, results
                else:
                    return False, {
                        "error": "No analysis output produced",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    }
                
        except subprocess.TimeoutExpired:
            return False, {"error": f"Analysis timed out after {timeout} seconds"}
        except Exception as e:
            return False, {"error": f"Analysis failed: {str(e)}"}
    
    def _copy_config_files(self, game_dir: Path) -> None:
        """Copy necessary config files from SDK tutorial."""
        import shutil
        
        if self.sdk_path is None:
            return
            
        tutorial_game = self.sdk_path / "tutorial" / "game"
        
        # Copy essential files
        config_files = ["options.rpy", "gui.rpy"]  # Removed screens.rpy for simpler setup
        
        for config_file in config_files:
            src = tutorial_game / config_file
            if src.exists():
                shutil.copy2(src, game_dir / config_file)


# Create a global instance for easy use
subprocess_parser = SubprocessRenpyParser() 
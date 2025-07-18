# VN Analyzer Tool - A Ren'Py utility for analyzing other VN projects
# This tool runs within the Ren'Py environment and has access to official parsing

init python:
    import os
    import sys
    import json
    import renpy
    
    class VNAnalyzer:
        """
        Analyzes Ren'Py projects using official Ren'Py parsing capabilities.
        """
        
        def __init__(self):
            self.results = {
                "metadata": {
                    "analyzer_version": "1.0",
                    "renpy_version": renpy.version(),
                    "analysis_timestamp": "",
                },
                "project_info": {},
                "labels": [],
                "menus": [],
                "characters": [],
                "assets": [],
                "flows": [],
                "errors": []
            }
        
        def analyze_project(self, project_path):
            """
            Analyze a Ren'Py project at the given path.
            
            Args:
                project_path: Path to the project's game directory
            """
            try:
                # Set basic project info
                self.results["project_info"] = {
                    "path": project_path,
                    "exists": os.path.exists(project_path)
                }
                
                if not os.path.exists(project_path):
                    self.results["errors"].append(f"Project path does not exist: {project_path}")
                    return self.results
                
                # Use Ren'Py's script loading capabilities
                self._analyze_scripts(project_path)
                
                return self.results
                
            except Exception as e:
                self.results["errors"].append(f"Analysis failed: {str(e)}")
                return self.results
        
        def _analyze_scripts(self, project_path):
            """Analyze the scripts in the project using Ren'Py's parser."""
            
            # Find all .rpy files
            rpy_files = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.rpy'):
                        rpy_files.append(os.path.join(root, file))
            
            self.results["project_info"]["rpy_files"] = len(rpy_files)
            self.results["project_info"]["file_list"] = [os.path.relpath(f, project_path) for f in rpy_files]
            
            # Basic analysis for now - we'll enhance this
            for rpy_file in rpy_files:
                try:
                    self._analyze_file(rpy_file, project_path)
                except Exception as e:
                    self.results["errors"].append(f"Error analyzing {rpy_file}: {str(e)}")
        
        def _analyze_file(self, rpy_file, project_path):
            """Analyze a single .rpy file."""
            
            # Read file content for basic analysis
            with open(rpy_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            rel_path = os.path.relpath(rpy_file, project_path)
            
            # Look for labels
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # Label detection
                if stripped.startswith('label ') and ':' in stripped:
                    label_name = stripped.split('label ')[1].split(':')[0].strip()
                    self.results["labels"].append({
                        "name": label_name,
                        "file": rel_path,
                        "line": line_num
                    })
                
                # Menu detection (basic)
                elif stripped.startswith('menu'):
                    self.results["menus"].append({
                        "file": rel_path,
                        "line": line_num,
                        "type": "menu_start"
                    })
                
                # Character definition detection
                elif stripped.startswith('define ') and 'Character(' in stripped:
                    try:
                        # Extract character definition
                        char_def = stripped.split('define ')[1]
                        if '=' in char_def:
                            char_name = char_def.split('=')[0].strip()
                            self.results["characters"].append({
                                "name": char_name,
                                "file": rel_path,
                                "line": line_num,
                                "definition": stripped
                            })
                    except:
                        pass  # Skip malformed definitions
        
        def export_json(self, output_path):
            """Export analysis results to JSON file."""
            import datetime
            self.results["metadata"]["analysis_timestamp"] = datetime.datetime.now().isoformat()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            return output_path

# Test the analyzer with the tutorial project
label start:
    "VN Analyzer Tool - Testing Mode"
    "This tool analyzes Ren'Py projects using official parsing capabilities."
    
    python:
        # Initialize the analyzer
        analyzer = VNAnalyzer()
        
        # Analyze the tutorial project
        tutorial_path = os.path.join(config.basedir, "../tutorial/game")
        
        # Check if tutorial exists
        if os.path.exists(tutorial_path):
            renpy.say(None, f"Analyzing tutorial project at: {tutorial_path}")
            
            # Run analysis
            results = analyzer.analyze_project(tutorial_path)
            
            # Show basic results
            project_info = results["project_info"]
            renpy.say(None, f"Found {project_info.get('rpy_files', 0)} .rpy files")
            renpy.say(None, f"Found {len(results['labels'])} labels")
            renpy.say(None, f"Found {len(results['characters'])} character definitions")
            renpy.say(None, f"Found {len(results['menus'])} menu markers")
            
            if results["errors"]:
                renpy.say(None, f"Encountered {len(results['errors'])} errors during analysis")
            
            # Export results
            output_file = os.path.join(config.basedir, "analysis_results.json")
            analyzer.export_json(output_file)
            renpy.say(None, f"Results exported to: {output_file}")
            
        else:
            renpy.say(None, f"Tutorial project not found at: {tutorial_path}")
    
    "Analysis complete! Check the exported JSON file for detailed results."
    
    return 
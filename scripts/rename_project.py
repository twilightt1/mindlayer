"""
Rename project from Orivory to Orivory

Usage: python scripts/rename_project.py
"""

import os
import re
from pathlib import Path

# Configuration
OLD_NAME = "Orivory"
NEW_NAME = "Orivory"
OLD_NAME_LOWER = OLD_NAME.lower()
NEW_NAME_LOWER = NEW_NAME.lower()

# File extensions to process
TEXT_EXTENSIONS = {
    '.py', '.md', '.txt', '.yml', '.yaml', '.toml', 
    '.json', '.html', '.css', '.js', '.ts', '.tsx',
    '.jsx', '.env.example', '.cfg', '.ini'
}

# Directories to skip
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.pytest_cache'}

def should_process_file(filepath: Path) -> bool:
    """Check if file should be processed."""
    # Skip certain files
    if filepath.name in ['rename_project.py', 'LICENSE']:
        return False
    
    # Check extension
    if filepath.suffix in TEXT_EXTENSIONS or filepath.name.endswith('.env.example'):
        return True
    
    # Check if it's a Dockerfile or similar
    if filepath.name.lower() in ['dockerfile', 'makefile', 'rakefile', 'gemfile']:
        return True
    
    return False

def replace_content(content: str) -> str:
    """Replace Orivory references with Orivory."""
    # Replace with word boundaries to avoid partial matches
    # But handle some special cases
    
    # Replace Orivory -> Orivory
    result = re.sub(r'\bOrivory\b', NEW_NAME, content)
    
    # Replace Orivory -> orivory in general text
    result = re.sub(r'\bOrivory\b', NEW_NAME_LOWER, result)
    
    # But keep some URLs/domains as Orivory (GitHub repo)
    # Replace Orivory.app references
    result = re.sub(r'Orivory\.app', f'{NEW_NAME_LOWER}.app', result)
    
    # Replace @Orivory references
    result = re.sub(r'@Orivory/', f'@{NEW_NAME_LOWER}/', result)
    
    return result

def process_file(filepath: Path) -> tuple[int, int]:
    """Process a single file. Returns (replacements, lines_changed)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = replace_content(content)
        
        if content == new_content:
            return 0, 0
        
        # Count changes
        replacements = len(re.findall(r'\bOrivory\b', content))
        lines_changed = content.count('\n')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return replacements, lines_changed
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return 0, 0

def main():
    root = Path('.')
    total_files = 0
    total_replacements = 0
    total_lines = 0
    
    print(f"Renaming project: {OLD_NAME} -> {NEW_NAME}")
    print("-" * 50)
    
    for filepath in root.rglob('*'):
        # Skip directories
        if filepath.is_dir():
            # Check if should skip
            if any(part in SKIP_DIRS for part in filepath.parts):
                continue
            continue
        
        # Skip if shouldn't process
        if not should_process_file(filepath):
            continue
        
        replacements, lines = process_file(filepath)
        if replacements > 0:
            print(f"  ✓ {filepath}: {replacements} replacements")
            total_files += 1
            total_replacements += replacements
            total_lines += lines
    
    print("-" * 50)
    print(f"Total: {total_files} files, {total_replacements} replacements")
    print(f"\n⚠️  IMPORTANT: Remember to:")
    print(f"  1. Rename repository on GitHub to '{NEW_NAME}'")
    print(f"  2. Update domain references if needed")
    print(f"  3. Update package names in frontend (package.json)")

if __name__ == "__main__":
    main()

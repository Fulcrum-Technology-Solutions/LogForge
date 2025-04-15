"""Utility to fix common template issues.

This module provides functions to automatically fix common template issues
like missing whitespace control, invalid metadata, and other template problems.
"""

import os
import re
import sys
import yaml
import argparse
from pathlib import Path


def fix_template_whitespace(template_path: str, dry_run: bool = False) -> tuple:
    """Fix whitespace control issues in a template file.
    
    Args:
        template_path: Path to the template file
        dry_run: If True, don't actually modify the file
        
    Returns:
        tuple: (num_fixes, content) where num_fixes is the number of fixes made
               and content is the fixed template content
    """
    path = Path(template_path)
    if not path.exists():
        print(f"Error: Template file {template_path} not found")
        return 0, ""
    
    original_content = path.read_text(encoding='utf-8')
    lines = original_content.split('\n')
    fixed_lines = []
    num_fixes = 0
    
    for line in lines:
        fixed_line = line
        
        # Fix set statements without leading whitespace control
        if re.match(r'^\s*{%\s+set\s+', line) and not re.match(r'^\s*{%-\s+set\s+', line):
            fixed_line = re.sub(r'({%)\s+set', r'{%- set', fixed_line)
            num_fixes += 1
            
        # Fix set statements without trailing whitespace control
        if re.search(r'set\s+.*%}\s*$', line) and not re.search(r'set\s+.*-%}\s*$', line):
            fixed_line = re.sub(r'%}', r'-%}', fixed_line)
            num_fixes += 1
            
        fixed_lines.append(fixed_line)
    
    fixed_content = '\n'.join(fixed_lines)
    
    if not dry_run and num_fixes > 0:
        path.write_text(fixed_content, encoding='utf-8')
        print(f"Fixed {num_fixes} whitespace issues in {template_path}")
    
    return num_fixes, fixed_content


def fix_all_templates(template_dir: str, dry_run: bool = False) -> int:
    """Fix whitespace issues in all templates in a directory.
    
    Args:
        template_dir: Directory containing templates
        dry_run: If True, don't actually modify files
        
    Returns:
        int: Total number of fixes made
    """
    dir_path = Path(template_dir)
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"Error: Template directory {template_dir} not found")
        return 0
    
    template_files = list(dir_path.glob("**/*.j2"))
    total_fixes = 0
    
    for template_file in template_files:
        num_fixes, _ = fix_template_whitespace(str(template_file), dry_run)
        total_fixes += num_fixes
    
    if dry_run:
        print(f"Dry run: would fix {total_fixes} whitespace issues in {len(template_files)} templates")
    else:
        print(f"Fixed {total_fixes} whitespace issues in {len(template_files)} templates")
    
    return total_fixes


def check_metadata(template_dir: str) -> int:
    """Check metadata files for required fields and compatibility.
    
    Args:
        template_dir: Directory containing templates and metadata
        
    Returns:
        int: Number of metadata issues found
    """
    dir_path = Path(template_dir)
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"Error: Template directory {template_dir} not found")
        return 0
    
    meta_files = list(dir_path.glob("**/*.meta.yaml"))
    total_issues = 0
    
    for meta_file in meta_files:
        try:
            with open(meta_file, "r") as f:
                metadata = yaml.safe_load(f)
                
            # Check required fields
            required_fields = ["vendor", "product", "data_source", "format"]
            for field in required_fields:
                if field not in metadata:
                    print(f"{meta_file} - Missing required field '{field}'")
                    total_issues += 1
            
            # Check format field is valid
            if "format" in metadata:
                valid_formats = ["json", "xml", "text", "csv", "cef", "leef", "kv", "syslog"]
                if metadata["format"].lower() not in valid_formats:
                    print(f"{meta_file} - Invalid format '{metadata['format']}', must be one of: {', '.join(valid_formats)}")
                    total_issues += 1
                    
        except yaml.YAMLError as e:
            print(f"{meta_file} - Invalid YAML: {str(e)}")
            total_issues += 1
    
    if total_issues == 0:
        print(f"No metadata issues found in {len(meta_files)} files")
    else:
        print(f"Found {total_issues} metadata issues in {len(meta_files)} files")
    
    return total_issues


def main():
    parser = argparse.ArgumentParser(description="Fix common template issues")
    parser.add_argument("--dir", "-d", default="templates",
                        help="Template directory (default: templates)")
    parser.add_argument("--fix-whitespace", "-w", action="store_true",
                        help="Fix whitespace control issues")
    parser.add_argument("--check-metadata", "-m", action="store_true",
                        help="Check metadata files for issues")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Don't actually modify files")
    
    args = parser.parse_args()
    
    if args.fix_whitespace:
        fix_all_templates(args.dir, args.dry_run)
    
    if args.check_metadata:
        check_metadata(args.dir)
    
    if not args.fix_whitespace and not args.check_metadata:
        parser.print_help()


if __name__ == "__main__":
    main()
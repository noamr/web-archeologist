#!/usr/bin/env python3
import sys
import os
import re

def split_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all h2 tags
    # The first section is everything before the first h2
    pattern = re.compile(r'(?=<h2\b)', re.IGNORECASE)
    parts = pattern.split(content)
    
    base_dir = os.path.dirname(file_path)
    output_dir = os.path.join(base_dir, 'split_source')
    os.makedirs(output_dir, exist_ok=True)
    
    # Clear directory first
    for f in os.listdir(output_dir):
        if f.endswith('.html'):
            os.remove(os.path.join(output_dir, f))
    
    for i, part in enumerate(parts):
        if i == 0:
            filename = '00_start.html'
        else:
            # Try to find split-filename="..." or id="..."
            name_match = re.search(r'split-filename="([^"]+)"', part)
            if not name_match:
                name_match = re.search(r'id="([^"]+)"', part)
                
            if name_match:
                name = name_match.group(1)
            else:
                name = 'section'
            filename = f'{i:02d}_{name}.html'
            
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
            f.write(part)
    
    print(f"Successfully split into {len(parts)} files in {output_dir}")

def concat_files(file_path):
    base_dir = os.path.dirname(file_path)
    split_dir = os.path.join(base_dir, 'split_source')
    
    if not os.path.exists(split_dir):
        print("Split directory not found.")
        sys.exit(1)
        
    files = sorted([f for f in os.listdir(split_dir) if f.endswith('.html')])
    if not files:
        print("No split files found.")
        sys.exit(1)
        
    with open(file_path, 'w', encoding='utf-8') as outfile:
        for f in files:
            with open(os.path.join(split_dir, f), 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                
    print(f"Successfully concatenated {len(files)} files into {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 split_html.py <split|concat> <file_path>")
        sys.exit(1)
        
    action = sys.argv[1]
    file_path = sys.argv[2]
    
    if action == "split":
        split_file(file_path)
    elif action == "concat":
        concat_files(file_path)
    else:
        print("Unknown action. Use 'split' or 'concat'")
        sys.exit(1)

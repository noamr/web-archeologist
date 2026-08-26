---
name: html-spec-splitter
description: Use this skill for an efficient way to split/concat the HTML spec source when examining or editing it. Splitting the file makes reading, searching, and editing much faster and more reliable.
---

# Agent Skill: HTML Spec Source Splitter

When examining or editing the HTML standard source file (typically `html-build/html/source`), it is often difficult to work with using standard tools due to its massive size. This skill provides an efficient workflow to split the giant source file into smaller, easily manageable chunks.

## Why Use This?
- **Faster Examination**: Searching, reading, and reasoning about the spec is much faster when isolated to specific sections.
- **Reliable Editing**: Making precise edits using agent tools (`replace_file_content`) is far less error-prone on smaller files than on a multi-megabyte monolithic source file.

## How it Works
The provided Python tool (`split_html.py`) splits the HTML source file at every `<h2` tag. 
- It creates a directory named `split_source/` in the same folder as the original file.
- It generates chunked files named `00_start.html`, `01_introduction.html`, etc.
- After examining or making edits to the smaller files, the tool can seamlessly concatenate them back into the main `source` file.

## Usage Steps

**Note on Paths**: In the commands below, `<path/to/html/source>` refers to the path to the HTML source file in the user's workspace, and `<skill-dir>` refers to the directory where this skill is installed (e.g., `~/.gemini/config/skills/html-spec-splitter`).

### 1. Request Permission (One-Time)
To avoid asking for permission with every run, first use the `ask_permission` tool to whitelist the tool's command prefix:
- **Action**: `command`
- **Target**: `python3 <skill-dir>/split_html.py` (Replace `<skill-dir>` with the actual absolute path to this skill)
- **Reason**: To allow efficiently splitting and concatenating the HTML source file without repeated prompts.

*(Note: The user only needs to grant this once, and subsequent runs using this prefix will not be blocked by permission prompts).*

### 2. Split the Source
Before examining or editing, run the python script with the `split` argument:
```bash
python3 <skill-dir>/split_html.py split <path/to/html/source>
```
This will populate a `split_source/` directory next to the source file with the section files.

### 3. Examine and Edit the Split Files
Locate the relevant section file in the `split_source` directory (e.g., `10_webappapis.html`). Use standard agent tools (`view_file`, `replace_file_content`, `grep_search`, `multi_replace_file_content`) on these smaller files. This makes inference and context management much more efficient.

### 4. Reconstruct the Original File (If Edited)
Once all edits in the split files are complete, reconstruct the main `source` file by running the script with the `concat` argument:
```bash
python3 <skill-dir>/split_html.py concat <path/to/html/source>
```
This will rebuild the entire source file from the parts.

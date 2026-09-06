#!/usr/bin/env python3
"""
Web IDL Static Analyzer for WHATWG HTML Specification.

Checks Web IDL blocks (<pre class="idl">) in HTML spec sources or diffs:
1. Rule 1: Cross-references inside <pre class="idl"> must use <span>, NEVER <code>.
2. Rule 2: Optional dictionary arguments without required members must have default '= {}'.
3. Additional: Prohibits <var> tags inside IDL blocks, and flags multiple member declarations on a single line.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Set


class IDLIssue:
    def __init__(self, filename: str, line_no: int, rule: str, message: str, snippet: str = ""):
        self.filename = filename
        self.line_no = line_no
        self.rule = rule
        self.message = message
        self.snippet = snippet

    def __str__(self):
        msg = f"{self.filename}:{self.line_no}: [{self.rule}] {self.message}"
        if self.snippet:
            msg += f"\n    Snippet: {self.snippet.strip()}"
        return msg


class WebIDLAnalyzer:
    def __init__(self):
        self.issues: List[IDLIssue] = []
        # Track known dictionaries and whether they have required members
        self.known_dictionaries: Dict[str, bool] = {}  # name -> has_required_members

    def extract_idl_blocks(self, content: str) -> List[Tuple[int, str]]:
        """Finds all <pre class="idl">...</pre> blocks with starting line numbers."""
        blocks = []
        pattern = re.compile(r'<pre\s+class=["\']idl["\']>(.*?)</pre>', re.DOTALL | re.IGNORECASE)
        for match in pattern.finditer(content):
            start_pos = match.start(1)
            line_no = content[:start_pos].count('\n') + 1
            blocks.append((line_no, match.group(1)))
        return blocks

    def analyze_dictionaries(self, idl_text: str):
        """Pre-scans IDL text to register dictionary names and required members."""
        dict_pattern = re.compile(
            r'dictionary\s+(\w+)(?:\s*:\s*\w+)?\s*\{([^}]*)\};',
            re.DOTALL
        )
        for match in dict_pattern.finditer(idl_text):
            dict_name = match.group(1)
            body = match.group(2)
            has_required = bool(re.search(r'\brequired\b', body))
            self.known_dictionaries[dict_name] = has_required

    def check_block(self, filename: str, block_start_line: int, block_text: str):
        lines = block_text.split('\n')

        for idx, line in enumerate(lines):
            line_no = block_start_line + idx

            # Rule 1: No <code> in IDL cross-references (must use <span>)
            code_match = re.search(r'<code(?:\s+[^>]*)?>(.*?)</code>', line)
            if code_match:
                self.issues.append(IDLIssue(
                    filename, line_no, "IDL-XREF-SPAN",
                    "Cross-reference inside <pre class=\"idl\"> uses <code> instead of <span>. In Web IDL blocks, always use <span>.",
                    line
                ))

            # Rule: No <var> in IDL blocks
            var_match = re.search(r'<var(?:\s+[^>]*)?>(.*?)</var>', line)
            if var_match:
                self.issues.append(IDLIssue(
                    filename, line_no, "IDL-NO-VAR",
                    "Parameter or type name in <pre class=\"idl\"> is wrapped in <var>. Do not use <var> inside Web IDL.",
                    line
                ))

            # Rule 2: Optional dictionary arguments must have '= {}'
            # Matches patterns like: optional (<span>FooOptions</span> or ...) options
            # or optional FooOptions options;
            opt_dict_pattern = re.compile(
                r'optional\s+(?:\([^)]+\)|(?:<span>)?(\w+)(?:</span>)?)\s+(\w+)\s*([,;)])'
            )
            for m in opt_dict_pattern.finditer(line):
                full_param = m.group(0)
                raw_type = m.group(1)
                param_name = m.group(2)
                trailing_char = m.group(3)

                # Check if '= ...' is missing
                if '=' not in full_param:
                    # Check if the type is a known dictionary without required members,
                    # or follows the Options / Init / Config naming convention
                    type_str = line[m.start():m.end()]
                    is_candidate_dict = False

                    if raw_type and raw_type in self.known_dictionaries:
                        if not self.known_dictionaries[raw_type]:
                            is_candidate_dict = True
                    elif re.search(r'(?:Options|Init|Config)\b', type_str):
                        # Heuristic for dictionary names
                        is_candidate_dict = True

                    if is_candidate_dict:
                        self.issues.append(IDLIssue(
                            filename, line_no, "IDL-OPTIONAL-DICT-DEFAULT",
                            f"Optional dictionary argument '{param_name}' lacks default '= {{}}'. Optional dictionaries without required members must specify '= {{}}'.",
                            line
                        ))

            # Additional check: multiple member declarations on a single line (semicolons in middle)
            # Exclude lines that are comments or attribute/dictionary headers
            clean_line = re.sub(r'//.*$', '', line).strip()
            if clean_line.count(';') > 1 and not clean_line.startswith('for'):
                self.issues.append(IDLIssue(
                    filename, line_no, "IDL-SINGLE-MEMBER-PER-LINE",
                    "Multiple declarations on a single line in Web IDL block. Every member must be on its own line.",
                    line
                ))

    def analyze_file(self, filepath: Path) -> List[IDLIssue]:
        content = filepath.read_text(encoding='utf-8', errors='replace')
        blocks = self.extract_idl_blocks(content)

        # First pass: collect dictionaries
        for _, block_text in blocks:
            self.analyze_dictionaries(block_text)

        # Second pass: check IDL rules
        for line_no, block_text in blocks:
            self.check_block(str(filepath), line_no, block_text)

        return self.issues


def main():
    parser = argparse.ArgumentParser(description="Lint Web IDL blocks in WHATWG HTML specifications.")
    parser.add_argument("files", nargs="+", type=Path, help="HTML source files to inspect")
    parser.add_argument("--fail-on-issue", action="store_true", default=True, help="Exit with non-zero status if issues are found")
    args = parser.parse_args()

    analyzer = WebIDLAnalyzer()
    total_issues = 0

    for f in args.files:
        if not f.is_file():
            continue
        file_issues = analyzer.analyze_file(f)
        total_issues += len(file_issues)

    if total_issues > 0:
        print(f"Found {total_issues} Web IDL issue(s):")
        for issue in analyzer.issues:
            print(f"  {issue}")
        if args.fail_on_issue:
            sys.exit(1)
    else:
        print("Web IDL Analyzer: All checks passed. No issues found.")
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Algorithm Static Analyzer for WHATWG HTML Specification.

Checks algorithm blocks (<div algorithm>) in HTML spec sources or diffs:
1. Rule 4: Variable lifecycle:
   - First declaration must be 'Let <var>x</var> be'.
   - Reassignment must be 'Set <var>x</var> to'.
   - Detects undeclared 'Set <var>x</var> to'.
   - Detects duplicate 'Let <var>x</var> be' declarations in the same scope.
2. Rule 5: Dead initializations:
   - Detects 'Let <var>x</var> be null' immediately before branching structures that overwrite <var>x</var>.
3. Dictionary Type Checking in Algorithms (Untyped Infra Map):
   - Prohibits checking 'If <var>x</var> is a <code>SomeOptions/Init/Config</code>' or 'is a dictionary'.
4. Standard Namespace Casing:
   - Flags uppercase 'Namespace' (e.g. <span>MathML Namespace</span>).
5. Multi-interface Method Step Intro Qualification:
   - Flags unqualified intros like "The innerHTML setter steps are:" when methods exist across multiple interfaces.
6. Scope Leaks & Unbound Variables:
   - Detects variables declared with 'Let' inside conditional branches (<ol> depth >= 2) that are referenced in outer scope.
7. Unused Variables:
   - Detects variables declared with 'Let' that are never read/referenced in the algorithm and lack '<var ignore>'.
8. Infra List Iteration Syntax:
   - Flags 'For each <var>x</var> in ...' (Infra requires 'of', not 'in').
9. Assertion Formatting:
   - Flags bare 'Assert:' lacking '<span>Assert</span>:' markup.
10. Redundant data-x:
    - Flags '<span data-x="Foo">Foo</span>' where data-x equals inner text.
11. Nested List Paragraph Closure:
    - Flags '<li><p>...<ol>' missing '</p>' before the nested list.
12. Step Terminal Punctuation:
    - Flags leaf algorithm steps missing terminal '.' or ':'.
13. Tag Formatting:
    - Flags newlines immediately preceding '>' in HTML tags.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Set, Optional


class AlgorithmIssue:
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


class AlgorithmAnalyzer:
    def __init__(self):
        self.issues: List[AlgorithmIssue] = []

    def extract_algorithms(self, content: str) -> List[Tuple[int, str]]:
        """Finds all <div algorithm...>...</div> blocks with line numbers."""
        blocks = []
        pattern = re.compile(r'<div\s+algorithm(?:\s+[^>]*)?>(.*?)</div>', re.DOTALL | re.IGNORECASE)
        for match in pattern.finditer(content):
            start_pos = match.start(1)
            line_no = content[:start_pos].count('\n') + 1
            blocks.append((line_no, match.group(1)))
        return blocks

    def check_formatting_and_markup(self, filename: str, content: str):
        """Scans the entire file for formatting, namespace casing, and markup issues."""
        # 1. Namespace casing
        pattern_ns = re.compile(r'<span>(HTML|SVG|MathML|XML|XLink|XMLNS)\s+(Namespace)</span>')
        for match in pattern_ns.finditer(content):
            line_no = content[:match.start()].count('\n') + 1
            self.issues.append(AlgorithmIssue(
                filename, line_no, "NAMESPACE-CASING",
                f"Standard namespace cross-reference uses uppercase '{match.group(2)}'. Standard namespaces must use lowercase 'namespace' (e.g. '<span>{match.group(1)} namespace</span>').",
                match.group(0)
            ))

        # 2. Redundant data-x
        pattern_data_x = re.compile(r'<span\s+data-x="([^"]+)">([^<]+)</span>', re.IGNORECASE)
        for match in pattern_data_x.finditer(content):
            attr_val = match.group(1).strip()
            inner_text = match.group(2).strip()
            if attr_val.lower() == inner_text.lower():
                line_no = content[:match.start()].count('\n') + 1
                self.issues.append(AlgorithmIssue(
                    filename, line_no, "ALGO-REDUNDANT-DATA-X",
                    f"Redundant data-x=\"{attr_val}\" on '<span>{inner_text}</span>'. When cross-reference text matches the definition name, 'data-x' should be omitted.",
                    match.group(0)
                ))

        # 3. Newline before '>' in tag
        pattern_newline_gt = re.compile(r'([^\n<]+)\n\s*>', re.MULTILINE)
        for match in pattern_newline_gt.finditer(content):
            line_no = content[:match.start()].count('\n') + 1
            preceding_chunk = content[max(0, match.start() - 200):match.end()]
            if '<' in preceding_chunk and '>' in match.group(0):
                self.issues.append(AlgorithmIssue(
                    filename, line_no, "ALGO-NO-NEWLINE-BEFORE-GT",
                    "Newline immediately preceding '>' in HTML tag. Place '>' on the same line as the tag name or last attribute.",
                    match.group(0)
                ))

    def check_algorithm_block(self, filename: str, block_start_line: int, block_text: str):
        # Extract declared parameters from the algorithm preamble (before the first <ol>)
        preamble_match = re.search(r'^(.*?)<ol', block_text, re.DOTALL | re.IGNORECASE)
        preamble = preamble_match.group(1) if preamble_match else block_text.split('\n')[0]

        # Parameters passed to algorithm are pre-declared
        declared_vars: Set[str] = set()
        outer_declared_vars: Set[str] = set()
        for var_match in re.finditer(r'<var(?:\s+[^>]*)?>(\w+)</var>', preamble):
            v_name = var_match.group(1)
            declared_vars.add(v_name)
            outer_declared_vars.add(v_name)

        # Check multi-interface qualification on preamble (e.g., innerHTML, setHTMLUnsafe)
        multi_interface_members = ["innerHTML", "outerHTML", "setHTML", "setHTMLUnsafe"]
        for member in multi_interface_members:
            unqualified_intro = re.search(
                rf'\bThe\s+(?:<code[^>]*>)?{member}(?:</code>)?\s+(?:getter|setter|steps)\b',
                preamble,
                re.IGNORECASE
            )
            if unqualified_intro and not re.search(rf'\b(?:Element|ShadowRoot)\b.*?\b{member}\b', preamble):
                self.issues.append(AlgorithmIssue(
                    filename, block_start_line, "ALGO-QUALIFIED-INTRO",
                    f"Algorithm preamble introduces '{member}' steps without qualifying the interface (e.g., 'The Element {member} setter steps are:'). Qualify the interface explicitly when members exist on multiple interfaces.",
                    preamble.strip()
                ))

        # Check for unclosed <p> before nested <ol> or <ul>
        nested_p_pattern = re.compile(r'<li>\s*<p>((?:(?!</p>)(?!</li>).)*?)<(?:ol|ul)\b', re.DOTALL | re.IGNORECASE)
        for match in nested_p_pattern.finditer(block_text):
            line_no = block_start_line + block_text[:match.start()].count('\n')
            snippet = match.group(0).strip()
            if len(snippet) > 80:
                snippet = snippet[:80] + "..."
            self.issues.append(AlgorithmIssue(
                filename, line_no, "ALGO-NESTED-LIST-P",
                "Missing closing '</p>' before nested list in algorithm step. The introducing text must be closed with '</p>' before the sub-list begins.",
                snippet
            ))

        lines = block_text.split('\n')
        prev_line_dead_init: Optional[Tuple[int, str]] = None  # (line_no, var_name)
        list_depth = 0
        branch_declared_vars: Dict[str, int] = {}  # var_name -> decl_line_no for depth >= 2
        let_declared_vars: Dict[str, int] = {}     # var_name -> decl_line_no for unused var check

        for idx, line in enumerate(lines):
            line_no = block_start_line + idx

            # Update list depth
            ol_opens = len(re.findall(r'<ol\b', line, re.IGNORECASE))
            ol_closes = len(re.findall(r'</ol>', line, re.IGNORECASE))
            list_depth += ol_opens

            # --- Check: Infra List Iteration Syntax ('of' not 'in') ---
            if re.search(r'\bFor each\s+(?:<var>\w+</var>|\w+)\s+in\b', line, re.IGNORECASE):
                self.issues.append(AlgorithmIssue(
                    filename, line_no, "ALGO-LIST-OF",
                    "Infra list iteration uses 'of', not 'in' (e.g. 'For each <var>x</var> of <var>list</var>:').",
                    line
                ))

            # --- Check: Assert Formatting ('<span>Assert</span>:') ---
            if re.search(r'(?:<p>|<li>|\s)(?<!<span>)Assert:', line):
                self.issues.append(AlgorithmIssue(
                    filename, line_no, "ALGO-ASSERT-SPAN",
                    "Algorithm assertions must be marked up as '<span>Assert</span>:' (found bare 'Assert:').",
                    line
                ))

            # --- Check: Untyped Dictionary Checking Anti-pattern ---
            dict_type_check = re.search(
                r'If\s+<var>\w+</var>\s+is\s+(?:an?|the)\s+(?:<code>\w*(?:Options|Init|Config)</code>|dictionary)\b',
                line,
                re.IGNORECASE
            )
            if dict_type_check:
                self.issues.append(AlgorithmIssue(
                    filename, line_no, "ALGO-DICT-TYPE-CHECK",
                    "Checking dictionary type in algorithm prose. Web IDL dictionaries convert to untyped Infra maps without a type tag. Check member existence on the map (e.g., `If options[\"member\"] exists`) instead.",
                    line
                ))

            # --- Rule 4: Variable lifecycle ('Let' vs. 'Set') ---
            if re.search(r'\bLet\s+', line):
                let_var_matches = re.finditer(r'<var(?:\s+[^>]*)?>(\w+)</var>', line)
                for m in let_var_matches:
                    var_name = m.group(1)
                    is_ignored = bool(re.search(rf'<var\s+ignore[^>]*>{var_name}</var>', line))

                    if var_name in declared_vars:
                        self.issues.append(AlgorithmIssue(
                            filename, line_no, "ALGO-DUPLICATE-LET",
                            f"Variable '<var>{var_name}</var>' is re-declared with 'Let'. Use 'Set <var>{var_name}</var> to' for reassignments, or rename if a distinct variable was intended.",
                            line
                        ))
                    declared_vars.add(var_name)

                    if list_depth <= 1:
                        outer_declared_vars.add(var_name)
                    else:
                        if var_name not in outer_declared_vars:
                            branch_declared_vars[var_name] = line_no

                    if not is_ignored:
                        let_declared_vars[var_name] = line_no

                    # Track potential dead initialization: Let <var>x</var> be null
                    if re.search(rf'\bLet\s+<var>{var_name}</var>\s+be\s+null\b', line):
                        prev_line_dead_init = (line_no, var_name)
                    else:
                        prev_line_dead_init = None

            # Match: "Set <var>x</var> to"
            set_matches = re.finditer(r'\bSet\s+<var>(\w+)</var>\s+to\b', line)
            for m in set_matches:
                var_name = m.group(1)
                if var_name not in declared_vars:
                    self.issues.append(AlgorithmIssue(
                        filename, line_no, "ALGO-UNDECLARED-SET",
                        f"Variable '<var>{var_name}</var>' is mutated with 'Set' before being declared with 'Let'. Every variable must first be introduced via 'Let <var>{var_name}</var> be'.",
                        line
                    ))
                    declared_vars.add(var_name)

            # Check: Outer scope referencing branch-scoped variable
            if list_depth <= 1:
                for b_var, b_decl_line in list(branch_declared_vars.items()):
                    if b_var not in outer_declared_vars and b_decl_line < line_no:
                        if re.search(rf'\b<var>{b_var}</var>\b', line) and not re.search(r'\bLet\s+', line):
                            self.issues.append(AlgorithmIssue(
                                filename, line_no, "ALGO-UNBOUND-VAR-OUTER-SCOPE",
                                f"Variable '<var>{b_var}</var>' was declared with 'Let' inside a conditional branch at line {b_decl_line}, but is referenced at outer scope without being declared in the outer scope. It will be unbound on alternative execution paths. Initialize with 'Let <var>{b_var}</var> be null' in outer scope before branching.",
                                line
                            ))
                            del branch_declared_vars[b_var]

            # --- Rule 5: Dead initializations ---
            if prev_line_dead_init:
                dead_line, dead_var = prev_line_dead_init
                if idx < len(lines) - 1 and re.search(r'If\s+.*?:', line):
                    next_chunk = "\n".join(lines[idx:min(idx + 10, len(lines))])
                    if next_chunk.count(f'Set <var>{dead_var}</var> to') >= 2 and 'Otherwise' in next_chunk:
                        self.issues.append(AlgorithmIssue(
                            filename, dead_line, "ALGO-DEAD-INIT",
                            f"Dead initialization of '<var>{dead_var}</var>' to null immediately before an If/Otherwise block where all branches set its value. Declare without null or assign directly in branches.",
                            line
                        ))
                prev_line_dead_init = None

            # Terminal punctuation check for leaf steps (<li><p>...</p></li>)
            leaf_step_match = re.search(r'<li>\s*<p>(.*?)</p>\s*</li>', line)
            if leaf_step_match:
                inner_text = leaf_step_match.group(1)
                clean_text = re.sub(r'<[^>]+>', '', inner_text).strip()
                if clean_text and not clean_text.endswith(('.', ':', '?', '!')):
                    self.issues.append(AlgorithmIssue(
                        filename, line_no, "ALGO-STEP-PUNCTUATION",
                        "Algorithm step is missing terminal punctuation (expected '.' or ':').",
                        line
                    ))

            list_depth -= ol_closes

        # --- Check: Unused Variables ---
        for var_name, decl_line in let_declared_vars.items():
            occurrences = len(re.findall(rf'<var(?:\s+[^>]*)?>\s*{re.escape(var_name)}\s*</var>', block_text))
            if occurrences <= 1:
                self.issues.append(AlgorithmIssue(
                    filename, decl_line, "ALGO-UNUSED-VAR",
                    f"Variable '<var>{var_name}</var>' is declared with 'Let' but never referenced again in this algorithm. Remove it if unneeded, or mark with '<var ignore>{var_name}</var>' if intentionally unused.",
                    f"Let <var>{var_name}</var> be..."
                ))

    def analyze_file(self, filepath: Path) -> List[AlgorithmIssue]:
        content = filepath.read_text(encoding='utf-8', errors='replace')

        # Check global file-level rules (like namespace casing, formatting)
        self.check_formatting_and_markup(str(filepath), content)

        # Check algorithm blocks
        algos = self.extract_algorithms(content)
        for line_no, block_text in algos:
            self.check_algorithm_block(str(filepath), line_no, block_text)

        return self.issues


def main():
    parser = argparse.ArgumentParser(description="Lint algorithm blocks in WHATWG HTML specifications.")
    parser.add_argument("files", nargs="+", type=Path, help="HTML source files to inspect")
    parser.add_argument("--fail-on-issue", action="store_true", default=True, help="Exit with non-zero status if issues are found")
    args = parser.parse_args()

    analyzer = AlgorithmAnalyzer()
    total_issues = 0

    for f in args.files:
        if not f.is_file():
            continue
        file_issues = analyzer.analyze_file(f)
        total_issues += len(file_issues)

    if total_issues > 0:
        print(f"Found {total_issues} Algorithm issue(s):")
        for issue in analyzer.issues:
            print(f"  {issue}")
        if args.fail_on_issue:
            sys.exit(1)
    else:
        print("Algorithm Analyzer: All checks passed. No issues found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
